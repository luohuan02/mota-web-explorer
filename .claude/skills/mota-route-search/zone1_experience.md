# zone1 经验（4F -> MT10 Boss）

来源 = 已验证 walk `best/current_best_boss_walk.md`（Phase-1 产物，boss 后终态 HP=122 ATK=27 DEF=27，final-score=1376.5）+ **2攻线录像 zone1 复刻** `best/zone12_2atk0def_recording_walk.md`（KILL 线 converter 版，MT4-20 web 0 mismatch；zone1 部分经 MT10 boss + thief 事件终态 HP=625 ATK=30 DEF=30 YK=3）。经验记**策略思路 + 关键抉择 + 原因**，详细坐标/数据看 walk。宝石顺序的数值依据来自 Game 类实测（`tmp/seg3_trace.py` 可复跑）。

## 两条 zone1 walk 的关系

- **current_best_boss**（HP=122 ATK=27 DEF=27）：27/27 策略，**止于 boss**（pre-boss HP≈756，boss 634 伤 -> 122），不含 MT10 thief 事件。是 Phase-1 分数产物。
- **2攻线录像 zone1**（HP=625 ATK=30 DEF=30）：同一 27/7 骨架（redDoor 前 HP=659 ATK=27 DEF=27），boss -> HP=25，**继续走 MT10 thief 事件**（+3ATK/+3DEF/+600HP/+3YK -> 625/30/30）。thief 事件见下「seg3 D3」。
- 二者 pre-boss HP 不同（756 vs 659）：current_best_boss 的 zone1 收集略更省血（Phase-1 优化目标不同）；2攻线 zone1 不优化单区 HP，为 end-to-end 2攻服务。**27/27 阈值策略本身一致**（红宝石按 atk 阈值、蓝宝石按钥匙流 + 路径成本，见下）。

## 分段依据

按**装备/属性里程碑**切分（与 `milestone_strategy` 一致：关键装备作阶段目标，分阶段访问楼层比一次搜完更优）。每段终点是一个里程碑状态，段间有耦合。

| 段 | 里程碑 | 起止属性 | 核心策略 |
|---|---|---|---|
| seg1 | 拿剑 sword1 | atk 10->20（MT4->MT5）| 没剑打怪太贵，先拿剑解锁可负担战斗 |
| seg2 | 拿盾 shield1 + 9F 宝石 | def 10->21, atk 20->22（MT4flyback->MT9）| flyback 红宝石过 bat 阈值 + MT8 钥匙循环 + 段间耦合 |
| seg3 | 攻防到 27/27 + MT10 Boss | atk 22->27, def 21->27（MT9->MT10 boss）| 红宝石按 atk 阈值排、蓝宝石按钥匙流排 + 红钥匙获取 + boss 触发 |

**为什么不在 seg2 一次搜完所有宝石？** 拿盾前 atk/def 低，绕远拿宝石伤害高；先冲盾（防御里程碑）再回头清扫，伤害更低。这造成 seg2 绕过宝石、seg3 延后回收的段间分工--也是 seg2/seg3 切分的根本原因。

## 口径

walk 的 HP delta 含 auto_sweep 副作用（血瓶 +50 等计入同一步），**不是纯单怪伤害**。纯伤害看 dmg 增量或 Game `enemy_damage`。例：MT4fly bluePriest 纯伤 88，同步 auto 血瓶 +50，HP 净变 -38（dmg 仍记 +88）。读 walk 伤害用 dmg 累计校验，勿直接用 HP delta。

## seg1：拿剑 sword1

**思路**：4F 存档起，最小代价上 5F 拿剑（atk 10->20）。没剑时只打最便宜的 greenSlime/redSlime 凑路，不开多余门。

**抉择**：无重大分叉，直奔剑。seg1 的作用是解锁战斗，为 seg2 flyback 扫清成本。

## seg2：拿盾 shield1 + 9F 攻防宝石

**思路框架**：拿剑后**不直上 6F**，而是回 4F flyback 拿 redGem 过 bat 阈值，再一路上 9F 拿盾（def 20）+ 9F 宝石（atk 22/def 21）。核心是「先过 bat 阈值再打蝙蝠群」，把 seg2 主差从搜索的 932 压到 754。

