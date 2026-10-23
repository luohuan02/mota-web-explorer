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
- 开门 sweep 归属（2026-08-31 定稿）：hero 点击开门会经 walk-through 踏上刚开的门格，auto sweep 从门格起跑并归入**门步本身**（`Game._apply_door_live`，含门格带火时的踏格清火）；审计 walk 时门后可达资源应记在门步，不要推到后续步。例外：事件开门、Boss 掉落等**非 hero 移动**的开门不触发 auto，仍等下一次 hero 移动/战斗/拾取再结算。
- strict walk 必须以一次真实 target-click 为原子。寻路途中一旦遇到战斗、拾取、开门或事件，就结束当前原子、结算本次允许的 auto，再从新状态重新寻路；不能让一条离线路径跨过多个动作格后才统一 auto。
- 事件开门、Boss 掉落、击杀后生成资源等地图变化本身不触发 auto。触发动作只记录自身结果；下一次真实移动/战斗/拾取才可结算新出现或新可达的资源组。
- 被 auto 消费的资源坐标应在机器路线状态中标记为已完成，后续种子再次引用这些坐标时直接跳过，不能生成空地移动；Markdown 只能忠实格式化机器 JSON，不能在展示层隐藏多余步骤。
- 压血不能只从 JSON 删除血瓶再做 HP 算术。每个删瓶候选必须重新检查可达性和战斗存活；若血瓶是封闭资源的唯一入口，应把“血瓶 + 后续资源”作为同一资源组整体保留或整体跳过。
- 只列差异时，不输出整张资源表。

## 常用命令

审计或解释 1-4 区路线关系时，先看：

- `best/route_chains.json`
- `best/route_chains.md`

这两个文件记录攻略线、非攻略/搜索线、save36/slot26/save37 桥接关系，以及哪些段能连续复现。

按楼层拆分 + 剩余资源对账（分层剩余 + 汇总 gold/钥匙/商店 2-sheet xlsx）：用 `scripts/audit/gen_recording_floor_breakdown.py`（一条命令自动读 walk.provenance；分层 sheet 列权威 Game 重放的全部 50 层，接续段未到楼层标 `*` 继承种子存档末态；拼接 walk 用 `--rem-walk <接续段walk>` 提供权威重放 provenance）。**战略节点累计快照**（区界楼层/魔龙前/TE最终boss前）加 `--checkpoints 11层,31层,41层,魔龙前,TE最终boss前` 追加第三个「检查点记录」sheet（dmg/恢复血量/药瓶恢复HP/消耗yk·bk·rk/剩余yk·bk 自己+地图+合计/获得金币合计+打怪双口径/持有金币/地图剩余金币/商店购买情况；打怪口径=实机「数据统计」金币）——**不要为单条录像手写一次性 tmp 报告脚本**（41206 教训）。**关键口径与陷阱详见 `mota-route-search/floor_breakdown_experience.md`**（尤其：剩余怪金/剩余资源必须用共享 Game 重放 g.floors，walk-diff 会因 auto_sweep note 截断高估；打怪金=金币增量分类含事件生成怪；钥匙分裸拾取/商人买；剩余商人/事件剔消费与纯剧情与 step-on 已触发；TE最终boss前必须限定 MT50 真魔王，49F 假魔王 eid 同为 redKing）。

多条已验证 walk 的整体+逐层差异对比（差异层门坐标/击杀/金币 + checkpoint 表 + 结论行）：用 `scripts/audit/gen_route_compare.py --walk 标签=walk.json(可重复) --out x.xlsx --note 结论(可重复)`。逐层差异表 N==2 布局（2026-09-17 用户定稿）：dmg/黄/蓝/金币每组×2 列后插 diff 具体值列（前一线−后一线，红门不加；不用 Excel 公式，脚本 data_only 可直读），门坐标差异=真 diff 只列各线独有坐标。checkpoint 取首次到达/首次攻略完（末次离层会被飞行回访污染）；门经济对比用「各层开门耗钥差异」口径。详见 `mota-route-search/floor_breakdown_experience.md`「多线对比报告」节。

