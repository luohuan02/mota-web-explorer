#!/usr/bin/env python3
"""PreToolUse hook: guard `cd` usage in Bash commands.

Two checks (either triggers a deny):

1. Compound `cd` + output redirection (`>`, `>>`, `|`, `2>`, `&>`, `1>`).
   `cd X && cmd > out` / `cd X; cmd | head` can obscure which directory the
   redirection actually targets (path-resolution-bypass risk). The built-in
   check only raises a manual-approval prompt; this hook denies outright.

2. `cd` with two or more arguments, e.g. `cd /d D:/path`.
   Git Bash runs POSIX sh, where `cd` takes exactly one path and does NOT
   understand the Windows `cmd.exe` `/d` drive-change flag. `cd /d D:/path`
   is parsed as `cd` with two args (`/d`, `D:/path`) and errors with
   "cd: too many arguments". This hook catches it pre-execution.

Allowed:
  - Standalone `cd X` (single path, no redirection, no compound separator).
  - `cd "D:/my path"` (single quoted path with spaces).
  - `cd /d/claude/...` (single POSIX path; the `/d` here is part of the path,
    not a flag, because there is no space).
  - `cd X && ls` (compound but no redirection, single arg).
  - `python D:/abs/path/script.py > out` (redirection but no `cd`).

Blocked:
  - `cd /d D:/path`, `cd a b`, `cd /d "D:/x"`, etc. (2+ args).
  - `cd X && cmd > out`, `cd X; cmd 2>/dev/null`, `cd X && cmd | head`, etc.
"""
import json
import re
import sys

# `cd` as a command token (preceded by start/space/separator, followed by space).
CD = re.compile(r"(^|[\s;&|])cd\s+")
# Any output redirection operator. `|` is included as a pipe redirect.
REDIR = re.compile(r">>>?|2>|&>|1>|\|")
# A compound separator means cd and the redirect live in different arms.
SEP = re.compile(r"&&|\|\||;|\|")
# Separators used to bound the cd argument segment.
SEG_SEP = re.compile(r"&&|\|\||;|\|")


def _tokenize(segment: str):
    """Quote-aware whitespace tokenizer (no backslash escaping, so Windows
    backslash paths stay intact). Returns the list of non-empty tokens."""
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


def cd_arg_count_violation(command: str):
    """Return the offending arg-list string if some `cd` has 2+ args, else None."""
    for m in CD.finditer(command):
        rest = command[m.end():]
        segment = SEG_SEP.split(rest, maxsplit=1)[0]
        tokens = _tokenize(segment)
        # Drop a leading `--` (end-of-options marker) before counting.
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]
        if len(tokens) >= 2:
            return segment.strip()
    return None


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command or not CD.search(command):
        return

    # Check 2: multi-argument cd (e.g. `cd /d D:/path`).
    offending = cd_arg_count_violation(command)
    if offending is not None:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Blocked: `cd` with multiple arguments (`cd %s`). Git Bash "
                    "(POSIX sh) `cd` takes a single path and does NOT understand "
                    "the Windows `cd /d` drive flag -- this errors with "
                    "'cd: too many arguments'. Remediation: use a single quoted "
                    "path, e.g. `cd \"D:/claude/mota-web-explorer\"` or "
                    "`cd /d/claude/mota-web-explorer`; or skip `cd` entirely and "
                    "use absolute paths (e.g. `python D:/claude/mota-web-explorer/tmp/tmp.py`)."
                    % offending
                ),
            }
        }))
        sys.exit(0)

    # Check 1: cd + output redirection in a compound command.
    if REDIR.search(command) and SEP.search(command):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Blocked: compound command mixes `cd` with output redirection "
                    "(> >> | 2> &>), which can obscure the redirection's target directory "
                    "(path-resolution-bypass risk). Remediation: drop `cd` and use absolute "
                    "paths (e.g. `python D:/claude/mota-web-explorer/scripts/xxx.py`), or run "
                    "`cd X` as its own standalone command first (cwd persists across Bash "
                    "calls), then run the redirected command in the next call."
                ),
            }
        }))
        sys.exit(0)


if __name__ == "__main__":
    main()
