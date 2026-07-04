# 路线链

本文件是 `best/` 下稳定路线产物的人读索引。机器可读版本是 `best/route_chains.json`。

游戏：https://h5mota.com/games/51/

官方榜单/论坛：https://h5mota.com/tower/?name=51

攻略基线：https://www.taptap.cn/moment/15225056477054087

## 连续性规则

- 不要把 slot36/save37 攻略检查点与 slot26 非攻略检查点混用，除非有 bridge walk 证明状态匹配。
- `guide_chain_to_22264` 是检查点链接的，post-40 尾段已网页验证，但项目仍缺一条拼接的 1F-50F 实机回放。
- `non_guide_current_best_branch` 稳定到 3 区 slot26 clean 完成，但其 4 区尾段待定。未经新搜索/回放，22264 尾段不得复用到 slot26。
- 当前跟踪的缺口是 20F 到 31F：bridge 以浏览器存档检查点形式存在，还没作为 `best/` 里机器可读 walk 跟踪。

## 链路概览

| 链 | 段顺序 | 状态 | 最终 |
|---|---|---|---|
| `guide_chain_to_22264` | 1 区攻略 -> 2 区攻略 -> save36 bridge -> 3 区 slot36 -> 4 区 save37 | 检查点链接；尾段网页验证；拼接回放待定 | `HP=22264 ATK=418 DEF=517 G=1235 MT50 x6y5` |
| `non_guide_current_best_branch` | 1 区当前最优 -> 2 区当前最优 2ATK1DEF 分支 -> slot26 bridge -> 3 区 slot26 -> 4 区待定 | 分支谱系；非连续通关；2 区当前最优 canonical 3ATK 是兄弟对比分支 | 最优干净 3 区 HP 状态：`HP=556 ATK=170 DEF=198 G=926 MT40 x6y1` |

## 各区产物

| 区 | 变体 | 起点 | 终点 | 产物 | 连接到 |
|---|---|---|---|---|---|
| 1 | 攻略基线 | 新游戏/固定前缀 | Boss：`HP=25 ATK=27 DEF=27 G=304`，补给后：`HP=625 ATK=30 DEF=30 YK=3` | `best/guide_boss_walk.md` | 2 区攻略 |
| 1 | 当前最优 | 新游戏/固定前缀 | Boss：`HP=122 ATK=27 DEF=27 G=305`，补给后：`HP=722 ATK=30 DEF=30 YK=3` | `best/current_best_boss_summary.json`、`best/current_best_boss_walk.md` | 2 区当前最优 |
| 2 | 攻略 canonical 3ATK | `MT10 HP=625 ATK=30 DEF=30 G=304 YK=3` | `MT20 HP=76 ATK=72 DEF=58 G=842 YK=5` | `best/zone2_canonical_replay.json`、`best/zone2_canonical_walk.md` | save36 bridge |
| 2 | 当前最优 canonical 3ATK | `MT10 HP=722 ATK=30 DEF=30 G=305 YK=3` | `MT20 HP=203 ATK=72 DEF=58 G=838 YK=3` | `best/zone2_canonical_replay.json`、`best/zone2_canonical_walk.md` | 未来 20F->31F bridge |
| 2 | 当前最优 2ATK1DEF 分支 | 当前最优 10F 补给后家族 | `MT20 HP=577 ATK=70 DEF=66 G=930 YK=1` | `best/zone2_2atk1def_branch_summary.json`、`best/zone2_2atk1def_branch_walk.md` | slot26 bridge |
| 3 | 攻略 slot36 快速通过 | `MT31 HP=1276 ATK=78 DEF=64 G=864 YK=8` | `MT40 HP=78 ATK=166 DEF=218 G=2269 YK=4` | `best/zone3_guide_slot36_to_40_walk.json`、`best/zone3_guide_slot36_to_40_walk.md` | 4 区 save37 |
| 3 | 攻略 slot36 到 37F 计划 | 同 slot36 起点 | `MT37 HP=572 ATK=150 DEF=154 G=438 YK=2` | `best/zone3_guide_slot36_to_37_plan.json`、`best/zone3_guide_slot36_to_37_plan.md` | 仅中间审计 |
| 3 | slot26 clean，7买 DEF | `MT31 HP=1249 ATK=76 DEF=64 G=176 YK=4` | `MT40 HP=224 ATK=170 DEF=182 G=1846 YK=3`，simple stock `1297.0` | `best/zone3_slot26_clean_walk.json`、`best/zone3_slot26_clean_walk.md` | 非攻略分析 |
| 3 | slot26 clean，8买 DEF | `MT31 HP=1249 ATK=76 DEF=64 G=176 YK=4` | `MT40 HP=556 ATK=170 DEF=198 G=926 YK=3`，simple stock `1169.0` | `best/zone3_slot26_clean_walk.json`、`best/zone3_slot26_clean_walk.md` | 4 区待定 |
| 4 | save37 生命榜单 | `MT40 HP=78 ATK=166 DEF=218 G=2269 YK=4` | `MT50 HP=22264 ATK=418 DEF=517 G=1235 YK=4` | `best/post40_hp_leaderboard_summary.json`、`best/post40_hp_leaderboard_walk.json`、`best/post40_hp_leaderboard_walk.md`、`best/51_20260627113720_hp22264.h5route` | 存到 slot42 |

## 复现说明

攻略链复现，按此顺序使用产物：

1. 跑 `best/guide_boss_walk.md` 到 10F Boss，收集 2 区要用的 Boss 后补给状态。
2. 回放 `best/zone2_canonical_replay.json` / `best/zone2_canonical_walk.md` 里的 `guide_after_mt10_boss_supply`。
3. 重建或加载 save36 bridge 检查点：`MT31 HP=1276 ATK=78 DEF=64 G=864 YK=8`。
4. 回放 `best/zone3_guide_slot36_to_40_walk.json`。
5. 接 `best/post40_hp_leaderboard_walk.json`，或加载 save37 跑网页验证器。

非攻略探索，保持分支独立：

1. 从 `best/current_best_boss_summary.json` / `best/current_best_boss_walk.md` 起。
2. 把 2 区当前最优 canonical 3ATK 和 `2ATK1DEF` 产物作为兄弟分支对比。
3. `2ATK1DEF` 线用于当前 slot26 谱系，canonical 3ATK 线作为单独 20F 对比，直到它有自己的 20F-31F bridge。
4. 在 20F-31F bridge walk 重建前，slot26 只作为文档化的非攻略检查点。
5. 在任何最终 HP 声明前，从 slot26 的 3 区终态搜索新的 4 区尾段。

## 验证状态

- 1 区当前最优和攻略基线在当前 final-score 模型下本地评分。
- 2 区 canonical 回放在攻略和当前最优起点下都 `errors=0`。
- 2 区 `2ATK1DEF` 分支摘要 `errors=0` 且 `strict_errors=0`。
- 3 区 slot36 和 slot26 稳定 walk `errors=0`。
- 4 区 save37 尾段已网页验证，最终红魔王战后存到 slot42。
