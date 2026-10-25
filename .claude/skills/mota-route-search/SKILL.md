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
- 3区末接 4区半血陷阱时，血瓶不要只按“顺路就吃”处理；应把它们视作可开关的 `support_resource`，先固定动作序列，再做一次“最低存活 HP 压缩”：从后往前枚举/DP 删除晚段血瓶，约束是每一步 `after.hp > 0` 且动作序列不变。这样得到的是“当前路线骨架下的最小存活 HP”，可用于压低半血陷阱损失；它是路线内优化，不等于全局最优路线证明。
- 46F 蓝门路线需要比较从 `x3y1` 进入的替代方案；若终局金币无处可花，少量额外金币未必转化为 HP。
- **终局 2420G 生命商店不总是值得买出**（38624 vs 39003 同骨架对照）：MT46 `x6y1` 生命商店 2420G→+1600HP（0.66 HP/G）。38624 买出后 `G 3579→1159→159`（2420 商店 + 1000 hp2000），最终 HP=38624 G=159；39003 不买商店改买 MT31 keyBundle（1000G→4YK+1BK）解锁散落蓝瓶，收 5 蓝瓶(+800 各)+3 红瓶，最终 HP=39003 G=1707，**反超 379 HP**。教训：不要默认"买出 2420 商店最优"；把等量金币投到蓝钥匙（MT31 keyBundle）+收散落 +800 蓝瓶（3.2 HP/G）通常更优。
  - **真正的约束是金币预算，不是蓝钥匙够不够**。39003 证明：只要买得起 keyBundle（1000G），拿到的 4YK+1BK 蓝钥匙**足够**收完全部散落 +800 蓝瓶（MT31 x8y8、MT20 x11y4 各需开一扇黄/蓝门，keyBundle 全解锁）。38624 之所以没收这些蓝瓶，是 `G 3579` 被 2420 商店 + 1000 hp2000 吃掉只剩 159G、**买不起 keyBundle 才没蓝钥匙**——不是"买出后蓝钥匙不够"。不要把根因写成"蓝钥匙被商店吃掉"。
  - **买出的条件（何时该买 2420 商店）**：① 已先把 keyBundle+收散落蓝瓶这条更高价值路径（3.2 HP/G）的资金留足，之后仍有 ≥2420G 富余 → 用富余买出（纯 +1600HP 叠加）；② 或散落 +800 蓝瓶已收完/不可达，keyBundle 不再与商店抢资金 → 用剩余金币买出。**只要买出会挤掉 keyBundle（金币耗尽买不起 1000G keyBundle→丢蓝瓶），就不该买出**，因为那会损失 ~3.2 HP/G 的血瓶换取 0.66 HP/G 的商店。
  - **后续优化方向**：买出与收蓝瓶不是互斥的，只是 38624 当时金币不够。若某线在 MT49 附近能凑到 `≥2420(商店)+1000(hp2000)+1000(keyBundle)=4420G`，就能**既买出商店又收齐散落蓝瓶**，得到 +1600 商店 + +800×5 蓝瓶双重收益，会同时压过 38624 与 39003。这是值得往"多凑 ~850G（38624 3579→4420）"方向优化的目标。
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
- **神圣盾后的硬切换**：若取得 44F 神圣盾后 `magicImmune=true`，且后续不存在非魔法的比例扣血路线，必须立即把 `__auto__.item` 从 `"nopotion"` 切为 `true`。切换必须由共享 `Game` 生成一条 `设置自动` step，写入 JSON、Markdown 和 verifier 时间线；不能只在启动参数或说明文字里改。`item=true` 只负责当前点击触发的同层 auto-BFS，不等于全图血瓶已经收完。
- 对 3区末/4区前的控血报告，除了“自动吃血收益 vs 保留血瓶收益”，再补一列“固定动作序列下的最小存活 HP”。实践上优先删除晚段大血瓶（尤其不影响前面开门/穿怪/过商店的 `+800` 蓝瓶），若删掉后某一步 `after.hp <= 0`，则该血瓶不是冗余资源，而是当前骨架的生存垫。
- 门钥匙预算：红钥匙通常是核心分支，蓝钥匙常决定区域进入方式，黄钥匙是补充资源但会影响卖钥匙/门路线/商人转换。不要只用当前钥匙余额替代累计开门成本。
- 事件后资源和通路：Boss 后生成资源、开门、占位格消失会改变可达性；搜索要把 `event_groups` 和 `event_map_changes` 作为触发后的新图状态。
- 转换节点：老人、商人、商店、圣水、祝福不能静态估值。必须按当时状态计算收益，尤其是圣水使用时机、祝福时机、卖黄钥匙补金币、买黄/蓝钥匙续航。
- 黄钥匙不是“没用就丢弃”的终局库存：终战前必须比较“开门取得净资源”和“28F 按 100G/把出售后凑 46F 生命商店”两条用途。搜索资金状态至少使用 `gold + sellable_yk * 100`，并执行真实商人/商店动作；蓝钥匙、红钥匙也要逐个探测门后净 HP/属性/金币收益。
- 局部批处理：同一楼层或相邻楼层的 0伤怪、血瓶、钥匙、宝石清扫应成批展开，减少“一层杀一怪”式候选噪音。
- Pareto 保留：保留状态时至少区分 HP、ATK、DEF、金币、黄/蓝/红钥匙、已触发事件、商店次数、关键道具、可达楼层/通路。不要用单一资源分数替代安全的 dominance。
- 参考攻略使用：攻略/榜单思路用于生成宏顺序 seed 和关键分支，不作为局部最优证明；每个偏离攻略的分支要输出 checkpoint 差异，方便对比为什么更好或为什么失败。

