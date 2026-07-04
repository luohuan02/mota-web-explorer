---
name: mota-route-search
description: 用于魔塔/h5mota 本地路线搜索、最优寻路、攻略-vs-最优探索、Pareto/beam/A*/资源组搜索,或解释当前最优策略。是选择和运行搜索脚本的项目入口,尤其用于 1区/2区路线优化。
---

# 魔塔本地寻路 Skill

这个 skill 用于本地搜索、候选路线扩展、攻略线与最优线对比。它不负责直接操作网页游戏；网页实机执行请改用 `mota-live-verify`。

## 默认语言

报告、walk、阶段名和给用户的结论默认使用中文。保留脚本名、JSON 字段名、坐标和资源 id，便于机器复查。

## 关键事实

- 追踪稳定结果以 `best/` 为准：
  - `best/route_chains.json`
  - `best/route_chains.md`
  - `best/post40_hp_leaderboard_summary.json`
  - `best/post40_hp_leaderboard_walk.json`
  - `best/post40_hp_leaderboard_walk.md`
  - `best/current_best_boss_walk.md`
  - `best/current_best_boss_summary.json`
  - `best/guide_boss_walk.md`
- 当前 37 号存档 / 40F 后续生命榜单路线：
  - `HP=22264 ATK=418 DEF=517 YK=4 BK=0 RK=0 G=1235`
  - `dmg=27134 door=53/10/7`
  - 已网页实机复现，最终态保存到 42 号存档。
  - 1-4 区关联、攻略线/非攻略线分支和剩余 stitched replay 缺口见 `best/route_chains.md`。
- 当前 guide 链：`zone1.guide_baseline -> zone2.guide_canonical -> save36 bridge -> zone3.guide_slot36_to40 -> zone4.save37_hp_leaderboard`。
- 当前 non-guide 分支：`zone1.current_best -> zone2.current_best_2atk1def_branch -> slot26 bridge -> zone3.slot26_clean_boss8def -> zone4.slot26_tail_pending`；`zone2.current_best_canonical` 是同一 10F 起点下的 sibling 对照分支。
- 不要把 save37 的 22264 尾段直接套到 slot26；slot26 的 4区尾段需要单独搜索和实机验证。
- 旧 `1482.5` 结果无效，不要引用为当前最优。
- 10F 后起点有两类：
  - 攻略起点：`guide_after_mt10_boss_supply`
  - 当前最优起点：`best_after_mt10_boss_supply`
- 二区当前脚本不是完整逐格全局搜索，而是“攻略宏顺序 + 关键分支枚举 + replay 校验”的宏策略搜索。

## 当前探索目标：纯净版-TE HP

- 从 2026-06-28 起，后续主目标是 `50层魔塔（H5）-2026全新复刻版` 的 `纯净版-TE（生命/最高血量）` 最优。
- 官方榜单/评论入口：`https://h5mota.com/tower/?name=51`。
- 版本说明参考：`https://h5mota.com/bbs/thread/?tid=1790&p=1`。
- 2026-06-28 读取到的生命榜单参考值：
  - `纯净版-NE（生命）`：26164。
  - `纯净版-TE（生命）`：41477。
  - `特性版-NE（生命）`：29848。
  - `特性版-TE（生命）`：50675。
- 这些榜单值是外部参考，不是本仓库已复现结果；项目内结果仍必须有可 replay 的 walk、审计结果和必要的网页实机验证。
- 纯净版约束：不能使用对话破墙、破门、破怪；雪花必须在击杀魔龙后出现；无 32F 圣水复活。
- TE 约束：不要先打 49F 假魔王。应救公主、24F 上 50F、问小偷显出真魔王，再立刻用下楼飞行器到 49F 触发并清魔法警卫/假魔王封印，最后回 50F 打封印后的真魔王。2026 复刻版已取消旧版“保留下楼器 + 稿/地震直接打真魔王”的 TE。
- 搜索姿态：完整全局逐格最优搜索目前不现实，优先采用攻略/榜单思路、人工策略拆解、关键 checkpoint 分段、宏分支枚举、局部 Pareto/beam 探索、replay 审计和网页复现的组合模式。

## 纯净版-TE / Post-40 探索经验

