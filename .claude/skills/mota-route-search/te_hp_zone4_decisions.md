# zone4 决策逻辑（2攻全防 / TE HP 路线，钥匙-金币-掉血权衡）

本文档记录 **2攻全防线**（`best/zone12_2atk6def_39944_walk.json`）在 zone4（MT31-40，项目脚本里叫
「zone3」）的**逐决策权衡逻辑**，格式同 `te_hp_zone1_decisions.md`。zone4 的中心议题：
**防商店购买 + 凑 4000G 买地震卷轴**。这两件事都吃金币，而金币来源 = 杀怪掉落 + MT28 卖 yk +
MT38 买 yk —— 每条都是「花血/花钥匙换金」的权衡。zone4 的高伤怪是**为金币而打的**（凑 4000G），
不是必经阻路。

> **跨区关联（funding 视角）**：zone4 末 G 若不足，会直接压垮 5 区的防商店 funding（见
> `te_hp_optimization_experience.md`「末段防商店 funding-critical」）。所以 zone4「花多少血凑金」
> 的每一项都要算到「这 100G 最终能换多少血」—— 在防商店未买满时 ~1.58 HP/G，买满后 stranded ~0。

## 通用原则（贯穿 zone4 决策）

- **掉血口径**：用 `dmg` 增量（HP delta 含 auto_sweep 血瓶副作用）。
- **金币节奏**：zone4 是「收入期」——杀怪 + 卖 yk + 买 yk 都是为了凑 4000G 地震 + 后续防商店。
- **目标排序**：防商店（~1.58 HP/G near-dragon）> 地震卷轴（结构性必需）> 买 yk（若 yk 卖更值则反转）。

## Z4-D1：MT32 防商店购买（8 次，DEF 64→202）

**决策**：zone4 起在 MT32 买满 8 次防商店（step417-583，DEF 64→202，花 ~3440G）。
**理由**：zone4 的怪（ghostSkeleton/soldier/redKnight/swordsman）物理伤害高，不堆 DEF 扛不住；
且 MT32 防（+16/次，成本 80,140,220,320,440,580,740,920G）比 MT46 防（+20/次，成本 1120+）便宜
（G/DEF 更省）。先买便宜的 MT32 防，再买贵的 MT46 防（5 区）。
**翻面**：MT32 防 vs MT46 防是「便宜先、贵后」的阶梯——若 5 区 MT46 防能提前买（金够），
重排购买顺序可能更优；但 MT32 防是 zone4 生存必需，**不能省**。改防购买会触发 auto_sweep
属性敏感 → from-scratch 重搜墙，非安全区。

## Z4-D2：凑 4000G 买地震卷轴（杀怪 + 卖 yk + 买 yk 的组合）

**决策**：zone4-5 初累积 ~4000G 买 MT47 地震卷轴（step793，-4000G，G 151）。资金来源 =
zone4 杀怪（MT31 zKnight×2、MT33 soldier×2、MT36 redKnight×2、MT38 swordsman）+ MT28 卖 yk +
MT38 买 yk 的排列组合。
**理由**：地震卷轴是 5 区 / 假魔王线结构性必需（4000G 一次性）。
**翻面（凑款替代集）**：skill 强调「为凑 4000G 的怪要做替代集比较」——`MT32 x8y7 redKnight`、
`MT36 x9y1 redKnight`（各 168 伤）这类高伤怪，若能用底层 0 伤怪或低伤怪补最后金币，通常更优。
**每一项「花血凑金」的判据 = `gold×边际HP/G > dmg`**；在防商店未买满时边际 ~1.58 HP/G，所以
dmg<158 的怪都值得为金打，dmg>158 的要省。

## Z4-D3：MT28 卖 yk vs 留 yk 开门（100G/把）

**决策**：zone4 在 MT28 specialTrader 卖 yk 换金（step536-540 卖 5 把 +500G，G 413→813）补贴防商店。
**理由**：把「现在用不上的 yk」变现成金 → 买防商店。
**翻面（funding 关键）**：**卖 yk 是否值得取决于这把 yk 后面会不会开门**。5 区还要开不少黄/蓝门
（keyBundle 蓝瓶、MT45 黄门、MT31 等），卖太多 yk 后面没钥匙开门 = 换不来门后资源。判断 =
`该 yk 未来开门能换的 HP > 100G×边际HP/G`。39944 分两批卖（zone4 卖 5 把、5 区末卖 4 把），
第二次卖 4 把**正好够最后一个防商店 funding 阈值**（见 te_hp_optimization_experience.md），是
funding-critical 的精确操作。