**抉择**：

- **D1 flyback redGem 过 bat 阈值（与搜索 932 的首要分歧）**：回 MT4 杀 bluePriest 触发 auto redGem（atk 20->21）。atk21 是 bat 伤害阈值（56->28，半伤），seg2 一路 6 只蝙蝠省 168（占搜索差 178 的大头）。
- **D2 MT7 走下线（主路线）**：第一次过 MT7 走下线（x1y1 上楼），不碰 x3y5/x3y3 红宝石区，直奔 MT8/MT9 拿盾。红宝石留给 seg3 回头收。
- **D3 MT8 钥匙自给循环 + 段间耦合**：进 MT8 需 YK≥3，开 3 门（YK 3->0），take yellowKey 触发 auto +2（YK 0->3），净耗 0。这反向卡住 **MT7 出门必须 YK=3**（seg2 内部段间耦合：MT7 出口 YK 被 MT8 入口需求锁定）。

**替代线路（variant，非当前最优 walk）**：MT7 走上线 - 开 x3y5 -> 打蝙蝠拿红宝石到 22 攻 -> 杀 x2y6 skeletonSoldier 上楼。因这个红宝石后续必拿，走上线省去下线的 2 道门（2 yk）；22 攻过 skeletonSoldier 阈值降伤。当前最优 walk 走下线 + seg3 回头收此红宝石；上线方案作对照保留，2 yk 是否净赚取决于「上线多打的伤害 vs 下线 2 门价值」，未定。

## seg3：攻防到 27/27 + MT10 Boss

**思路框架**：seg2 冲到 9F 拿盾，绕过了大量宝石。seg3 用更高的 atk/def（22/21）**延后清扫**这些宝石到 27/27，再获取红钥匙开门打 boss。宝石顺序的核心思路是：**红宝石按 atk 阈值排，蓝宝石按钥匙流排**。原因见下。

### 为什么红宝石看阈值、蓝宝石不看（机制）

atk 影响**战斗回合数** turns=ceil(怪hp/(atk-怪def))，回合数跳变点 = 阈值，跨过即降伤。def 只降每回合伤害（per=怪atk-def），**不改变 turns**。所以**蓝宝石（+def）无阈值**，红宝石（+atk）才有。这决定了红宝石顺序按阈值 urgency 排，蓝宝石顺序纯按钥匙/门流排。

### 红宝石顺序 = atk 阈值驱动

| 红宝石 | atk | 跨过的阈值（def=21 实测） | 受益的后续战斗 |
|---|---|---|---|
| **MT7红（首拿）** | 22->23 | skeleton 63->42（t4->3）、bluePriest 44->33（t5->4）、skeletonSoldier 155->124（t6->5，route 内骷髅士兵均 atk26 打，未直接受益）| MT6 骷髅、MT3 蓝法师、MT8 骷髅/蓝法师降伤 |
| MT1红 | 23->24 | 无（2-for-1 触发点，按钥匙流定位）| - |
| MT8红 | 24->25 | 无（2-for-1 触发点）| - |
| **MT3红（必须先于 MT5）** | 25->26 | skeletonSoldier 124->93（t5->4）| MT5 x2y7 骷髅士兵紧接其后，省 31 伤 |
| MT10红 | 26->27 | yellowGuard t13->10、skeletonCaptain t10->9（def27 实测）| 终局：红钥匙守卫 + boss（见「红钥匙守卫和 boss 都在 27/27」）|

- **为什么 MT7 红首拿**：atk23 是 seg3 早段唯一阈值，一次跨 skeleton/bluePriest 两怪阈值（skeletonSoldier 阈值同跨但 route 内骷髅士兵均 atk26 打，未实现，见上表）。原 ROUTE 把 6F 蓝放第一（MT6 骷髅在 atk22 打 = 63）；refined 把 MT7 红提前（MT6 骷髅在 atk23 打 = 42），单点省 21 + 一路蓝法师/骷髅兵降伤。这是 seg3 最大的单点优化。
- **为什么 MT3 红必须先于 MT5**：MT3 红（atk25->26）跨 skeletonSoldier 阈值（124->93），而 MT5 紧接打 skeletonSoldier x2y7。若 MT3 红晚于 MT5，MT5 骷髅士兵在 atk25 打 = 124（t5），多 31 伤。这条红宝石顺序被阈值锁定，不可换。

