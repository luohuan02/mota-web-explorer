#!/usr/bin/env python3
"""PreToolUse hook: block multi-line python -c, suggest tmp/tmp.py instead."""
import json
import sys
import re

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = data.get("tool_input", {}).get("command", "")
    if not re.match(r'^python\s+-c\s+', command):
        return
    if "\n" in command:
        print(json.dumps({
            "decision": "block",
            "reason": "Multi-line python -c detected. Write the script to tmp/tmp.py and run `python tmp/tmp.py` instead. This avoids permission prompts for multi-line shell commands."
        }))
        sys.exit(0)

if __name__ == "__main__":
    main()
