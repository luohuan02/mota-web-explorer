# zone2 决策逻辑（2攻全防 / TE HP 路线，钥匙-金币-掉血权衡）

本文档记录 **2攻全防线**（39944 同族，`best/zone12_2atk6def_39944_walk.json`）在 zone2
（MT11-20）的**逐决策权衡逻辑**，格式同 `te_hp_zone1_decisions.md`：每条 = 决策 / 理由 / 翻面条件。
zone2 的「钥匙」主要是**金币**（买红钥匙 800G、买 2 攻、买 BK），「掉血」是区内心态 + 进 4 区的
剩余血量。机制级经验（cross/事件/宝石序）另见 `zone2_experience.md`（D1-D9）；本文件只留
**钥匙-掉血权衡**的决策与翻面。

> **跨区关联（funding 视角）**：zone2 的每一项金币花销都与终局「防商店 funding」竞争——见
> `te_hp_optimization_experience.md`「末段防商店 funding-critical」：末段 1 把 yk ≈ 835 血
> （只在凑够防商店 funding 阈值时），**zone2 省下的每一分钱/每一把 yk 都可能决定 4 区防商店档位**。
> 所以 zone2 的「省 80G / 省 800G / 卖 yk」决策不是局部的，而是终局阶梯函数的输入。

## 通用原则（贯穿 zone2 决策）

- **2 攻线骨架**：MT12 只买 2 攻（省 80G 延后 4 区防），红钥匙**买**（官方路线 B：2攻+800红钥匙+4区爆防）。
- **掉血口径**：walk HP delta 含 auto_sweep 血瓶副作用，读纯伤害用 `dmg` 增量或 `enemy_damage`。
  dmg = `(turns-1)×per`，turns=ceil(怪hp/(atk-怪def))，per=怪atk-hero_def。
- **钥匙/金币机会成本动态**：zone2 前期金币紧（买 2 攻 + BK + redKey 抢钱）、后期富余
  （MT28 卖 yk 补防商店）。同一权衡随终局 funding 档翻面。

## Z2-D1：MT12 商店只买 2 攻（省 80G 延后 4 区防）

**决策**：MT12 blueShop 买 **2 攻**（ATK 30→38，60G），**不买第 3 攻、不买防**。
**理由**：资源花费对比——
- 第 3 攻 ATK38→42 花 80G(=400HP) 只跨 yellowGuard（hp50 def22）1 个阈值，4 只省 72 伤，**净亏 328**。
- zone2 防 DEF30→38 花 80G 只 +8 DEF（ratio2），同金币 4 区（ratio5）给 +20 DEF，净亏 ~260。
**翻面**：仅当 4 区防已买满（13 次全买）或金在 zone2 必须花掉才考虑；否则「2 攻 + 防延后 4 区」最优。

## Z2-D2：剑先盾后（ATK 杠杆 > DEF）

**决策**：先 MT17 sword2（ATK 40→60）后 MT11 shield2（DEF 32→52）。
**理由**：zone2 ATK 主导——高防怪（吸血鬼 def66/zKnight def15）靠 atk 减回合数，收益 > def 减每回合。
sword2 +20 ATK 跨多怪回合阈值（yellowGuard t3→2、zombie t8→5、blackSlime t4→3、redPriest t10→4）。
**翻面**：无（结构性：ATK 是 zone2 主杠杆）。

## Z2-D3：MT16 blackSlime 先于 MT17 sword2（过 yellowGuard 阈值）

**决策**：先拿 MT16 blackSlime（+2 ATK，38→40）再打 MT17 sword2 的 4 个 yellowGuard。
**理由**：ATK38 时 yellowGuard hero_hit=16→turns=4（per=18，DEF30）dmg=54/只；ATK40 时 hero_hit=18→turns=3
（per=16，DEF32）dmg=32/只。**跨 4→3 回合阈值，4 只省 (54-32)×4=88 伤**。这不是「+2 ATK」小事，是 gem 序硬约束。
**翻面**：无（gem 序锁死）。

## Z2-D4：MT11 shield2 的 200G BK 值不值

**决策**：花 200G 在 MT15 买 BK（`trader blueKey1_15`，G 234→34）开 MT11 蓝门拿 shield2。
**理由**：shield2 +20 DEF 是 zone2 里程碑（DEF 32→52）；MT11 蓝门是盾房唯一入口，zone2 BK 紧
（MT6 商人 50G/BK、MT15 商人 200G/BK）。
**翻面**：若 BK 更紧（别处要用）或缺 200G，比较 shield2 的 +20 DEF 收益 vs 200G 在 4 区防的
价值（~1.58 HP/G near-dragon → 200G ≈ 316 血）；zone2 的 200G 通常仍值得（shield2 贯穿 zone2/3 减伤）。

## Z2-D5：ATK70 硬地板锁宝石序（MT19 redGem 先于 rock）