- 用户指出当前 save37/post-40 尾段在优化后有望到 `HP=23254`；此值先作为待复现目标，不写入 `best/` 作为已证明结果。
- 43F 初始爬楼阶段不要默认开 `MT43 x3y1` 黄门；后续拿盾后可从右侧区域杀怪进入，除非 replay 证明该门在特定分支有净收益。
- 凑 4000G 买地震卷轴时，不要“一层杀一怪”式跳楼。优先把同楼层可达怪物批处理，并用小额、0 伤或低伤金币源精确补到 4000G，减少 redKnight 这类高额怪导致的金币溢出和 HP 损耗。
- `MT32 x8y7 redKnight`、`MT36 x9y1 redKnight` 这类为凑 4000G 的怪要做替代集比较；若能用底层 0 伤怪或低伤怪补最后金币，通常更优。
- 旧线路分支值得保留比较：46F 右侧三黄门上 47F，取 47F `x10y11` 对称飞行器，上 48F，回 15F 杀章鱼拿稿，回 48F `x11y10` 破墙吃圣剑，再回 33F 拿蓝钥匙并清 0 伤怪到 4000G，最后 47F 蓝门商人买地震卷轴。用户估计该线可提升约 200 HP。
- 42F `x10y8` checkBlock 之后如果不再经过半血夹击，后续血瓶原则上可随手吃；这主要影响步数和批处理，不应改变最终 HP。
- 46F 蓝门路线需要比较从 `x3y1` 进入的替代方案；若终局金币无处可花，少量额外金币未必转化为 HP。
- 拿地震卷轴前如果顺路先清若干前置怪，可能改善金币/购物节奏；必须和双倍金币后的收益损失一起算。
- 41F 右上 `x10y2 redWizard` 后的楼层传送可达性要特别小心：若 `MT41 x8y7 slimelord` 未清，实机可能提示“无法到达任何一个楼梯边”，不能把脚本侧飞行器可用当成合法。
- 45F 拿上楼飞行器时，路线可按 `x6y2 -> x6y3 -> x7y3 -> x7y4 -> x7y5 -> x6y5 -> x5y6` 附近杀怪拿道具；拿完回来仅 `x6y3` 掉 100 血，可节省少量 HP。
- 关键策略节点应作为搜索阶段边界：地震卷轴、神圣盾、圣盾、双倍金币、49F 假魔王、35F 魔龙、24F 大法师、49F 圣剑、44F 圣神剑。每个节点前后分别记录 HP/ATK/DEF/钥匙/金币和可达资源。
- 关键策略节点不是固定顺序剧本。搜索应把节点顺序作为宏策略变量比较，例如先地震卷轴还是先双倍金币、先圣盾还是先魔龙雪花、先凑 4000G 还是先拿若干低损属性资源。攻略顺序可作为 seed/基线，但 beam/A*/宏枚举必须允许围绕这些节点重排，并记录每种 ordering 的终局 HP、金币利用率、门钥匙余额和可达资源差异。
- 拿神圣盾后，见到 0 资源成本血瓶可顺手吃；拿双倍金币后，见到 0 伤怪可清，并可考虑从 1F 到当前最高层做一次按楼层批处理的大清洗，把金币尽早转成属性或血量。
- 资源缓存和搜索不要只看当前地面物品组：必须区分当前可见 `groups`、战斗/事件后生成物品 `event_groups`、战斗/事件后开门/消失/变墙的 `event_map_changes`，以及老人/商人/商店等 `npc_resource_groups`。商店侧翼不可当通路，`tile=17` 等特殊怪物/事件占位格在触发前阻断，触发后是否通行必须来自事件变化。
- 搜索排序应区分资源战略层级：剑、盾、十字架、雪花、地震卷轴、红钥匙、关键飞行器、稿、屠龙匕首等是 `core_target`，适合做阶段目标和 beam/A* hint；攻防宝石与 boss 后批量宝石是 `secondary_stat`，主要用于阈值调优；黄/蓝钥匙、血瓶、0伤怪金币等是 `support_resource`，优先在缺口、批处理或商店凑钱时展开；老人、商人、商店、祝福、圣水是 `conversion_node`，必须作为显式状态转移建模。

## 高价值策略变量

