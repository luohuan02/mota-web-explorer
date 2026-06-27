#!/usr/bin/env python3
"""PreToolUse hook: block multi-line `python -c`, suggest tmp/tmp.py instead.

The check is not anchored to the start of the command, so it still fires when
the python invocation is wrapped in a prefix such as `cd X && python -c "..."`,
`curl ... | python -c "..."`, or chained with `;` / `&&` / `|`.

A "multi-line python -c" is one whose script body contains a newline. We find
every `python<ver> -c <body>` occurrence and inspect the body:
  - if the body is quote-delimited (`"..."` / `'...'`), look for a newline
    between the opening and closing quote;
  - otherwise, look for a newline before the next shell separator.
"""
import json
import sys
import re

# python / python3 / python3.11 / python.exe ...
PY = r"python[\d.]*\.?(?:exe)?"

# python ... -c   (allow flags like -u between python and -c)
INVOCATION = re.compile(PY + r"\s+(?:-[A-Za-z]+\s+)*-c\s+")


def _quoted_body_has_newline(command: str, start: int) -> bool:
    """Body begins at `start` with a quote char. Return True if a newline sits
    inside the (first) quoted region before its closing quote."""
    if start >= len(command):
        return False
    q = command[start]
    if q not in ('"', "'"):
        return False
    close = command.find(q, start + 1)
    body = command[start + 1:] if close == -1 else command[start + 1:close]
    return "\n" in body


def _unquoted_body_has_newline(command: str, start: int) -> bool:
    """Body is unquoted; a newline before the next top-level separator counts."""
    rest = command[start:]
    seg = re.split(r"(?<!\\)(?:&&|\|\||;|\|)", rest, maxsplit=1)[0]
    return "\n" in seg


def has_multiline_python_c(command: str) -> bool:
    for m in INVOCATION.finditer(command):
        body_start = m.end()
        if body_start >= len(command):
            continue
        ch = command[body_start]
        if ch in ('"', "'"):
            if _quoted_body_has_newline(command, body_start):
                return True
        else:
            if _unquoted_body_has_newline(command, body_start):
                return True
    return False


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return
    if not has_multiline_python_c(command):
        return
    print(json.dumps({
        "decision": "block",
        "reason": "Multi-line `python -c` detected. Write the script to tmp/tmp.py and run `python tmp/tmp.py` instead (per CLAUDE.md), to avoid the multi-line shell permission prompt."
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
