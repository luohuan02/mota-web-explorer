#!/usr/bin/env python3
"""PreToolUse hook (Bash matcher): consolidated command-shape guard.

Merges 7 former hooks into one file, each as a check function returning a deny
reason or None. First non-None wins. Checks (in order):

  1. check_unicode_whitespace     - invisible/Unicode whitespace chars
  2. check_multiline_python_c     - multi-line `python -c`
  3. check_heredoc_expansion      - `${...}` inside heredoc + quotes
  4. check_cd_redirection         - `cd` with 2+ args, or `cd` + redirection
  5. check_multiple_redirects     - 2+ file-redirects to same fd in one segment
  6. check_simple_expansion       - shell `$VAR` / `${VAR}` expansion
  7. check_command_substitution   - `$(...)` command substitution
  8. check_dedicated_tool_commands- sed/head/tail/find/grep (use dedicated tools)
  9. check_background_operator    - bare `&` background operator (defers execution
                                    past approval-time safety checks; use the Bash
                                    tool's run_in_background instead)

Why one file + $CLAUDE_PROJECT_DIR: the former 7 entries in settings.local.json
each ran `python .claude/hooks/check_xxx.py` with a RELATIVE path. If the Bash
cwd ever drifted off the project root (e.g. `cd outputs/results && ...`), every
hook failed to find its script (Python exit 2) and Claude Code blocked ALL Bash
calls -- including `pwd`/`cd` to recover. One file removes the 7-file clutter;
`$CLAUDE_PROJECT_DIR/.claude/hooks/check_bash.py` (absolute) removes the
cwd-drift footgun entirely.
"""
import json
import re
import sys


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------

def _strip_single_quoted(s: str) -> str:
    """Blank out single-quoted regions (shell does NOT expand $/$( there).
    Double-quoted regions kept verbatim (shell DOES expand there). Backslash
    escapes outside single quotes are honored (next char kept literally)."""
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


# ---------------------------------------------------------------------------
# check 1: Unicode whitespace / invisible characters
# ---------------------------------------------------------------------------

_OK_ASCII = {0x20, 0x09, 0x0A, 0x0D, 0x0B, 0x0C}
_BAD_RANGES = [
    (0x00A0, 0x00A0),  # NO-BREAK SPACE
    (0x1680, 0x1680),  # OGHAM SPACE MARK
    (0x180E, 0x180E),  # MONGOLIAN VOWEL SEPARATOR
    (0x2000, 0x200F),  # EN QUAD .. HAIR SPACE + ZERO WIDTH SPACE / joiners / marks
    (0x2028, 0x2029),  # LINE / PARAGRAPH SEPARATOR
    (0x202F, 0x202F),  # NARROW NO-BREAK SPACE
    (0x205F, 0x205F),  # MEDIUM MATHEMATICAL SPACE
    (0x2060, 0x2060),  # WORD JOINER
    (0x3000, 0x3000),  # IDEOGRAPHIC SPACE
    (0xFEFF, 0xFEFF),  # ZERO WIDTH NO-BREAK SPACE / BOM
]


def _is_bad_cp(cp: int) -> bool:
    if cp in _OK_ASCII:
        return False
    return any(lo <= cp <= hi for lo, hi in _BAD_RANGES)


def check_unicode_whitespace(command: str):
    found = {}
    for ch in command:
        cp = ord(ch)
        if _is_bad_cp(cp):
            name = f"U+{cp:04X}"
            found[name] = found.get(name, 0) + 1
    if not found:
        return None
    parts = ", ".join(f"{n} x{c}" if c > 1 else n for n, c in sorted(found.items()))
    return (
        f"Bash command contains Unicode whitespace/invisible characters ({parts}). "
        "These are usually copied by mistake (a literal BOM, a non-breaking space, a "
        "zero-width char) and break shell commands. Replace the literal character with "
        "a \\uXXXX escape in code (e.g. /^\\uFEFF/ instead of a literal BOM), or retype "
        "the command with plain ASCII spaces."
    )


# ---------------------------------------------------------------------------
# check 2: multi-line `python -c`
# ---------------------------------------------------------------------------

_PY = r"python[\d.]*\.?(?:exe)?"
_INVOCATION = re.compile(_PY + r"\s+(?:-[A-Za-z]+\s+)*-c\s+")


def _quoted_body_has_newline(command: str, start: int) -> bool:
    if start >= len(command):
        return False
    q = command[start]
    if q not in ('"', "'"):
        return False
    close = command.find(q, start + 1)
    body = command[start + 1:] if close == -1 else command[start + 1:close]
    return "\n" in body


