# Background

This project aims to explore the optimal route for the "Magic Tower 50 Floors" game using AI. The current main approach involves A* search combined with Pareto optimality and some optimization strategies.
Game link: https://h5mota.com/games/51/
The goal is to compute the optimal route locally by reading game data, with a current focus on algorithmic exploration.

All subsequent project content will be AI-generated, although the walk route has been manually verified.
The time and cost invested so far are relatively high. If you're interested, feel free to join the discussion and exploration.

# mota-web-explorer

Magic Tower / h5mota route-search workspace for the 51-floor game variant.

Guide source used as the manual baseline:
https://www.taptap.cn/moment/15225056477054087

## Current Result

Tracked stable artifacts live in `best/`.

```text
current best:
HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=305 dmg=2454 door=41/2/1 final-score=1376.5

guide baseline:
HP=25 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=304 dmg=2601 door=40/2/1 final-score=1327.5
```

The current best is stored as:

- `best/current_best_boss_walk.md`
- `best/current_best_boss_summary.json`
- `best/guide_boss_walk.md`

The older `1482.5` result is invalid and should not be used. It allowed an MT10 special action before the MT9 upFloor path was actually opened; `scripts/post9_resource_group_search.py` now guards special actions before replay.

## Score Model

- `1YK = 50HP`
- `1BK = 4YK = 200HP`
- `100G = 1YK = 50HP`
- red potion = `50`, blue potion = `200`
- red key and gems are route resources but have `0` leftover score by default
- final-score includes current HP/key/gold stock plus full-map remaining resource groups
- future monster gold is counted as zero-damage future income
- unopened doors still cost key value
- unused merchants are counted only as future net resources, and buying from a merchant consumes actual gold

Known merchants modeled as resource groups:

- MT7 `x6y1`: `50G -> 5YK`
- MT6 `x8y4`: `50G -> 1BK`

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

Important checkpoint:

```text
after MT7:redGem, MT3:blueGem, MT6:blueGem, MT7 skeleton key pocket:
HP=361 ATK=23 DEF=23 YK=2 BK=1 RK=0 G=93 dmg=915 door=28/0/0
```

## Useful Commands

Regenerate the tracked best artifacts from the validated sequence:

```powershell
python scripts\gen_local_refined_best_walk.py
```

Re-run the validated MT7-red-first probe:

```powershell
python scripts\probe_mt7_red_first_swap_sequence.py --variant user-def-before-key --beam 160 --out-json outputs\results\user_def_before_key_probe_after_mt10_guard.json --out-md outputs\reports\user_def_before_key_probe_after_mt10_guard.md
```

Basic checks after edits:

```powershell
python -m py_compile scripts\post9_resource_group_search.py scripts\compare_merchant_resource_paths.py scripts\merchant_finalscore_audit.py scripts\probe_mt7_red_first_swap_sequence.py scripts\local_order_refine_current_best.py scripts\gen_local_refined_best_walk.py
python tests\run_merchant_fullmap_score_test.py
python tests\run_pareto_test.py
python tests\run_floorsearch_test.py
```

## Browser Game Access

The game runs at https://h5mota.com/games/51/ . The project uses [agent-browser](https://www.npmjs.com/package/agent-browser) (Chrome CDP) to read and control it. The browser profile stores the h5mota save data and is ignored by git.

### Connect to a running game

If Chrome is already open with the game, auto-connect:

```bash
agent-browser --auto-connect snapshot -i
```

Or open a fresh session with the project profile:

```bash
agent-browser close
agent-browser --profile "D:\claude\mota-web-explorer\browser-profile" --session-name mota-session open https://h5mota.com/games/51/
```

### Read hero state (CLI)

```bash
agent-browser --auto-connect eval "(function(){
  const h = core.status.hero, loc = h.loc, t = h.items.tools;
  return JSON.stringify({
    floor: core.status.floorId, x: loc.x, y: loc.y,
    hp: h.hp, atk: h.atk, def: h.def,
    yk: t.yellowKey||0, bk: t.blueKey||0, rk: t.redKey||0,
    gold: h.money||0
  });
})()"
```

### Read floor map (CLI)

```bash
agent-browser --auto-connect eval "(function(){
  const fid = 'MT10';
  const m = core.status.maps[fid];
  const items = m.blocks.filter(b => b.event && b.event.id !== 'yellowWall')
    .map(b => ({x:b.x, y:b.y, id:b.event.id, noPass:b.event.noPass}));
  return JSON.stringify({floorId:fid, hero:{x:core.status.hero.loc.x,y:core.status.hero.loc.y}, items});
})()"
```

### Read hero state (Python)

```python
from src.legacy.browser import BrowserController

bc = BrowserController()          # defaults to project browser-profile
bc.connect_existing()             # --auto-connect
state = bc.read_game_state()      # .floor .x .y .hp .atk .def_ .yk .bk .rk
floor_data = bc.export_floor_map()  # .map .blocks .width .height
```

### Notes

- Always `agent-browser close` before re-opening; otherwise the `--profile` flag is ignored.
- Never use `close --all` or close the user's own browser.
- The game canvas only shows as `[Canvas]` in snapshots — use `eval` with `core.status` JS API instead.
- Save data is in the browser profile's `localStorage`, not in the project repo.

## Repository Layout

- `best/`: tracked stable walkthroughs and summary JSON
- `scripts/`: route search, replay, audit, report, and browser helper scripts
- `src/solver/`: shared map/search implementation
- `data/`, `config/`: source data and local configuration
- `tests/`: lightweight regression checks
- `outputs/`: ignored search reports, checkpoints, and temporary walkthroughs
- `browser-profile/`: ignored local browser profile with h5mota save data

Do not delete `src/solver/`, `src/legacy/`, `data/`, `browser-profile/`, or `config/`.