- 阶段节点顺序：不要固定“攻略顺序”。至少比较地震卷轴前置/后置、双倍金币前置/后置、圣盾前置/后置、魔龙雪花前置/后置、49F 假魔王/下楼器触发时机。
- 商店路线：每个区域要比较攻/防/血购买次数和购买时机；纯净版 TE 里尤其要比较 `二区四区各加2攻` 与 `二区加2攻 四区全加防` 这类大方向。
- 金币节奏：双倍金币前后打怪收益不同，凑地震卷轴 4000G 不应只看能否到达，还要比较金币溢出、可替代低损怪、0伤怪批处理和商店消费闭环。
- 血瓶策略：1区/2区缺血复现可用 `item=true` 自动吃血瓶；进入 3区或需要保留血瓶时切到 `item=nopotion`。之后拿圣盾或确认不再经过半血/固定血量损耗后再切回自动拾血瓶。搜索报告要标明“当前自动吃血收益”和“保留血瓶收益”的差异。
- 门钥匙预算：红钥匙通常是核心分支，蓝钥匙常决定区域进入方式，黄钥匙是补充资源但会影响卖钥匙/门路线/商人转换。不要只用当前钥匙余额替代累计开门成本。
- 事件后资源和通路：Boss 后生成资源、开门、占位格消失会改变可达性；搜索要把 `event_groups` 和 `event_map_changes` 作为触发后的新图状态。
- 转换节点：老人、商人、商店、圣水、祝福不能静态估值。必须按当时状态计算收益，尤其是圣水使用时机、祝福时机、卖黄钥匙补金币、买黄/蓝钥匙续航。
- 局部批处理：同一楼层或相邻楼层的 0伤怪、血瓶、钥匙、宝石清扫应成批展开，减少“一层杀一怪”式候选噪音。
- Pareto 保留：保留状态时至少区分 HP、ATK、DEF、金币、黄/蓝/红钥匙、已触发事件、商店次数、关键道具、可达楼层/通路。不要用单一资源分数替代安全的 dominance。
- 参考攻略使用：攻略/榜单思路用于生成宏顺序 seed 和关键分支，不作为局部最优证明；每个偏离攻略的分支要输出 checkpoint 差异，方便对比为什么更好或为什么失败。

## 1区 / 4F-10F Boss 探索规范

- 从 4F 存档继续探索时，当前 1区/2区缺血实机复现优先注明 live 自动设置：`__auto__.battle=true`、`__auto__.item=true`、`__auto__.wall=true`。进入 3区或需要保留血瓶时再切到 `__auto__.item="nopotion"`。walk 打印应反映自动清 0 伤怪、自动拾取物品、自动吃血瓶、暗墙/岩浆设置口径。
- 自动 BFS 不会在开门后立即结算；搜索回放和 walk 生成要等下一次移动、战斗、拾取或事件触发后，再把门后资源记为自动处理。典型例子：4F 开 `x8y8` 黄门后，打 `x8y9` 法师才会自动吃 `x7y10` 红宝石和 `x9y10` 红血瓶；6F 从 `x4y4` 打 `x4y3` 红史莱姆后，周围 4 把黄钥匙会自动拾取。
- 4F-10F boss 探索至少保留三类候选：攻略线 seed、之前延后/当前最优线 seed、围绕 9F 蓝门/蓝门绕法的替代线。若搜索发现 9F 蓝门相关候选，即使暂时不是最优，也要保存到 `outputs/` 并在报告里单列。
- 1区目标不只是最小伤害：需要同时比较 boss 后 HP、ATK/DEF、黄/蓝/红钥匙、金币、剩余资源组价值、商人可用性和后续二区接续友好度。旧 `1482.5` 非法结果不能作为候选基线。
- 输出 walk 时要列出关键分支说明：是否走 9F 蓝门、是否提前/延后拿 7F 红宝石、是否使用 6F/7F 商人、是否保留血瓶、是否漏掉顺路 0 伤怪/非血瓶物品。
- 10F Boss 后，`MT10 x6y2` 是骷髅队长剧情事件格；清完生成怪并开 `x6y3` 后必须先走/点 `x6y2` 处理事件，再点 `x6y1` 打队长，不能从远处直接点 `x6y1`。
- 2026-06-28 首轮自动设置探索结论：`user-def-before-key` 本地复跑当前最高 `final-score=1376.5`（Boss 后本地模型 `HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=305 dmg=2454 door=41/2/1`）；同路线网页实机在 `battle=true,item=true,wall=true` 下因自动清理额外 0 伤收益，Boss 后为 `HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=313`。`blue-up` 固定顺序为 `1361.5`；`MT9_NO_BLUE_UP` / TapTap244 省蓝钥匙候选已保存但当前最好仅 `1173.5`，暂不替代 current best，后续只作为 1区/2区接续对照或宏顺序改良 seed。
- `outputs/results/merchant_phase1_long_search_state.pkl` 是 ignored 临时缓存，可能不存在。1区探针若缺这个 pkl，应从 `best/current_best_boss_walk.md` 的 phase1 seed 回退重建状态，不要把 pkl 当唯一 source of truth。

## 搜索入口

1. 重新生成当前 1区到 10F Boss 最优 artifact：

```powershell
python scripts\gen_local_refined_best_walk.py
```

2. 验证当前 MT7 红宝石优先分支：

```powershell
python scripts\probe_mt7_red_first_swap_sequence.py --variant user-def-before-key --beam 160 --out-json outputs\results\user_def_before_key_probe_after_mt10_guard.json --out-md outputs\reports\user_def_before_key_probe_after_mt10_guard.md
```