**决策**：MT19 redGem（x11y1，杀 bigBat 时 auto 拾，ATK 68→70）必须先于 MT19 rock（x5y6，ATK70 地板）。
**理由**：rock hp20 atk100 **def68**，ATK<69 则 hero_hit≤0 杀不掉（dmg=inf）。ATK70 才能杀（turns=10，
dmg=378 @DEF58）。rock 守 MT19 cross。**redGem 在 rock 前是 visit 顺序锁**。
**翻面**：无（硬门槛，ATK70 是 rock 地板）。

## Z2-D6：cross 必备（吸血鬼 15510→705）

**决策**：MT19 拿 cross（(6,3) fakeWall2+setBlock 事件锁，需 rock + 蓝门前置）。
**理由**：吸血鬼 hp444 atk199 def66。无 cross：ATK70 hero_hit=4→turns=111→dmg=**15510（必死）**；
有 cross（atk×2=140）：hero_hit=74→turns=6→dmg=**705**。cross 把必死变可打，**非可选**。
**翻面**：无（硬门槛）。

## Z2-D7：红钥匙买(800G) vs 杀(3 zombieKnight)——核心金币权衡

**决策**：39944（2攻全防）**买** MT12 redKey（800G）。另一选择：MT14 杀 3 zombieKnight。
**理由**：
- 纯 zone2 HP 等价：杀略便宜（372 伤 -90G ≈ 327 HP）< 买（0 伤 -800G ≈ 400 HP）。
- 但**买是官方路线 B**，且杀需 MT14 蓝门+黄门绕路。
- **end-to-end 风险**：买 800G 使 zone2 末 G 贫（MT20 后 ~345），4 区攻商店饿死 → 魔龙战 ATK 低
  多挨 6180 → redkey12 线实测 19562 < 2ATK1DEF 23076。
**翻面（关键，与终局 funding 联动）**：这 800G 若改杀 zKnight 保下，可能：
- ① 补贴 4 区攻商店（魔龙 ATK 更高，伤更少）；
- ② 或直接进终局防商店 funding（多 800G → 可能多买一档防/更接近 2420 商店）。
所以「买 vs 杀」不是 zone2 局部最优，而是**要算到魔龙 + 防商店 funding 之后**。39944 选买（路线B）
并靠 4 区爆防补偿，是本 repo 已 web 验证的最优实现；改杀需 from-scratch 重搜验证。

## Z2-D8：吸血鬼触发 = cross + redKey + 踩 (6,8)

**决策**：拿 cross + redKey 后，hero 踩 MT20 **(6,8)** 触发吸血鬼（非 floor-entry），杀 (6,6) 吸血鬼，
afterBattle +6 ATK +6 DEF + HP + 3 YK。
**理由**：事件机制——(6,8) 是空格但是 event trigger 格，跳过则吸血鬼不 spawn。
**翻面**：无（事件触发，不能跳）。

## Z2-D9：MT16 钥匙差≥3 时用 MT7 商人补（1yk + 44血 → 5yk）

**决策**：若 MT16 遇到 yk 差 ≥3（要开的黄门多），回 MT7 商人花 `1YK + 44 血` 换 `5 YK`。
**理由**：MT7 商人（x6y1，`G50→5YK`）是 zone2 最便宜的补钥匙源。当手上 yk 不够应付「开
MT16/18/19 多扇黄门」时，用 1yk 现钥 + 44 血一次性补到富余，避免因缺钥在某扇低价值门处
绕坑/少开资源门。**前提是这笔补钥不会饿死 MT12 买 2 攻 + redKey 的 800G**——补钥花的是
血不是 G，所以只与「终局 funding 阶梯」无直接冲突，纯 zone2 局部划算。
**翻面**：yk 差 <3 → 不值得回程（44 血 > 补钥收益）；或该分支「门少开」哲学下本就不开那几扇黄门
（见下文「门少开 vs 补钥」），则不需要补钥。

## Z2-D10：MT16 上楼取 1BK（x6y4）+ 1YK（x6y8）

**决策**：MT16 上楼前拿 x6y4 blueKey 和 x6y8 yellowKey。
**理由**：这两格是 zone2 白拿的钥匙资源，成本只是绕路步数；BK 缓解 MT11 盾房蓝门（配合 D4）。
**翻面**：若某分支已从 MT15 买 BK 且 MT16 上楼会多绕一段高代价走廊，则可延后；多数分支顺路必拿。

## Z2-D11：拿盾后回 1 区清 0 伤资源（indirect）

**决策**：拿到 shield2（DEF 52）后回 zone1 清扫所有 0 伤怪（greenSlime/redSlime/蝙蝠）金币与
散落宝石/血瓶。
**理由**：DEF 52 让 zone1 大多数怪变 0 伤（无成本金币）→ 金币是终局防商店 funding 的输入，
越早批处理越赚。这是「双倍金币后大清洗」的 zone2 版（见 skill「局部批处理」/「清理策略」）。
**翻面**：nopotion 约束下某些 +800 蓝瓶要留到 zone3-4（圣盾后）再收（免半血陷阱损失），
此时只清 0 伤怪不出 +800 蓝瓶。

