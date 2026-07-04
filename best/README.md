# Best Walk 产物

跟踪的稳定 walkthrough：

- `route_chains.json`：机器可读的 1-4 区路线族 manifest。
- `route_chains.md`：人读版攻略/非攻略连续性地图。
- `post40_hp_leaderboard_summary.json`：当前 save37 起的生命榜单延续。
- `post40_hp_leaderboard_walk.json`：save37 延续的机器可读实机回放 walk。
- `post40_hp_leaderboard_walk.md`：save37 延续的人读中文 walk。
- `zone2_canonical_replay.json`：2 区回放（攻略和当前最优 1 区起点都适用）。
- `zone2_canonical_walk.md`：中文 2 区攻略/当前最优规范 walk。
- `zone2_2atk1def_branch_summary.json`：2 区 2ATK1DEF 分支摘要，供后续 slot26 探索。
- `zone2_2atk1def_branch_walk.md`：中文 2 区 2ATK1DEF 分支 walk。
- `zone3_guide_slot36_to_40_walk.json`：3 区攻略/save36 到 post-40 状态的快速通过。
- `zone3_guide_slot36_to_40_walk.md`：中文 3 区攻略/save36 快速通过。
- `zone3_guide_slot36_to_37_plan.json`：较早的攻略/save36 到 37F 审计计划。
- `zone3_guide_slot36_to_37_plan.md`：中文较早攻略/save36 到 37F 审计计划。
- `zone3_slot26_clean_walk.json`：3 区非攻略/slot26 干净分支变体。
- `zone3_slot26_clean_walk.md`：中文 3 区非攻略/slot26 干净分支 walk。
- `current_best_boss_walk.md`：当前最优 final-score Boss 路线。
- `guide_boss_walk.md`：攻略基线 Boss 路线。
- `current_best_boss_summary.json`：当前最优的机器可读摘要。

分数模型：

- `1YK = 50HP`、`1BK = 4YK = 200HP`、`100G = 1YK = 50HP`。
- `final-score` 包括当前 HP/钥匙/金币存量 + 全图剩余资源组。
- 未来怪物金币按零伤害未来收入计；未开门仍扣钥匙价值。
- 未用商人是未来净资源，商人购买消耗实际金币。
- 游戏地址：https://h5mota.com/games/51/
- 官方榜单/论坛：https://h5mota.com/tower/?name=51
- 攻略来源：https://www.taptap.cn/moment/15225056477054087

当前 save37 起的生命榜单延续：

```text
HP=22264 ATK=418 DEF=517 YK=4 BK=0 RK=0 G=1235 dmg=27134 door=53/10/7
source save=37 verified save=42
```

该结果从浏览器存档槽 37 起网页验证，最终红魔王战后存到 42 号槽。它还不是从 1F 到通关的单一连续证明；要先拼接并验证前面的 1F-40F 前缀，才能称为整局最优。

路线族索引：

```text
best/route_chains.json
best/route_chains.md
```

当前攻略链路：

```text
zone1.guide_baseline
-> zone2.guide_canonical
-> bridge.save36_mt20_to_mt31
-> zone3.guide_slot36_to40
-> zone4.save37_hp_leaderboard
```

当前非攻略/搜索分支：

```text
zone1.current_best
-> zone2.current_best_2atk1def_branch
-> bridge.slot26_mt20_to_mt31
-> zone3.slot26_clean_boss8def
-> zone4.slot26_tail_pending
related sibling: zone2.current_best_canonical
```

非攻略分支在给出最终 HP 声明前必须有自己独立的 4 区尾段；不得把 save37 的 22264 尾段复用到 slot26。

Phase-1 / 10F 当前最优：

```text
HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=305 dmg=2454 door=41/2/1 final-score=1376.5
```

要保留的重要源/资源路径：

- `AGENTS.md`、`CLAUDE.md`、`README.md`、`.gitignore`
- `config/`、`data/`、`src/`、`scripts/`、`tests/`
- `browser-profile/` 仅本地，存放 h5mota 浏览器存档/profile。
- 当前策略脚本：`scripts/post9_gem_supply_search.py`、`scripts/post9_action_search.py`、`scripts/post9_resource_group_search.py`、`scripts/post9_merchant_seed_search.py`、`scripts/run_corrected_phase1_best_boss_until_deadline.py`。
- 当前修正分数/搜索脚本：`scripts/compare_merchant_resource_paths.py`、`scripts/long_merchant_phase1_search.py`、`scripts/rescore_merchant_phase1_cache.py`、`scripts/gen_corrected_merchant_phase1_best_walk.py`、`scripts/gen_best_current_boss_walk.py`。
- 攻略/延后脚本：`scripts/fixed_shield_strategy.py`、`scripts/replay_user_post9_route.py`、`scripts/continue_delayed_phase1_with_post9_resource.py`、`scripts/gen_delayed_phase1_detailed_walk.py`、`scripts/compare_delayed_phase1_vs_user_guide.py`。
- 测试：`tests/run_merchant_fullmap_score_test.py`，以及现有 solver/search 回归测试。

注意：被 git 忽略的 `outputs/` 里旧的 `1482.5` 产物已过期。它们因 MT10 特殊动作守卫而失效——MT10 资源不得在 MT9 upFloor 路线实际打开前可达。

`outputs/` 仍被 git 忽略，可存放临时搜索运行/检查点。
