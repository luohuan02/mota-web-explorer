# Allow scripts to import project-root modules after being moved under scripts/.
import os as _codex_os
import sys as _codex_sys
_codex_root = _codex_os.path.dirname(_codex_os.path.dirname(_codex_os.path.abspath(__file__)))
if _codex_root not in _codex_sys.path:
    _codex_sys.path.insert(0, _codex_root)

from tmp import run_strategy, hero

collected = set()
state = {'hp': hero['h'], 'atk': hero['a'], 'def': hero['d'], 'yk': hero['yk'], 'bk': hero['bk'], 'collected': collected}

run_strategy("A: 4FredGem -> 5Fsword -> 3Ffb -> 7F(YK保留) -> 1Ffb", state, ['upFloor', 'redGem'], True, True)