## Z2-D12：宝石序 = 15防 → 12防 → 12攻 → 11攻（DEF 先行）

**决策**：zone2 宝石收集顺序：MT15 蓝（DEF）→ MT12 蓝 → MT12 红（ATK）→ MT11 红。
**理由**：zone2 ATK 虽有阈值，但**防御宝石无阈值只降每回合伤**；在 ATK 主杠杆已由 sword2/redGem
提供的骨架下，先加上乘风 DEF 宝石（15/12 蓝）能稳定压低所有打怪伤，再补 12/11 红宝石调阈值。
顺序不同 → 同场战斗最终 dsame，但对「先打高伤怪还是先打宝石」的访问路径成本有影响（蓝宝石
路径便宜的先拿，如 zone1 的蓝宝石路径成本原则，见 `te_hp_zone1_decisions.md` seg3）。
**翻面**：ATK 卡某硬阈值（如 68→70 comf rock）时优先红宝石跨阈；此骨架主要靠 sword2(60)+redGem(70) 达标。

## Z2-D13：BK 来源选择（MT6 商人 / MT15 商人 / MT16 x6y4 / MT18 蓝门）

**决策**：zone2 需要 BK 时按成本排序：MT16 x6y4 白拿 > MT6 商人(50G) > MT15 商人(200G) ≈ MT18 蓝门。
**理由**：BK 是 zone2-3 steel 门槛（rock/cross/steel 频繁吃 BK）；白拿优先、便宜的 G50 次之、
G200 最后。**翻面**：若终局 funding 紧（MT28 卖 yk 补防商店），G50/G200 买 BK 的机会成本要算成
「那笔 G 在 4 区防的 1.58 HP/G」；BK 确实需时才买，不囤。

## Z2-D14：boss（吸血鬼）前补 700 血的血瓶组合

**决策**：吸血鬼（MT20，dmg=705 @cross+redKey 后）前确保 HP≥所需，用 zone1-2 血瓶组合补
（3/8/11/14/15/16/17/18/20 楼各 +50/+200/+800 蓝瓶）。
**理由**：吸血鬼是 zone2 终点 boss，cross+redKey 后 dmg=705 固定；血瓶在 zone2 无半血陷阱（zone3
才有），所以**zone2 的血瓶可以全部吃掉不留**（nopotion 不适用于 zone2，见 skill「auto 配置」）。
**翻面**：若某分支要把 +800 蓝瓶留到 zone3-4（圣盾后）共享 mt 即为该走法；否则 zone2 内吃干。

## zone2 决策-翻面清单（供优化探查）

| 决策 | 当前选择 | 翻面条件 | 39944 是否满足？ |
|---|---|---|---|
| D1 只买 2 攻 | 省 80G 延后 4 区防 | 4 区防买满/金必须花 | **否**（4 区防未买满，延后正确）|
| D7 红钥匙买 | 买 800G | 杀 zKnight 保 800G 能补贴 4 区攻/防商店 | **待探**（改杀需 from-scratch 重搜，见 [[two_attack_line_search_lessons]]）|
| D4 200G BK | 买 | BK 更紧/缺 200G | **否**（shield2 贯穿 zone2/3 减伤）|
| D9 补钥(1yk+44血→5yk) | yk 差≥3 才补 | 只开少门则不需补 | 视分支（门少开族：少开门🔊不高）|
| D13 BK 来源 | 白拿>50G>200G | funding 紧时 BK 机会成本↑ | 需时才买，不囤 |

## 门少开 vs 补钥 / 红利（2攻 录像族跨 zone2 差异）

**关键洞见**：39944 全防线与**2攻录像线（停31楼→40943）**在 zone2 属性路径相同（ATK76/DEF64），
但录像线**少开若干黄/蓝门**，省下 N 把 YK + 少打若干低值怪（dmg −213，HP +13，YK +2 at MT31）。
这 +2 YK 不是 zone2 局部的「库存」，而是**终局 MT28 卖 yk 的可变现资源**——40943 walk 末端
MT28 卖出**10 把 yk**（3411→4011 六把 + 1760→2160 四把）→ 直接补贴 15 次防商店 **8920G** 的
一大块。⇒ **zone2 的「少开门省 YK」决策是终局防商店 funding 的前置输入**，比「少打几个怪省那点
血」更值钱。任何比较「开这扇门 vs 不开省 YK」的决策要把省下的 YK 按「MT28 100G/把 → 4 区防
~1.0 HP/G」折算，而**不是**只算「门后资源的 HP」。

> 注：zone2 的「省钥匙」决策（D1 省 80G、D7 省 800G、少开门省 YK）都通过**金币→防商店 funding**
> 影响终局——不能只看 zone2 局部掉血，要接 `te_hp_optimization_experience.md` 的终局闭环反推边际值。