def _unquoted_body_has_newline(command: str, start: int) -> bool:
    rest = command[start:]
    seg = re.split(r"(?<!\\)(?:&&|\|\||;|\|)", rest, maxsplit=1)[0]
    return "\n" in seg


_MULTILINE_PY_REASON = (
    "Multi-line `python -c` detected. Write the script to tmp/tmp.py and run "
    "`python tmp/tmp.py` instead (per CLAUDE.md), to avoid the multi-line shell "
    "permission prompt."
)


def check_multiline_python_c(command: str):
    for m in _INVOCATION.finditer(command):
        body_start = m.end()
        if body_start >= len(command):
            continue
        ch = command[body_start]
        if ch in ('"', "'"):
            if _quoted_body_has_newline(command, body_start):
                return _MULTILINE_PY_REASON
        else:
            if _unquoted_body_has_newline(command, body_start):
                return _MULTILINE_PY_REASON
    return None


# ---------------------------------------------------------------------------
# check 2b: python fed by heredoc (python - <<EOF / python3 - <<EOF ...)
# ---------------------------------------------------------------------------

_PY_HEREDOC = re.compile(_PY + r"[^\n|;&]*<<-?")


def check_python_heredoc(command: str):
    if _PY_HEREDOC.search(command):
        return (
            "Blocked: `python - <<EOF` (inline python via heredoc) detected. "
            "Per CLAUDE.md, python temp scripts must go to a file: use the Write "
            "tool to write the script to tmp/tmp.py, then run `python tmp/tmp.py`. "
            "Heredoc-inline python bypasses the multi-line permission prompt but "
            "produces unreviewable one-shot scripts that vanish from the repo."
        )
    return None


# ---------------------------------------------------------------------------
# check 3: heredoc + ${...} + quotes (expansion obfuscation)
# ---------------------------------------------------------------------------

_HEREDOC = re.compile(r"<<-?")


def _heredoc_bodies(command: str):
    """Yield the body text of each heredoc (from <<marker to the next line that
    equals the marker). Best-effort: heredocs nested in compounds are rare here."""
    for m in _HEREDOC.finditer(command):
        rest = command[m.end():]
        marker = rest.split(None, 1)[0] if rest.split() else ""
        if not marker:
            continue
        body_start = rest.find("\n")
        if body_start == -1:
            continue
        body = rest[body_start + 1:]
        end = -1
        for line in body.split("\n"):
            if line.strip() == marker:
                end = body.find(line)
                break
        yield body if end == -1 else body[:end]


def check_heredoc_expansion(command: str):
    if not _HEREDOC.search(command):
        return None
    if "${" in command and ("'" in command or '"' in command):
        return (
            "Blocked: command embeds ${...} expansion inside a heredoc/script body mixed "
            "with quotes (brace-with-quote / expansion obfuscation pattern). Do NOT inline "
            "scripts via heredoc. Use the Write tool to write the script to a file (e.g. "
            "tmp/tmp.js), then run that file with Bash."
        )
    # 2026-09-06: f-string 式花括号 + 引号同样触发沙箱人工审批
    # ("Contains brace with quote character"); 无 $ 也拦, 提示改走 Write 工具。
    for body in _heredoc_bodies(command):
        if "{" in body and ("'" in body or '"' in body):
            return (
                "Blocked: heredoc script body mixes brace blocks with quote "
                "characters (brace-with-quote pattern, triggers sandbox manual "
                "approval). Do NOT inline scripts via heredoc -- even without ${...}. "
                "Use the Write tool to write the script to a file (e.g. tmp/tmp.py or "
                "tmp/tmp.js), then run that file with Bash."
            )
    return None


# ---------------------------------------------------------------------------
# check 4: cd misuse (2+ args, or cd + output redirection)
# ---------------------------------------------------------------------------

_CD = re.compile(r"(^|[\s;&|])cd\s+")
_REDIR = re.compile(r">>>?|2>|&>|1>|\|")
_SEP = re.compile(r"&&|\|\||;|\|")
_SEG_SEP = re.compile(r"&&|\|\||;|\|")