### 蓝宝石顺序 = 钥匙流 + 路径成本驱动（无阈值）

蓝宝石只 +1 def（每回合降 1 伤），无 turns 跳变。顺序由两个驱动：(1) **YK/BK 流和门**锁前 3 颗相对序（MT3->MT6 YK 链、MT6->（MT7骷髅 +2yk 补给）->MT1）；(2) **获取路径成本**锁后续（MT1->MT8、MT5蓝->MT10蓝 都是贵路径放后享更高 def，详见各 bullet + SKILL「宝石排序原则」）。

- **MT3蓝 -> MT6蓝（YK 链）**：MT7 红开门耗 1 YK（2->1）；MT3 蓝法师击杀掉 1 YK（开门 1->0，掉落回 0->1）；这把 YK 正好给 MT6 开 x1y10 门（1->0）。若 MT6 先于 MT3，MT6 门耗完 YK 后 MT3 门无 YK 可开，卡死。**MT3蓝必须在 MT6蓝前。**
- **MT7骷髅（YK+2 补给）-> MT1**：MT1 要开 2 道黄门（x6y6/x9y5），YK 需求大；MT6 后 YK=0，所以插一个 MT7 x9y5 骷髅（掉 2 YK）专门补给 MT1。
- **MT1 先于 MT8 = 路径成本序（非钥匙流、非 HP）**：两者都是 2-for-1 红蓝 bundle（MT1 redPotion 触发 x7y4蓝+x7y3红；MT8 yellowKey 触发 x5y11蓝+x4y10红），无阈值差。**钥匙两种顺序都可行**——MT7骷髅 +2yk 后 yk=2，够 MT1 两门（2->0、bundle 回吐1）或 MT8 一门（2->1、bundle 回吐+2），不强制；MT8 耗的初始 BK 自始可用。红药 +50hp 两序都拿，HP 非约束。真正驱动是**获取战损**：MT1 段 3 战 = 57 伤（@23/23）且红药回 50；MT8 段 5 战 = 102 伤（@24/24）无回血。贵的 MT8 放后享 def24：MT8@24/24 比 @23/23 省 8（102 vs 110），MT1@24/24 仅省 5（52 vs 57），交换总伤 162 vs 159，**多 3**。实测 `tmp/swap_mt1_mt8.py`。
- **MT8 -> MT4 -> MT9（BK 链）**：MT8 开 blueDoor 耗初始 BK（1->0）；MT4 x2y1 blueKey 补 BK（0->1）；MT9 开 blueDoor 上 MT10 耗 BK（1->0）。BK 链锁死三者顺序。**核心决策=稀缺 BK 换必经蓝门路权**：zone1 仅 2 把 BK（初始+MT4），全花在两扇必经蓝门上--MT8 蓝门 [3,11] 是红蓝宝石簇唯一入口（簇四周墙，蓝门是唯一连接主区），MT9 蓝门 [3,11] 是上 MT10 唯一通道（upFloor [1,11] 被墙围死，无黄门替代）。**两段上楼一黄一蓝**：MT8->MT9 上楼走 3 黄门（[3,1]/[4,1]/[6,3]，耗 YK 不耗 BK）；MT9->MT10 上楼只能走蓝门（耗 BK）。正因为 MT9 上楼必耗 BK，必须把 BK 留到 MT9--MT8 只能用初始 BK、MT4 补后再给 MT9。蓝门=用稀缺 BK 换必经路权（绕开长黄门战斗路径省血），BK 比 YK 紧，比较重要。
- **MT10蓝/红分两次 + MT7骷髅士兵补给**：MT10 第二次（拿红宝石）要开 3 道黄门（x3y9/x9y9/x11y9），中间插 MT7 x9y7 骷髅士兵（掉 2 YK + bluePotion）补 YK（补给可取非硬卡，见下节）。
- **MT5蓝 先于 MT10蓝 = 路径成本序（非钥匙流）**：这两颗相对序不由 YK/BK 决定（MT5蓝 不耗钥匙，MT10蓝 耗 BK 链但由 MT4/MT9 满足），而由获取路径成本：MT5蓝 只打 1 个骷髅士兵，MT10蓝 要打 MT4 蓝法师+MT9 蝙蝠+MT10 骷髅（3 战）。第 6 颗享 def26、第 5 颗卡 def25，贵路径（MT10蓝）放第 6。实测提前 +3 伤（见下节）。

