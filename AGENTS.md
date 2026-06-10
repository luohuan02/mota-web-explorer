# Codex Project Notes

This repository searches and audits Magic Tower / h5mota routes for the game linked from the guide baseline:
https://www.taptap.cn/moment/15225056477054087

`CLAUDE.md` should stay synchronized with this file.

## Current Canonical Result

Use the tracked `best/` artifacts as the source of truth.

```text
best/current_best_boss_walk.md
best/current_best_boss_summary.json

HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=305 dmg=2454 door=41/2/1 final-score=1376.5
```

Guide baseline under the same scoring model:

```text
HP=25 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=304 dmg=2601 door=40/2/1 final-score=1327.5
```

Important: old `1482.5` artifacts are invalid. They allowed an MT10 special action before MT9 upFloor was actually reachable. `scripts/post9_resource_group_search.py::apply_action` now rejects special actions unless `special_action_allowed(...)` passes.

## Score Model

- `1YK = 50HP`
- `1BK = 4YK = 200HP`
- `100G = 1YK = 50HP`
- red potion = `50`, blue potion = `200`
- red key and gems have `0` leftover score unless a script explicitly uses another objective
- `final-score` = current HP/key/gold stock + full-map remaining resource groups
- remaining monsters are future zero-damage gold income
- unopened yellow/blue doors still subtract key value
- unused merchants count only as net future resources; actual merchant actions consume actual gold

Merchant resources:

- MT7 `x6y1`: pay `50G` for `5YK`
- MT6 `x8y4`: pay `50G` for `1BK`
- Keep MT6 `x8y3` red potion and MT6 `x8y4` merchant as separate resource groups because the merchant consumes gold.

`finalStock` / `netStock` terms:

- `scripts/post9_resource_group_search.py::final_resource_stock`: HP + current key stock + remaining resource value with monster damage ignored for residual pickups.
- `scripts/post9_gem_supply_search.py::net_final_stock`: HP + current key stock + recoverable remaining resource net value with residual door / monster costs included.

## Current Best Sequence

```text
MT7:redGem
MT3:blueGem
MT6:blueGem
MT7:yellowKey
MT1:blueGem
MT8:blueGem
MT3:redGem
MT5:blueGem
MT4:blueKey
MT9:upFloor
MT10:blueGem
MT7:yellowKey
MT10:redGem
MT10:bluePotion
MT6:yellowKey
MT8:redKey
MT1:bluePotion
MT7:bluePotion
MT10:redDoor / boss
```

Key checkpoint:

```text
after MT7:redGem, MT3:blueGem, MT6:blueGem, MT7 skeleton key pocket:
HP=361 ATK=23 DEF=23 YK=2 BK=1 RK=0 G=93 dmg=915 door=28/0/0
```

## Search Conventions

- Search starts from 4F; 1F-3F are fixed prefix but their remaining resources can be collected later.
- Stage targets: sword, shield, 9F red/blue gems, 27/27 stats, 8F red key, 10F boss.
- `dmg` remains the core path cost; HP is a tie-breaker inside comparable candidates.
- `yk/bk/rk` are current reachable key stock.
- `_yd/_bd/_rd` are cumulative door consumption and must not be replaced by current key stock alone.
- Resource group score is for ordering and reporting. Do not use it as a substitute for Pareto retention unless the dominance condition is explicitly safe.
- Do not add hand-only special lanes without documenting why they remain legal under real floor replay.

## Files To Keep

- `README.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`
- `best/`
- `config/`, `data/`, `src/`, `scripts/`, `tests/`
- `browser-profile/` locally only; it stores the h5mota browser save/profile and is ignored by git

Do not delete `src/solver/`, `src/legacy/`, `data/`, `browser-profile/`, or `config/`.

`outputs/` is ignored by git and may contain large temporary reports, checkpoints, and stale experiments.

## Useful Commands

Regenerate tracked best artifacts:

```powershell
python scripts\gen_local_refined_best_walk.py
```

Validated probe for the current best:

```powershell
python scripts\probe_mt7_red_first_swap_sequence.py --variant user-def-before-key --beam 160 --out-json outputs\results\user_def_before_key_probe_after_mt10_guard.json --out-md outputs\reports\user_def_before_key_probe_after_mt10_guard.md
```

Baseline checks after code edits:

```powershell
python -m py_compile scripts\post9_resource_group_search.py scripts\compare_merchant_resource_paths.py scripts\merchant_finalscore_audit.py scripts\probe_mt7_red_first_swap_sequence.py scripts\local_order_refine_current_best.py scripts\gen_local_refined_best_walk.py
python tests\run_merchant_fullmap_score_test.py
python tests\run_pareto_test.py
python tests\run_floorsearch_test.py
```

## Browser Notes

Use the `agent-browser` skill for h5mota browser interaction. Keep `--auto-connect` when reading an existing opened game:

```powershell
agent-browser --auto-connect snapshot -i
```

The local browser profile is `browser-profile/`; do not delete it.
