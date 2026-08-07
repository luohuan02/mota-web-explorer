# Best Walk 产物

跟踪的稳定 walkthrough：

- `route_chains.json`：机器可读的 1-4 区路线族 manifest。
- `zone3_2atk1def_game_route_summary.json`：3 区当前 2ATK1DEF 通用 Game 路线摘要（离线与网页精确一致）。
- `zone3_2atk1def_game_route_walk.json`：同一离线 JSON 派生的 234 步机器 walk，供统一真实点击 verifier 使用。
- `zone3_2atk1def_game_route_walk.md`：由 `gen_zone_walk_md.py` 从同一 JSON 生成人读 walk。
- `route_chains.md`：人读版攻略/非攻略连续性地图。
- `post40_hp_leaderboard_summary.json`：当前 save37 起的生命榜单延续。
- `post40_hp_leaderboard_walk.json`：save37 延续的机器可读实机回放 walk。
- `post40_hp_leaderboard_walk.md`：save37 延续的人读中文 walk。
- `zone2_canonical_replay.json`：2 区回放（攻略和当前最优 1 区起点都适用）。
- `zone2_canonical_walk.md`：中文 2 区攻略/当前最优规范 walk。
- `zone2_2atk1def_branch_summary.json`：2 区 2ATK1DEF 分支摘要，供后续 slot26 探索。
- `zone2_2atk1def_branch_walk.md`：2 区 2ATK1DEF 分支人读 walk（Game 类 auto_sweep 金币）。
- `zone2_2atk1def_branch_walk.json`：2 区 2ATK1DEF 机器可读 walk（供 zone3 walk replayer）。
- `zone2_2atk1def_branch_walk_source.md`：2 区 2ATK1DEF 原始中文 steps 源（game route 输入，金币过期；`zone2_2atk1def_game_route.py` 读它跑 Game 类，勿覆盖）。
- `zone3_guide_slot36_to_40_walk.json`：3 区攻略/save36 到 post-40 状态的快速通过。
- `zone3_guide_slot36_to_40_walk.md`：中文 3 区攻略/save36 快速通过。
- `zone3_guide_slot36_to_37_plan.json`：较早的攻略/save36 到 37F 审计计划。
- `zone3_guide_slot36_to_37_plan.md`：中文较早攻略/save36 到 37F 审计计划。
- `zone3_slot26_clean_walk.json`：3 区非攻略/slot26 干净分支变体。
- `zone3_slot26_clean_walk.md`：中文 3 区非攻略/slot26 干净分支 walk。
- `current_best_boss_walk.md`：当前最优 final-score Boss 路线（1 区，Game 类 auto_sweep 金币，G=313）。
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

## auto_sweep 与 walk 金币标注

1/2 区 walk 的金币标注由 **Game 类（auto ON，含 auto_sweep）** 离线推导生成，不是旧
search 模型。关键点：

- auto 配置：`__auto__={battle,item,wall}` 全开（1/2 区）。auto_sweep 在每次 `go_to`
  后用 BFS 一次性清掉所有可达的零伤怪/道具/暗墙。
- **显式动作**（open/kill/take/pass/trigger）由玩家点击触发；**隐式清理**（auto_sweep
  清的零伤怪/道具）在 .md 行末 `(auto: xNyN eid, ...)` 注明。
- 金币/属性标注是 **auto_sweep 后**的实机值。部分自动击杀 Game 类 note 未详（金币已
  计入 delta，行末标 `(auto: +NG)`）。
- 旧 .md（`gen_best_current_boss_walk.py` 产出）金币过期（无 auto_sweep 隐式击杀），
  已原地覆盖（git 历史保留）。

重生流程：
1. 跑 Game 类：`python scripts/search/zone1_game_route.py`（1 区）或
   `python scripts/search/zone2_2atk1def_game_route.py`（2 区 2ATK1DEF），产出
   `best/<zone>_walk.json`（recording_seed_to_game.py 产出在 `best/`）。
2. 生成 .md + summary：`python scripts/build/gen_zone_walk_md.py --game-route-json <json>
   --md <md> --summary-json <summary> --zone <N> --old-final-gold <old>`。

