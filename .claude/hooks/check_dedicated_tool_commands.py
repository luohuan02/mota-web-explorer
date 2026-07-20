#!/usr/bin/env python3
"""PreToolUse hook: deny shell commands that duplicate dedicated tools.

CLAUDE.md says to avoid `find`, `grep`, `cat`, `head`, `tail`, `sed`, `awk`,
`echo` when a dedicated tool fits. The ones NOT already allow-listed
(`sed`, `head`, `tail`, `find`, `grep`) trigger a manual-approval prompt each
time. This hook denies them outright with a remediation hint, so the agent
switches to the dedicated tool (Read / Grep / Glob / Edit) instead of asking
for approval.

Already allow-listed and therefore NOT denied here: cat, echo, awk, tee,
`xargs grep`, `git grep` (git subcommand).

Denied (command position only -- first token of a segment split by |, ||, &&, ;):
  - sed (any form)   -> Read (offset/limit to print lines) or Edit (substitute)
  - head / tail      -> Read with offset/limit
  - find             -> Glob
  - grep (standalone)-> Grep tool

Escape hatch: if a dedicated tool genuinely cannot do the job (e.g. `head` to
limit a command's stdout), the deny reason tells the agent to ask the user.
"""
import json
import re
import sys

# Commands that duplicate dedicated tools and should be denied.
BLOCKED = {"sed", "head", "tail", "find", "grep"}
# Also catch the .exe variants on Windows git bash.
BLOCKED_ALL = BLOCKED | {f"{c}.exe" for c in BLOCKED}

# Separators that start a new command segment in a compound command.
SEP = re.compile(r"\|\||&&|\||;")

# Remediation hint per blocked command (keyed by the bare name).
HINT = {
    "sed": "Read (offset/limit to print lines) or Edit (for substitutions)",
    "head": "Read (use offset/limit, or read the whole file)",
    "tail": "Read (use offset to read the end of a file)",
    "find": "Glob (e.g. pattern '**/*.py')",
    "grep": "Grep tool (pattern + glob/type filters)",
}


def _tokenize(segment: str):
    """Quote-aware whitespace tokenizer (backslash paths stay intact)."""
    tokens = []
    cur = []
    quote = None
    for ch in segment:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            cur.append(ch)
        elif ch.isspace():
            if cur:
                tokens.append("".join(cur))
                cur = []
        else:
            cur.append(ch)
    if cur:
        tokens.append("".join(cur))
    return tokens


def _first_tokens(command: str):
    """Yield the first token of each segment of a compound command."""
    for seg in SEP.split(command):
        seg = seg.strip()
        if not seg:
            continue
        tokens = _tokenize(seg)
        if tokens:
            yield tokens


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return

    for tokens in _first_tokens(command):
        first = tokens[0]
        # Allow `xargs grep` (grep is an arg to xargs) and `git <subcommand>`.
        if first in ("xargs", "git"):
            continue
        if first in BLOCKED_ALL:
            base = first[:-4] if first.endswith(".exe") else first
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "Blocked: `%s` duplicates a dedicated tool. Remediation: "
                        "use the %s instead (per CLAUDE.md, avoid shell "
                        "read/search commands when a dedicated tool fits). If a "
                        "dedicated tool genuinely cannot do this (e.g. limiting a "
                        "command's stdout), ask the user to run it or allow it."
                        % (first, HINT.get(base, "dedicated tool"))
                    ),
                }
            }))
            sys.exit(0)


if __name__ == "__main__":
    main()