def check_cd_redirection(command: str):
    if not _CD.search(command):
        return None
    # 2+ arg cd (e.g. `cd /d D:/path`).
    for m in _CD.finditer(command):
        rest = command[m.end():]
        segment = _SEG_SEP.split(rest, maxsplit=1)[0]
        tokens = _tokenize(segment)
        if tokens and tokens[0] == "--":
            tokens = tokens[1:]
        if len(tokens) >= 2:
            return (
                "原因：你写了 `cd %s`。Git Bash 是 POSIX sh，`cd` 只接受单个路径，"
                "不认 Windows 的 `/d` 盘符，所以 `/d` 被当成第一个路径参数，"
                "`cd` 实际收到 2 个参数 (`/d` 和路径)，执行报 'cd: too many arguments' 失败。"
                "建议：脚本已自带 chdir/sys.path 时直接用绝对路径 "
                "`python D:/abs/path/script.py`（不要 cd）；"
                "或改单路径 `cd \"D:/claude/mota-web-explorer\"` / "
                "POSIX 路径 `cd /d/claude/mota-web-explorer`。" % segment.strip()
            )
    # cd + output redirection in a compound command.
    if _REDIR.search(command) and _SEP.search(command):
        return (
            "原因：复合命令把 `cd` 和输出重定向 (> >> | 2> &>) 混在一起，"
            "重定向目标目录取决于 `cd` 是否生效，沙箱无法静态解析实际写入路径"
            "（路径解析绕过风险）。建议：去掉 `cd` 用绝对路径 "
            "`python D:/abs/path/script.py`；或先单独执行 `cd X`（cwd 跨 Bash "
            "调用保留），下一句再跑带重定向的命令。"
        )
    return None


# ---------------------------------------------------------------------------
# check 5: multiple file-redirects to the same fd in one segment
# ---------------------------------------------------------------------------

# File-target redirect operators. Excludes dup forms `2>&1` / `1>&2` / `>&1`
# (an `&` follows the operator, so the negative lookahead fails). Matches
# `>`, `>>`, `1>`, `1>>`, `2>`, `2>>`, `&>`, `&>>` followed by a non-`&`
# target (file path / /dev/null). The char BEFORE the operator must be a
# whitespace / `(`/`;`/start — 否则 JS 的 `>=`、比较链等会被误判 (2026-09-06:
# agent-browser eval 的 JS 箭头/比较误触发)。
_FILE_REDIR = re.compile(r"(?<![=\w>&|<+\-*/^(])(?:(?:[12]|&)?>>?)(?!\s*&)")


def _redir_fd(op: str) -> int:
    """Classify a redirect operator's fd: 1=stdout (> >> 1> 1>>), 2=stderr
    (2> 2>>), 0=both (&> &>>)."""
    if op.startswith("&"):
        return 0
    if op.startswith("2"):
        return 2
    return 1


def check_multiple_redirects(command: str):
    """Deny a single command segment that redirects the same fd to 2+ files,
    e.g. `node x.js 2>/dev/null 195 205 2>/dev/null`. The bash parser rejects
    this as 'Redirect has multiple targets - post-redirect args swallowed':
    args sandwiched between the two redirects (here 195 205) get misread as
    redirect targets and the whole segment fails to parse. Legitimate
    `> out 2> err` (different fds) and `> out 2>&1` (dup, not a file target)
    are NOT blocked."""
    stripped = _strip_single_quoted(command)
    for seg in re.split(r"&&|\|\||;|\|", stripped):
        fds: dict[int, int] = {}
        for m in _FILE_REDIR.finditer(seg):
            fd = _redir_fd(m.group(0))
            fds[fd] = fds.get(fd, 0) + 1
        if fds and max(fds.values()) >= 2:
            return (
                "原因：单个命令段里对同一个文件描述符写了 2 个及以上文件重定向 "
                "(如 `2>/dev/null ... 2>/dev/null` 或 `> a > b`)。bash 解析器会报 "
                "'Redirect has multiple targets - post-redirect args swallowed'："
                "夹在两个重定向之间的参数 (如 195 205) 被误当成重定向目标，整段"
                "无法解析、触发授权拦截。修改方式：每个命令段每个 fd 只保留一个"
                "重定向并放到末尾；删掉多余的 `2>/dev/null`；复合命令 (`;`/`&&`/`|`)"
                "拆成多个独立 Bash 调用，或用 Write 写到 tmp/tmp.js 后 "
                "`node tmp/tmp.js` 一次跑完。"
            )
    return None


# ---------------------------------------------------------------------------
# check 6: simple expansion $VAR / ${VAR}
# ---------------------------------------------------------------------------

_SIMPLE_EXPANSION = re.compile(r"\$(?!\()\{|\$[A-Za-z_0-9@#?$*!]")