## Z4-D4：MT38 yellowKey3 商人（200G→3yk）值不值

**决策**：step621 MT38 花 200G 买 3 yk（G 1633→1433，yk 5→8）。
**理由**：zone4 后半 + 5 区需要很多 yk 开门（MT45 黄门、keyBundle 蓝瓶门等），200G 换 3 yk 相当于
66.7G/把，比 MT28 卖价 100G/把便宜，是「低买高卖」的套利。
**翻面**：若 yk 富余（卖都卖不完）则不该买；若 yk 极紧（要开很多门）则很值。39944 买（yk 由 5→8），
因为 5 区开门多。

## Z4-D5：MT40 swordsman ×3（426×3=1278，物理硬挡）

**决策**：step686-688 打 MT40 三 swordsman（每只 426 伤，@ATK134 DEF254）才能进 MT40 boss（zone5 入口闸门）。
**理由**：swordsman atk=680 special=0 是**物理**（per=680-254=426），神圣盾/magicImmune 无效；且是唯一路径。
**翻面**：**无**——结构性硬挡，见 `te_hp_optimization_experience.md`「结构性封闭」点 6。唯一可降的是
DEF（MT40 前 def 254→更高，但已 max）。

## Z4-D6：zone4 低伤怪金币（0伤/低伤怪批处理）

**决策**：zone4 对 0 伤/低伤怪（红史莱姆、蝙蝠类、goldSlime 等）批量清，凑金币。
**理由**：`item/battle auto` 顺带清 0 伤怪得金币，无 HP 成本；是「凑 4000G」的最低成本来源。
**翻面**：无（0 伤怪永远值得清）。

## zone4 决策-翻面清单（供优化探查）

| 决策 | 当前选择 | 翻面条件 | 39944 是否满足？ |
|---|---|---|---|
| D2 凑 4000G 地震 | 高伤怪(168)×2 + 卖 yk + 买 yk | 有 0伤/低伤怪替代，dmg>158 的怪不划算 | **待探**（MT36 redKnight 168 伤是否可用低伤替代，见 skill「凑 4000G」经验）|
| D3 卖 yk | 分两批卖（zone4 5把 + 5区 4把）| 那把 yk 未来开门换的 HP > 100G×边际HP/G | **5 区末 4 把是 funding-critical**（正确）；zone4 5把待核（是否卖早了）|
| D4 买 yk(200G→3) | 买 | yk 富余则不该买 | **是**（5 区开门多，需 yk）|

> 注：zone4 的核心可探空间 = **凑 4000G 地震的替代集**（D2）——能否用更少血凑到 4000G。
> 这直接改变 5 区进入时的剩余 HP / 防商店 funding。见 skill「纯净版-TE / Post-40 探索经验」。

---

# 门少开全防停41楼 变体（zone4，2026-08-22 web 复现）

## 路线来源与复现

来源 = 用户录像 `2区2攻+买800rk+1yk换100血的门少开+4区全防停41楼.h5route`，从
zone2 门少开录像的 **MT31 终点种子**接续（`best/checkpoints/save103_mt31_1yk100hp_snapshot.json`，
MT31 x6y2 HP=1245 ATK=76 DEF=64 YK=7 G=352）。converter 用通用 `Game` 类转：
`outputs/results/zone4_alldef_stop41_walk.json`（**321** 步，MT31->MT41）。web 复验
`outputs/results/zone4_alldef_stop41_live_verify.json` = **ok:true, goldMode exact,
finalState 全等, 0 mismatch**，触发命令：

```bash
node scripts/live/live_zone3_mouse_replayer_cdp.js \
  --walk outputs/results/zone4_alldef_stop41_walk.json --load-slot 103 \
  --target-click-only --set-auto "battle=true,item=true,wall=true" \
  --out-json outputs/results/zone4_alldef_stop41_live_verify.json
```

**终点：MT41 x6y2 HP=43 ATK=146 DEF=266 YK=10 BK=1 RK=0 G=3031**
（dmg=4102 yd=40 bd=4 rd=1 times1=10 centerFly=2 pickaxe=1 superPotion=1）。
已存槽 105 = `best/checkpoints/save105_mt41_hp43_nopotion_snapshot.json`（MT41 忠实终点，
5 区接续起点）。

> **auto-base 陷阱（本线必踩）**：MT31 种子来自 zone2 全开 auto-OFF->ON 的录像端点，
> 所以 converter **必须显式 `--auto "battle=true,item=true,wall=true"`**（不能用默认
> 全 false）。默认全 false 会让首个 游戏说明 help 反切换把后续层误关 auto，导致跨层
> RouteError。这是「后半段录像接续」通用坑，见 `recording_seed_converter_experience.md`
> 「converter seed auto base」。

