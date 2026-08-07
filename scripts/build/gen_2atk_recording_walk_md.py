#!/usr/bin/env python3
"""从 2攻线录像 (51_20260717073423.h5route) + ground-truth stat log 生成人看 walk.md。

录像 web 完整复现 (core.startGame 回放 1134 action) 到 save26 零差异；stat log 是
ground truth。本脚本把录像 route + stat log 渲染成人看路线，区分 1区(MT1-10)/2区(MT11-20)。

注意：Game 类离线 exact 复现被 path_to vs automaticRoute 寻路分歧阻断（见
h5route_step_facing_behavior 记忆），故 walk 直接从录像 ground truth 生成，不从 Game 类。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)

TMP = Path(os.environ.get("CLAUDE_JOB_DIR", "C:/Users/peiyan.liang/.claude/jobs/79814e6b")) / "tmp"
ROUTE_JSON = TMP / "decoded_route_1134.json"
STATLOG_JSON = TMP / "replay_statlog.json"
OUT_MD = ROOT / "best" / "zone12_2atk_recording_walk.md"

# eid 中文
CN = {
    "yellowKey": "黄钥匙", "blueKey": "蓝钥匙", "redKey": "红钥匙",
    "redGem": "红宝石", "blueGem": "蓝宝石",
    "redPotion": "红药水", "bluePotion": "蓝药水", "superPotion": "圣水",
    "yellowDoor": "黄门", "blueDoor": "蓝门", "redDoor": "红门", "specialDoor": "机关门",
    "sword1": "铁剑", "sword2": "银剑", "sword3": "圣剑",
    "shield1": "铁盾", "shield2": "银盾",
    "fakeWall": "暗墙", "cross": "十字架", "fly": "楼层传送器",
    "upFloor": "上楼", "downFloor": "下楼",
}


def floor_no(f: str) -> int:
    return int(f[2:])


def zone_of(f: str) -> str:
    n = floor_no(f)
    if n <= 10:
        return "1区"
    if n <= 20:
        return "2区"
    return "3区"


def main() -> int:
    route = json.loads(ROUTE_JSON.read_text(encoding="utf-8"))
    log = json.loads(STATLOG_JSON.read_text(encoding="utf-8"))

    # route -> stat index
    route_stat = [None] * len(route)
    si = 0
    for ri, a in enumerate(route):
        if not (isinstance(a, str) and a.startswith("choices")):
            route_stat[ri] = si
            si += 1

    lines: list[str] = []
    lines.append("# 2攻线录像 walk（1/2 区）")
    lines.append("")
    lines.append("- 来源：`51_20260717073423.h5route`（2攻线，创 save26）")
    lines.append("- web 完整复现：`core.startGame` 回放全部 1134 action，结束 MT31 = save26（HP=1249 ATK=76 DEF=64 YK=4 G=176），零差异")
    lines.append("- 起点：MT4（SAVE1 = 录像 stat i=55：HP=926 ATK=10 DEF=10 YK=4 BK=1 G=7，含 MT1-3 固定前缀 + 纯净版 reset）")
    lines.append("- 终点（2区末）：MT20 stat i=989（HP=1249 ATK=76 DEF=64 YK=4 BK=0 RK=0 G=154）")
    lines.append("- 商店：MT12 买 2 攻（2×+4=+8 ATK，60G）。商人：MT7(5YK/50G)、MT6(1BK/50G)、MT15(1BK/200G)、MT12(1红钥匙/800G)")
    lines.append("- 注意：Game 类离线 exact 复现被 path_to vs automaticRoute 寻路分歧阻断；本 walk 从录像 ground truth 生成")
    lines.append("")

    # per-floor visit summary (zone1/2 only: MT1-20)
    emitted_zone = set()
    prev = None
    for ri, a in enumerate(route):
        if route_stat[ri] is None:
            continue
        e = log[route_stat[ri]]
        f = e["f"]
        if floor_no(f) > 20:
            break
        z = zone_of(f)
        if z not in emitted_zone:
            emitted_zone.add(z)
            lines.append(f"\n## {z}（MT{1 if z=='1区' else 11}-MT{10 if z=='1区' else 20}）\n")
        # floor change
        if prev is None or prev["f"] != f:
            lines.append(f"- {f} 进入  HP={e['hp']} ATK={e['atk']} DEF={e['def']} YK={e['yk']} BK={e['bk']} RK={e['rk']} G={e['g']}  [{z}]")
        prev = e

    lines.append("")
    # key events table (stat jumps in zone1/2)
    lines.append("## 关键事件（1/2 区 stat 跳变）\n")
    lines.append("| stat i | 楼层 | 事件 | HP | ATK | DEF | YK | BK | RK | G |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for i in range(1, len(log)):
        e = log[i]
        p = log[i - 1]
        if floor_no(e["f"]) > 20:
            break
        if e["f"] != p["f"]:
            continue
        diffs = []
        if e["atk"] != p["atk"]:
            diffs.append(f"ATK {p['atk']}→{e['atk']}")
        if e["def"] != p["def"]:
            diffs.append(f"DEF {p['def']}→{e['def']}")
        if e["yk"] != p["yk"]:
            diffs.append(f"YK {p['yk']}→{e['yk']}")
        if e["bk"] != p["bk"]:
            diffs.append(f"BK {p['bk']}→{e['bk']}")
        if e["rk"] != p["rk"]:
            diffs.append(f"RK {p['rk']}→{e['rk']}")
        if e["hp"] != p["hp"]:
            diffs.append(f"HP {p['hp']}→{e['hp']}")
        if e["g"] != p["g"]:
            diffs.append(f"G {p['g']}→{e['g']}")
        if diffs:
            lines.append(f"| {e['i']} | {e['f']} | {e['a']} ({e['x']},{e['y']}) | {e['hp']} | {e['atk']} | {e['def']} | {e['yk']} | {e['bk']} | {e['rk']} | {e['g']} |")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"md={OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