def check_simple_expansion(command: str):
    if _SIMPLE_EXPANSION.search(_strip_single_quoted(command)):
        return (
            "Blocked: command contains shell parameter expansion (simple_expansion: "
            "$VAR / ${VAR} / $1 / $@ / $? ...). The sandbox cannot statically resolve "
            "the expanded value, which makes the actual command unpredictable and "
            "triggers a manual-approval prompt. Remediation: inline the literal value "
            "with an absolute path (e.g. `cat D:/claude/mota-web-explorer/x`), or write "
            "the logic to a file with the Write tool (e.g. tmp/tmp.py) and run "
            "`python tmp/tmp.py`. $VAR inside SINGLE quotes (e.g. `awk '{print $1}'`) "
            "is literal and allowed; only shell-expanded $VAR is blocked. Command "
            "substitution `$(...)` and arithmetic `$((...))` are different categories "
            "and not blocked by this check."
        )
    return None


# ---------------------------------------------------------------------------
# check 7: command substitution $(...)
# ---------------------------------------------------------------------------

_COMMAND_SUB = re.compile(r"\$\((?!\()")


def check_command_substitution(command: str):
    if _COMMAND_SUB.search(_strip_single_quoted(command)):
        return (
            "Blocked: command contains shell command substitution $(...) "
            "(e.g. `$(cat file)`, `$(date)`). The sandbox cannot statically resolve "
            "the substituted value, which makes the actual command unpredictable and "
            "triggers a manual-approval prompt. Remediation: write the logic to a file "
            "with the Write tool (e.g. tmp/tmp.js) and run `node tmp/tmp.js`, OR inline "
            "the literal argument directly without $(...) wrapping -- never `$(cat file)`. "
            "Arithmetic $((...)) and $( or $VAR inside SINGLE quotes are different and allowed."
        )
    return None


# ---------------------------------------------------------------------------
# check 8: dedicated-tool duplicates (sed/head/tail/find/grep)
# ---------------------------------------------------------------------------

_BLOCKED = {"sed", "head", "tail", "find", "grep"}
_BLOCKED_ALL = _BLOCKED | {f"{c}.exe" for c in _BLOCKED}
_CMD_SEP = re.compile(r"\|\||&&|\||;")
_HINT = {
    "sed": "Read (offset/limit to print lines) or Edit (for substitutions)",
    "head": "Read (use offset/limit, or read the whole file)",
    "tail": "Read (use offset to read the end of a file)",
    "find": "Glob (e.g. pattern '**/*.py')",
    "grep": "Grep tool (pattern + glob/type filters)",
}


def check_dedicated_tool_commands(command: str):
    for seg in _CMD_SEP.split(command):
        seg = seg.strip()
        if not seg:
            continue
        tokens = _tokenize(seg)
        if not tokens:
            continue
        first = tokens[0]
        # Allow `xargs grep` (grep is an arg to xargs) and `git <subcommand>`.
        if first in ("xargs", "git"):
            continue
        if first in _BLOCKED_ALL:
            base = first[:-4] if first.endswith(".exe") else first
            return (
                "Blocked: `%s` duplicates a dedicated tool. Remediation: use the %s "
                "instead (per CLAUDE.md, avoid shell read/search commands when a "
                "dedicated tool fits). If a dedicated tool genuinely cannot do this "
                "(e.g. limiting a command's stdout), ask the user to run it or allow it."
                % (first, _HINT.get(base, "dedicated tool"))
            )
    return None


# ---------------------------------------------------------------------------
# check 9: bare `&` background operator
# ---------------------------------------------------------------------------

# Bare `&` = background operator: 前面是空白/行首, 后面是空白/结尾, 且不属于
# `&&` / `>&` / `&>` / `2>&1`。`a & b` / `cmd &` 命中; JS 位运算 `a & b` 在
# eval 表达式里理论上会误伤, 但本项目 shell eval 一律走单引号字面量
# (_strip_single_quoted 后双引号区保留), 风险可接受。
_BARE_AMP = re.compile(r"(?<![&>\w])&(?![&>\w])")


def check_background_operator(command: str):
    if _BARE_AMP.search(_strip_single_quoted(command)):
        return (
            "Blocked: bare `&` background operator detected (command defers "
            "execution past approval-time safety checks). Remediation: use the "
            "Bash tool's run_in_background=true parameter instead of `&`, or "
            "split into sequential commands."
        )
    return None


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------

_CHECKS = [
    check_unicode_whitespace,
    check_multiline_python_c,
    check_python_heredoc,
    check_heredoc_expansion,
    check_cd_redirection,
    check_multiple_redirects,
    check_simple_expansion,
    check_command_substitution,
    check_dedicated_tool_commands,
    check_background_operator,
]


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return
    for check in _CHECKS:
        reason = check(command)
        if reason:
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }))
            sys.exit(0)


if __name__ == "__main__":
    main()