**产物固定校验（每次生成 breakdown/compare 后必须跑，全 PASS 才算完成）**：`python scripts/audit/verify_route_artifacts.py --walk <walk.json>`。六项：① 权威重放 final==walk final（防漂移）；② 击杀/拾取格集合==walk（两侧同用「击杀步+note 条目」提取——**静态差集法对事件生成怪失效**（MT10 骷髅/MT50 redKing 均为 tile 17/0 事件格），且 sweep 击杀在 Game 步内折叠进 note，两侧必须同一套提取）；③ 钥匙对账每色=0（note 条目优先、商人步排除）；④ 金币恒等式 Σ正−Σ负==final−start；⑤ 门闭合残差逐层列出（须=魔法钥匙 bigKey/事件开门，人工确认——MT41 19/16=bigKey、MT1/3/39 各 1=事件开门为已知项）；⑥ 剩余怪金 ≤ walk-diff 上界。

审计 37 号存档 / 40F 后续生命榜单 walk：

```powershell
python src/solver/game_route.py
node scripts\build\prepend_40f_prefix_walk.js
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
python scripts\baseline\replay_zone2_guide_route.py
```

生成二区宏策略搜索结果和最佳 walk：

```powershell
python scripts\search\search_zone2_macro_routes.py
```

审计同层路径是否穿过未清资源、门或暗墙：

```powershell
python scripts\audit\audit_zone2_path_legality.py
```

生成剩余资源差异：

```powershell
python scripts\audit\report_zone2_remaining_diff.py
```

## final-score 0 伤口径对比（含剩余资源）

比较两条路线**不要只看 `final-stock`**（存量 = HP + YK×50 + BK×200 + G/2），它会漏掉未拾资源。用 **`final-score` = stock + 剩余资源组**（0 伤拾取、BK=200、未开门扣钥匙、0 伤怪金币 money/2；宝石/红钥匙默认 0 除非 atk/def<27 或脚本另有目标）。

**关键特性**：资源在存量还是剩余（0 伤可达）final-score 总值等价 -- 拾取只把资源从 residual 移到 stock，不改变 final-score。所以"吃不吃 boss 后资源"在 final-score 口径下不影响对比，只影响存量分布。同理 auto ON/OFF 若资源都 0 伤可达，final-score 不变（auto ON 把资源从 residual 移到 stock）。

录像转 Game 后用 `recording_to_game.py --residual-out` 导出 zone1-20 剩余资源分类 + final-score：

```powershell
python scripts\search\recording_to_game.py --route <decoded_route.json> --statlog <statlog_pre.json> --save1 best\checkpoints\save1_mt4_snapshot.json --out <conv.json> --auto battle=true,item=true,wall=true --stop-floor MT21 --residual-out <res.json>
```

**`--paths` 现为可选**（2026-08-09）：`recording_to_game.py` 无 `--paths` 能跑通多数录像
（V1 买 rk 线 0 mismatch 到 MT31 HP=1232 web 复验全过）。旧"Game 寻路必发散、须喂
captured path"结论已推翻 -- 发散根因是 4 个可修通用模型 bug（事件门没开 / 触发格没踩 /
no-op 误跳 spawn 型 trigger / coalesce 折了 shop 目标）。**新录像先跑无 `--paths`**，
发散再退 `--paths`；发散点先按 4 类模型 bug 排查并修 `game_route.py` / converter，**别写
浏览器侧 path 捕获绕过根因**（见 CLAUDE.md「根因优先约束」）。4 修复 + 诊断方法论详见
`mota-route-search/recording_converter_experience.md`「无需 captured path 的 4 个模型修复」。

`res.json` 含：`current_stock`（当前 yk/bk/gold/hp）、`stock`、`residual_value`、`final_score`、`cat_summary`（剩余 YK/BK/药/宝石/未开门/0伤怪金币 分类计数）、`cats`（每类坐标明细）、`residual_breakdown`（逐项 +-）。