### 为什么 MT10 宝石最后--路径成本 + 终局阈值 + 减伤，不是 BK/YK 短缺

BK 不是阻塞（seg3 起手 BK=1 够开 MT9 蓝门上 MT10；BK 链只要求 MT4 夹在两消耗者间）。**YK 也不是硬短缺**--MT10 区域需 4 黄门（蓝 1 + 红 3），MT10 入口 YK=2 + MT7 x9y7 骷髅士兵补给（+2 YK + bluePotion）恰好 = 4，不缺；补给插在 MT10蓝 之后是为享 def27 减伤（下条），不是拿不到。真正原因三层：

- **MT10红 最后 = 路径成本最贵（非 YK 卡死）**：MT10红需 3 黄门（其它红仅 1-2 门：MT7红/MT3红 1 门、MT1红 2 门、MT8红 1 门+1 蓝门），3 门要插骷髅士兵补给战凑 YK，再加 2 蓝法师 + 骷髅（共 4 战 + 3 门，4 战含 1 补给战）。其它红均无需 YK 补给战。按路径成本序最贵的放最后。钥匙可先拿（补给在 def26 也能打），但 MT10红战斗 def26 打比 def27 多 11 伤（下条），晚拿更便宜。
- **MT10蓝 先于 MT10红 = 减伤（非钥匙）**：MT10蓝（def26->27）先做，让骷髅士兵补给 + MT10红战斗享 def27。实测（`tmp/seg3_points234.py`）：防御先总伤 167（B1 骷髅 32@26/26 + B2 骷髅士兵 75@26/27 + B3 两蓝法师+骷髅 60@26/27）；钥匙先（def26 打 B2+B3）总伤 178，**多 11**。B1 骷髅 atk26/27 均 3 回合（无阈值），差额纯来自 def27 降 B2(78->75)+B3(68->60)。钥匙两序都可行，是减伤非钥匙。
- **MT10蓝 最后 = 贵路径享高 def（非搭便车）**：MT10蓝获取路径最贵（MT4 蓝法师+MT9 蝙蝠+MT10 骷髅，3 战 + BK 链），6 颗蓝里第 6 颗享 def26、第 5 颗卡 def25。实测提前到 MT5蓝 前（`tmp/reorder_mt10blue.py`）：HP 122->119、dmg +3 更差。故 MT10蓝 最后是伤害最优。
- **atk23 阈值是下限**：MT10 skeleton×2、bluePriest×2 在 atk23 阈值（skeleton 63->42、bluePriest 44->33），atk22 先打多挨 +64。故 MT10 不在 MT7红（atk23）前做（route 在 atk26 做，远高于下限）。
- **MT10红 atk27 跨终局阈值（非 gem-phase）**：MT10红 atk26->27 跨 yellowGuard（13->10 回合，def22 致 hero_hit 4->5）和 skeletonCaptain/boss（10->9 回合）。但这些都是**终局**战斗（红钥匙守卫 + boss），宝石提升阶段 atk27 不减任何 gem-phase 战斗（MT10红自己战斗在 atk26 打，redGem 是奖励）。故宝石排序里 MT10红按路径成本（最贵）排最后，其 atk27 阈值归终局（下节），二者一致：最贵 + 终局阈值 = 最后。
- **MT10 分两次访**：MT10蓝（visit1，1 YK 起手够）-> MT7骷髅士兵补给（YK+2+bluePotion，享 def27）-> MT10红（visit2，3 YK，享 def27）。拆两次因一次 4 门 YK 不够，但补给可取非硬卡；蓝先红后是减伤（上条）。

