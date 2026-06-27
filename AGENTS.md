# Codex Project Notes

This repository searches and audits Magic Tower / h5mota routes for the game linked from the guide baseline:
https://www.taptap.cn/moment/15225056477054087

Game URL: https://h5mota.com/games/51/

Official ranking / forum URL: https://h5mota.com/tower/?name=51

`CLAUDE.md` should stay synchronized with this file.

## Project Skills

Before changing route/search/live-browser code, read the relevant project skill
under `skills/` and follow its workflow. These local skills are the project
entry points and may override older habits from generic browser tooling:

- `skills/mota-route-search/SKILL.md`: local route search, Pareto/beam/A* probes, strategy comparison.
- `skills/mota-route-audit/SKILL.md`: replay legality checks, Chinese walk generation, remaining-resource audits.
- `skills/mota-live-browser/SKILL.md`: reading or probing the already-open h5mota browser state.
- `skills/mota-live-verify/SKILL.md`: executing a generated walk in the live browser and comparing live state.

For live h5mota access, the current project convention is `agent-browser.cmd --cdp 9222`; do not use `--auto-connect`.

## Current Canonical Result

Use the tracked `best/` artifacts as the source of truth.

Full route-family index:

```text
best/route_chains.json
best/route_chains.md
```

These files record the 1-4 zone guide and non-guide branches, their checkpoint
links, and which parts can be replayed continuously. Current chain summary:

```text
guide_chain_to_22264:
zone1.guide_baseline -> zone2.guide_canonical -> save36 bridge
-> zone3.guide_slot36_to40 -> zone4.save37_hp_leaderboard

non_guide_current_best_branch:
zone1.current_best -> zone2.current_best_2atk1def_branch
-> slot26 bridge -> zone3.slot26_clean_boss8def -> zone4.slot26_tail_pending
related sibling: zone2.current_best_canonical
```

The save37 22264 tail is web-verified, but it must not be reused for slot26
without a new Zone 4 search/replay.

Current HP-leaderboard continuation from save37 / post-40:

```text
best/post40_hp_leaderboard_summary.json
best/post40_hp_leaderboard_walk.json
best/post40_hp_leaderboard_walk.md

HP=22264 ATK=418 DEF=517 YK=4 BK=0 RK=0 G=1235 dmg=27134 door=53/10/7
source save=37 verified save=42
```

This is a web-verified continuation from browser save slot 37. See
`best/route_chains.md` for the current 1-4 zone linkage and the remaining
full stitched replay gap.

Phase-1 / 10F boss artifacts:

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

Regenerate and live-verify the save37 post-40 HP route:

```powershell
python scripts\search_post40_guide_route.py
node scripts\prepend_40f_prefix_walk.js
node scripts\live_zone3_mouse_replayer_cdp.js --walk best\post40_hp_leaderboard_walk.json --load-slot 37 --target-click-only
```

Baseline checks after code edits:

```powershell
python -m py_compile scripts\post9_resource_group_search.py scripts\compare_merchant_resource_paths.py scripts\merchant_finalscore_audit.py scripts\probe_mt7_red_first_swap_sequence.py scripts\local_order_refine_current_best.py scripts\gen_local_refined_best_walk.py
python tests\run_merchant_fullmap_score_test.py
python tests\run_pareto_test.py
python tests\run_floorsearch_test.py
```

## Browser Notes

Use the `agent-browser` skill for h5mota browser interaction.

Important: when reading or controlling the already-open h5mota game, connect to the existing Chrome DevTools port directly. Use `--cdp 9222`, not `--auto-connect`; `--auto-connect` may attach to agent-browser's own blank daemon/tab instead of the real game page.

```powershell
agent-browser.cmd --cdp 9222 eval "(() => { const h = core.status.hero, loc = h.loc, t = h.items.tools; return { floor: core.status.floorId, x: loc.x, y: loc.y, hp: h.hp, atk: h.atk, def: h.def, yk: t.yellowKey || 0, bk: t.blueKey || 0, rk: t.redKey || 0, gold: h.money || 0 }; })()"
```

The local browser profile is `browser-profile/`; do not delete it.

For live route replay, prefer `scripts/live_zone3_mouse_replayer_cdp.js` and the
`skills/mota-live-verify/SKILL.md` notes. The verifier should use real map-click
handlers, not forced hero movement. Known h5mota replay edge cases include empty
`waitAsync` event shells, adjacent noPass targets that require a second click,
logical route targets whose live coordinates differ after the side effect, and
the 39F/40F center-symmetry item (`centerFly3` pickup, `centerFly` usable tool).
For the final 50F adjacent boss trigger, use the real keyboard/game key event
path; do not use `core.moveHero` or direct coordinate edits.