> **本线最重要教训 = SET_AUTO item->nopotion（必读，用户已点破）**：录像在 zone4（MT20 绕路
> 处）关掉了自动拿血瓶（`help`+`choices` 链 → item true->nopotion）。**旧 converter 因
> `_statlog_to_route_map` 粗线性映射把 route-730 的 item-nopotion help 错快照到 route-849 的
> `choices:6` 空操作**，导致 nopotion 步从未被写出 → 我用 item=true 把省下的血瓶全 auto 喝掉 →
> 复验错误地 HP=6643。修复 = converter 用 statlog-help-run 与 route-help 精确对应（每次 help 快照
> 到自己的 route index），重转后 walk 在**步 13（MT20）正确发出 SET_AUTO item=nopotion**，
> web 复验降到 **HP=43**（原 6643 - ~6600 省下血瓶）。39944 族先前全防线没有此问题（MT20 前就
> 已 nopotion），本线是「MT31 种子接 zone4 中途才关血瓶」才踩到。教训：**后半段录像接续必须先
> 审计 SET_AUTO 何时下发，不能默认 item 一直开**。

## 本线 vs 39944 族 zone4（结构差异）

本线是「门少开」哲学在 zone4 的延续：MT28 卖 yk **6 把**（39944 卖 5 把），把更多
yk 提前变现用作 MT32 防商店 funding；停 41F 时 DEF 已堆到 **266**（39944 同点 def 254）。
zone4 购买/卖钥匙结构详见下方逐条；整体是「保守开门 + 早卖 yk + 堆防」的变体。

## Z4S-1：MT32 防商店（9 次，DEF 64->202）+ MT28 卖 yk 6 把补 funding

**决策**：MT32 分 9 批买防（步 9,10,11,71,108,122,142,188,204），DEF 64->202，
G 流 467->327->107->432->440->40->28->733->813 逐批。第一次缺钱时 **MT28
specialTrader 连卖 6 把 yk**（步 135-140，yk 8->3，G 268->768）一次性补满 → 买下一步
防店。**卖 6 把而非 5 把** = 本线门少开省下 1 yk 的变现，是 parent 族 Z4-D3 的 funding 变体。
后续还有 MT38 防店（步 267，def 202->242）+ 各层散蓝宝石（MT18/MT17/MT14/MT31/MT34/MT39
各 +2/+4），终局 def 到 266。

**翻面**：卖 6 把已把 yk 打到 3，5 区（MT45 黄门、keyBundle 蓝瓶门）开门会紧；本线赌
「5 区有 MT38 买 yk + 额外散 yk」回血。若 5 区开门超预算，应少卖 1 把留 yk。

## Z4S-2：MT38 yellowKey3 商人（200G->3yk，低买高卖）

**决策**：步 247 MT38 花 200G 买 3 yk（yk 8->11，G 1508->1308）。与 39944 Z4-D4 相同
套利（66.7G/把 < MT28 卖价 100G/把）。本线买 3 把 **在卖 6 把之后**回血，维持 5 区 yk
敞口。

## Z4S-3：低位跳门/保守开门（门少开哲学）

**决策**：走 ld 黄门序号明显低于全防族（MT33/MT34/MT38 等多处 `开门` 后 yk 不降 =
顺路拾到钥匙 + auto 已提前清门内怪）。整体 yd=40，比放开门线路省，把省下的 yk 留给
MT28 变现（见 Z4S-1）。这是 zone2「门少开」在 zone4 的对应延续。

## Z4S-4：MT40 swordsman 物理挡层 + boss，停 41F

**决策**：步 312-314 打 MT40 三 swordsman（每只 426 伤 @DEF254）后才能进 MT40 boss
（步 316 yellowKnight，0 伤）；终点走 MT41（步 320 upFloor，zone4 出口，本线停 41F
不继续 5 区）。**这是验证目的的天然截点**——zone4 全防骨架到此为止，5 区接续需另录/另搜。

## Z4S-5：MT20 关自动血瓶（item=nopotion，本线 HP 守恒的根基）