对比要点：
- 当前存量 yk/bk/gold + 剩余 yk/bk/药瓶/0伤怪金币 分类逐项对比。
- **花费钥匙开门的必须扣**：未开黄门 ×50、未开蓝门 ×200（已计入 residual，开门消耗钥匙价值）。
- 用 auto 设置匹配录像的转换跑（auto OFF 录像传 `battle=false,item=false,wall=false`）；auto ON 转换若 mismatch 多（路径分叉）终态不可信，用 auto OFF（web 验证 0 mismatch）的终态更可靠，boss 资源在 final-score 下不必单独补（存量/剩余等价）。
- 0 伤怪金币要求 atk >= enemy.def（cross 对 zombie/zombieKnight/vampire atk×2）；高伤怪不计入 final-score 剩余。
- `final-stock`（只存量）只能当 tie-breaker，不能替代 final-score 对比；它会奖励"多拾资源进存量"的线，惩罚"留资源在剩余"的线，即使两线总资源等价。

基础回归：

```powershell
python -m py_compile scripts\search\post9_resource_group_search.py scripts\audit\compare_merchant_resource_paths.py scripts\audit\merchant_finalscore_audit.py scripts\search\probe_mt7_red_first_swap_sequence.py scripts\build\local_order_refine_current_best.py scripts\build\gen_local_refined_best_walk.py scripts\baseline\replay_zone2_guide_route.py scripts\search\search_zone2_macro_routes.py scripts\audit\audit_zone2_path_legality.py scripts\audit\report_zone2_remaining_diff.py
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
- 44F 神圣盾后确认 `magicImmune=true`，并检查机器 JSON 紧随其后存在 `设置自动`、`auto.item=true`；后续实机也必须回读为 true。只有说明文字或只改 verifier 启动参数不合格。
- 单独列出 49F 封印后每一件事件奖励的坐标、id、倍率和实际增量；不能只看中心三瓶或依赖一条 `auto_sweep` 备注。事件生成后必须再次做全图剩余资源审计。
- 终战前把每层剩余红/蓝药、攻防宝石、钥匙、可杀怪金币列成紧凑差异。黄钥匙按“开门净收益 vs 28F 售卖 100G”审计，蓝/红钥匙按门后资源净收益审计；最终 Boss 后 500G 不算可消费资金。
- `best/` 中声称“HP 最优/压榨完成”的路线必须有固定点审计：可达正 HP 资源为 0、无盈利钥匙/金币转换、有效资金不足下一次 46F 生命商店。未满足时状态只能写“已验证可通关下界”。
- “免费怪”审计不能要求入口不花钥匙。逐组模拟门成本、组内钥匙回收、auto 连锁和金币收益；把净钥匙非负或可由别处补回的门后组组合起来检查商店阈值，而不是只检查单组。
- 终局资金审计必须枚举组合闭包：`当前金币 + 可售黄钥匙 + 门后净金币组` 是否跨过下一档 46F 商店。对同一区域会被一次 auto 同时清掉的目标去重，避免把一个资源口袋重复计价。
- 攻防宝石既要做末局残余清点，也要做“最早可拿时间”审计。若宝石在31F/32F而路线到末局仍未拿，必须比较提前取得后的累计减伤、钥匙成本、金币与商店购买序列，不能仅按终局剩余属性判断。
- 报告每次 46F 商店的类型和序号，并比较最终攻防与 TE Boss 阈值；固定 `攻攻攻攻防` 一类序列不构成优化证明。
- 终局资金报告必须同时给两层账：第一层是无视门、伤害和可达性的宽松上界 `当前金币 + 当前黄钥匙售值 + 剩余黄钥匙售值 + 所有余怪实际金币`；第二层才是共享 `Game` 组合回放得到的可达净值。宽松上界计算要显示幸运金币是否存在及 1x/2x 倍率，Boss 战后金币不得倒算成战前资金。
- 审计每个筹资步骤是否越过 `no_auto_farm` 战略时序。魔龙若出现在“key investment / gold cleanup”等通用筹资备注中，候选直接无效，不能再用最终 HP 比较。
- 不得仅因怪物坐标存在 `afterBattle` 事件就从剩余资源中排除；应由共享 `Game` 执行击杀及事件后地图变化，再按真实金币、门和 auto 副作用计账。
- 提前宝石审计要输出逐战斗差分：宝石取得后每个敌人的基线伤害、候选伤害和累计节省；若分支战斗集合不同，要先定位首个分叉并解释，不能把后续强制怪提前击杀造成的额外伤害归咎于宝石。
- 终局组合搜索的审计起点必须是“强制 TE 事件后、可选资源闭包前”的严格 `Game` checkpoint；报告要列出 checkpoint 状态、状态键包含的事件/商人 flags、宽松资金上界、搜索预算与实际完整 TE 复跑结果。不得把终局零钥匙状态下的“无可达怪”写成全图无 2420G 方案的证明。

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

## 2026-07-10 2区 2ATK1DEF 审计补充

- Markdown 生成时不要输出只有 before/after、没有可见动作的楼层小节；飞行、换层、已清理等被跳过动作不应制造“废动作”段。
- 2区分支文档可以引用 `best/current_best_boss_walk.md` 作为 1区前缀；详细 walk 从 10F boss 后开始，完整 JSON 保留全拼接。
- 审计 `MT9 x1y3 skeletonSoldier` 时，要确认它是否用于立即补 `MT16 x4y10` 黄门所需的 1 把黄钥匙；如果后续不立刻用钥匙，再标为可疑绕路。
- 15F 蓝钥匙商人与 11F 盾房应批处理：先买蓝钥匙，再一次性完成 11F 左下钥匙、蓝门、两个高级法师和银盾，避免额外飞行往返。
- 16F 圣水不要只按当前 HP 加值审计；它随 ATK+DEF 缩放。若 `HP=676 ATK=70 DEF=66` 已能打 20F 吸血鬼并以 `HP=11` 存活，则 20F 前应跳过圣水，留到后续属性更高或 HP 门槛必须时再取/用。
- 19F 十字架前 `x6y4/x6y3` 暗墙要和实机对齐：击杀 `x7y6 rock` 后可以自动拿附近黄钥匙，但不要把两格 fakeWall 完全压进 auto_sweep；walk JSON 应保留显式 pass/take，实机验证要覆盖这一段。

## 2026-07-16 walk .md auto 显示判读（gen_zone_walk_md.py）

审查人读 walk `.md` 时，"属性对但 auto 没写" 或 "HP 突跳无解释" 通常是生成器 `scripts/build/gen_zone_walk_md.py` 的显示层问题，不是路线错。三类根因（已修）：

1. **步内 auto（击杀步 `(auto: 列表)` 漏显）**：Game 类 go_to 路径内击杀折叠把 auto 写成 `"auto: "` 前缀（game_route.py:1385），而 `extract_clear_note` 旧版只认 `"auto_sweep:"`。判读：若击杀步 delta 有 `[YK 0->4]` 但无 `(auto: ...)` 列表，且 note 含 `auto:`，是显示漏显。修复后两种前缀都认。

2. **gap auto（到达步整步消失）**：延迟 auto_sweep 把本步移动中清的资源折进 `step.before`，使 before==after、步内 delta 为空，被 `should_emit_arrive` 当空步抑制。判读：楼层 `before:` 到 `after:` 属性跳变（如 yk 1->2、HP 101->1301）但中间无任何 step 解释，是 gap auto 被抑制。修复后 `delta_before` 用上一发出步的 after（prev_after），gap 计入本步 delta 并放出该步。

3. **击杀步 auto 列表重复目标**：0-dmg 自动击杀目标的点击步（strict_auto_enemy_target）会把被杀目标本身列进 auto（如 `kill bigBat (auto: x9y11 bigBat, x8y11 bluePotion)`）。判读：auto 列表首项 = 被杀坐标即重复。修复后按 step.pos 剔除。

判读 .md 时的基线规则：**每步 `[delta]` 的基线是上一条已发出步的 after，不是本步 before**（正常步两者相等；gap auto 步 before 已含 auto，必须用 prev_after 才能看到变化）。楼层 `before:`/`after:` 应连续（上一楼层 after == 下一楼层 before），不连续说明有 gap auto 或路线问题。

验证 .md 正确性：跑 `python tests/run_zone_walk_md_test.py` + `python tests/run_project_docs_sync_test.py`；逐 step 核对可用 node 脚本扫 `steps[].before/after` 与 .md 的 delta/连续性（参考 `tmp/consistency_check.js`：82 floor block 0 连续性缺口、final after == JSON final）。相关 memory：`gen-md-auto-display-fix`。

注意区分：**显示 bug（上面三类，改 gen_md 即可）** vs **路线废动作（往返楼层/楼梯代飞/0 伤怪主动清，属录像复刻 zone12_recording_autoon.py 继承的录像低效，改路线需重生成+web 验证）**。.md 修好后仍出现的 "废动作" 才是路线问题。

## 2026-07-16 walk 生成管线零手写（协议常量单一真相源）

「录像 -> Game walk JSON -> web 复验 -> 人看 walk」全管线要求：**游戏知识映射只写在 `src/solver/game_route.py` 一处，converter / replayer / gen 零手写**。gen 不得本地定义任何映射，一律 import：

- `ACTION_VERB_EN`：action 中文名 -> 人读 .md 英文动词（含 `破墙`->pass、zone2+ 适配层 `商店/商人/对话/事件/事件奖励/事件战斗`）。`record()` 新增 action 必须在此登记，否则 .md action 行 fallback 中文。
- `SKIP_ACTIONS`（不 emit 的 action，含 zone2 适配层 `事件开门`）/ `FLOOR_TRANSITIONS`（deferred 归因硬边界 `换层/飞行`）。
- `DOOR_KEY`：门 eid -> (钥匙 state key, 开门计数 key)。Game 内部 `_apply_door_live` / `apply_block` / auto 门判断共用同一份。
- `AUTO_KEYS`：`("battle","item","wall")`，`set_auto` 校验与 gen `fmt_auto_config` 共用。
- `Game.TRIGGER_EVENT_DESC`：事件 trigger 格人读描述，与 `trigger_tile_event` 分支一一对应；gen 在 trigger-event pass 步自动加 `(触发: ...)`。

新增 action / 事件触发点 checklist：只改 `game_route.py`（`ACTION_VERB_EN` 登记 / `trigger_tile_event` 分支 + `TRIGGER_EVENT_DESC` 条目）。converter 的 trigger-event 标记由 `apply_block` / `trigger_tile_event` 返回值驱动（无坐标表），gen 描述自动拾取，管线其余脚本零改动。

失败模式（2026-07-16 MT10 (6,9) stall 实证）：通用 `trigger_tile_event` 漏注册某事件格时，converter `step_path` 调 `trigger_tile_event` 返回 False → step note 不打 `trigger-event` → `move:x:y` 的 `_has_trigger` 不分段、把含事件格的 captured path 合并成「直达终点」一步 → replayer 只点终点；但 web automaticRoute 寻路途中踩事件格会**中断、hero 停在事件格** → replayer 期望 hero 在终点 → 位置 mismatch / stall（`game_route.py:466` 早注释过此模式）。判读：replayer 卡在某步、live hero 坐标停在某个事件格而 conv 期望更远的终点，先查该格是否在 `TRIGGER_EVENT_DESC` / `trigger_tile_event` 登记。

区域适配层 vs 通用 Game 类的事件同步：`zoneN_game_route.py` 的 `apply_*` 适配方法可能早建模了某事件（如 zone2 `apply_mt10_supply` 已建模 MT10 (6,9) thief：auto-eat 12 + hero 停 6,9），但 converter 用的是**通用 `Game` 类**、不读适配层。适配层已建模的事件必须**同步**到通用 `trigger_tile_event` + `TRIGGER_EVENT_DESC`，否则 converter 转换时漏中断点。新增事件点先 grep 适配层有无现成建模可参考，避免知识只落在适配层。

验证与判读：

- 改 `game_route.py` / gen 后：重生成 .md 应与改前**零 diff**（行为等价），再跑 `run_zone_walk_md_test` + `run_zone3_game_model_test` + `run_project_docs_sync_test`。
- `run_strict_live_click_model_test` 的 MT48 `y: expected 7, got 6` 失败是 pre-existing（干净 HEAD 同样复现）。隔离验证法：`git stash push -- <改动文件>; python tests\...; git stash pop`（用 `;` 不用 `&&`，保证 pop 总执行）。
- 剩余耦合（非手写，暂不改）：note 字符串协议 `auto_sweep:` / `auto:` / `动态清:` / `trigger-event` 前缀（Game 写、gen/converter 解析），升级结构化字段（`step["auto_clear"]`）需动 Game record 全部写入点 + 存量 JSON，单独立项；summary label `best_after_mt10_boss_supply` 只服务 zone1 旧 summary 更新路径。
