#!/usr/bin/env python3
"""Regression tests for human walk deferred-auto attribution."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.build.gen_zone_walk_md import collect_following_arrives


def main() -> int:
    same_floor = [
        {"action": "击杀"},
        {"action": "已清理"},
        {"action": "到达", "floor": "MT39"},
        {"action": "拾取"},
    ]
    assert len(collect_following_arrives(same_floor, 0)) == 1

    cross_floor = [
        {"action": "击杀"},
        {"action": "飞行", "floor": "MT38"},
        {"action": "到达", "floor": "MT38"},
        {"action": "拾取"},
    ]
    assert collect_following_arrives(cross_floor, 0) == []
    print("zone walk markdown attribution: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