**决策**：zone4 起点附近（MT20 绕路，步 13，hp=127）经游戏说明菜单 SET_AUTO 把
`item` 从 true 切为 **nopotion**。之后 zone4 全程不自动喝血瓶，把能拿的 +800/+200/+100
血瓶**攒进库存**，只在 MT40 boss 战前**显式逐瓶喝**（步 304-309：MT38 +800、MT2 +200×2、
MT18 +100，共 +1300），把 HP 压到进 boss 打满。
**理由**：zone4 有半血陷阱（special 16）+ 需要控血到 MT40 boss，自动喝酒会把省下的血瓶在内
半血/零收益处浪费，守恒更优。这是**用户点破的失真根源**——旧转换 item=true 把省下的 ~6600HP
全自动喝掉 → 复验错误地 HP=6643；nopotion 守恒后降到 HP=43。
**翻面**：无——nopotion 是本线核心生存策略；越过 MT40 后 5 区若不再有半血陷阱才可切回
item=true（且必须如 step 13 一样下发 SET_AUTO，不能只在启动参数改）。

## Z4S-6：MT38 防御宝石跳（user 决策）

**决策**：用户明确 **跳过 MT38 防御宝石**——它要花 双手 426 血走完这段，只带来 4 DEF，
在 MT40 boss 阶段只减 `4*3=12` 伤，**血亏**（426 血换 12 减伤）。
**理由**：def 宝石对 boss 阶段的减伤 = `Δdef × 剩余刀数`，不跨阈值时极低；凑 4000G 地震 +
MT32 防商店用的是更优的低伤怪 + 卖 yk 组合。**不是真「0 伤」，是「花血换低减伤」的负收益**。
**翻面**：若该 def 能让某怪跨回合阈值（turns 减 1），价值陡升；但 MT38 后只剩 MT40 boss，
无阈值可跨 → 不可翻。

## Z4S-7：MT40 攻防宝石跳，直接 40 boss（user 决策）

**决策**：用户**跳过 MT40 x?y? 的 1bk+1yk 攻防宝石门**（打开要花 1bk+1yk），拿攻 +12/防 +12
但只减 MT40 boss 阶段 `4*3=12` 伤；且 5 区要拿地震卷轴需 **2bk**，当前只剩 1bk，花掉就断了 5 区
funding → **直接打 MT40 boss**。
**理由**：1bk 的机会成本 = 5 区 root 卷轴 2bk 硬需求；12 减伤 < bk 价值 → 跳。
**翻面**：若 5 区 earthquakes 不依赖这 1bk（有额外 bk 来源），或攻防宝石能减更多，才考虑拿。
**复现佐证**：walk 步 318 只在**免费** gem/yk 簇 auto 拾取（+12atk/+12def/+3yk，bk 仍=1），
**未开** 1bk 门 → 与用户「跳过 gated 攻防宝石、收免费簇」的决策一致。

## 本线终局资源负载（供 39944 家族对比）

MT41 出口携带：HP=43 DEF=266 **YK=10**（卖 6 把后仍是最高 YK，证明门少开省钥有效），
gold=3031（enough 继续 5 区 MT46 防商店 funding 起点）。`times1=10` 已买 10 次 1-linkage
宝石。**pickaxe/superPotion 已在途中取得**（复验最终态确认），为 5 区准备了工具。
> 与 39944 同点对比：39944 MT41 附近 DEF=254、本线 DEF=266（门少开多卖 yk->更多防店）；
> HP=43 是**nopotion 守恒下的低 HP**（血瓶攒着留 5 区），非线路差——5 区继续时血瓶库存是
> 额外资本。

---

# 7防 swap 变体（zone4，2026-08-23，web 复验）

## 思想：跳 MT32 第 8 次防店，挪 MT46 买 +20 def（ratio 净 +4）

**路线**：从已验证 8 防 walk（上面「门少开全防停41楼」321 步）固化出**跳一次防购买**的变体：

- 删 step188 的 MT32 第 8 次 def 店（920G/+16，ratio4）；
- 这 920G 挪去 5 区 MT46 买 1 次 def（+20，ratio5，净 +4 def）；
- **代价 = zone4 -16 def 窗口**（MT41 前要顶着少 16 防清完 zone4）。

**净收益 = 魔龙**：DEF 592→596，MagicDragon atk600 def250，同名 ATK259 下 def592 龙伤 1336→def596 龙伤 668，**净省 668 HP**。扣除 -16 def 窗口多吃的血（由插血瓶覆盖），是正杠杆。
**MT38 东侧**：8 防在东侧（9,4-6 黄钥匙 + 10,7/10,10 红骑士）靠西侧着陆(1,7) 的自动收集收齐；7 防因 DEF 低 go_to(1,7) 不收此处，必须**在 upFloor(11,1) 前显式收集**（见 Z4S7F-1）。

