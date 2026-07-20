# zone1 分段经验（4F -> MT10 Boss）

> 经验驱动搜索：walk 是 ground truth（网页 0 mismatch），经验是策略知识，搜索降为 hypothesis 探索器。
> 来源 = `best/current_best_boss_walk.md`（HP=122 已验证最优 zone1）。详细坐标/状态见 walk。
> 思路框架 + 关键抉择点为主，详细数据归 walk。

## 口径
walk HP delta 含 auto_sweep 副作用（血瓶+50 等计入同一步），不是纯单怪伤害。纯伤害看 dmg 增量或 Game `enemy_damage`。例：MT4fly bluePriest 纯伤 88 + auto 血瓶 50 = HP 净变 -38（dmg 仍记 +88）。

## seg1 · 拿剑 (sword1 @ MT5)
### 思路
4F 起点到 MT5 拿 sword1（atk 10->20）。拿剑前 atk10 只秒低伤怪（greenSlime/redSlime），避开 bat/bluePriest。拿剑后 atk 翻倍怪变零伤。dmg 200 全在拿剑前（早拿剑价值）。
### 抉择
- **D1 拿剑前选低伤怪开路** -- atk10 时 bat/bluePriest 伤高。
- **D2 拿剑后清 x8y2 greenSlime 补 4YK** -- atk20 后零伤，为 seg2 多门准备。
### 对比
搜索能达同结果（剑是强目标，易收敛）。

## seg2 · 拿盾 + 9楼攻防宝石 (shield1 @ MT9)
### 思路
MT5(seg1终) 回 MT4 flyback 拿 redGem，上到 MT9 拿盾+红蓝宝石。核心：早拿 redGem 过 bat 阈值，MT7 绕 skeletonSoldier，MT8 钥匙自给循环，MT9 三资源 auto 顺带。搜索止 932，最优 754。
### 抉择
- **D1 回 MT4 flyback 拿 redGem(atk20->21) 过 bat 阈值** -- 6 bat 省 168，占搜索差 178 的 168。搜索顺路拿 MT7 redGem 不回 MT4，bat 群已过阈值收益丢失。
- **D2 MT7 绕 skeletonSoldier** -- 高伤（atk21 时 252），走左侧绿怪。攻略 25hp 杀它。
- **D3 MT8 钥匙自给循环（净耗0）** -- 卡 MT7 出门 YK=3（段间耦合），不需 supplement 杀 skeletonSoldier。
- **D4 MT9 盾+红蓝宝石全 auto 顺带（显式仅 26 dmg）** -- redGem 到 atk22 为 seg3 打 skeletonSoldier 降伤铺垫。
### 对比
- 攻略 25hp：杀 skeletonSoldier（D2 反例）。
- 搜索 932：不回 MT4（bat 不过阈值 -168）+ 顺路 redGem 杀多怪 + over-eat MT6 blueGem。

## seg3 · 红蓝宝石到 27/27 + MT10 Boss
### 思路
9F 拿盾后（atk22 def21）不直接打 boss，回头 flyback 全图收红蓝宝石到 27/27 再打 boss。早升属性降收集怪伤和 boss（skeletonCaptain）伤。boss 前补 bluePotion×2（+400HP）+ 杀 yellowGuard×2 拿 RK 开 redDoor。
### 抉择
- **D1 9F 后 flyback 全图收宝石到 27/27** -- 不急打 boss，先升满属性全程降伤。
- **D2 7楼红宝石走上线省 2 yk** -- 开 x3y5 门 -> 打蝙蝠拿红宝石到 22 攻 -> 杀 x2y6 skeletonSoldier 上楼。因这个红宝石后续必拿，走上面拿省去下面线路的 2 道门（2 yk）。22 攻过 skeletonSoldier 阈值降伤。
- **D3 MT8 blueDoor 用起点 BK** -- 开门拿里面 redGem+blueGem+yellowKey，BK 全程留到此。
- **D4 yellowGuard×2 杀拿 RK** -- 高伤（HP 510->132）但必须，RK 开 boss redDoor；配 bluePotion+200 回血。
- **D5 boss 事件清生成怪** -- MT10 x6y5 trigger 后清 6 skeleton + 2 skeletonSoldier + skeletonCaptain。
### 对比
- 攻略：[待补]
- 搜索：[待补]

## 搜索瓶颈（seg2 止 932，非 enemy_h）
MT7 redGem 顺路优先（A* 选近不回 MT4，bat 群已过阈值收益丢失）+ 钥匙搜索杀 skeletonSoldier（seg1 YK 少补钥匙）。多因素耦合，非单 enemy_h 可解。