### 为什么红钥匙守卫和 boss 都在 27/27 打（atk 是杠杆，非 def）

红钥匙（MT8 x10y2）由 2 yellowGuard（x9y5/x11y5）守，之后开 MT10 redDoor 打 boss。两者都在 27/27（MT10红 atk27 + MT10蓝 def27 之后）打，原因相同--**atk27 跨阈值，def27 只降每回合**：

- **yellowGuard def=22**：atk26 hero_hit=4（13 回合）、atk27 hero_hit=5（10 回合）。实测（`tmp/seg3_points234.py`）：yellowGuard @27/27=189 / @26/27=252 / @26/26=264。**26/27->27/27 省 63（atk 跨阈值），26/26->26/27 只省 12（def）**。故 26/27（有 def27 缺 atk27）远不如 27/27--atk 是杠杆，不能拿 def 顶 atk。2 守卫 @27/27=378（trace step127-128 dmg +378 印证）；26/27 打=504，多 126。
- **boss 同理**：boss=6 skeleton+2 skeletonSoldier+skeletonCaptain，@27/27=634（trace step139 印证）/ @26/27=672 / @26/26=699。atk27 省 38（队长 10->9 回合），def27 省 27。
- **结论**：MT10红（atk27）必须先于红钥匙守卫 + boss，因 atk27 跨二者阈值。守卫延到 27/27 省 126 血；boss 在 27/27 省 38+27。这也是 MT10红 atk27 的终局阈值价值。

### 抉择

- **D1 红钥匙获取（seg3 最贵）**：MT8 杀 2 yellowGuard（HP 510->132，约 378 伤）+ bluePotion 触发 auto redKey。红钥匙是 MT10 redDoor（boss）硬门槛；2 yellowGuard 必在 27/27 打（atk27 跨其 def22 阈值省 126 血，见「红钥匙守卫和 boss 都在 27/27」），是 seg3 最大单笔伤害，靠前后 bluePotion(+200)+redPotion(+50) 回血。
- **D2 blueKey 获取**：MT4 x2y1 blueKey（gated by bluePriest + yellowDoor），打通 BK 链上 MT10。
- **D3 boss 触发时机**：集齐 27/27 + redKey + bluePotion 后，开 MT10 redDoor 触发 boss 事件（清生成怪 skeletonSoldier×2 + skeleton×6 + skeletonCaptain，约 634 伤），终态 HP=122（current_best_boss 止于此）。

### MT10 thief 事件（boss 后补给，2攻线录像继续走）

boss 杀完队长后，**MT10 (6,9) thief 事件**是 zone1 -> zone2 的衔接补给（`zone12_recording_autoon.py` 用 `apply_mt10_supply` 建模）：

- 触发：开 (6,3) yellowWall + thief 对话。auto-eat 12 supply 资源 = 3 redGem + 3 blueGem + 3 bluePotion + 3 yellowKey。
- 收益：+3 ATK（3 redGem）+3 DEF（3 blueGem）+600 HP（3 bluePotion ×200）+3 YK（3 yellowKey）。2攻线录像 HP 25->625、ATK 27->30、DEF 27->30、YK 0->3。
- **current_best_boss 不含此事件**（Phase-1 止于 boss），故终态 122/27/27 而非 625/30/30。做 end-to-end（接 zone2）时必须走 thief 事件，否则 zone2 起点 ATK 少 3、HP 少 600。

## 搜索瓶颈（seg2 止 932，非 enemy_h 单因）

MT7 redGem 顺路优先（A* 选近不回 MT4，且 MT7 redGem 时 bat 群已打完，阈值收益丢失）+ 钥匙搜索杀 skeletonSoldier（seg1 YK 少补钥匙）。多因素耦合，非单 enemy_h 可解。

## 对比工具

`scripts/audit/compare_segment_walks.py`（待建）：找分叉点 + HP 归因（哪个怪/gem/门导致差异），用于攻略线/搜索线/最优线对照。每段可存 `variants/`（最优/搜索/攻略）供其分析。