3. 跑二区宏策略搜索：

```powershell
python scripts\replay_zone2_guide_route.py
python scripts\search_zone2_macro_routes.py
python scripts\audit_zone2_path_legality.py
python scripts\report_zone2_remaining_diff.py
```

4. 更完整枚举二区宏分支时使用：

```powershell
python scripts\search_zone2_macro_routes.py --full --suffix full
```

5. 重新生成 37 号存档 / 40F 后续生命榜单路线：

```powershell
python scripts\search_post40_guide_route.py
node scripts\prepend_40f_prefix_walk.js
```

## 生成物整理

- 搜索脚本默认写入 `outputs/`；`outputs/` 是临时区，忽略 git，可在结果提升到 `best/` 后清理。
- 一个结果只有满足这些条件才提升到 `best/`：
  - 有 JSON 或 Markdown walk 可以复现；
  - replay/audit 的 `errors=0`，或 manifest 明确标注为 experimental；
  - 起点/终点状态能接到 `best/route_chains.json` 的某个 segment；
  - 生成命令或来源脚本可追溯。
- 提升后同步：
  - `best/route_chains.json`
  - `best/route_chains.md`
  - `best/README.md`
  - 必要时同步 `README.md` / `AGENTS.md` / `CLAUDE.md`
- 不要把旧搜索缓存、失败候选、截图、日志、`.pkl` beam 缓存提升到 `best/`。
- `outputs/results/*.pkl`、`outputs/logs/`、`outputs/screenshots/`、旧 smoke/seeded 报告通常可删；但如果某个脚本仍依赖 ignored snapshot，例如 `slot26_snapshot.json`、`slot36_snapshot.json`、`guide40_current_snapshot.json`，清理前要确认能重新导出或已有 tracked 替代。

## 当前最优搜索方案说明

当前项目同时有两层搜索：

- 1区到 10F Boss：更接近通用策略搜索。脚本会用资源组、阶段目标、Pareto 保留、局部顺序精修、Dijkstra/A* 与 beam/probe 组合搜索。
- 10F Boss 后到 20F Boss：目前是受约束的宏策略搜索。它以用户攻略大顺序作为合法骨架，枚举 12F 商店购买组合和关键可选资源点，再通过 `replay_zone2_guide_route.py` 重放计算状态、伤害、开门和剩余资源。

因此，回答“现在是不是通用策略搜索”时要说明：1区部分较通用，二区部分还不是完整通用逐格搜索；二区的优势是稳定、快、方便实机复现，风险是会漏掉攻略骨架外的全新路线。

## 判断路线优劣

使用项目约定评分：

- `1YK = 50HP`
- `1BK = 200HP`
- `100G = 50HP`
- 红血瓶 `50`，蓝血瓶 `200`
- 红钥匙和宝石默认不计剩余分，除非脚本另有目标
- `stock` 可包含保留圣水的下界价值

比较时同时看：

- 最终 HP/攻/防/钥匙/金币
- 总伤害 `dmg`
- 开门数 `door=黄/蓝/红`
- 剩余资源差异
- 是否可被路径审计和网页实机验证复现

搜索报告和 walk 的阶段输出要求：

- 每个大阶段必须打印状态、纯伤害 `dmg`、开门数、`final-score` 或脚本对应的综合分；同时列关键组成，例如库存分、剩余资源组、未来 0 伤怪金币、商人残值、钥匙/金币折算。
- 1区用 10F Boss 后作为阶段分数；2区用 20F Boss/吸血鬼后；3区用 40F Boss 后；4区按策略节点拆分：40F 后起点、地震卷轴、神圣盾/圣盾、双倍金币/49F 假魔王、魔龙雪花、24F 上 50F 前、最终真魔王后。
- 详细 walk 不逐步打印完整前后状态；单步只列动作和变化属性，完整状态以 `快照@步数` 行插入详细步骤中。普通快照间隔约 50 步以上，关键道具、Boss、大事件、重要商店/补给后可立即插入。

## 风险点

- 不要把资源评分当作 Pareto 保留的替代条件，除非脚本明确证明安全。
- 不要手写“特殊通道”绕过真实楼层可达性；需要说明为什么可以在真实游戏中重放。
- 二区报告里如果出现剩余顺路资源，例如 `MT1 x1y3 红血瓶`，优先检查是不是宏路线漏了真实移动成本或漏了顺手补给。
- 老人、商人、商店是显式状态转移，不是静态物品价值；搜索要按金币、钥匙、购买次数、当前攻防和一次性/可重复限制分别建模。
