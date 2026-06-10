
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
    out = result.stdout.strip()
    if out.startswith('"') and out.endswith('"'):
        out = out[1:-1]
    try:
        return json.loads(out)
    except:
        return out


print("floorId:", run("core.status.floorId"))
print("hero.loc:", run("JSON.stringify(core.status.hero.loc)"))
print("hero.hp:", run("core.status.hero.hp"))
print("hero.atk:", run("core.status.hero.atk"))
print("hero.def:", run("core.status.hero.def"))
print("tools:", run("JSON.stringify(core.status.hero.items?.tools || {})"))