## 1区 / 4F-10F Boss 探索规范

- 从 4F 存档继续探索时，当前 1区/2区缺血实机复现优先注明 live 自动设置：`__auto__.battle=true`、`__auto__.item=true`、`__auto__.wall=true`。进入 3区或需要保留血瓶时再切到 `__auto__.item="nopotion"`。walk 打印应反映自动清 0 伤怪、自动拾取物品、自动吃血瓶、暗墙/岩浆设置口径。
- **auto sweep 归属语义（2026-08-31 定稿，推翻旧「开门不立即结算」表述）**：web 的 `control.prototype.moveOneStep` 补丁在 hero 每移动一格后触发 `core.auto()`——开门的 route-resume 让 hero 踏上**刚开的门格**，那一刻 sweep 从门格起跑（deep 通常=∞；但 2026-09-05 40145 修正：未拿盾时 special 15/16 法术场/夹击**入 checkBlock.damage 图**——damage 格不扩展 BFS、其上道具不可远程拾取、hero 站 damage 格 deep=0，MT47 damage=[] 仅因已魔免。详见 `recording_seed_converter_experience.md`「40145 复验两大根因」）。搜索回放/walk 生成按 `Game._apply_door_live` 把门后可达资源记入**门步本身**；具体例子的资源落点不变（4F 开 `x8y8` 黄门后打 `x8y9` 法师吃 `x7y10` 红宝石等），变的只是归属步的判定规则。verifier 对开门步确定性补一次「走进门格」点击使 live 归属与 walk 一致。
- 4F-10F boss 探索至少保留三类候选：攻略线 seed、之前延后/当前最优线 seed、围绕 9F 蓝门/蓝门绕法的替代线。若搜索发现 9F 蓝门相关候选，即使暂时不是最优，也要保存到 `outputs/` 并在报告里单列。
- 1区目标不只是最小伤害：需要同时比较 boss 后 HP、ATK/DEF、黄/蓝/红钥匙、金币、剩余资源组价值、商人可用性和后续二区接续友好度。旧 `1482.5` 非法结果不能作为候选基线。
- 输出 walk 时要列出关键分支说明：是否走 9F 蓝门、是否提前/延后拿 7F 红宝石、是否使用 6F/7F 商人、是否保留血瓶、是否漏掉顺路 0 伤怪/非血瓶物品。
- 10F Boss 后，`MT10 x6y2` 是骷髅队长剧情事件格；清完生成怪并开 `x6y3` 后必须先走/点 `x6y2` 处理事件，再点 `x6y1` 打队长，不能从远处直接点 `x6y1`。
- 2026-06-28 首轮自动设置探索结论：`user-def-before-key` 本地复跑当前最高 `final-score=1376.5`（Boss 后本地模型 `HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=305 dmg=2454 door=41/2/1`）；同路线网页实机在 `battle=true,item=true,wall=true` 下因自动清理额外 0 伤收益，Boss 后为 `HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=313`。`blue-up` 固定顺序为 `1361.5`；`MT9_NO_BLUE_UP` / TapTap244 省蓝钥匙候选已保存但当前最好仅 `1173.5`，暂不替代 current best，后续只作为 1区/2区接续对照或宏顺序改良 seed。
- `outputs/results/merchant_phase1_long_search_state.pkl` 是 ignored 临时缓存，可能不存在。1区探针若缺这个 pkl，应从 `best/current_best_boss_walk.md` 的 phase1 seed 回退重建状态，不要把 pkl 当唯一 source of truth。

## 1区分段经验库（经验驱动搜索）

搜索找不到最优时（如 seg2 搜索止 932，最优 754），用「经验 + walk + 对比」补充：walk 是 ground truth（网页 0 mismatch），经验是策略知识，搜索降为 hypothesis 探索器。和 `two_attack_line_search_lessons`（replay-as-baseline）一致：walk 不骗人，搜索模型会。

### 经验文件
- **纯净版-TE HP 最优宏观经验（当前探索目标总纲）**：路线族/当前最优 + 通向 41477 的已封闭结构性杠杆（别再撞）+ 伤害归因 + 剩余「降低钥匙消耗」微优化方向：`skills/mota-route-search/te_hp_optimization_experience.md`。
- **用户经验 2026-10-24（41477 族配方 + 最高防御 653 防攻略 + 漏探根因）**：用户手玩 41477 全族关键点（7楼省2yk/9楼蓝门、800红钥匙、卖yk 7防、38F 商人延后到魔龙后、2120 悬崖、终局顺序）+ 官方 653 防线摘要 + 为什么之前没探到（微交换/转换时点算子缺口、分区出口规格写死、微收益阈值歧视）与 OP-SWAP/OP-DEFER 算子规格：`skills/mota-route-search/te_user_experience_20261024.md`。TE 搜索前必读。
- **钥匙-掉血决策逻辑（2攻全防，按区）**：
  - zone1（11 条）：`skills/mota-route-search/te_hp_zone1_decisions.md`
  - zone2（MT11-20，金币-掉血：2攻/红钥匙/BK）：`skills/mota-route-search/te_hp_zone2_decisions.md`
  - zone4（MT31-40，防商店+凑4000G地震）：`skills/mota-route-search/te_hp_zone4_decisions.md`
  - zone5（MT41-50，防商店funding+魔龙+终局）：`skills/mota-route-search/te_hp_zone5_decisions.md`
  - 各区决策共同点 = **金币/钥匙机会成本由终局防商店 funding 阶梯决定（不连续）**，详见 te_hp_optimization_experience.md「Game 建模优化」。
