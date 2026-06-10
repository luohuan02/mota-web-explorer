#!/usr/bin/env python3
"""Regression checks for merchant full-map final-score accounting."""

from __future__ import annotations

import os
import pickle
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)
os.chdir(ROOT)

from scripts import compare_merchant_resource_paths as cm
from scripts import merchant_finalscore_audit as audit
from src.solver import gen_walkthrough as gw


def test_mt6_future_resources_reachable() -> None:
    if not os.path.exists(audit.DELAYED_WALK):
        return
    cm.ensure_merchant_maps()
    cm._FUTURE_BREAKDOWN_CACHE.clear()
    cm._FUTURE_FLOOR_CACHE.clear()
    delayed, _boss = audit.replay_delayed_walk()
    row = cm.future_floor_breakdown(delayed, "MT6")
    assert row is not None, "MT6 future resources should be reachable from flyback entrance"
    assert row["value"] >= 600, row
    assert any(item["eid"] == "merchant:MT6_BK" for item in row.get("merchants", ())), row


def test_buying_mt6_bk_is_not_double_counted() -> None:
    cache_path = os.path.join("outputs", "results", "merchant_phase1_long_search_state.pkl")
    if not os.path.exists(cache_path):
        return
    with open(cache_path, "rb") as f:
        payload = pickle.load(f)
    gw._entry_store.clear()
    gw._entry_store.update(payload.get("entry_store", {}))
    gw._next_id[0] = payload.get("next_id", gw._next_id[0])
    target = None
    for ent in payload.get("merchant_goals", []):
        if (
            ent["hp"],
            ent["atk"],
            ent["def"],
            ent["yk"],
            ent["bk"],
            cm.inferred_gold(ent, include_boss_spawn=False),
            ent.get("_dmg"),
            ent.get("_yd"),
        ) == (371, 22, 21, 2, 2, 25, 855, 24):
            target = ent
            break
    if target is None:
        return
    parent = gw._entry_store[target["_parent_id"]]
    assert any(
        item["eid"] == "merchant:MT6_BK"
        for row in cm.merchant_residual_breakdown(parent)
        for item in row.get("items", ())
    )
    assert not any(
        item["eid"] == "merchant:MT6_BK"
        for row in cm.merchant_residual_breakdown(target)
        for item in row.get("items", ())
    )


if __name__ == "__main__":
    test_mt6_future_resources_reachable()
    test_buying_mt6_bk_is_not_double_counted()
    print("merchant full-map score tests passed")
