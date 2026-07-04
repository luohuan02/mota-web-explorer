#!/usr/bin/env python3
"""PreToolUse hook: block "expansion obfuscation" in Bash commands.

Pattern: a heredoc/script body that embeds `${...}` shell-style expansion
alongside quote characters. This is exactly the "brace with quote character
(expansion obfuscation)" shape the sandbox flags: a `<<` heredoc whose body
mixes `${...}` and quotes is ambiguous (is the `${...}` shell expansion on an
unquoted heredoc, literal text on a quoted heredoc, or a JS template literal?)
and is treated as hiding shell expansion.

When matched, deny and route the agent to write the script to a file with the
Write tool (e.g. tmp/tmp.js), then run it with Bash — never inline it via
heredoc. Legit single-line shell expansions like `echo "${HOME}"` are NOT
heredocs, so they pass.
"""
import json
import re
import sys

# A heredoc operator anywhere in the command: `<<` or `<<-`.
HEREDOC = re.compile(r"<<-?")


def is_obfuscation(command: str) -> bool:
    if not HEREDOC.search(command):
        return False
    if "${" not in command:
        return False
    # "brace with quote character": a quote next to the brace expansion.
    if "'" not in command and '"' not in command:
        return False
    return True


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return
    if not is_obfuscation(command):
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked: command embeds ${...} expansion inside a heredoc/script "
                "body mixed with quotes (brace-with-quote / expansion obfuscation "
                "pattern). Do NOT inline scripts via heredoc. Use the Write tool to "
                "write the script to a file (e.g. tmp/tmp.js), then run that file "
                "with Bash."
            ),
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
