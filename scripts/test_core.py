
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

#!/usr/bin/env python3
import json
import subprocess

agent = r"D:\nvm4w\nodejs\agent-browser.cmd"


def run(js):
    result = subprocess.run(
        [agent, "--auto-connect", "eval", js],
        capture_output=True, text=True,
        shell=True, encoding='utf-8', errors='ignore',
        timeout=10
    )
    print("STDOUT:", repr(result.stdout))
    print("STDERR:", repr(result.stderr))
    try:
        return json.loads(result.stdout.strip())
    except:
        return result.stdout.strip()


print("Test 1: typeof window.core")
print(run("typeof window.core"))
print()

print("Test 2: typeof core")
print(run("typeof core"))
print()

print("Test 3: window.location.href")
print(run("window.location.href"))
print()

print("Test 4: document.title")
print(run("document.title"))
