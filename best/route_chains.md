# Route Chains

This file is the human-readable index for the stable route artifacts in `best/`.
The machine-readable version is `best/route_chains.json`.

Game: https://h5mota.com/games/51/

Official ranking / forum: https://h5mota.com/tower/?name=51

Guide baseline: https://www.taptap.cn/moment/15225056477054087

## Continuity Rules

- Do not mix slot36/save37 guide checkpoints with slot26 non-guide checkpoints unless a bridge walk proves the states match.
- `guide_chain_to_22264` is checkpoint-linked and the post-40 tail is web-verified, but the project still lacks one stitched 1F-to-50F web replay.
- `non_guide_current_best_branch` is stable through Zone 3 slot26 clean finishes, but its Zone 4 tail is pending. The 22264 tail must not be reused for slot26 without a new search/replay.
- The current tracked gap is 20F to 31F: the bridge exists as browser save checkpoints, not yet as a tracked machine-readable walk in `best/`.

## Chain Overview

| Chain | Segment order | Status | Final |
|---|---|---|---|
| `guide_chain_to_22264` | Zone 1 guide -> Zone 2 guide -> save36 bridge -> Zone 3 slot36 -> Zone 4 save37 | checkpoint-linked; tail web-verified; stitched replay pending | `HP=22264 ATK=418 DEF=517 G=1235 MT50 x6y5` |
| `non_guide_current_best_branch` | Zone 1 current best -> Zone 2 current-best 2ATK1DEF branch -> slot26 bridge -> Zone 3 slot26 -> Zone 4 pending | branch lineage; not a continuous clear; Zone 2 current-best canonical 3ATK is a sibling comparison branch | best clean Zone 3 HP state: `HP=556 ATK=170 DEF=198 G=926 MT40 x6y1` |

## Zone Artifacts

| Zone | Variant | Start | End | Artifacts | Connects to |
|---|---|---|---|---|---|
| 1 | guide baseline | new-game / fixed prefix | Boss: `HP=25 ATK=27 DEF=27 G=304`, post-supply: `HP=625 ATK=30 DEF=30 YK=3` | `best/guide_boss_walk.md` | Zone 2 guide |
| 1 | current best | new-game / fixed prefix | Boss: `HP=122 ATK=27 DEF=27 G=305`, post-supply: `HP=722 ATK=30 DEF=30 YK=3` | `best/current_best_boss_summary.json`, `best/current_best_boss_walk.md` | Zone 2 current best |
| 2 | guide canonical 3ATK | `MT10 HP=625 ATK=30 DEF=30 G=304 YK=3` | `MT20 HP=76 ATK=72 DEF=58 G=842 YK=5` | `best/zone2_canonical_replay.json`, `best/zone2_canonical_walk.md` | save36 bridge |
| 2 | current-best canonical 3ATK | `MT10 HP=722 ATK=30 DEF=30 G=305 YK=3` | `MT20 HP=203 ATK=72 DEF=58 G=838 YK=3` | `best/zone2_canonical_replay.json`, `best/zone2_canonical_walk.md` | future 20F->31F bridge |
| 2 | current-best 2ATK1DEF branch | current-best 10F post-supply family | `MT20 HP=577 ATK=70 DEF=66 G=930 YK=1` | `best/zone2_2atk1def_branch_summary.json`, `best/zone2_2atk1def_branch_walk.md` | slot26 bridge |
| 3 | guide slot36 quick pass | `MT31 HP=1276 ATK=78 DEF=64 G=864 YK=8` | `MT40 HP=78 ATK=166 DEF=218 G=2269 YK=4` | `best/zone3_guide_slot36_to_40_walk.json`, `best/zone3_guide_slot36_to_40_walk.md` | Zone 4 save37 |
| 3 | guide slot36 to 37F plan | same slot36 start | `MT37 HP=572 ATK=150 DEF=154 G=438 YK=2` | `best/zone3_guide_slot36_to_37_plan.json`, `best/zone3_guide_slot36_to_37_plan.md` | intermediate audit only |
| 3 | slot26 clean, 7buy DEF | `MT31 HP=1249 ATK=76 DEF=64 G=176 YK=4` | `MT40 HP=224 ATK=170 DEF=182 G=1846 YK=3`, simple stock `1297.0` | `best/zone3_slot26_clean_walk.json`, `best/zone3_slot26_clean_walk.md` | non-guide analysis |
| 3 | slot26 clean, 8buy DEF | `MT31 HP=1249 ATK=76 DEF=64 G=176 YK=4` | `MT40 HP=556 ATK=170 DEF=198 G=926 YK=3`, simple stock `1169.0` | `best/zone3_slot26_clean_walk.json`, `best/zone3_slot26_clean_walk.md` | Zone 4 pending |
| 4 | save37 HP leaderboard | `MT40 HP=78 ATK=166 DEF=218 G=2269 YK=4` | `MT50 HP=22264 ATK=418 DEF=517 G=1235 YK=4` | `best/post40_hp_leaderboard_summary.json`, `best/post40_hp_leaderboard_walk.json`, `best/post40_hp_leaderboard_walk.md`, `best/51_20260627113720_hp22264.h5route` | saved to slot42 |

## Reproduction Notes

For guide-chain reproduction, use the artifacts in this order:

1. Run `best/guide_boss_walk.md` through the 10F boss and collect the post-boss supply state used by Zone 2.
2. Replay `guide_after_mt10_boss_supply` inside `best/zone2_canonical_replay.json` / `best/zone2_canonical_walk.md`.
3. Recreate or load the save36 bridge checkpoint: `MT31 HP=1276 ATK=78 DEF=64 G=864 YK=8`.
4. Replay `best/zone3_guide_slot36_to_40_walk.json`.
5. Continue with `best/post40_hp_leaderboard_walk.json`, or load save37 and run the web verifier.

For non-guide exploration, keep the branch separate:

1. Start from `best/current_best_boss_summary.json` / `best/current_best_boss_walk.md`.
2. Compare Zone 2 current-best canonical 3ATK and `2ATK1DEF` artifacts as sibling branches.
3. Use the `2ATK1DEF` line for the current slot26 lineage, and keep the canonical 3ATK line as a separate 20F comparison until it has its own 20F-to-31F bridge.
4. Use slot26 only as the documented non-guide checkpoint until the 20F-to-31F bridge walk is reconstructed.
5. Search a new Zone 4 tail from the slot26 Zone 3 end state before making any final HP claim.

## Verification Status

- Zone 1 current best and guide baseline are locally scored under the current final-score model.
- Zone 2 canonical replay has `errors=0` for both guide and current-best starts.
- Zone 2 `2ATK1DEF` branch summary has `errors=0` and `strict_errors=0`.
- Zone 3 slot36 and slot26 stable walks have `errors=0`.
- Zone 4 save37 tail was web-verified and saved to slot42 after the final redKing battle.