实机验证（统一点击 verifier `live_zone3_mouse_replayer_cdp.js`，1-4 区通用；旧 zone 专用 runner 已于 2026-08-08 pre-cleanup 删除，git tag `pre-cleanup-2026-08-08` 可恢复）：
- 3 区（2区2攻3区3攻5防录像线 stage-2）：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk best/zone3_2atk3atk5def_recording_walk.json --load-slot 33 --target-click-only --set-auto battle=true,item=nopotion,wall=true`
- 全程（save32 MT20 -> MT41）：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk best/zone3_2atk3atk5def_recording_full_walk.json --load-slot 32 --target-click-only --set-auto battle=true,item=nopotion,wall=true`

当前状态：
- 1 区 G=313（Game 类 auto_sweep），**MT9 末 G=67 实机已对齐**。
- 2 区 2ATK1DEF G=1146（Game 类 auto_sweep 预测，**未实机验证**，+216G 含 36 零伤怪自动击杀）。
- 2 区 canonical G=989（predicted，未实机验证）。


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

当前留镐 2ATK1DEF 分支已有自己独立的 4 区尾段：从槽150的 MT41 HP=45 检查点出发，共享 `Game` 生成451步，提前取得31F红蓝宝石与32F红蓝宝石，并联合枚举攻/防/生命商店；胜者商店序列为防、防、防、攻、生命。44F神圣盾后动态切换 `item=true`，35F魔龙只在拿刀前的强制阶段击杀。网页 target-click-only 为0数值差异，纯净版 TE 终态为 `MT50 HP=23076 ATK=417 DEF=475 YK=5 BK=1 G=906`（Boss前G=406）。稳定产物为 `best/zone4_2atk1def_te_hp23076_{summary,walk,live_verify,resource_audit,gem_damage_audit,macro_astar,terminal_astar}.*`；同target261逐伤害组审计证明三组早期宝石净省2365纯伤，固定点HP增量为0；宏 A* 的8个一跳邻居均有成功或明确失败结果，0个缺失，比20137提升2939HP。该邻域结果不是全图最优证明，且没有复用 save37 的22264尾段。旧20137候选曾因通用筹资器提前杀35F魔龙而误判31/32F宝石收益；筹资器现统一尊重 `Game.no_auto_farm`。

Phase-1 / 10F 当前最优：

```text
HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=305 dmg=2454 door=41/2/1 final-score=1376.5
```

要保留的重要源/资源路径：

- `AGENTS.md`、`CLAUDE.md`、`README.md`、`.gitignore`
- `config/`、`data/`、`src/`、`scripts/`、`tests/`
- `browser-profile/` 仅本地，存放 h5mota 浏览器存档/profile。
- 当前策略脚本：`scripts/search/post9_gem_supply_search.py`、`scripts/search/post9_action_search.py`、`scripts/search/post9_resource_group_search.py`、`scripts/search/post9_merchant_seed_search.py`、`scripts/search/run_corrected_phase1_best_boss_until_deadline.py`。
- 当前修正分数/搜索脚本：`scripts/audit/compare_merchant_resource_paths.py`、`scripts/long_merchant_phase1_search.py`、`scripts/rescore_merchant_phase1_cache.py`、`scripts/gen_corrected_merchant_phase1_best_walk.py`、`scripts/build/gen_best_current_boss_walk.py`。
- 攻略/延后脚本：`scripts/baseline/fixed_shield_strategy.py`、`scripts/baseline/replay_user_post9_route.py`、`scripts/search/continue_delayed_phase1_with_post9_resource.py`、`scripts/build/gen_delayed_phase1_detailed_walk.py`、`scripts/audit/compare_delayed_phase1_vs_user_guide.py`。
- 测试：`tests/run_merchant_fullmap_score_test.py`，以及现有 solver/search 回归测试。

注意：被 git 忽略的 `outputs/` 里旧的 `1482.5` 产物已过期。它们因 MT10 特殊动作守卫而失效——MT10 资源不得在 MT9 upFloor 路线实际打开前可达。

`outputs/` 仍被 git 忽略，可存放临时搜索运行/检查点。