- **路线族差异（同族 walk 结构性对比 + 各自可优化点）**：`skills/mota-route-search/te_hp_route_families.md`（39944 全防 vs 4区2攻 的 +415 HP 纯分配对照；38624 弱 body 换 2420 反例；2攻800红钥匙/镐挖炸弹 fallback）。
- **2420 生命商店资金上限推导（39944 族冲 41477 的结论）**：`skills/mota-route-search/te_hp_2420_funding_analysis.md`（**2420 已证明不可凑**：乐观资金上界 1345<2420；微优化封顶 +336→40280，因 MT33 soldier 骑士剑硬挡板；39944 族无路到 41477）。
- zone1 完整经验（思路 + 抉择 + 对比，seg1-3 合并）：`skills/mota-route-search/zone1_experience.md`。经验少时合并成一个文件放 skill，不放 best。
- zone2 完整经验（2攻线，思路 + 抉择 + 事件机制，seg1-4）：`skills/mota-route-search/zone2_experience.md`。
- zone1-2 KILL 线经验（2atk0def，杀 zKnight 不买红钥匙，vampire 固定伤害 + 三类资源 drop 教训）：`skills/mota-route-search/zone12_kill_line_experience.md`。
- zone2 **2攻录像**经验（2区2攻 + 买800G红钥匙 + 少开门停 31F，web 0 mismatch；与 39944 全防族 zone2 前缀对比：属性同 ATK76/DEF64 但 HP+13 YK+2 dmg−213，score +101.5 HP-equiv / funding +177G equiv，且属性路径不变不需 zone3/4 重搜；用户购买/宝石/少开门思路）：`skills/mota-route-search/zone2_2atk_recording_experience.md`。
- recording_to_game converter 合并经验（.h5route 录像 -> Game walk 的 coalesce：fold move-waypoint 安全性论证 + 走门格移除 + 零效果 move 剪枝 + 楼梯 U 型折返提升 + 双验证）：`skills/mota-route-search/recording_converter_experience.md`。
- recording_seed_to_game converter 经验（录像 statlog -> Game walk：三类 NPC 通用转换[shop/trader delta 检测 + oldman trigger_tile_event] + 激进 coalesce 删空地到达步[replayer 远点点击+重试] + centerFly·upFly·downFly 源位置依赖例外 + 100+槽无法录像改用普通槽 + **automaticRoute 语义[go_to 目的地才 auto_sweep；path_cost 不折扣事件格、破坏性事件中断路线]**）：`skills/mota-route-search/recording_seed_converter_experience.md`。
- **zone1-2 语义重放搜索经验（V-A 基建 + yk 贪婪吸收定律）**：`skills/mota-route-search/te_hp_zone12_semantic_search_experience.md`（录像 zone1-2 -> 可编辑语义 action 列表的完整基建[楼梯 :next/:before 转换/set_auto choices 须以 4 开头/statlog 金币='g'/商店组 delta 扫描] + 可跳过性插桩扫描[clone 写时复制污染坑] + 21 零损失门 skip 全部被即时吸收 + **yk 贪婪吸收定律：局部编辑搜索的钥匙流被 pathfinder 即时锁死，残余药瓶需拓扑级重排** + 手术脚本切片基准/索引冲突教训）。
- walk 按楼层拆分 / 剩余资源对账经验（复用脚本 `scripts/audit/gen_recording_floor_breakdown.py`，一条命令自动读 provenance；口径：截点=MT50真魔王击杀前 / 打怪金=金币增量分类含事件生成怪 / **剩余怪金必须用共享Game重放 g.floors，walk-diff 会因 auto_sweep note 截断高估(41228 8277→385)** / 钥匙分离裸拾取与商人买 / 剩余商人·事件剔消费与纯剧情与 step-on 已触发）：`skills/mota-route-search/floor_breakdown_experience.md`。
- 来源 = 已验证 walk：zone1 `best/current_best_boss_walk.md`（HP=122）+ zone1-2 KILL 线（当前最优）`best/zone12_2atk0def_recording_walk.md`（358 步 MT4-20，2攻0def 杀 zKnight，web 0 mismatch；zone1 末 625/30/30、zone2 末 MT20 HP=1215 ATK=76 DEF=66 YK=5）。旧买红钥匙 2 攻线（autoon）walk、drop753_774（HP=1241）已删，经验沉淀于 `zone2_experience.md` / `zone12_kill_line_experience.md`。
- 每段可存 `variants/`（最优/搜索/攻略对照），供 `scripts/audit/compare_segment_walks.py`（待建）找分叉点 + HP 归因。

### 录像复刻方法论（auto ON + skip-if-cleared）

