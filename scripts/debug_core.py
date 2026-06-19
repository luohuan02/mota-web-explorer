
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
        [agent, "--cdp", "9222", "eval", js],
        capture_output=True, text=True,
        shell=True, encoding='utf-8', errors='ignore',
        timeout=15
    )
    try:
        return json.loads(result.stdout.strip())
    except:
        return result.stdout.strip()


print("[1] core.status keys:")
print(run("Object.keys(core.status || {})"))
print()

print("[2] core.status.floorId:")
print(run("core.status.floorId || 'none'"))
print()

print("[3] core.status.hero:")
print(run("typeof core.status.hero"))
print()

print("[4] core.status.hero keys (if exists):")
print(run("core.status.hero ? Object.keys(core.status.hero) : 'no hero'"))
print()

print("[5] core.status.maps keys:")
print(run("core.status.maps ? Object.keys(core.status.maps) : 'no maps'"))
