---
name: mota-route-audit
description: 用于审计魔塔/h5mota 攻略合法性、回放攻略路线、生成中文 walk 报告、对比剩余资源、检查路径顺序 bug,或验证路线可回放且没有不可能的门/怪顺序。
---

# 魔塔路线审计与报告 Skill

这个 skill 用于重放路线、检查顺序合法性、生成 walk、生成剩余资源差异报告。搜索候选请先用 `mota-route-search`；网页实机验证请用 `mota-live-verify`。

## 输出约定

- 面向人的 Markdown 报告必须使用中文标题、中文表头、中文阶段名。
- JSON 字段名可以保持英文，方便脚本消费。
- 坐标统一写成 `MT楼层 x横坐标y纵坐标`。
- 网页复现 walk 默认按“核心摘要 -> 关键节点 -> 阶段分数 -> 自动设置校验 -> 详细步骤 -> 校验结果”输出。
- 详细步骤只保留中文动作、坐标、数值变化和必要备注；不要每步重复完整前后状态。完整状态以“快照@步数”行插入详细步骤中，便于复现时顺路对照。
- 快照不要太密：普通间隔约 50 步以上；拿关键道具、过 Boss/大事件、重要补给/商店后可立即插入快照，不受 50 步限制。
- 大阶段结尾必须打印 `dmg`、开门数、`final-score` 或当前脚本对应的综合分，并列出关键组成，例如库存分、剩余资源组价值、未来 0 伤怪金币、商人/商店残值、钥匙/金币折算。
- 自动操作造成的拾取/清怪应写为“自动处理跳过”，但不能丢掉由上一动作触发的 HP、钥匙、金币和地图块变化。
- 自动资源组要按真实点击入口压缩成一步：选择会触发自动 BFS 的近端目标格作为点击点，把同组被自动拾取/清理的资源写进备注，不要把本地逐资源顺序逐行输出。典型例子：9F 中部资源组应点击 `MT9 x7y4`，备注自动处理 `x5y4 黄钥匙`、`x6y5 红宝石`、`x7y6 红头怪`，然后下一步直接点 `x4y5` 黄门。
- 开门后不会立刻触发自动 BFS；审计 walk 时不要假设门后资源已经结算，必须等后续移动、战斗、拾取或事件触发后再记录自动处理。
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
- 10F 骷髅队长前的 `MT10 x6y2` 是剧情事件格；Boss 后清怪和开门完成后，walk 必须先记录/执行 `MT10 x6y2` 事件，再记录 `MT10 x6y1` 队长战斗，不能从远处直接点击 `x6y1`。
- 审计资源缓存时同时检查 `event_groups`、`event_map_changes` 和 `npc_resource_groups`：例如 MT15 章鱼周围 `tile=17` 触发前阻断、战斗后消失；商店侧翼不可作为通路；老人/商人/商店要作为状态转移而不是普通拾取物。
- 审计剩余资源时按战略层级看：`core_target` 遗漏通常是路线大问题；`secondary_stat` 遗漏要看是否影响伤害/商店阈值；`support_resource` 遗漏多用于补钥匙、补血或凑金币；`conversion_node` 必须核对真实金币、钥匙、购买次数、一次性/可重复限制和使用时机。
- 审计宏策略时不要把攻略顺序当唯一合法顺序；对地震卷轴、双倍金币、圣盾、魔龙雪花、49F 假魔王/下楼器等关键节点，要说明当前候选采用的 ordering，以及是否和替代 ordering 做过对比。
- 剩余资源差异里是否有明显顺路资源没有拿。

## 大阶段分数边界

- 1区：10F Boss 后，必要时另列 10F Boss 后补给状态。
- 2区：20F Boss/吸血鬼后；若路线从 20F 接到 31F 存档桥，另列 31F 桥接状态。
- 3区：40F Boss 后 / save37 或 slot26 对应的 40F 终点。
- 4区不只看单个 Boss，按策略节点分段：40F 后起点、地震卷轴买入/使用、神圣盾/圣盾后、双倍金币/49F 假魔王后、35F 魔龙雪花后、24F 上 50F 前、最终真魔王后。脚本有更细 segment 时，可以在这些节点之间追加局部分数快照。

## 纯净版-TE / Post-40 审计清单

- 报告中标明版本目标：`2026 复刻版 / 纯净版-TE / 生命`。不要把特性版技巧或旧版 TE 技巧混入纯净版 replay。
- 检查 43F 初始阶段是否误开 `MT43 x3y1` 黄门；若打开，必须说明它比拿盾后从右侧区域进入更优。
- 检查凑 4000G 买地震卷轴的怪物集合是否过度溢出金币，尤其是 `MT32 x8y7 redKnight`、`MT36 x9y1 redKnight`；优先寻找 0 伤/低伤/同楼层批处理替代。
- 标记“一层杀一怪”式金币农场和血瓶清扫，这通常是步数和楼层往返没有批处理的信号。
- 审计 41F 右上区域时，不要只看目标格可达。击杀 `MT41 x10y2 redWizard` 后，若 `MT41 x8y7 slimelord` 未清，实机楼层传送可能提示“无法到达任何一个楼梯边”；walk 必须保证真实可到楼梯或先清连通怪。
- 检查 46F 蓝门路线是否比较过 `x3y1` 入口；若终局剩金币无法消费，额外金币不应被误记为 HP 收益。
- 审计 45F 上楼飞行器路线时，保留用户指出的低损绕法：拿道具前清 `x6y2/x6y3/x7y3/x7y4/x7y5/x6y5/x5y6` 附近，拿完后只让 `x6y3` 再触发 100 血损耗。
- 关键节点报告应分段列出：地震卷轴、神圣盾、圣盾、双倍金币、49F 假魔王、35F 魔龙、24F 大法师、49F 圣剑、44F 圣神剑。

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