**两条录像->walk pipeline**（按录像路径是否 Game 兼容选）：
- `scripts/search/zone12_recording_autoon.py`（本节）：auto ON + skip-if-cleared，内容驱动逐目标 `go_to`。录像路径恰好 Game 兼容时用（旧录像 MT4-9 零 stat 错）。
- `scripts/search/recording_to_game.py`：解码 route events + 逐格 captured path 精确复现录像 exact 路径（PRE-state statlog 0 mismatch），再 coalesce 成节点级直达步，最后跑零效果 move 剪枝 + 楼梯 U 型折返提升。用户手玩调整路径与 Game 寻路分歧时用（autoon 失败的 fallback）。coalesce 合并逻辑（fold move-waypoint / 走门格移除 / 零效果 move 剪枝 / 楼梯 U 型折返提升）见 `recording_converter_experience.md`。

有 .h5route 录像（auto OFF 显式步）作 ground truth 时，用 **auto ON** 离线复刻成可验证 walk（`scripts/search/zone12_recording_autoon.py`）：

- 按录像 statlog hero 位置顺序走；下一目标格若已被 auto 清空（`block_at is None`）则**跳过**，否则 `go_to(target)` auto ON，auto_sweep 顺带清路上零伤怪/道具/暗墙。
- 楼层切换：相邻层楼梯、跨层 fly。商店/商人：同层同位 + gold 变化判定走 `buy_shop`/`talk_trader`。
- **event trigger 格不能跳**：空格（id 0）但是 event trigger 的（如 MT20 (6,8) vampire、MT29 (6,2) thief）必须走上去触发，用 `is_event_trigger = f"{x},{y}" in events` 守卫 skip-if-cleared。
- **金币口径**：auto ON 比录像多杀零伤小怪，gold 比录像高约 +190（HP/ATK/DEF/YK/BK/RK/位置全匹配，gold 差已接受）。web 验证比 walk JSON vs 实机（0 mismatch），非 walk vs 录像 gold。
- hero-step 事件（MT20 vampire/MT29 thief）建模在通用 `Game.trigger_tile_event`（go_to ARRIVE 触发），**不是 floor-entry**；fakeWall2+setBlock 事件锁（MT19 cross）需 replayer ARRIVE setBlock retry。详见 `zone2_experience.md`「事件机制」。

### 移除录像绕路（skip_ranges + stop_before_idx）

录像里某段是另一条线（如买红钥匙线）的专属绕路、当前分支不需要时，用 `rec_main(skip_ranges=[(lo,hi)], stop_before_idx=N, ...)` 跳过：

- `skip_ranges`：跳过 statlog `[lo,hi)` 区间（飞行绕路等）。跳过后 hero 留在实际楼层，下一条目标跨层时按 position-agnostic fly。
- `stop_before_idx`：在处理某 statlog idx 前停（跳过其后整段，如不买红钥匙则跳红钥匙接近段）。
- **楼层检测必须用 hero 实际楼层 `g.state["floor"]`，不能用 statlog 相对 `cur["f"]`**，否则 skip_ranges 飞行绕路失同步（跳段后 statlog cur["f"] 还停在绕路起点楼层，误判后续换层）。rec_main 已修，非跳段时 no-op（不回归）。
- **耦合段陷阱**：跳一段绕路前，检查是否有另一段也经同一格。例（2攻0防 KILL 线，2026-07-16）：移除 [362] MT12 绕路（seg5 fly MT19->MT12 杀 x2y5 -74HP），但 seg6（红钥匙商人接近）也经 x2y5--只跳 seg5 会让 seg6 重打 x2y5（无收益）。解法 = 跳 seg5 且 `stop_before_idx=951` 跳 seg6（KILL 分支不买红钥匙，seg6 整段多余）。移除后 web 验证 0 值不匹配（含金币），+74 HP / +2 YK / -46 G ≈ +151 HP 等价。

### 可移除刷怪排查（per-visit 净资源流）

判断 walk 里是否有“多打”的可移除刷怪，按楼层访问段（visit = 同层连续步，飞行/换层为界）汇总净 hp/gold/yk/bk/rk/atk/def：

- 净 HP 负 且无属性/钥匙收益的段 = 纯金币刷怪候选（若非阻路怪可移除）。
- **auto_sweep 把拾取/零伤击杀藏在 step.note**（如 `auto_sweep: x1y5 redPotion`），肉眼读 HP delta 会误判。例：MT8「开门->到达->飞走」看似 -1 YK 白开门，实为 auto_sweep 拾 redPotion(+50 HP)，净正收益不可移除。
- 候选必须核对 note 的 auto_sweep 列表 + 跨段资源依赖（商人/门/钥匙流）才能确认可移除；阻路怪、商人购买（如 MT15 blueKey 200G、MT7 5YK 50G）、硬闸门（如 MT19 rock ATK70 地板，挡 zKnight 区）不可移除。
- 2攻0防 KILL 线 zone1-2 经此排查：除 [362] 外无其它可移除刷怪（其余高伤段全是阻路/商人/rock 闸门/zKnight 核心杀）。

### 道具拾取 pass 优化（挡路 vs auto 顺带）

walk 里的「路过 pass」步（note 含 `auto_sweep:` 拾道具）是否可优化（合并进下一目标让 auto 远程顺带），判断 = **道具是否挡路**：

