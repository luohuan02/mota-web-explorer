# Best Walk Artifacts

Tracked stable walkthroughs:

- `route_chains.json`: machine-readable 1-4 zone route-family manifest.
- `route_chains.md`: human-readable guide/non-guide continuity map.
- `post40_hp_leaderboard_summary.json`: current HP-leaderboard continuation from save37.
- `post40_hp_leaderboard_walk.json`: machine-readable live replay walk for the save37 continuation.
- `post40_hp_leaderboard_walk.md`: human-readable Chinese walk for the save37 continuation.
- `zone2_canonical_replay.json`: Zone 2 replay for both guide and current-best Zone 1 starts.
- `zone2_canonical_walk.md`: Chinese Zone 2 guide/current-best canonical walk.
- `zone2_2atk1def_branch_summary.json`: Zone 2 2ATK1DEF branch summary for later slot26 exploration.
- `zone2_2atk1def_branch_walk.md`: Chinese Zone 2 2ATK1DEF branch walk.
- `zone3_guide_slot36_to_40_walk.json`: Zone 3 guide/save36 quick pass to the post-40 state.
- `zone3_guide_slot36_to_40_walk.md`: Chinese Zone 3 guide/save36 quick pass.
- `zone3_guide_slot36_to_37_plan.json`: earlier guide/save36 audit plan to 37F.
- `zone3_guide_slot36_to_37_plan.md`: Chinese earlier guide/save36 audit plan to 37F.
- `zone3_slot26_clean_walk.json`: Zone 3 non-guide/slot26 clean branch variants.
- `zone3_slot26_clean_walk.md`: Chinese Zone 3 non-guide/slot26 clean branch walk.
- `current_best_boss_walk.md`: current best final-score boss route.
- `guide_boss_walk.md`: guide baseline boss route.
- `current_best_boss_summary.json`: machine-readable summary for current best.

Scoring model:

- `1YK = 50HP`, `1BK = 4YK = 200HP`, `100G = 1YK = 50HP`.
- `final-score` includes current HP/key/gold stock plus full-map remaining resource groups.
- Future monster gold is counted as zero-damage future income; unopened doors still cost key value.
- Unused merchants are future net resources and merchant purchases consume actual gold.
- Game URL: https://h5mota.com/games/51/
- Official ranking / forum URL: https://h5mota.com/tower/?name=51
- Guide source: https://www.taptap.cn/moment/15225056477054087

Current HP-leaderboard continuation from save37:

```text
HP=22264 ATK=418 DEF=517 YK=4 BK=0 RK=0 G=1235 dmg=27134 door=53/10/7
source save=37 verified save=42
```

This result is web-verified from browser save slot 37 and saved to slot 42 after
the final redKing battle. It is not yet a single continuous 1F-to-clear proof;
the earlier 1F-40F prefix must be concatenated and verified before calling it a
full-game best.

Route-family index:

```text
best/route_chains.json
best/route_chains.md
```

The current guide-linked chain is:

```text
zone1.guide_baseline
-> zone2.guide_canonical
-> bridge.save36_mt20_to_mt31
-> zone3.guide_slot36_to40
-> zone4.save37_hp_leaderboard
```

The current non-guide/search branch is:

```text
zone1.current_best
-> zone2.current_best_2atk1def_branch
-> bridge.slot26_mt20_to_mt31
-> zone3.slot26_clean_boss8def
-> zone4.slot26_tail_pending
related sibling: zone2.current_best_canonical
```

The non-guide branch must get its own Zone 4 tail before making a final HP
claim; do not reuse the save37 22264 tail for slot26.

Phase-1 / 10F current best:

```text
HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=305 dmg=2454 door=41/2/1 final-score=1376.5
```

Important source/resource paths to keep:

- `AGENTS.md`, `CLAUDE.md`, `README.md`, `.gitignore`
- `config/`, `data/`, `src/`, `scripts/`, `tests/`
- `browser-profile/` locally, because it stores the h5mota browser save/profile.
- Current strategy scripts: `scripts/post9_gem_supply_search.py`, `scripts/post9_action_search.py`, `scripts/post9_resource_group_search.py`, `scripts/post9_merchant_seed_search.py`, `scripts/run_corrected_phase1_best_boss_until_deadline.py`.
- Current corrected scoring/search scripts: `scripts/compare_merchant_resource_paths.py`, `scripts/long_merchant_phase1_search.py`, `scripts/rescore_merchant_phase1_cache.py`, `scripts/gen_corrected_merchant_phase1_best_walk.py`, `scripts/gen_best_current_boss_walk.py`.
- Guide/delayed scripts: `scripts/fixed_shield_strategy.py`, `scripts/replay_user_post9_route.py`, `scripts/continue_delayed_phase1_with_post9_resource.py`, `scripts/gen_delayed_phase1_detailed_walk.py`, `scripts/compare_delayed_phase1_vs_user_guide.py`.
- Tests: `tests/run_merchant_fullmap_score_test.py`, plus existing solver/search regression tests.

Note: older `1482.5` artifacts in ignored `outputs/` are stale. They were invalidated by the MT10 special-action guard because MT10 resources must not be reachable before the MT9 upFloor route is actually opened.

`outputs/` remains ignored by git and can hold temporary search runs/checkpoints.
