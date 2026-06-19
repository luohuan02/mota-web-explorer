#!/usr/bin/env python3
"""Compatibility wrapper for extracting MT41+ maps through CDP.

Use the Node implementation for the actual CDP WebSocket connection.  Calling
`agent-browser.cmd` from Python with captured stdout is unreliable on this
Windows setup for large payloads, so this wrapper intentionally avoids that
path.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NODE_SCRIPT = ROOT / "scripts" / "extract_high_maps_cdp.js"


def main() -> int:
    args = sys.argv[1:] or ["41", "50"]
    proc = subprocess.run(["node", str(NODE_SCRIPT), *args], cwd=str(ROOT))
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