- **不挡路道具**（在下一目标 auto_sweep BFS 可达范围、但不在 hero 寻路必经路上）：auto_sweep 远程顺带吃（`core.getItem` 不走路），不必专门走 pass。例（MT16 zone2，KILL 线 converter walk）：`x7y3 pass (auto: x7y3 yellowKey)` -> `x6y4 open blueDoor`——(7,3) yellowKey 在 (6,4) 的 auto BFS 范围且不挡路，直接到 (6,4) 开蓝门时 auto 顺带吃，(7,3) pass 冗余（可优化）。
- **挡路道具**（在到下一目标的必经路上）：hero 寻路必经、走过拾取（路径拾取，非 auto 远程），不能 auto 顺带；须显式走吃或接受路径拾取。例（MT16 zone2，KILL 线 converter walk）：`x5y5 pass (auto: x5y5 redPotion, x7y7 yellowKey)` -> `x6y8 open yellowDoor`——若直接到 (6,8)，路线被 (5,5)(7,7) 道具挡，hero 走过去拾取而非 auto 远程顺带（降速），故先吃挡路道具是对的，符合可达矩阵访问逻辑。

注：converter 逐格复现录像 captured path，录像里手玩多走的 pass（如不挡路道具）会保留（删则 web mismatch）。此经验用于判断录像/walk 里哪些 pass 是可优化点（重新规划/录像时可省），非改 converter 删步。auto_sweep 远程吃不走路见 `recording_converter_experience.md`。

### 工作流
1. 写经验：从已验证 walk 反推策略 + 关键决策点 D1-D4 + 对比基准（攻略/搜索）。
2. 生成 walk：通用 Game 类 -> walk.json（每步 before/after）。
3. 对比：compare_segment_walks.py 找分叉点 + HP 归因（哪个怪/gem/门导致差异）。
4. 搜索对照：跑搜索后对照经验 D1-D4 检查是否违背机制约束（阈值/循环/段间耦合）。

### HP delta 口径（重要）
walk 的 HP delta 含 auto_sweep 副作用（血瓶 +50 等计入同一步），**不是纯单怪伤害**。纯伤害看 dmg 增量或 Game `enemy_damage`。例：MT4fly bluePriest 纯伤 88，同步 auto 血瓶 +50，HP 净变 -38（dmg 仍记 +88）。读 walk 伤害务必用 dmg 累计校验，勿直接用 HP delta。

### 要点（详见 zone1_experience.md）
分段依据 = 装备里程碑（剑->盾+9F宝石->27/27+boss），seg2/seg3 切分因「先冲盾再回头清扫宝石」伤害更低。seg2 D1 回 MT4 redGem 过 bat 阈值省 168（搜索 932 主差）；seg2 D3 MT8 钥匙自给循环卡 MT7 出门 YK=3；seg2 替代线 MT7 上线省 2 yk（非当前最优）；seg3 宝石顺序：红宝石按 atk 阈值排（MT7红首拿跨 atk23 三怪阈值、MT3红先于 MT5 跨 atk26 骷髅士兵阈值；MT10红 atk27 跨终局 yellowGuard/boss 阈值故最后），蓝宝石无阈值按钥匙流+路径成本排（MT3蓝->MT6蓝 YK 链、MT8->MT4->MT9 BK 链、MT1->MT8 与 MT5蓝->MT10蓝 贵路径放后享高 def），MT10 最后=路径成本最贵+终局阈值+MT10蓝先于MT10红减伤 11（非 YK 短缺，钥匙可先拿但多掉血），非 BK（起手 BK=1 可直接上）。红钥匙守卫+boss 必 27/27 打（atk27 跨 yellowGuard def22 / 队长阈值，atk 是杠杆非 def）。

### 阈值表（atk 回合数跳变点；def 不影响 turns 故蓝宝石无阈值）

阈值 = atk 跨过时 turns 降 1 的点（turns=ceil(怪hp/(atk-怪def))），def 只降每回合伤害不改变 turns，所以**蓝宝石（+def）无阈值、红宝石（+atk）才有**--seg3 宝石排序的总原则。dmg 为 def=21 实测示例（`tmp/seg3_trace.py` 可复跑）。

| 怪 | 阈值 atk | turns 跳变 | 用在 |
|---|---|---|---|
| bat | 21 | t3->2 | seg2 flyback redGem（atk20->21）|
| skeleton | 23 | t4->3 | seg3 MT7红首拿（atk22->23）|
| bluePriest | 23 | t5->4 | seg3 MT7红首拿 |
| skeletonSoldier | 22 / 23 / 26 | t7->6 / t6->5 / t5->4 | seg2 atk22；seg3 MT7红(atk23)、MT3红(atk26 先于 MT5)|
| greenSlime/redSlime | 0 伤 | - | 无阈值 |
| yellowGuard | 27 | t13->10 | 终局：红钥匙守卫（def22，atk26 hero_hit 4->5）。必须 27/27 打非 26/27--atk 是杠杆非 def，见 `zone1_experience.md`「红钥匙守卫和 boss」|
| skeletonCaptain(boss) | 27 | t10->9 | 终局：MT10 boss（def15）。27/27 打省 38(atk)+27(def) |

def=21 dmg 示例（验证用）：skeleton atk22=63/t4, atk23=42/t3；bluePriest atk22=44/t5, atk23=33/t4；skeletonSoldier atk25=124/t5, atk26=93/t4。def=27 终局示例：yellowGuard atk26=252/t13、atk27=189/t10；skeletonCaptain atk26=342/t10、atk27=304/t9（`tmp/seg3_points234.py`）。

