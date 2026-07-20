#!/usr/bin/env python3
"""Ensure AGENTS.md and CLAUDE.md remain one canonical file."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
agents = ROOT / "AGENTS.md"
claude = ROOT / "CLAUDE.md"

assert agents.read_bytes() == claude.read_bytes(), "AGENTS.md / CLAUDE.md 内容已分叉"
assert os.path.samefile(agents, claude), "AGENTS.md / CLAUDE.md hardlink 已断开"
print("project docs canonical hardlink: ok")