## Z4S7F-1：MT38 东侧收集时序 = 最阴的时序错位（web 卡死的根因）

**症状**：web 复验在 MT38 upFloor(11,1) 穿过时，`go_to(9,4)` 点击卡 `target click stopped before target x9y4`。
**根因**：`(9,4)` 的点击路径要穿 noPass 红骑士 `(10,7)`（`go_to` 会走但 live 点击 automaticRoute 穿不过 noPass 挡路怪，先 auto_sweep 收东侧时路径被 (10,7) 挡）。
**修复**：把东侧收集拆成 2 步显式插入——先 `go_to(10,7)` 击杀进门 redKnight（这一步的 auto_sweep 顺带把 yk 8→11），再 `go_to(9,4)`（此时已收齐，成为 no-op，但对应 live 收集时机）。**不是** `go_to(11,1)`（一次 go_to 让离线 auto_sweep 收东侧的尝试输出 `yk8->8` 没收全 = 错误修复，回退）。
**教训**：**不要把「live 在某次自动穿行时远程收集的区域」当成离线某次 go_to 一定能复现**。若离线 go_to 收集量 wrong，先看 noPass（挡路怪）是否在目标路径上；把挡路怪拆成显式击杀步（同既有 5 处 one-shot insert：MT31(8,2)/MT34(9,10)/MT37(1,9)/MT38(9,11)/MT31(4,10)）。

## Z4S7F-2：HP 压缩（427 -> 27 的最小喝水）是 5 区半血陷阱的最大杠杆

**根因**：7 防为活过 -16def 的 MT32(1,4) soldier（HP51 < 54）**被迫在步 200 喝 +800 bluePotion**，之后 zone4 全程血量一直溢在 400+，到尾段吃满 +1300（MT38 +800, MT2 +200×2, MT18 +100）到 1753，被 MT40 boss 群砍到 427。
**8 防对比**：8 防 def266 时同 soldier 只掉 6，无 insert，到尾段基线只剩 21，吃满 +1300 到 1321，被 boss 砍到 **43**。
**优化**：用固定动作序列的**最小存活 HP 压缩**（后文 skill「最低存活 HP 压缩」，从后往前 DP 只喝必要血瓶），计算得到 **MT41 到达血可压到 27**（start 1245 − 总伤 4518 + 必要喝 3300 = 27），比建成的 427 **省 400**。这 400 就是原本要被 5 区 MT44 半血陷阱（special 16，两个同魔法守卫间 HP 减半）减半浪费的部分。**压缩本质 = 把可延后的血瓶从 MT41 前延到 5 区穿过半血陷阱之后再喝**（nopotion 守恒的延续），不是减少总血瓶——总 3700 血瓶一个不少，只是更晚喝、且被陷阱减半的基数更小。
**实现坑**：压缩不是「删血瓶」而是「改喝的时刻」。在 builder 中要么让 walk 在 MT41 前**只喝最小必要**（其余攒库存留 5 区），要么把尾段 +1300 的喝血步延到 zone5 接续里。**改任何喝血时刻都改变 walk 的 HP 轨迹 → 必须重新 web 复验**（含 gold）。
**验证（2026-08-23 web 0 mismatch，含 gold）**：最小切法是在 builder 里**整体跳过尾段 MT2 +200×2 蓝瓶兜圈**——源步 `i==305 飞MT2 → [306][307] 拾取 MT2 bluePotion×2` 三个源步全 skip（`defer_mt2` 标记）。这样 MT38+800 后 HP=1253 不必飞 MT2，直接飞 MT18 吃 +100=1353，进 MT40 boss（3×442=1326）后到 **27**。实测最终态 **MT41 HP=27 ATK=146 DEF=250 G=3951 YK=10 BK=1**，web 复验 `verify9.json` 282 entry 扫 entries[] 0 值不匹配（含金币）、12 纯坐标偏移，`finalState` HP27 全等。**这两个 +200 蓝瓶留在 5 区穿过半血陷阱后喝**。
> **7 防 MT41 出口 vs 8 防**：DEF 250（−16），HP **27**（比建成 427 省 400，8 防为 43），G 3951（+920，因跳防店金没花在 zone4）。`times1=9`。7 防净胜 = 魔龙 +668 − zone4 多耗血（≈插血瓶覆盖量），需 5 区接续后算总账。**注意**：27 是刻意「只够过 MT40 boss」的极限，5 区接续必须在半血陷阱后立刻喝 MT2 留守的两个 +200 蓝瓶 + MT14/MT20/MT19 之类可及血瓶，否则 27 以下半血陷阱危险。