### 宝石排序原则（红按阈值，蓝按路径成本）

- **红宝石（+atk，有阈值）**：按 atk 阈值紧迫度排，跨阈值的早拿降回合数（见阈值表 + `zone1_experience.md` seg3）。例：MT7红首拿跨 atk23 三怪阈值；MT3红 先于 MT5 跨 atk26 骷髅士兵阈值。
- **蓝宝石（+def，无阈值）**：def 不降回合数，但同一清扫段内按**获取路径战损成本**排--路径越贵的越靠后，让贵路径在更高累积 def 下打（第 N 颗享最高 def，第 N-1 颗卡次高）。zone1 seg3 实测：MT10蓝 获取路径最贵（MT4 蓝法师+MT9 蝙蝠+MT10 骷髅，3 战 + BK 链），放第 6 享 def26；提到 MT5蓝（1 战路径）之前 +3 伤（HP 122->119，`tmp/reorder_mt10blue.py`）。同理 MT1蓝 先于 MT8蓝：两 bundle 钥匙流都可行（MT7骷髅 +2yk 够任一），按战损 MT1 段 3 战 57 伤、MT8 段 5 战 102 伤，贵的 MT8 放后享 def24，交换 +3 伤（`tmp/swap_mt1_mt8.py`）--别因它们靠近钥匙流段就误当钥匙序。
- 适用所有区延后清扫段：def/无阈值宝石别随意排，按获取路径成本升序（便宜先、贵后）最优；同时受 YK/BK 流约束的，先满足钥匙流，再在钥匙流允许的范围内按路径成本细调。

### 搜索瓶颈（seg2 止 932，非 enemy_h）
MT7 redGem 顺路优先（A* 选近不回 MT4，且 MT7 redGem 时 bat 群已打完，阈值收益丢失）+ 钥匙搜索杀 skeletonSoldier（seg1 YK 少补钥匙）。多因素耦合，非单 enemy_h 可解。

## 2区分段经验库（2攻线，已验证 walk）

来源 = zone1-2 KILL 线（当前最优）`best/zone12_2atk0def_recording_walk.md`（MT4-20，2攻0def 杀 zKnight，web 0 mismatch；zone2 末 MT20 HP=1215 ATK=76 DEF=66 YK=5）。2 攻线通用经验（宝石序/cross/vampire 机制）详见 `zone2_experience.md`，KILL 线 redKey 抉择详见 `zone12_kill_line_experience.md`。

### 要点（详见 zone2_experience.md）
分段 = 装备里程碑（MT12 2攻 -> sword2+shield2 -> ATK70+cross -> redKey+吸血鬼）。核心抉择 = **MT12 只买 2 攻**（ATK30->38），省 80G 延后 4 区防（ratio5 +20 vs zone2 ratio2 +8，同金币多 +12 DEF）。宝石序（已验证 walk）：MT16 blackSlime(38->40) **必须先于 MT17 sword2**（过 yellowGuard 4->3 回合阈值，省 88 伤；旧「2攻比3ATK多花72伤打卫兵」基于 ATK38 前提已过时，实际 ATK40 与 3ATK 同 3 回合）；ATK70 来自 **MT19 redGem**（非 MT18 redPriest，旧归因错），必须先于 MT19 rock（ATK70 地板，rock def68）。**cross 是吸血鬼硬门槛**（无 cross 15510 必死、有 cross 705），在 MT19 (6,3) fakeWall2+setBlock 拾取。**MT20 吸血鬼 = hero 踩 (6,8) 触发**（8 bigBat 合并进 vampire，不单独战斗无金币；afterBattle spawn 3红3蓝宝石+3蓝血瓶+3黄钥，+6/+6/+HP），非 floor-entry。redKey 买(800G)/杀(3 zKnight 372伤)：纯 zone2 杀略便宜(327<400)，但 end-to-end 买饿死 4 区攻（G 贫 -> ATK142 vs 166 -> 魔龙多挨 6180 -> 19562<23076），2攻+杀zKnight 是未探方向。

### 阈值表（zone2，atk 回合数跳变点；breakpoint = atk_needed，见 `data/heuristics_table.json`）

| 怪 | 阈值 atk | turns 跳变 | 用在 |
|---|---|---|---|
| yellowGuard（MT17 sword2 卫兵）| 39 | t4->3 | seg2 MT16 blackSlime(38->40) 先于 MT17 剑跨此阈值，4 卫兵省 88 伤 |
| zombie | 43/49/57 | t8->7->6->5 | seg2 sword2(ATK40->60) 跨多 zombie 阈值（zone2 常见怪）|
| rock（MT19 cross 守卫）| 69 | 不可杀->t20 | seg3 ATK70 地板（hero_hit=atk-68，<69 则 0 杀不掉；atk70 t10）|
| vampire（MT20 boss）| 140（70+cross）| inf->t6 | seg4 cross 翻倍 atk(70->140)，无 cross=15510 必死、有 cross=705 |

## 搜索入口

1. 重新生成当前 1区到 10F Boss 最优 artifact：

```powershell
python scripts\build\gen_local_refined_best_walk.py
```

2. 验证当前 MT7 红宝石优先分支：

```powershell
python scripts\search\probe_mt7_red_first_swap_sequence.py --variant user-def-before-key --beam 160 --out-json outputs\results\user_def_before_key_probe_after_mt10_guard.json --out-md outputs\reports\user_def_before_key_probe_after_mt10_guard.md
```

