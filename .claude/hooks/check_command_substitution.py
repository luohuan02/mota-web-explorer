#!/usr/bin/env python3
"""PreToolUse hook: block shell command substitution $(...) in Bash commands.

The Claude Code bash sandbox cannot statically resolve the VALUE of a $(...)
command substitution (e.g. `agent-browser eval "$(cat script.js)"`), because it
does not know what is inside the file being cat'd. This makes the actual command
unpredictable and triggers a manual-approval "Contains command_substitution"
prompt. This matches project guidance (see memory avoid_unanalyzable_shell_syntax.md):
forbid $(cat)/|| fallback chains; use a `node tmp/x.js` script file or inline the
agent-browser eval argument directly.

Blocked (the $( is run by the shell, i.e. OUTSIDE single quotes):
  - `agent-browser eval "$(cat x.js)"`   (file content as argument)
  - `echo "$(date)"`, `git log $(rev)`   (any $(...) substitution)
  - `x="$(cat file)"; cmd "$x"`          (assignment from substitution)

Allowed:
  - `node tmp/tmp.js`                    (run a script file directly -- the fix)
  - `agent-browser eval "(function(){...})()"`  (inline the eval body literally)
  - `echo $((1+2))`                      (arithmetic_expansion, different node)
  - `awk '{print $1}'`                   ($1 in SINGLE quotes is literal to awk)

Remediation: write the logic to a file with the Write tool (e.g. tmp/tmp.js)
and run `node tmp/tmp.js`, OR inline the literal argument directly without
$(...) wrapping -- never `$(cat file)`.
"""
import json
import re
import sys

# Command substitution: $( ... ) -- but NOT $(( ... )) arithmetic expansion.
COMMAND_SUB = re.compile(r"\$\((?!\()")


def _strip_single_quoted(s: str) -> str:
    """Return s with single-quoted regions blanked out.

    Inside '...' the shell does NOT run $(...), so $(...) there is literal
    (e.g. awk '{print $(1)}'). Double-quoted regions are preserved verbatim --
    the shell DOES run $(...) inside "...", and that must still be caught.
    Single quotes inside double quotes are literal. Backslash escapes outside
    single quotes are honored (the next char is kept literally).
    """
    out = []
    i = 0
    in_squote = False
    in_dquote = False
    while i < len(s):
        ch = s[i]
        if in_squote:
            if ch == "'":
                in_squote = False
            out.append(" ")
            i += 1
        elif in_dquote:
            if ch == "\\" and i + 1 < len(s):
                out.append(ch)
                out.append(s[i + 1])
                i += 2
            elif ch == '"':
                in_dquote = False
                out.append(ch)
                i += 1
            else:
                out.append(ch)
                i += 1
        elif ch == "'":
            in_squote = True
            out.append(" ")
            i += 1
        elif ch == '"':
            in_dquote = True
            out.append(ch)
            i += 1
        elif ch == "\\" and i + 1 < len(s):
            out.append(s[i + 1])
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def has_command_sub(command: str) -> bool:
    return bool(COMMAND_SUB.search(_strip_single_quoted(command)))


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return
    if not has_command_sub(command):
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked: command contains shell command substitution $(...) "
                "(e.g. `$(cat file)`, `$(date)`). The sandbox cannot statically "
                "resolve the substituted value, which makes the actual command "
                "unpredictable and triggers a manual-approval prompt. Remediation: "
                "write the logic to a file with the Write tool (e.g. tmp/tmp.js) "
                "and run `node tmp/tmp.js`, OR inline the literal argument directly "
                "(e.g. `agent-browser eval \"(function(){...})()\"` with the JS "
                "body written out, not `$(cat file)`). Arithmetic $((...)) and "
                "$( or $VAR inside SINGLE quotes are different and allowed."
            ),
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
