#!/usr/bin/env python3
"""PreToolUse hook: block Bash commands containing Unicode whitespace or
invisible characters (BOM U+FEFF, NO-BREAK SPACE U+00A0, IDEOGRAPHIC SPACE
U+3000, ZERO WIDTH SPACE U+200B / joiners, LINE/PARAGRAPH SEPARATOR, etc.).

These are almost always mistakes -- a literal BOM copied out of a file, a
non-breaking space pasted from a web page, a zero-width char from an editor --
and they break shell commands in subtle, hard-to-spot ways. Use \\uXXXX escapes
inside code instead of the literal character (e.g. /^\\uFEFF/ not /^<BOM>/), or
retype the command with plain ASCII spaces.

ASCII space/tab/newline (0x20, 0x09, 0x0A, 0x0D, 0x0B, 0x0C) are allowed.
"""
import json
import sys

# ASCII whitespace that is legitimate in shell commands.
_OK_ASCII = {0x20, 0x09, 0x0A, 0x0D, 0x0B, 0x0C}

# Codepoint ranges that are Unicode whitespace or invisible/zero-width and should
# never appear literally in a Bash command.
_BAD_RANGES = [
    (0x00A0, 0x00A0),  # NO-BREAK SPACE
    (0x1680, 0x1680),  # OGHAM SPACE MARK
    (0x180E, 0x180E),  # MONGOLIAN VOWEL SEPARATOR
    (0x2000, 0x200F),  # EN QUAD .. HAIR SPACE + ZERO WIDTH SPACE / joiners / marks
    (0x2028, 0x2029),  # LINE SEPARATOR / PARAGRAPH SEPARATOR
    (0x202F, 0x202F),  # NARROW NO-BREAK SPACE
    (0x205F, 0x205F),  # MEDIUM MATHEMATICAL SPACE
    (0x2060, 0x2060),  # WORD JOINER
    (0x3000, 0x3000),  # IDEOGRAPHIC SPACE
    (0xFEFF, 0xFEFF),  # ZERO WIDTH NO-BREAK SPACE / BOM
]


def _is_bad(cp: int) -> bool:
    if cp in _OK_ASCII:
        return False
    for lo, hi in _BAD_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def find_bad_chars(command: str):
    found = {}
    for ch in command:
        cp = ord(ch)
        if _is_bad(cp):
            name = f"U+{cp:04X}"
            found[name] = found.get(name, 0) + 1
    return found


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    command = data.get("tool_input", {}).get("command", "")
    if not command:
        return
    bad = find_bad_chars(command)
    if not bad:
        return
    parts = ", ".join(
        f"{name} x{cnt}" if cnt > 1 else name for name, cnt in sorted(bad.items())
    )
    print(json.dumps({
        "decision": "block",
        "reason": (
            f"Bash command contains Unicode whitespace/invisible characters ({parts}). "
            "These are usually copied by mistake (a literal BOM, a non-breaking space, a "
            "zero-width char) and break shell commands. Replace the literal character with "
            "a \\uXXXX escape in code (e.g. /^\\uFEFF/ instead of a literal BOM), or retype "
            "the command with plain ASCII spaces."
        )
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
