
# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

import subprocess
import sys

agent_path = r"D:\nvm4w\nodejs\agent-browser.cmd"
result = subprocess.run(
    [agent_path, "close", "--all"],
    capture_output=True, text=True, shell=True,
    encoding='utf-8', errors='ignore'
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
print("Done!")
