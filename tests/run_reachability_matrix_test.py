#!/usr/bin/env python3
"""P1 单测：可达矩阵在 4 个 checkpoint 上的行为锁定。

验证：
- 钥匙门感知（YK=0 时门后宝石被挡）
- 可杀性感知（高 HP 怪挡路）
- 楼层内拾钥匙开新门
- 跨层（已访问楼层经楼梯入口可达）
- npc 商店贴邻登记（blueShop）
- MT12 blueShop 在 zone2+ 可达（2 攻线买 2 atk 的店）
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from src.solver.game_route import Game, read_json
from src.solver.reachability_matrix import compute_matrix


def _load(path: str) -> Game:
    g = Game(read_json(ROOT / path))
    g.strict_live_model = True
    g.auto_flags = {"battle": True, "item": True, "wall": True}
    return g


def test_save1_mt4():
    g = _load("outputs/results/save1_current_snapshot.json")
    rm = compute_matrix(g)
    # 已访问 MT1-4，宝石在 MT1/3/4
    assert g.state["floor"] == "MT4", g.state["floor"]
    skel_fids = {e.fid for e in rm.skeleton_entries}
    assert skel_fids <= {"MT1", "MT3", "MT4"}, skel_fids
    assert any(e.fid == "MT4" and e.eid == "redGem" for e in rm.skeleton_entries)
    # MT4 blueShop 登记
    assert any(e.fid == "MT4" and e.eid == "blueShop" for e in rm.shop_entries), \
        f"MT4 shop not detected: {rm.shop_entries}"
    print("OK save1 MT4: skeleton + MT4 shop detected")


def test_save100_yk0_door_blocked():
    g = _load("best/checkpoints/zone1_end_save.json")
    rm = compute_matrix(g)
    assert g.state["yk"] == 0
    # MT10 六宝石（post-boss 区，dmg=0）
    mt10_gems = [e for e in rm.skeleton_entries if e.fid == "MT10"]
    assert len(mt10_gems) == 6, f"MT10 gems={len(mt10_gems)}"
    assert all(e.access_dmg == 0 for e in mt10_gems)
    # MT1-9 钥匙门挡（YK=0）：这些层有 door blocker
    door_blk_fids = {b.fid for b in rm.blockers if b.kind == "door"}
    assert {"MT1", "MT3", "MT6", "MT7", "MT8", "MT9"} <= door_blk_fids, door_blk_fids
    # MT1-9 没有骨架宝石（都被门挡）
    assert not any(e.fid in {"MT1", "MT3", "MT6", "MT7", "MT8", "MT9"} for e in rm.skeleton_entries)
    print("OK save100 MT10: YK=0 door-gating correct, MT10 6 gems dmg=0")


def test_mt12_shop_zone2plus():
    for path in ("best/checkpoints/zone2_end_save.json",
                 "best/checkpoints/zone3_bridge_mt31_save.json",
                 "best/checkpoints/zone3_2atk1def_preserve_pickaxe_end_save.json"):
        g = _load(path)
        rm = compute_matrix(g)
        mt12 = [e for e in rm.shop_entries if e.fid == "MT12" and e.eid == "blueShop"]
        assert mt12, f"{path}: MT12 blueShop not detected"
        print(f"OK {path.split('/')[-1]}: MT12 blueShop x{mt12[0].pos[0]}y{mt12[0].pos[1]} reachable")


def test_save150_mt32_shop_and_killability():
    g = _load("best/checkpoints/zone3_2atk1def_preserve_pickaxe_end_save.json")
    rm = compute_matrix(g)
    # MT32 blueShop（zone3 店）可达
    mt32 = [e for e in rm.shop_entries if e.fid == "MT32" and e.eid == "blueShop"]
    assert mt32, f"MT32 shop not detected: {rm.shop_entries}"
    # zone3/4 高 HP 怪挡路（enemy blocker 存在）
    enemy_blk = [b for b in rm.blockers if b.kind == "enemy"]
    assert enemy_blk, "expected enemy blockers at zone3/4 (tough monsters)"
    assert any(b.fid in {"MT31", "MT32", "MT36"} for b in enemy_blk), \
        [(b.fid, b.eid) for b in enemy_blk]
    print(f"OK save150 MT41: MT32 shop + {len(enemy_blk)} enemy blockers (killability)")


def test_onfloor_key_collection():
    """save1 MT3 拾楼层内钥匙后能开黄门到宝石（collected_keys>0）。"""
    g = _load("outputs/results/save1_current_snapshot.json")
    rm = compute_matrix(g)
    mt3 = rm.floors.get("MT3")
    assert mt3 is not None
    # MT3 有可拾钥匙 + 可达宝石（blueGem/redGem）
    assert mt3.collected_keys[0] > 0, mt3.collected_keys
    assert any(e.fid == "MT3" and e.eid in {"redGem", "blueGem"} for e in rm.skeleton_entries)
    print(f"OK save1 MT3: on-floor key collection = {mt3.collected_keys}, gems reachable")


if __name__ == "__main__":
    test_save1_mt4()
    test_save100_yk0_door_blocked()
    test_mt12_shop_zone2plus()
    test_save150_mt32_shop_and_killability()
    test_onfloor_key_collection()
    print("\nALL reachability_matrix tests passed.")