3. 跑二区宏策略搜索：

```powershell
python scripts\baseline\replay_zone2_guide_route.py
python scripts\search\search_zone2_macro_routes.py
python scripts\audit\audit_zone2_path_legality.py
python scripts\audit\report_zone2_remaining_diff.py
```

4. 更完整枚举二区宏分支时使用：

```powershell
python scripts\search\search_zone2_macro_routes.py --full --suffix full
```

5. 重新生成 37 号存档 / 40F 后续生命榜单路线：

```powershell
python src/solver/game_route.py
node scripts\build\prepend_40f_prefix_walk.js
```

## 生成物整理

- 搜索脚本默认写入 `outputs/`；`outputs/` 是临时区，忽略 git，可在结果提升到 `best/` 后清理。
- 一个结果只有满足这些条件才提升到 `best/`：
  - 有 JSON 或 Markdown walk 可以复现；
  - replay/audit 的 `errors=0`，或 manifest 明确标注为 experimental；
  - 起点/终点状态能接到 `best/route_chains.json` 的某个 segment；
  - 生成命令或来源脚本可追溯。
  - 纯净版-TE 生命路线附有终战前剩余资源审计；所有可达正 HP 资源、可盈利钥匙/金币转换均已收敛为 0，或逐项说明为何保留更优。没有该证据只能标为“已验证可通关下界”，不能称“压榨完成/HP 最优”。

## 终战前资源闭环（纯净版-TE 硬规则）

最终真魔王前必须反复执行到固定点，而不是只做一遍清扫：

1. 枚举当前物品、战斗/事件新生成的 `event_groups`（尤其 49F 封印奖励），收取所有可达正 HP 血瓶和能提前减伤的攻防宝石。
2. 清 0 伤/低净损怪，计算金币与门钥匙真实成本；新属性可能使更多怪变成 0 伤，因此要重新枚举。
3. 对黄钥匙比较开门与 28F 售卖；对蓝/红钥匙探测门后资源组。把可消费金币投入 46F 生命商店后，再从第 1 步重跑。**不要无条件买出 46F 生命商店**：见「纯净版-TE / Post-40 探索经验」的 2420G 商店对照（38624 vs 39003）——同一骨架下买出商店（2420G→+1600HP）比把钱投 MT31 keyBundle+收散落 +800 蓝瓶 低 379 HP；先对比两条消费路径再决定。注意真正的约束是金币预算（凑齐 4420G 可商店+keyBundle+收蓝瓶三者兼得），不是蓝钥匙不够。
4. 真魔王击杀后的 500G 不可回头消费，不得计入终战前可用资金。
5. 收敛断言至少包括：可达正 HP 药水价值为 0；无盈利钥匙转换；`gold + sellable_yk*100 + 可恢复净金币` 仍不足下一次生命商店；49F 奖励逐件有拾取或保留说明。

auto、清扫和闭环是三件事：开启 `item=true` 不会主动飞遍全图，也不会替代剩余资源审计。
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

### 4区资源组压缩 A*（共享 Game）

- `src/solver/game_astar.py` 只是共享 Game 的通用 A*/Dijkstra 引擎；是否使用资源组压缩图取决于调用方。`zone4_game_astar_optimize.py` 只搜索地震卷轴前凑 4000G 的单怪/按楼批处理，不能据此声称整条 4区已经做过资源组搜索。
- 晚 49 买攻资金阶段使用 `scripts/search/zone4_resource_group_astar_optimize.py`：从可复用 Game pickle 恢复，先完成确定性的正 HP 组清理，再把一个物品/怪入口经过 `go_to_decomposed` 后产生的完整门、战斗、auto、钥匙、金币和地图变化压成一条边；等价结果按资源地图状态去重，不能按目标坐标当作不同策略。
- 成本使用“当前 HP + 全图剩余血瓶价值”的势能损失；血瓶从地图转入当前 HP 的成本为 0，真实战斗/领域损失才增加成本。商人和商店仍是显式转换，黄钥匙售卖只能计入实际可出售库存。
- 搜索必须以已验证路线作 incumbent，上界剪枝后仍报告 `pool / expansions / generated / reason / preserve keys`。达到 `max_expansions` 只能写“该预算/压缩邻域未发现提升”，不能写全局最优或穷尽全图。
- 局部势能更优也不是最终胜者。候选必须从搜索后的 Game 状态继续跑完整 TE、比较最终 HP，并重新生成 canonical JSON、中文 walk 与统一 web 验证；过早卖钥匙等局部 0 伤方案可能破坏后续资源口袋和生命商店闭环。

### 4区攻防资源与商店联合搜索（强制）

