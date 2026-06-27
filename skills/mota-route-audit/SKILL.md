---
name: mota-route-audit
description: Use this skill whenever auditing Magic Tower / h5mota walkthrough legality, replaying a guide route, generating Chinese walk reports, comparing remaining resources, checking path order bugs, or validating that a route can be replayed without impossible door/enemy ordering.
---

# 魔塔路线审计与报告 Skill

这个 skill 用于重放路线、检查顺序合法性、生成 walk、生成剩余资源差异报告。搜索候选请先用 `mota-route-search`；网页实机验证请用 `mota-live-verify`。

## 输出约定

- 面向人的 Markdown 报告必须使用中文标题、中文表头、中文阶段名。
- JSON 字段名可以保持英文，方便脚本消费。
- 坐标统一写成 `MT楼层 x横坐标y纵坐标`。
- 只列差异时，不输出整张资源表。

## 常用命令

审计或解释 1-4 区路线关系时，先看：

- `best/route_chains.json`
- `best/route_chains.md`

这两个文件记录攻略线、非攻略/搜索线、save36/slot26/save37 桥接关系，以及哪些段能连续复现。

审计 37 号存档 / 40F 后续生命榜单 walk：

```powershell
python scripts\search_post40_guide_route.py
node scripts\prepend_40f_prefix_walk.js
```

稳定结果在：

- `best/route_chains.json`
- `best/route_chains.md`
- `best/post40_hp_leaderboard_summary.json`
- `best/post40_hp_leaderboard_walk.json`
- `best/post40_hp_leaderboard_walk.md`
- `best/zone2_canonical_replay.json`
- `best/zone2_canonical_walk.md`
- `best/zone2_2atk1def_branch_summary.json`
- `best/zone2_2atk1def_branch_walk.md`
- `best/zone3_guide_slot36_to_40_walk.json`
- `best/zone3_guide_slot36_to_40_walk.md`
- `best/zone3_slot26_clean_walk.json`
- `best/zone3_slot26_clean_walk.md`

## 清理规则

审计完成后按下面规则整理文件：

- `best/` 是稳定 artifact 区。只有可复现、可解释、能接入 `best/route_chains.*` 的结果放这里。
- `outputs/` 是临时区。对应结果已经复制到 `best/` 后，`outputs/results`、`outputs/reports`、`outputs/walkthroughs` 里的同名生成物可以删除或重新生成。
- `outputs/results/*.pkl` 是搜索缓存，不作为审计证据；除非正在恢复长时间搜索，否则可以删除。
- `outputs/logs/`、`outputs/screenshots/`、`__pycache__/`、`tmp/` 都是本地缓存，上传 git 前不需要保留。
- 对仍被脚本读取的 snapshot 文件要谨慎，例如 `slot26_snapshot.json`、`slot36_snapshot.json`、`guide40_current_snapshot.json`。如果删除，需要能从浏览器存档重新导出，或先把必要 checkpoint 迁移到 tracked artifact。
- 删除前先确认该结果没有作为 `best/route_chains.json` 的唯一来源；如果是唯一来源，先保留或把生成命令/状态补进 manifest。

重放二区攻略/当前最优起点：

```powershell
python scripts\replay_zone2_guide_route.py
```

生成二区宏策略搜索结果和最佳 walk：

```powershell
python scripts\search_zone2_macro_routes.py
```

审计同层路径是否穿过未清资源、门或暗墙：

```powershell
python scripts\audit_zone2_path_legality.py
```

生成剩余资源差异：

```powershell
python scripts\report_zone2_remaining_diff.py
```

基础回归：

```powershell
python -m py_compile scripts\post9_resource_group_search.py scripts\compare_merchant_resource_paths.py scripts\merchant_finalscore_audit.py scripts\probe_mt7_red_first_swap_sequence.py scripts\local_order_refine_current_best.py scripts\gen_local_refined_best_walk.py scripts\replay_zone2_guide_route.py scripts\search_zone2_macro_routes.py scripts\audit_zone2_path_legality.py scripts\report_zone2_remaining_diff.py scripts\live_zone2_runner.py
python tests\run_merchant_fullmap_score_test.py
python tests\run_pareto_test.py
python tests\run_floorsearch_test.py
```

## 审计重点

优先检查这些问题：

- 门和怪物顺序是否反了，例如必须先打怪才能到门，却先记录开门。
- 路线是否通过了还没打开的暗墙、机关门或 Boss 事件区域。
- 商人购买是否消耗真实金币，而不是只作为剩余资源加分。
- 楼层传送是否是道具行为；报告和实机脚本不要直接把 `core.changeFloor(...)` 当合法移动。
- Boss 事件是否改变周围怪物，例如 20F 吸血鬼事件后不能再单独击杀合并前的大蝙蝠。
- 剩余资源差异里是否有明显顺路资源没有拿。

## 二区特殊修正

当前 replay 已显式处理 `MT1 x4y3` 与 `MT1 x1y3`：

- 当前最优 10F 后起点没有清 `MT1 x4y3` 黄门。
- 真实游戏飞到 1F 后进入左下资源区需要先开这个门。
- 既然已经开门，`MT1 x1y3 红血瓶` 是顺路收益，应在 replay 和 walk 中记录。

如果未来报告再次显示 `MT1 x1y3 物品:红血瓶` 只剩在最优路线中，优先怀疑 replay 或宏选项回退了。

## 报告检查顺序

1. 先看命令输出里 `errors=0`、`warnings=0` 或中文等价项。
2. 再看 Markdown 的阶段表，确认关键节点状态符合预期。
3. 最后看详细 walk，抽查用户指出过的风险段：
   - 7F/6F 商人顺序
   - 11F 左下补钥匙和盾房
   - 18F 暗墙与兽人武士
   - 19F 中路十字架
   - 14F 三兽人武士红钥匙
   - 20F 吸血鬼事件
