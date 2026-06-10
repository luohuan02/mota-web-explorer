---
name: mota-route-baselines
description: Use this skill whenever working on the h5mota 51 Mota search project, especially when changing Pareto pruning, key/door accounting, 1-3 fixed-state assumptions, MT10 gem access, red-key routing, Boss handling, or comparing generated walkthroughs against verified hand routes. Always check the verified baseline routes before judging a new strategy as better or pruning a route.
---

# Mota Route Baselines

This project has several verified route baselines that should be preserved as comparison targets while optimizing the search algorithm.

## Core Rule

When changing search logic, compare against verified route baselines by cumulative battle damage (`dmg`), cumulative door use (`doorY/B/R`), final stats, and remaining keys. Do not judge by HP alone.

Use:

```powershell
python scripts\replay_user_post9_route.py
python scripts\fixed_shield_strategy.py
python scripts\gen_walkthrough_fixed_prefix.py
```

## Fixed 1-3 Starting Assumption

The 4F search starts at:

```text
HP=926 ATK=10 DEF=10 YK=4 BK=1 RK=0
```

The fixed 1-3 route does not open the 1F `x4y3` yellow door. Therefore 1F `x1y3` red potion is not consumed by the fixed 1-3 prefix and must remain available for later flyback.

`src/solver/full_search.py::FLOOR_13_COLLECTED['MT1']` must exclude `(1,3)`.

## Verified Fixed 4-9 Prefix

The fixed 4-9 shield prefix reaches the post-9F red+blue gem state:

```text
HP=148 ATK=23 DEF=21 YK=2 BK=1 RK=0 dmg=928 doorY/B/R=23/0/0
```

Validate it with:

```powershell
python scripts\fixed_shield_strategy.py
```

## Verified User Post-9F Continuation

The user-provided post-9F route has been mechanically replayed and corrected for two hand-entry omissions:

- 6F blue gem segment must include `x8y11` red potion. The hand-written `x9y10` point is only an empty waypoint.
- 9F up-to-10F segment must include `x2y10` red potion.

The verified route starts from:

```text
HP=148 ATK=23 DEF=21 YK=2 BK=1 RK=0 dmg=928 doorY/B/R=23/0/0
```

It finishes:

```text
HP=25 ATK=27 DEF=27 YK=0 BK=0 RK=0 dmg=2601 doorY/B/R=40/2/1
```

Generated artifacts:

```text
outputs/walkthroughs/walkthrough_user_post9_route.md
outputs/reports/user_post9_route_replay.md
outputs/results/user_post9_route_replay.json
```

Replay it with:

```powershell
python scripts\replay_user_post9_route.py
```

## Why This Route Matters

This route enters MT10 early for the left-side blue gem with only:

```text
ATK=26 DEF=26 YK=1 BK=0 after the MT9 up-floor step
```

Earlier search logic used a coarse MT10 outside-entry budget such as `YK>=5 and BK>=1`; that can wrongly exclude this route shape. MT10 access should be budgeted by the target side:

- left blue gem access is cheaper than collecting both MT10 sides;
- right red gem access should be evaluated separately;
- MT10 blue potion is often a late HP refill and should not be forced into early gem collection.

When optimizing, keep this baseline in the candidate set or explain exactly why a generated route dominates it. A candidate that saves `dmg` but spends more doors does not strictly dominate it unless the comparison objective explicitly allows that tradeoff.

## Comparison Snapshot

As of the latest replay and existing generated artifacts:

```text
verified user post-9F route: HP=25 dmg=2601 doorY/B/R=40/2/1
fixed-prefix generated route: HP=88 dmg=2638 doorY/B/R=42/2/1
natural experimental route artifact: HP=30 dmg=2596 doorY/B/R=42/2/1
```

The natural experimental artifact has slightly lower `dmg`, but it should be rerun after data or search changes before final ranking. The verified user route spends two fewer yellow doors, so keep both as representative Pareto tradeoffs.