- 搜索起点必须早于最早候选资源。31F/32F 宝石若可能影响后续战损或商店，就必须从神圣盾后或更早 checkpoint 比较，不能从晚 49/末次商店前才开始。
- 不得把 incumbent 的 `YK/BK/RK` 库存硬编码成全程下限。门后组可能先耗钥匙、再补钥匙/金币并改变商店次数；约束必须按后续必需资源或完整 TE 可行性建立。
- TE 真魔王攻防较低，商店动作必须把 `attack/defence/hp/skip`、购买次数和购买时机纳入宏状态。不能固定购买序列后只优化凑钱顺序；每个候选必须跑到最终 TE HP 再比较。
- 农怪或取宝石后，目标属性可能已经达到阈值。`buy_shops_to_stat` 一类转换必须在资源清理后重新检查目标，禁止无条件多买一次。
- 先用资源审计和小规模宏枚举建立 incumbent，再运行 `zone4_incumbent_macro_astar.py` 检查一跳/多跳邻域。A* 只能用可证明安全的界剪枝；必须报告已评估邻居、缺失 frontier 和预算，`h=0` 的缓存宏 A* 只证明已完成邻域，不代表全图最优。
- 当前回归例：31F 红宝石提前取有利；31F 蓝宝石和 32F 红蓝组合必须实际比较，不能按“宝石必拿”猜测。9F/18F/33F 的门后零伤怪要按净钥匙与合并金币组参与 2420G 商店阈值计算；19F 怪若已在前缀清掉，不得重复计入末局残值。
- 宝石收益必须从其最早合法取得点开始做逐战斗差分账：同一后缀分别用取得前/取得后攻防重放，累计每场普通伤害、领域伤害和强制事件伤害的变化。只比较终局属性、只看一场 Boss，或让候选提前消费后续战略怪，都会把“早拿防御”的累计减伤算错。
- 所有自动筹资/清怪器必须尊重共享 `Game.no_auto_farm`。35F 魔龙等强制时序怪不得被 `farm_gold_with_key_investment`、卖钥匙筹资或一般金币清扫提前消费；完整候选还要断言战略怪恰在规定阶段被击杀。
- `afterBattle` 不是“不可搜索资源”的同义词。若共享 `Game` 已建模击杀后的开门、显怪或地图变化，就应让资源组边执行真实事件；例如 45F 机制怪仍是合法余怪金币源，不能因带 `afterBattle` 就从终局图删除。
- 终局先从实际地图状态输出人工可核的宽松资金账：`当前金币 + 当前可售黄钥匙 + 地图剩余黄钥匙售值 + 所有剩余怪实际金币`。必须使用当前 `coin` 状态决定 1x/2x，纯净版 TE 不得默认已有幸运金币；宽松账忽略门、战损、可达性和战略时序，若仍低于商店阈值即可安全判不可能，否则再运行含门/auto/事件的组合 A*。
- A* 的主代价必须保持为真实 HP 势能损失或另一个可证明目标；“距商店还差多少金币”只能作为同主代价队列的次级 tie-break，不能伪装成 HP 启发式改变最优性。缓存宏候选排序不等于由状态动态生成的 A*，报告必须明确二者边界。
- 低属性分支可能改变阻挡怪和 NPC 可达性。可选商人应事务式探测，真实路线必须用 `go_to_decomposed` 点击合法阻挡链，不能依赖 incumbent 的直达路径。
- **终局 A* 的检查点边界**：在所有强制 TE 战斗、49F 封印与必需事件完成后、第一次可选药瓶/钥匙售卖/46F 商店闭包之前导出严格 `Game` checkpoint。不得从“钥匙已耗尽、最终 Boss 已死”的终态反推组合；那会错误删除先开钥匙袋再买商店的分支。
- **终局 A* 的状态键**：除 HP/攻防/金币/钥匙/商店次数与剩余地图块外，必须包含 `blocked_items`、`retreat_wizards`、`no_auto_farm` 和影响 NPC/事件/倍率/封印的 `flags`。仅按坐标、库存或物品表合并状态都可能把不同的商人可用性误判为同一状态。
- **终局 A* 的结论边界**：先用宽松资金账作不可能性剪枝；若上界可达阈值，则组合搜索的每条边必须从 checkpoint 经 `go_to_decomposed` 回放，并把到达商店后的候选继续跑完整 TE。找到一次可买商店只证明局部资金分支，不证明最终 HP 改善。

## 判断路线优劣

使用项目约定评分：

- `1YK = 100HP`
- `1BK = 500HP`
- `100G = 100HP`（同 1YK，支撑卖钥匙凑 2420G 商店）
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

## 2026-07-10 2区 2ATK1DEF live 修正规则

- 2区 human Markdown 可以引用 `best/current_best_boss_walk.md` 作为 1区前缀，只展开 10F boss 后的 2区步骤；机器 JSON 仍保留完整拼接，便于从新档或检查点验证。
- `MT9 x1y3 skeletonSoldier -> x2y2 yellowKey` 是 16F 左下 `x4y10` 黄门的缺钥匙补给；报告时应标成 key-pocket/bootstrap，不要误读成无目的绕路。
- 同一批资源要减少往返：若 15F 商人买蓝钥匙仅用于 11F 盾房，先买 15F 蓝钥匙，再进入 11F 左下钥匙批处理和盾房，避免 `MT11 -> MT15 -> MT11` 的额外回跳。
- 圣水是属性缩放转换节点；只要当前 HP 足够通过 20F 吸血鬼，且后续还能继续加攻防，就不要在 20F 前吃 16F 圣水。当前 2ATK1DEF 实机证明 `HP=676 ATK=70 DEF=66` 可打吸血鬼，战后 `HP=11`，圣水段应跳过并留给后续。
- 19F 十字架前的连续暗墙不能简单被离线 `auto_sweep wall=true` 折叠。实机在 `MT19 x7y6 rock` 后会自动拿附近黄钥匙，但十字架前 `x6y4/x6y3` fakeWall 需要保留显式 pass / take 步骤。
