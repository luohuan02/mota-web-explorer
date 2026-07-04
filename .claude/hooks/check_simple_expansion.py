#!/usr/bin/env python3
"""PreToolUse hook: block shell parameter expansion (simple_expansion) in Bash.

The Claude Code bash sandbox parses commands with tree-sitter-bash. A `$VAR` /
`${VAR}` parameter expansion produces a `simple_expansion` node the sandbox
cannot statically resolve, so it falls back to a manual-approval prompt with the
message "Contains simple_expansion". This hook denies outright and tells the
agent how to rewrite the command without shell variable expansion -- consistent
with check_cd_redirection.py converting the built-in cd prompt into a hard deny.

Blocked (shell-expanded $, i.e. outside SINGLE quotes):
  - `echo $VAR`, `cat ${HOME}/x`, `ls $1`, `echo $@`, `echo $?`, `echo $$`
  - `for p in ...; do [ -f "$p" ] ...`   ($p in DOUBLE quotes is still expanded)
  - `"$p"`, `"$HOME"`   (double quotes do NOT suppress expansion)

Allowed:
  - `awk '{print $1}'`   ($1 inside SINGLE quotes is literal to awk, not the shell)
  - `node -e "console.log('x')"`   (no $ at all)
  - `echo "$(date)"`, `git log $(rev)`   (`$(...)` is command_substitution, a
    DIFFERENT tree-sitter node type -- not simple_expansion -- and not blocked here)
  - `echo $((1+2))`   (arithmetic_expansion, also not blocked here)

Remediation: inline the literal value with an absolute path
(e.g. `cat D:/claude/mota-web-explorer/x`), or write the logic to a file with
the Write tool (e.g. tmp/tmp.py) and run `python tmp/tmp.py`. Avoid `$VAR`-driven
shell loops; use a Python/Node script instead.
"""
import json
import re
import sys

# Parameter / "simple" expansion: $VAR, ${VAR}, $1, $@, $?, $$, etc.
# Excludes $( and $(( (command / arithmetic substitution -- different node types).
SIMPLE_EXPANSION = re.compile(r"\$(?!\()\{|\$[A-Za-z_0-9@#?$*!]")


def _strip_single_quoted(s: str) -> str:
    """Return s with single-quoted regions blanked out.

    Inside '...' the shell does NOT expand $, so $VAR there is literal (e.g.
    awk '{print $1}'). Double-quoted regions are preserved verbatim -- the shell
    DOES expand $VAR inside "...", and that must still be caught. Single quotes
    inside double quotes are literal. Backslash escapes outside single quotes
    are honored (the next char is kept literally).
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


def has_simple_expansion(command: str) -> bool:
    return bool(SIMPLE_EXPANSION.search(_strip_single_quoted(command)))


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return
    if not has_simple_expansion(command):
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked: command contains shell parameter expansion (simple_expansion: "
                "$VAR / ${VAR} / $1 / $@ / $? ...). The sandbox cannot statically resolve "
                "the expanded value, which makes the actual command unpredictable and "
                "triggers a manual-approval prompt. Remediation: inline the literal value "
                "with an absolute path (e.g. `cat D:/claude/mota-web-explorer/x`), or write "
                "the logic to a file with the Write tool (e.g. tmp/tmp.py) and run "
                "`python tmp/tmp.py`. $VAR inside SINGLE quotes (e.g. `awk '{print $1}'`) "
                "is literal and allowed; only shell-expanded $VAR is blocked. Command "
                "substitution `$(...)` and arithmetic `$((...))` are different categories "
                "and not blocked by this hook."
            ),
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
