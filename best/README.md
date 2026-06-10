# Best Walk Artifacts

Tracked stable walkthroughs:

- `current_best_boss_walk.md`: current best final-score boss route.
- `guide_boss_walk.md`: guide baseline boss route.
- `current_best_boss_summary.json`: machine-readable summary for current best.

Scoring model:

- `1YK = 50HP`, `1BK = 4YK = 200HP`, `100G = 1YK = 50HP`.
- `final-score` includes current HP/key/gold stock plus full-map remaining resource groups.
- Future monster gold is counted as zero-damage future income; unopened doors still cost key value.
- Unused merchants are future net resources and merchant purchases consume actual gold.
- Guide source: https://www.taptap.cn/moment/15225056477054087

Current best:

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
