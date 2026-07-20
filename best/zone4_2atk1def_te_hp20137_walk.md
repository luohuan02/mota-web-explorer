# 当前最优 Walk (zone4, auto ON)

## 说明

- 本 walk 由 Game 类 (`scripts/search/zone4_game_route.py`, auto_sweep, strict_live_model) 离线推导生成。
- auto 配置：battle=true, item=nopotion, wall=true。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone4_game_route.json --load-slot <100+> --target-click-only`（统一点击 verifier，1-4 区通用；3 区起按需 `--set-auto battle=true,item=nopotion,wall=true`）
- 源 JSON：`best/zone4_2atk1def_te_hp20137_walk.json`

## 摘要

- final: HP=20137 ATK=423 DEF=426 YK=3 BK=0 RK=0 G=1801 dmg=18498 door=48/11/7 MT50 x6y5

## Walk

### MT41

- before: HP=45 ATK=166 DEF=166 YK=7 BK=0 RK=0 G=2423 dmg=0 door=0/0/0
- MT41 x6y4 地图伤害 checkBlock [HP 45->23]
- MT41 x6y7 open yellowDoor [YK 7->6]
- MT41 x6y8 open yellowDoor [YK 6->5]
- MT41 x6y9 open yellowDoor [YK 5->4]
- MT41 x6y11 pass upFloor
- after: HP=23 ATK=166 DEF=166 YK=4 BK=0 RK=0 G=2423 dmg=22 door=3/0/0

### MT40

- before: HP=23 ATK=166 DEF=166 YK=4 BK=0 RK=0 G=2423 dmg=22 door=3/0/0
- MT40 x6y2 fly
- MT40 x5y4 take bluePotion [HP 23->823]
- MT40 x4y4 take bluePotion [HP 823->1623]
- after: HP=1623 ATK=166 DEF=166 YK=4 BK=0 RK=0 G=2423 dmg=22 door=3/0/0

### MT42

- before: HP=1623 ATK=166 DEF=166 YK=4 BK=0 RK=0 G=2423 dmg=22 door=3/0/0
- MT42 x5y11 fly
- MT42 x5y10 event yellowKnightEscape
- MT42 x8y5 open yellowDoor [YK 4->3]
- MT42 x9y5 地图伤害 checkBlock [HP 1623->1523]
- MT42 x10y4 地图伤害 checkBlock [HP 1523->1223]
- MT42 x10y3 move [YK 3->8, BK 0->1] (auto: resource group on move) (auto: x10y2 yellowKey, x10y1 blueKey, x9y2 yellowKey, x11y2 yellowKey, x9y1 yellowKey, x11y1 yellowKey)
- MT42 x10y4 地图伤害 checkBlock [HP 1223->923]
- MT42 x10y6 地图伤害 checkBlock [HP 923->823]
- MT42 x10y8 地图伤害 checkBlock [HP 823->412]
- MT42 x10y9 move [YK 8->13, BK 1->2] (auto: resource group on move) (auto: x10y10 yellowKey, x9y10 yellowKey, x10y11 blueKey, x11y10 yellowKey, x9y11 yellowKey, x11y11 yellowKey)
- MT42 x1y2 中心飞行 centerFly
- MT42 x1y1 pass upFloor
- after: HP=412 ATK=166 DEF=166 YK=13 BK=2 RK=0 G=2423 dmg=1233 door=4/0/0

### MT43

- before: HP=412 ATK=166 DEF=166 YK=13 BK=2 RK=0 G=2423 dmg=1233 door=4/0/0
- MT43 x3y1 open yellowDoor [YK 13->12]
- MT43 x1y4 open blueDoor [BK 2->1]
- MT43 x1y8 open yellowDoor [YK 12->11]
- MT43 x1y11 pass upFloor
- after: HP=412 ATK=166 DEF=166 YK=11 BK=1 RK=0 G=2423 dmg=1233 door=6/1/0

### MT45

- before: HP=412 ATK=166 DEF=166 YK=11 BK=1 RK=0 G=2423 dmg=1233 door=6/1/0
- MT45 x11y1 pass upFloor
- after: HP=412 ATK=166 DEF=166 YK=11 BK=1 RK=0 G=2423 dmg=1233 door=6/1/0

### MT14

- before: HP=412 ATK=166 DEF=166 YK=11 BK=1 RK=0 G=2423 dmg=1233 door=6/1/0
- MT14 x6y10 fly
- after: HP=412 ATK=166 DEF=166 YK=11 BK=1 RK=0 G=2423 dmg=1233 door=6/1/0

### MT18

- before: HP=412 ATK=166 DEF=166 YK=11 BK=1 RK=0 G=2423 dmg=1233 door=6/1/0
- MT18 x6y2 fly
- after: HP=412 ATK=166 DEF=166 YK=11 BK=1 RK=0 G=2423 dmg=1233 door=6/1/0

### MT17

- before: HP=412 ATK=166 DEF=166 YK=11 BK=1 RK=0 G=2423 dmg=1233 door=6/1/0
- MT17 x6y2 fly
- after: HP=412 ATK=166 DEF=166 YK=11 BK=1 RK=0 G=2423 dmg=1233 door=6/1/0

### MT46

- before: HP=412 ATK=166 DEF=166 YK=11 BK=1 RK=0 G=2423 dmg=1233 door=6/1/0
- MT46 x11y2 fly
- MT46 x11y3 open yellowDoor [YK 11->10]
- MT46 x11y5 open yellowDoor [YK 10->9]
- MT46 x11y8 open yellowDoor [YK 9->8]
- MT46 x11y9 地图伤害 checkBlock [HP 412->312]
- MT46 x11y11 pass upFloor
- after: HP=312 ATK=166 DEF=166 YK=8 BK=1 RK=0 G=2423 dmg=1333 door=9/1/0

### MT47

- before: HP=312 ATK=166 DEF=166 YK=8 BK=1 RK=0 G=2423 dmg=1333 door=9/1/0
- MT47 x7y11 open yellowDoor [YK 8->7]
- MT47 x6y11 地图伤害 checkBlock [HP 312->212]
- MT47 x6y10 take redGem [ATK 166->171]
- MT47 x6y2 中心飞行 centerFly
- MT47 x7y1 open yellowDoor [YK 7->6]
- MT47 x8y1 地图伤害 checkBlock [HP 212->12, DEF 166->171, YK 6->8] (auto: x11y1 yellowKey, x11y2 blueGem, x11y3 yellowKey)
- MT47 x3y1 open blueDoor [BK 1->0]
- MT47 x1y1 pass upFloor
- after: HP=12 ATK=171 DEF=171 YK=8 BK=0 RK=0 G=2423 dmg=1633 door=11/2/0

### MT48

- before: HP=12 ATK=171 DEF=171 YK=8 BK=0 RK=0 G=2423 dmg=1633 door=11/2/0
- MT48 x10y10 使用镐 pickaxe
- after: HP=12 ATK=221 DEF=171 YK=8 BK=0 RK=0 G=2423 dmg=1633 door=11/2/0

### MT40

- before: HP=12 ATK=221 DEF=171 YK=8 BK=0 RK=0 G=2423 dmg=1633 door=11/2/0
- MT40 x6y2 fly
- MT40 x3y4 take bluePotion [HP 12->812]
- after: HP=812 ATK=221 DEF=171 YK=8 BK=0 RK=0 G=2423 dmg=1633 door=11/2/0

### MT34

- before: HP=812 ATK=221 DEF=171 YK=8 BK=0 RK=0 G=2423 dmg=1633 door=11/2/0
- MT34 x6y10 fly
- after: HP=812 ATK=221 DEF=171 YK=8 BK=0 RK=0 G=2423 dmg=1633 door=11/2/0

### MT31

- before: HP=812 ATK=221 DEF=171 YK=8 BK=0 RK=0 G=2423 dmg=1633 door=11/2/0
- MT31 x6y10 fly
- after: HP=812 ATK=221 DEF=171 YK=8 BK=0 RK=0 G=2423 dmg=1633 door=11/2/0

### MT34

- before: HP=812 ATK=221 DEF=171 YK=8 BK=0 RK=0 G=2423 dmg=1633 door=11/2/0
- MT34 x2y1 fly
- MT34 x1y10 kill swordsman (auto: x1y10 swordsman)
- after: HP=812 ATK=221 DEF=171 YK=8 BK=0 RK=0 G=2478 dmg=1633 door=11/2/0

### MT40

- before: HP=812 ATK=221 DEF=171 YK=8 BK=0 RK=0 G=2478 dmg=1633 door=11/2/0
- MT40 x10y11 fly
- MT40 x10y9 kill swordsman [G 2478->2533] (auto: x10y9 swordsman) (+55G)
- after: HP=812 ATK=221 DEF=171 YK=8 BK=0 RK=0 G=2533 dmg=1633 door=11/2/0

### MT32

- before: HP=812 ATK=221 DEF=171 YK=8 BK=0 RK=0 G=2533 dmg=1633 door=11/2/0
- MT32 x10y1 fly
- MT32 x1y10 kill blueGuard [G 2533->2583] (+50G)
- MT32 x3y10 kill blueGuard [G 2583->2633] (+50G)
- MT32 x1y7 move (auto: x2y7 yellowKey, x1y7 yellowKey, x3y7 yellowKey, x4y8 blueKey, x4y7 yellowKey)
- after: HP=812 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2633 dmg=1633 door=11/2/0

### MT15

- before: HP=812 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2633 dmg=1633 door=11/2/0
- MT15 x6y2 fly
- MT15 x2y1 kill zombieKnight (auto: x2y1 zombieKnight)
- after: HP=812 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2663 dmg=1633 door=11/2/0

### MT18

- before: HP=812 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2663 dmg=1633 door=11/2/0
- MT18 x6y2 fly
- MT18 x7y4 kill zombieKnight (auto: x7y4 zombieKnight)
- after: HP=812 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2693 dmg=1633 door=11/2/0

### MT11

- before: HP=812 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2693 dmg=1633 door=11/2/0
- MT11 x11y10 fly
- MT11 x8y5 kill redPriest (auto: x8y5 redPriest)
- after: HP=812 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2715 dmg=1633 door=11/2/0

### MT7

- before: HP=812 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2715 dmg=1633 door=11/2/0
- MT7 x1y2 fly
- MT7 x2y6 kill skeletonSoldier (auto: x2y6 skeletonSoldier)
- after: HP=812 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2723 dmg=1633 door=11/2/0

### MT5

- before: HP=812 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2723 dmg=1633 door=11/2/0
- MT5 x1y2 fly
- MT5 x3y5 kill bluePriest (auto: x3y5 bluePriest)
- after: HP=812 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2728 dmg=1633 door=11/2/0

### MT38

- before: HP=812 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2728 dmg=1633 door=11/2/0
- MT38 x2y1 fly
- MT38 x1y3 kill ghostSkeleton [HP 812->803, G 2728->2763] (+35G)
- after: HP=803 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2763 dmg=1642 door=11/2/0

### MT39

- before: HP=803 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2763 dmg=1642 door=11/2/0
- MT39 x11y2 fly
- MT39 x3y9 kill ghostSkeleton [HP 803->794, G 2763->2798] (+35G)
- after: HP=794 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2798 dmg=1651 door=11/2/0

### MT31

- before: HP=794 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2798 dmg=1651 door=11/2/0
- MT31 x6y10 fly
- MT31 x2y3 kill soldier [HP 794->765, G 2798->2843] (+45G)
- after: HP=765 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2843 dmg=1680 door=11/2/0

### MT38

- before: HP=765 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2843 dmg=1680 door=11/2/0
- MT38 x2y1 fly
- MT38 x3y4 kill soldier [HP 765->736, G 2843->2888] (+45G)
- MT38 x4y4 kill soldier [HP 736->707, G 2888->2933] (+45G)
- after: HP=707 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2933 dmg=1738 door=11/2/0

### MT39

- before: HP=707 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2933 dmg=1738 door=11/2/0
- MT39 x11y2 fly
- MT39 x11y5 kill soldier [HP 707->678, G 2933->2978] (+45G)
- after: HP=678 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2978 dmg=1767 door=11/2/0

### MT40

- before: HP=678 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=2978 dmg=1767 door=11/2/0
- MT40 x10y11 fly
- MT40 x9y10 kill soldier [HP 678->649, G 2978->3023] (+45G)
- after: HP=649 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3023 dmg=1796 door=11/2/0

### MT32

- before: HP=649 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3023 dmg=1796 door=11/2/0
- MT32 x10y1 fly
- MT32 x8y7 kill redKnight [HP 649->590, G 3023->3088] (+65G)
- after: HP=590 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3088 dmg=1855 door=11/2/0

### MT38

- before: HP=590 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3088 dmg=1855 door=11/2/0
- MT38 x2y1 fly
- MT38 x10y10 kill redKnight [HP 590->531, G 3088->3153] (+65G)
- after: HP=531 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3153 dmg=1914 door=11/2/0

### MT39

- before: HP=531 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3153 dmg=1914 door=11/2/0
- MT39 x11y2 fly
- MT39 x7y9 kill redKnight [HP 531->472, G 3153->3218] (+65G)
- after: HP=472 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3218 dmg=1973 door=11/2/0

### MT43

- before: HP=472 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3218 dmg=1973 door=11/2/0
- MT43 x1y2 fly
- MT43 x2y5 kill slimelord [HP 472->333, G 3218->3258] (+40G)
- MT43 x5y1 kill slimelord [HP 333->194, G 3258->3298] (+40G)
- after: HP=194 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3298 dmg=2251 door=11/2/0

### MT46

- before: HP=194 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3298 dmg=2251 door=11/2/0
- MT46 x11y2 fly
- MT46 x10y6 kill slimelord [HP 194->55, G 3298->3338] (+40G)
- after: HP=55 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3338 dmg=2390 door=11/2/0

### MT6

- before: HP=55 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3338 dmg=2390 door=11/2/0
- MT6 x11y10 fly
- MT6 x10y3 kill skeleton (auto: x9y6 skeletonSoldier, x8y6 skeleton, x10y3 skeleton)
- after: HP=55 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3358 dmg=2390 door=11/2/0

### MT10

- before: HP=55 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3358 dmg=2390 door=11/2/0
- MT10 x1y10 fly
- MT10 x3y6 kill skeleton (auto: x2y7 skeletonSoldier, x3y6 skeleton, x10y7 skeletonSoldier, x11y6 skeleton)
- after: HP=55 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3386 dmg=2390 door=11/2/0

### MT12

- before: HP=55 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3386 dmg=2390 door=11/2/0
- MT12 x10y11 fly
- MT12 x5y3 kill redPriest (auto: x10y3 zombie, x10y1 fakeWall, x5y3 redPriest)
- after: HP=55 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3426 dmg=2390 door=11/2/0

### MT17

- before: HP=55 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3426 dmg=2390 door=11/2/0
- MT17 x5y11 fly
- MT17 x5y3 kill zombieKnight (auto: x5y7 zombie, x5y3 zombieKnight)
- after: HP=55 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3474 dmg=2390 door=11/2/0

### MT19

- before: HP=55 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3474 dmg=2390 door=11/2/0
- MT19 x1y2 fly
- MT19 x8y3 kill zombieKnight (auto: x6y9 zombieKnight, x8y8 zombieKnight, x8y3 zombieKnight)
- after: HP=55 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3564 dmg=2390 door=11/2/0

### MT37

- before: HP=55 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3564 dmg=2390 door=11/2/0
- MT37 x11y10 fly
- MT37 x9y11 kill ghostSkeleton [HP 55->46, G 3564->3629] (+65G)
- MT37 x1y9 kill soldier [HP 46->17, G 3629->3674] (+45G)
- after: HP=17 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3674 dmg=2428 door=11/2/0

### MT40

- before: HP=17 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3674 dmg=2428 door=11/2/0
- MT40 x10y11 fly
- MT40 x9y9 take redPotion [HP 17->217]
- after: HP=217 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3674 dmg=2428 door=11/2/0

### MT47

- before: HP=217 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3674 dmg=2428 door=11/2/0
- MT47 x11y10 fly
- MT47 x6y11 地图伤害 checkBlock [HP 217->117]
- MT47 x5y10 地图伤害 checkBlock [HP 117->17]
- MT47 x4y10 take redPotion [HP 17->267]
- after: HP=267 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3674 dmg=2628 door=11/2/0

### MT39

- before: HP=267 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3674 dmg=2628 door=11/2/0
- MT39 x11y10 fly
- MT39 x9y11 take redPotion [HP 267->467]
- after: HP=467 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3674 dmg=2628 door=11/2/0

### MT37

- before: HP=467 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3674 dmg=2628 door=11/2/0
- MT37 x2y1 fly
- MT37 x1y6 take redPotion [HP 467->667]
- after: HP=667 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3674 dmg=2628 door=11/2/0

### MT28

- before: HP=667 ATK=221 DEF=171 YK=12 BK=1 RK=0 G=3674 dmg=2628 door=11/2/0
- MT28 x2y11 fly
- MT28 x8y4 trader sellYellowKey [YK 12->11, G 3674->3774] (auto: +100G)
- MT28 x8y4 trader sellYellowKey [YK 11->10, G 3774->3874] (auto: +100G)
- MT28 x8y4 trader sellYellowKey [YK 10->9, G 3874->3974] (auto: +100G)
- MT28 x8y4 trader sellYellowKey [YK 9->8, G 3974->4074] (auto: +100G)
- after: HP=667 ATK=221 DEF=171 YK=8 BK=1 RK=0 G=4074 dmg=2628 door=11/2/0

### MT48

- before: HP=667 ATK=221 DEF=171 YK=8 BK=1 RK=0 G=4074 dmg=2628 door=11/2/0
- MT48 x11y10 fly
- MT48 x11y11 pass downFloor
- after: HP=667 ATK=221 DEF=171 YK=8 BK=1 RK=0 G=4074 dmg=2628 door=11/2/0

### MT47

- before: HP=667 ATK=221 DEF=171 YK=8 BK=1 RK=0 G=4074 dmg=2628 door=11/2/0
- MT47 x5y2 trader earthquake [G 4074->74]
- after: HP=667 ATK=221 DEF=171 YK=8 BK=1 RK=0 G=74 dmg=2628 door=11/2/0

### MT37

- before: HP=667 ATK=221 DEF=171 YK=8 BK=1 RK=0 G=74 dmg=2628 door=11/2/0
- MT37 x2y1 fly
- MT37 x2y1 地震卷轴 earthquake
- MT37 x5y3 take redPotion [HP 667->867, ATK 221->237, DEF 171->187, YK 8->17, BK 1->3, RK 0->1] (auto: x3y5 yellowKey, x4y5 yellowKey, x5y4 yellowKey, x3y7 blueGem, x5y5 bomb, x7y5 redKey, x3y8 yellowKey, x4y7 redGem, x8y5 yellowKey, x4y8 yellowKey, x7y7 redGem, x9y5 yellowKey, x4y9 blueKey, x5y8 yellowKey, x7y8 blueGem, x8y7 redGem, x5y9 blueKey, x8y8 blueGem, x9y7 redGem, x8y9 yellowKey, x9y8 blueGem)
- MT37 x5y4 move
- MT37 x4y4 take redPotion [HP 867->1067]
- MT37 x4y3 take redPotion [HP 1067->1267]
- after: HP=1267 ATK=237 DEF=187 YK=17 BK=3 RK=1 G=74 dmg=2628 door=11/2/0

### MT45

- before: HP=1267 ATK=237 DEF=187 YK=17 BK=3 RK=1 G=74 dmg=2628 door=11/2/0
- MT45 x2y1 fly
- MT45 x6y2 open yellowDoor [YK 17->16]
- MT45 x6y3 地图伤害 checkBlock [HP 1267->967]
- MT45 x6y5 地图伤害 checkBlock [HP 967->667]
- MT45 x6y6 open yellowDoor [YK 16->15]
- MT45 x4y7 open yellowDoor [YK 15->14]
- MT45 x2y8 open redDoor [RK 1->0]
- MT45 x6y5 地图伤害 checkBlock [HP 667->367]
- MT45 x6y3 地图伤害 checkBlock [HP 367->67]
- after: HP=67 ATK=237 DEF=187 YK=14 BK=3 RK=0 G=74 dmg=3828 door=14/2/1

### MT43

- before: HP=67 ATK=237 DEF=187 YK=14 BK=3 RK=0 G=74 dmg=3828 door=14/2/1
- MT43 x1y10 fly
- after: HP=67 ATK=237 DEF=187 YK=14 BK=3 RK=0 G=74 dmg=3828 door=14/2/1

### MT44

- before: HP=67 ATK=237 DEF=187 YK=14 BK=3 RK=0 G=74 dmg=3828 door=14/2/1
- MT44 x1y10 上楼器 upFly
- MT44 x6y9 炸弹 bomb [G 74->474] (auto: +400G)
- MT44 x6y7 take redPotion [HP 67->317, DEF 187->287] (auto: x6y6 shield5)
- MT44 x5y6 take redPotion [HP 317->567]
- MT44 x7y6 take redPotion [HP 567->817]
- MT44 x6y5 take redPotion [HP 817->1067]
- MT44 x6y5 设置自动：battle=true, item=true, wall=true
- after: HP=1067 ATK=237 DEF=287 YK=14 BK=3 RK=0 G=474 dmg=3828 door=14/2/1

### MT31

- before: HP=1067 ATK=237 DEF=287 YK=14 BK=3 RK=0 G=474 dmg=3828 door=14/2/1
- MT31 x6y10 fly
- MT31 x11y5 open yellowDoor [YK 14->13]
- MT31 x10y3 kill ghostSkeleton (auto: x11y3 ghostSkeleton, x10y3 ghostSkeleton, x10y1 redPotion, x8y2 soldier)
- MT31 x8y3 open yellowDoor [YK 13->12]
- MT31 x8y4 move (auto: x8y4 redGem)
- after: HP=1267 ATK=241 DEF=287 YK=12 BK=3 RK=0 G=589 dmg=3828 door=16/2/1

### MT43

- before: HP=1267 ATK=241 DEF=287 YK=12 BK=3 RK=0 G=589 dmg=3828 door=16/2/1
- MT43 x1y2 fly
- MT43 x3y6 open yellowDoor [YK 12->11]
- MT43 x5y7 kill slimelord [HP 1267->2244, G 589->629] (+40G)
- MT43 x8y6 open yellowDoor [YK 11->10]
- MT43 x11y5 open yellowDoor [HP 2244->2494] (auto: x10y8 yellowKey, x11y7 redPotion)
- MT43 x9y1 kill whiteKing [HP 2494->2331, G 629->729] (+100G)
- MT43 x11y9 open yellowDoor [YK 10->9]
- after: HP=2331 ATK=241 DEF=337 YK=9 BK=4 RK=0 G=729 dmg=4014 door=20/2/1

### MT46

- before: HP=2331 ATK=241 DEF=337 YK=9 BK=4 RK=0 G=729 dmg=4014 door=20/2/1
- MT46 x11y2 fly
- MT46 x9y11 open yellowDoor [YK 9->8]
- MT46 x6y11 open blueDoor [BK 4->3]
- MT46 x4y11 kill redSlime (auto: x4y11 redSlime, x2y11 skeleton, x1y10 bigBat, x1y8 zombie, x1y6 soldier, x3y6 swordsman, x5y6 redKnight, x5y8 slimelord)
- MT46 x4y9 kill brownWizard [HP 2331->2298, G 972->1052] (+80G)
- after: HP=2298 ATK=241 DEF=337 YK=8 BK=3 RK=0 G=1052 dmg=4047 door=21/3/1

### MT41

- before: HP=2298 ATK=241 DEF=337 YK=8 BK=3 RK=0 G=1052 dmg=4047 door=21/3/1
- MT41 x6y10 fly
- MT41 x6y10 魔法钥匙 bigKey
- MT41 x5y6 open blueDoor [BK 3->2]
- MT41 x2y2 kill redWizard [HP 2298->2755, ATK 241->246, YK 8->11, G 1052->1182] (+130G)
- MT41 x7y6 open blueDoor [BK 3->2]
- MT41 x9y5 kill brownWizard [HP 2755->3227, DEF 337->342, YK 11->14, BK 2->3, G 1182->1302] (+120G)
- MT41 x10y2 event redWizard
- MT41 x10y2 kill redWizard [HP 3227->3189, G 1302->1392] (+90G)
- after: HP=3189 ATK=246 DEF=342 YK=14 BK=3 RK=0 G=1392 dmg=4156 door=21/5/1

### MT40

- before: HP=3189 ATK=246 DEF=342 YK=14 BK=3 RK=0 G=1392 dmg=4156 door=21/5/1
- MT40 x6y2 fly
- after: HP=3189 ATK=246 DEF=342 YK=14 BK=3 RK=0 G=1392 dmg=4156 door=21/5/1

### MT41

- before: HP=3189 ATK=246 DEF=342 YK=14 BK=3 RK=0 G=1392 dmg=4156 door=21/5/1
- MT41 x6y2 fly
- after: HP=3189 ATK=246 DEF=342 YK=14 BK=3 RK=0 G=1392 dmg=4156 door=21/5/1

### MT42

- before: HP=3189 ATK=246 DEF=342 YK=14 BK=3 RK=0 G=1392 dmg=4156 door=21/5/1
- MT42 x5y11 fly
- MT42 x6y4 kill darkKnight [HP 3189->2837, RK 0->1, G 1392->1512] (+120G)
- after: HP=2837 ATK=246 DEF=342 YK=14 BK=3 RK=1 G=1512 dmg=4508 door=21/5/1

### MT46

- before: HP=2837 ATK=246 DEF=342 YK=14 BK=3 RK=1 G=1512 dmg=4508 door=21/5/1
- MT46 x11y2 fly
- MT46 x9y1 open blueDoor [BK 3->2]
- MT46 x6y1 shop atk [ATK 246->256, G 1512->392]
- after: HP=2837 ATK=256 DEF=342 YK=14 BK=2 RK=1 G=392 dmg=4508 door=21/6/1

### MT36

- before: HP=2837 ATK=256 DEF=342 YK=14 BK=2 RK=1 G=392 dmg=4508 door=21/6/1
- MT36 x11y10 fly
- MT36 x9y1 kill redKnight (auto: x9y1 redKnight, x7y1 zombieKnight, x3y1 soldier, x1y5 redKnight, x1y3 slimeMan)
- after: HP=2837 ATK=256 DEF=342 YK=14 BK=2 RK=1 G=627 dmg=4508 door=21/6/1

### MT41

- before: HP=2837 ATK=256 DEF=342 YK=14 BK=2 RK=1 G=627 dmg=4508 door=21/6/1
- MT41 x6y2 fly
- MT41 x5y4 kill whiteKing [HP 2837->2729, G 627->727] (+100G)
- MT41 x7y4 kill whiteKing [HP 2729->2621, G 727->827] (+100G)
- after: HP=2621 ATK=256 DEF=342 YK=14 BK=2 RK=1 G=827 dmg=4724 door=21/6/1

### MT42

- before: HP=2621 ATK=256 DEF=342 YK=14 BK=2 RK=1 G=827 dmg=4724 door=21/6/1
- MT42 x5y11 fly
- MT42 x9y8 kill whiteKing [HP 2621->2513, G 827->927] (+100G)
- MT42 x11y8 kill whiteKing [HP 2513->2405, G 927->1027] (+100G)
- MT42 x11y4 kill redWizard [HP 2405->2367, G 1027->1117] (+90G)
- MT42 x9y4 kill brownWizard [HP 2367->2339, G 1117->1197] (+80G)
- MT42 x11y6 kill brownWizard [HP 2339->2311, G 1197->1277] (+80G)
- after: HP=2311 ATK=256 DEF=342 YK=14 BK=2 RK=1 G=1277 dmg=5034 door=21/6/1

### MT43

- before: HP=2311 ATK=256 DEF=342 YK=14 BK=2 RK=1 G=1277 dmg=5034 door=21/6/1
- MT43 x1y2 fly
- MT43 x6y3 kill darkKnight [HP 2311->2047, G 1277->1397] (+120G)
- after: HP=2047 ATK=256 DEF=342 YK=14 BK=2 RK=1 G=1397 dmg=5298 door=21/6/1

### MT46

- before: HP=2047 ATK=256 DEF=342 YK=14 BK=2 RK=1 G=1397 dmg=5298 door=21/6/1
- MT46 x11y2 fly
- MT46 x6y1 shop atk [ATK 256->266, G 1397->57]
- after: HP=2047 ATK=266 DEF=342 YK=14 BK=2 RK=1 G=57 dmg=5298 door=21/6/1

### MT41

- before: HP=2047 ATK=266 DEF=342 YK=14 BK=2 RK=1 G=57 dmg=5298 door=21/6/1
- MT41 x6y10 fly
- MT41 x1y6 kill redBat [HP 2047->2999, G 57->107] (+50G)
- MT41 x11y6 kill redBat [HP 2999->3951, G 107->157] (+50G)
- MT41 x3y5 kill brownWizard [HP 3951->3923, G 157->237] (+80G)
- MT41 x2y7 kill redBat [HP 3923->3875, G 237->287] (+50G)
- MT41 x10y7 kill redBat [HP 3875->3827, G 287->337] (+50G)
- after: HP=3827 ATK=266 DEF=342 YK=14 BK=2 RK=1 G=337 dmg=5518 door=21/6/1

### MT43

- before: HP=3827 ATK=266 DEF=342 YK=14 BK=2 RK=1 G=337 dmg=5518 door=21/6/1
- MT43 x1y2 fly
- MT43 x7y4 kill darkKnight [HP 3827->3563, G 337->457] (+120G)
- MT43 x4y4 kill redWizard [HP 3563->3525, G 457->547] (+90G)
- MT43 x9y7 kill brownWizard [HP 3525->3497, G 547->627] (+80G)
- MT43 x2y9 kill redBat [HP 3497->3449, G 627->677] (+50G)
- MT43 x10y10 kill redBat [HP 3449->3401, G 677->727] (+50G)
- after: HP=3401 ATK=266 DEF=342 YK=14 BK=2 RK=1 G=727 dmg=5944 door=21/6/1

### MT45

- before: HP=3401 ATK=266 DEF=342 YK=14 BK=2 RK=1 G=727 dmg=5944 door=21/6/1
- MT45 x2y1 fly
- MT45 x3y6 kill darkKnight [HP 3401->3137, DEF 342->352, G 727->847] (+120G)
- MT45 x3y4 kill darkKnight [HP 3137->2903, ATK 266->276, G 847->967] (+120G)
- MT45 x7y3 kill redWizard [HP 2903->2875, G 967->1057] (+90G)
- MT45 x5y5 kill redWizard [HP 2875->2847, G 1057->1147] (+90G)
- MT45 x5y3 kill brownWizard [HP 2847->2829, G 1147->1227] (+80G)
- MT45 x7y5 kill brownWizard [HP 2829->2811, G 1227->1307] (+80G)
- MT45 x7y7 kill redBat [HP 2811->2773, YK 14->15, G 1307->1357] (+50G)
- MT45 x10y8 kill redWizard [HP 2773->2745, G 1357->1447] (+90G)
- after: HP=2745 ATK=276 DEF=352 YK=15 BK=2 RK=1 G=1447 dmg=6600 door=21/6/1

### MT46

- before: HP=2745 ATK=276 DEF=352 YK=15 BK=2 RK=1 G=1447 dmg=6600 door=21/6/1
- MT46 x11y2 fly
- MT46 x10y9 kill brownWizard [HP 2745->2727, G 1447->1527] (+80G)
- after: HP=2727 ATK=276 DEF=352 YK=15 BK=2 RK=1 G=1527 dmg=6618 door=21/6/1

### MT42

- before: HP=2727 ATK=276 DEF=352 YK=15 BK=2 RK=1 G=1527 dmg=6618 door=21/6/1
- MT42 x1y2 fly
- MT42 x3y2 kill slimelord [G 1527->1567] (auto: x3y2 slimelord) (+40G)
- after: HP=2727 ATK=276 DEF=352 YK=15 BK=2 RK=1 G=1567 dmg=6618 door=21/6/1

### MT46

- before: HP=2727 ATK=276 DEF=352 YK=15 BK=2 RK=1 G=1567 dmg=6618 door=21/6/1
- MT46 x11y2 fly
- MT46 x9y4 kill redBat [HP 2727->2689, G 1567->1617] (+50G)
- MT46 x6y1 shop def [DEF 352->372, G 1617->37]
- after: HP=2689 ATK=276 DEF=372 YK=15 BK=2 RK=1 G=37 dmg=6656 door=21/6/1

### MT48

- before: HP=2689 ATK=276 DEF=372 YK=15 BK=2 RK=1 G=37 dmg=6656 door=21/6/1
- MT48 x11y10 fly
- MT48 x11y11 pass downFloor
- after: HP=2689 ATK=276 DEF=372 YK=15 BK=2 RK=1 G=77 dmg=6656 door=21/6/1

### MT47

- before: HP=2689 ATK=276 DEF=372 YK=15 BK=2 RK=1 G=77 dmg=6656 door=21/6/1
- MT47 x1y10 event redWizard
- MT47 x1y11 event redWizard
- MT47 x1y11 kill redWizard [HP 2689->2681, G 77->167] (+90G)
- after: HP=2681 ATK=276 DEF=372 YK=15 BK=2 RK=1 G=167 dmg=6664 door=21/6/1

### MT48

- before: HP=2681 ATK=276 DEF=372 YK=15 BK=2 RK=1 G=167 dmg=6664 door=21/6/1
- MT48 x11y10 fly
- MT48 x3y5 kill slimelord (auto: x10y7 brownWizard, x3y5 slimelord)
- after: HP=2681 ATK=276 DEF=372 YK=15 BK=2 RK=1 G=287 dmg=6664 door=21/6/1

### MT37

- before: HP=2681 ATK=276 DEF=372 YK=15 BK=2 RK=1 G=287 dmg=6664 door=21/6/1
- MT37 x2y1 fly
- after: HP=5481 ATK=276 DEF=372 YK=15 BK=2 RK=1 G=287 dmg=6664 door=21/6/1

### MT42

- before: HP=5481 ATK=276 DEF=372 YK=15 BK=2 RK=1 G=287 dmg=6664 door=21/6/1
- MT42 x5y11 fly
- MT42 x4y5 open yellowDoor [YK 15->14]
- MT42 x3y5 kill slimelord [G 287->327] (auto: x3y5 slimelord) (+40G)
- MT42 x1y6 open yellowDoor [YK 14->13]
- MT42 x3y8 kill redBat [HP 5481->6463, YK 13->15, G 327->377] (+50G)
- MT42 x1y10 kill redBat [HP 6463->6445, DEF 372->377, YK 15->17, G 377->427] (+50G)
- after: HP=6445 ATK=276 DEF=377 YK=17 BK=2 RK=1 G=427 dmg=6700 door=23/6/1

### MT34

- before: HP=6445 ATK=276 DEF=377 YK=17 BK=2 RK=1 G=427 dmg=6700 door=23/6/1
- MT34 x6y10 fly
- MT34 x4y2 open yellowDoor [YK 17->16]
- MT34 x5y2 kill slimeMan [YK 16->17, G 427->522] (auto: x5y2 slimeMan, x6y1 yellowKey, x7y2 redKnight) (+95G)
- MT34 x8y2 open yellowDoor [YK 17->16]
- MT34 x9y1 move (auto: x9y1 yellowKey, x10y2 yellowKey, x10y1 yellowKey, x11y2 redPotion, x11y1 blueGem)
- MT34 x8y10 open yellowDoor [YK 19->18]
- MT34 x9y10 kill soldier [HP 6645->6845, ATK 276->280, YK 18->19, G 522->567] (auto: x9y10 soldier, x10y11 yellowKey, x11y10 redPotion, x11y11 redGem) (+45G)
- after: HP=6845 ATK=280 DEF=381 YK=19 BK=2 RK=1 G=567 dmg=6700 door=26/6/1

### MT47

- before: HP=6845 ATK=280 DEF=381 YK=19 BK=2 RK=1 G=567 dmg=6700 door=26/6/1
- MT47 x11y10 fly
- MT47 x5y11 kill brownWizard (auto: x8y9 slimelord, x5y11 brownWizard)
- MT47 x3y11 open yellowDoor [YK 19->18]
- MT47 x2y6 open yellowDoor [YK 18->17, G 687->777] (auto: x8y3 redWizard)
- MT47 x4y8 open blueDoor [BK 2->1]
- MT47 x5y4 kill redWizard (auto: x5y8 redGem, x5y7 blueKey, x6y8 blueGem, x6y7 yellowKey, x5y4 redWizard, x6y5 brownWizard)
- after: HP=6845 ATK=285 DEF=386 YK=18 BK=2 RK=1 G=947 dmg=6700 door=28/7/1

### MT48

- before: HP=6845 ATK=285 DEF=386 YK=18 BK=2 RK=1 G=947 dmg=6700 door=28/7/1
- MT48 x11y10 fly
- MT48 x4y6 open yellowDoor [YK 18->17]
- MT48 x4y7 kill brownWizard [HP 6845->7095, ATK 285->290, G 947->1157] (auto: x4y7 brownWizard, x3y8 redGem, x5y8 redPotion, x1y7 redBat, x1y9 brownWizard) (+210G)
- MT48 x4y9 open yellowDoor [YK 17->16]
- MT48 x4y10 kill darkKnight [HP 7095->8007, DEF 386->391, G 1157->1277] (+120G)
- after: HP=8007 ATK=290 DEF=391 YK=16 BK=2 RK=1 G=1277 dmg=6788 door=30/7/1

### MT47

- before: HP=8007 ATK=290 DEF=391 YK=16 BK=2 RK=1 G=1277 dmg=6788 door=30/7/1
- MT47 x2y1 fly
- MT47 x8y4 open yellowDoor [YK 16->15, G 1277->1327] (auto: x3y5 redBat)
- MT47 x9y5 kill brownWizard (auto: x8y6 yellowKey, x9y5 brownWizard, x11y6 redBat)
- after: HP=8007 ATK=290 DEF=391 YK=16 BK=2 RK=1 G=1457 dmg=6788 door=31/7/1

### MT46

- before: HP=8007 ATK=290 DEF=391 YK=16 BK=2 RK=1 G=1457 dmg=6788 door=31/7/1
- MT46 x11y10 fly
- MT46 x3y1 open yellowDoor [YK 16->15]
- MT46 x2y1 kill redWizard [HP 8007->8257, ATK 290->295, G 1457->1627] (auto: x2y1 redWizard, x1y2 redPotion, x1y3 redGem, x2y4 brownWizard) (+170G)
- after: HP=8257 ATK=295 DEF=391 YK=15 BK=2 RK=1 G=1627 dmg=6788 door=32/7/1

### MT36

- before: HP=8257 ATK=295 DEF=391 YK=15 BK=2 RK=1 G=1627 dmg=6788 door=32/7/1
- MT36 x11y10 fly
- MT36 x10y6 open yellowDoor [YK 15->14]
- MT36 x7y6 kill slimeMan (auto: x7y6 slimeMan, x6y5 ghostSkeleton, x5y6 slimeMan, x6y7 redKnight)
- after: HP=8257 ATK=295 DEF=391 YK=14 BK=2 RK=1 G=1787 dmg=6788 door=33/7/1

### MT40

- before: HP=8257 ATK=295 DEF=391 YK=14 BK=2 RK=1 G=1787 dmg=6788 door=33/7/1
- MT40 x10y11 fly
- MT40 x8y11 open yellowDoor [YK 14->13]
- MT40 x4y11 open blueDoor [BK 2->1, G 1787->1847] (auto: x7y9 slimeMan, x5y9 slimeMan)
- MT40 x3y11 kill redKnight [HP 8257->9057, ATK 295->299, DEF 391->395, YK 13->14, G 1847->1912] (auto: x3y11 redKnight, x1y11 redGem, x2y9 yellowKey, x1y10 bluePotion, x1y9 blueGem) (+65G)
- after: HP=9057 ATK=299 DEF=395 YK=14 BK=1 RK=1 G=1912 dmg=6788 door=34/8/1

### MT2

- before: HP=9057 ATK=299 DEF=395 YK=14 BK=1 RK=1 G=1912 dmg=6788 door=34/8/1
- MT2 x1y10 fly
- MT2 x11y7 trader specialTrader [ATK 299->308, DEF 395->407]
- after: HP=9057 ATK=308 DEF=407 YK=14 BK=1 RK=1 G=1912 dmg=6788 door=34/8/1

### MT16

- before: HP=9057 ATK=308 DEF=407 YK=14 BK=1 RK=1 G=1912 dmg=6788 door=34/8/1
- MT16 x6y2 fly
- MT16 x11y11 pass fakeWall2
- MT16 x11y11 老人 superPotion
- MT16 x10y11 使用 superPotion [HP 9057->14347]
- after: HP=14347 ATK=308 DEF=407 YK=14 BK=1 RK=1 G=1912 dmg=6788 door=34/8/1

### MT35

- before: HP=14347 ATK=308 DEF=407 YK=14 BK=1 RK=1 G=1912 dmg=6788 door=34/8/1
- MT35 x6y10 fly
- MT35 x6y7 kill magicDragon [HP 14347->9522, G 1912->2712] (+800G)
- MT35 x6y6 take snow [HP 9522->11922] (auto: x6y5 bluePotion, x5y5 bluePotion, x7y5 bluePotion)
- after: HP=11922 ATK=308 DEF=407 YK=14 BK=1 RK=1 G=2712 dmg=11613 door=34/8/1

### MT13

- before: HP=11922 ATK=308 DEF=407 YK=14 BK=1 RK=1 G=2712 dmg=11613 door=34/8/1
- MT13 x10y11 fly
- MT13 x6y10 open yellowDoor [YK 14->13]
- MT13 x6y10 move [ATK 308->408] (auto: resource group on move) (auto: x6y9 lava, x6y8 lava, x5y9 lava, x7y9 lava, x6y7 lava, x5y8 lava, x7y8 lava, x4y9 lava, x8y9 lava, x6y6 lava, x4y8 lava, x8y8 lava, x3y9 lava, x9y9 lava, x6y5 sword5, x4y7 lava, x3y8 lava, x8y7 lava, x9y8 lava, x2y9 lava, x10y9 lava, x3y7 lava, x2y8 lava, x9y7 lava, x10y8 lava, x1y9 lava, x11y9 lava, x3y6 lava, x2y7 lava, x1y8 lava, x9y6 lava, x10y7 lava, x11y8 lava, x3y5 lava, x2y6 lava, x1y7 lava, x9y5 lava, x10y6 lava, x11y7 lava, x3y4 lava, x2y5 lava, x1y6 lava, x9y4 lava, x10y5 lava, x11y6 lava, x3y3 lava, x2y4 lava, x1y5 lava, x9y3 lava, x10y4 lava, x11y5 lava, x3y2 lava, x2y3 lava, x4y3 lava, x1y4 lava, x9y2 lava, x8y3 lava, x10y3 lava, x11y4 lava, x3y1 lava, x2y2 lava, x4y2 lava, x1y3 lava, x9y1 lava, x8y2 lava, x10y2 lava, x11y3 lava, x2y1 lava, x4y1 lava, x1y2 lava, x5y2 lava, x8y1 lava, x10y1 lava, x7y2 lava, x11y2 lava, x1y1 lava, x5y1 lava, x6y2 lava, x7y1 lava, x11y1 lava, x6y1 lava)
- after: HP=11922 ATK=408 DEF=407 YK=13 BK=1 RK=1 G=2712 dmg=11613 door=35/8/1

### MT46

- before: HP=11922 ATK=408 DEF=407 YK=13 BK=1 RK=1 G=2712 dmg=11613 door=35/8/1
- MT46 x11y2 fly
- MT46 x6y1 shop hp [HP 11922->13322, G 2712->872]
- after: HP=13322 ATK=408 DEF=407 YK=13 BK=1 RK=1 G=872 dmg=11613 door=35/8/1

### MT25

- before: HP=13322 ATK=408 DEF=407 YK=13 BK=1 RK=1 G=872 dmg=11613 door=35/8/1
- MT25 x2y11 fly
- MT25 x6y10 open redDoor [RK 1->0]
- MT25 x6y6 kill blackMagician [HP 13322->6437, G 872->1872] (+1000G)
- after: HP=6437 ATK=408 DEF=407 YK=13 BK=1 RK=4 G=1872 dmg=18498 door=35/8/2

### MT26

- before: HP=6437 ATK=408 DEF=407 YK=13 BK=1 RK=4 G=1872 dmg=18498 door=35/8/2
- MT26 x2y11 fly
- MT26 x6y10 open redDoor [RK 4->3]
- MT26 x6y9 open redDoor [RK 3->2]
- MT26 x6y8 open redDoor [RK 2->1]
- MT26 x6y6 event princess
- after: HP=6437 ATK=408 DEF=407 YK=13 BK=1 RK=1 G=1872 dmg=18498 door=35/8/5

### MT45

- before: HP=6437 ATK=408 DEF=407 YK=13 BK=1 RK=1 G=1872 dmg=18498 door=35/8/5
- MT45 x2y1 fly
- MT45 x11y5 open yellowDoor [YK 13->12]
- MT45 x11y4 kill slimelord [G 1872->1912] (auto: x11y4 slimelord) (+40G)
- MT45 x9y3 trader hp2000 [HP 6437->8437, G 1912->912]
- after: HP=8437 ATK=408 DEF=407 YK=12 BK=1 RK=1 G=912 dmg=18498 door=36/8/5

### MT48

- before: HP=8437 ATK=408 DEF=407 YK=12 BK=1 RK=1 G=912 dmg=18498 door=36/8/5
- MT48 x11y10 fly
- MT48 x7y3 kill whiteKing (auto: x9y3 whiteKing, x9y5 whiteKing, x7y3 whiteKing, x7y5 whiteKing)
- after: HP=8437 ATK=408 DEF=407 YK=12 BK=1 RK=1 G=1312 dmg=18498 door=36/8/5

### MT31

- before: HP=8437 ATK=408 DEF=407 YK=12 BK=1 RK=1 G=1312 dmg=18498 door=36/8/5
- MT31 x6y10 fly
- after: HP=8437 ATK=408 DEF=407 YK=12 BK=1 RK=1 G=1312 dmg=18498 door=36/8/5

### MT24

- before: HP=8437 ATK=408 DEF=407 YK=12 BK=1 RK=1 G=1312 dmg=18498 door=36/8/5
- MT24 x2y11 fly
- MT24 x6y8 open redDoor [RK 1->0]
- after: HP=8437 ATK=408 DEF=407 YK=12 BK=1 RK=0 G=1312 dmg=18498 door=36/8/6

### MT50

- before: HP=8437 ATK=408 DEF=407 YK=12 BK=1 RK=0 G=1312 dmg=18498 door=36/8/6
- MT50 x6y5 event redKing
- after: HP=8437 ATK=408 DEF=407 YK=12 BK=1 RK=0 G=1312 dmg=18498 door=36/8/6

### MT49

- before: HP=8437 ATK=408 DEF=407 YK=12 BK=1 RK=0 G=1312 dmg=18498 door=36/8/6
- MT49 x5y6 下楼器 downFly
- MT49 x6y6 event redKing
- MT49 x6y4 kill whiteKing [G 1312->1412] (+100G)
- MT49 x5y3 kill whiteKing [G 1412->1512] (+100G)
- MT49 x7y3 kill whiteKing [G 1512->1612] (+100G)
- MT49 x6y2 kill whiteKing [G 1612->1712] (+100G)
- MT49 x5y2 kill whiteKing [G 1712->1812] (+100G)
- MT49 x7y2 kill whiteKing [G 1812->1912] (+100G)
- MT49 x5y4 kill whiteKing [G 1912->2012] (+100G)
- MT49 x7y4 kill whiteKing [G 2012->2112] (+100G)
- MT49 x6y3 kill redKing [G 2112->2612] (+500G)
- after: HP=11437 ATK=423 DEF=422 YK=12 BK=1 RK=1 G=2612 dmg=18498 door=36/8/6

### MT48

- before: HP=11437 ATK=423 DEF=422 YK=12 BK=1 RK=1 G=2612 dmg=18498 door=36/8/6
- MT48 x1y10 fly
- MT48 x1y11 pass upFloor
- after: HP=11437 ATK=423 DEF=422 YK=12 BK=1 RK=1 G=2612 dmg=18498 door=36/8/6

### MT49

- before: HP=11437 ATK=423 DEF=422 YK=12 BK=1 RK=1 G=2612 dmg=18498 door=36/8/6
- MT49 x3y11 open redDoor [RK 1->0]
- MT49 x5y10 kill redWizard [G 2612->2702] (+90G)
- after: HP=11437 ATK=423 DEF=422 YK=12 BK=1 RK=0 G=2702 dmg=18498 door=36/8/7

### MT43

- before: HP=11437 ATK=423 DEF=422 YK=12 BK=1 RK=0 G=2702 dmg=18498 door=36/8/7
- MT43 x1y10 fly
- MT43 x8y10 open yellowDoor [YK 12->11]
- MT43 x6y9 kill darkKnight (auto: x6y9 darkKnight, x4y9 bluePotion, x4y10 bluePotion, x4y11 bluePotion)
- after: HP=14437 ATK=423 DEF=422 YK=11 BK=1 RK=0 G=2822 dmg=18498 door=37/8/7

### MT45

- before: HP=14437 ATK=423 DEF=422 YK=11 BK=1 RK=0 G=2822 dmg=18498 door=37/8/7
- MT45 x2y1 fly
- MT45 x11y9 open yellowDoor [YK 11->10]
- MT45 x11y11 move (auto: x11y11 bluePotion)
- after: HP=15437 ATK=423 DEF=422 YK=10 BK=1 RK=0 G=2822 dmg=18498 door=38/8/7

### MT48

- before: HP=15437 ATK=423 DEF=422 YK=10 BK=1 RK=0 G=2822 dmg=18498 door=38/8/7
- MT48 x11y10 fly
- MT48 x2y4 open blueDoor [BK 1->0]
- MT48 x2y3 kill redWizard [HP 15437->16437, G 2822->2912] (auto: x2y3 redWizard, x2y1 bluePotion) (+90G)
- after: HP=16437 ATK=423 DEF=422 YK=10 BK=0 RK=0 G=2912 dmg=18498 door=38/9/7

### MT46

- before: HP=16437 ATK=423 DEF=422 YK=10 BK=0 RK=0 G=2912 dmg=18498 door=38/9/7
- MT46 x11y10 fly
- MT46 x9y6 open yellowDoor [YK 10->9]
- MT46 x7y6 move (auto: x7y6 redPotion, x8y7 redWizard)
- after: HP=16687 ATK=423 DEF=422 YK=9 BK=0 RK=0 G=3002 dmg=18498 door=39/9/7

### MT38

- before: HP=16687 ATK=423 DEF=422 YK=9 BK=0 RK=0 G=3002 dmg=18498 door=39/9/7
- MT38 x10y1 fly
- MT38 x7y3 open yellowDoor [YK 9->8]
- MT38 x7y6 kill ghostSkeleton (auto: x7y6 ghostSkeleton, x7y7 swordsman, x6y8 redPotion, x5y8 blueGem)
- after: HP=16887 ATK=423 DEF=426 YK=8 BK=0 RK=0 G=3092 dmg=18498 door=40/9/7

### MT31

- before: HP=16887 ATK=423 DEF=426 YK=8 BK=0 RK=0 G=3092 dmg=18498 door=40/9/7
- MT31 x6y10 fly
- MT31 x1y7 open yellowDoor [YK 8->7]
- MT31 x2y9 kill ghostSkeleton (auto: x1y9 ghostSkeleton, x2y9 ghostSkeleton, x2y11 redPotion, x4y10 redKnight)
- after: HP=17087 ATK=423 DEF=426 YK=7 BK=0 RK=0 G=3227 dmg=18498 door=41/9/7

### MT33

- before: HP=17087 ATK=423 DEF=426 YK=7 BK=0 RK=0 G=3227 dmg=18498 door=41/9/7
- MT33 x10y1 fly
- MT33 x5y4 open yellowDoor [YK 7->6]
- MT33 x4y6 kill swordsman (auto: x6y5 zombieKnight, x4y6 swordsman, x6y7 ghostSkeleton)
- MT33 x3y7 open yellowDoor [YK 6->5]
- MT33 x2y7 kill slimeMan [HP 17087->17287, G 3347->3407] (auto: x2y7 slimeMan, x2y4 redPotion, x1y5 slimeMan) (+60G)
- after: HP=17287 ATK=423 DEF=426 YK=5 BK=0 RK=0 G=3407 dmg=18498 door=43/9/7

### MT3

- before: HP=17287 ATK=423 DEF=426 YK=5 BK=0 RK=0 G=3407 dmg=18498 door=43/9/7
- MT3 x10y11 fly
- MT3 x9y2 open yellowDoor [YK 5->4]
- MT3 x10y2 kill bat [HP 17287->17337, G 3407->3410] (auto: x10y2 bat, x11y1 redPotion) (+3G)
- after: HP=17337 ATK=423 DEF=426 YK=4 BK=0 RK=0 G=3410 dmg=18498 door=44/9/7

### MT8

- before: HP=17337 ATK=423 DEF=426 YK=4 BK=0 RK=0 G=3410 dmg=18498 door=44/9/7
- MT8 x1y2 fly
- MT8 x1y3 open yellowDoor [YK 4->3]
- MT8 x1y5 move (auto: x1y5 redPotion, x2y6 redSlime, x3y6 greenSlime, x4y6 redSlime)
- after: HP=17387 ATK=423 DEF=426 YK=3 BK=0 RK=0 G=3415 dmg=18498 door=45/9/7

### MT32

- before: HP=17387 ATK=423 DEF=426 YK=3 BK=0 RK=0 G=3415 dmg=18498 door=45/9/7
- MT32 x6y11 fly
- MT32 x9y8 open yellowDoor [YK 3->2]
- MT32 x10y7 move (auto: x10y7 yellowKey, x11y8 yellowKey, x11y7 blueKey)
- after: HP=17387 ATK=423 DEF=426 YK=4 BK=1 RK=0 G=3415 dmg=18498 door=46/9/7

### MT31

- before: HP=17387 ATK=423 DEF=426 YK=4 BK=1 RK=0 G=3415 dmg=18498 door=46/9/7
- MT31 x6y10 fly
- MT31 x3y4 open yellowDoor [YK 4->3]
- MT31 x4y4 move (auto: x4y4 blueKey)
- after: HP=17387 ATK=423 DEF=426 YK=3 BK=2 RK=0 G=3415 dmg=18498 door=47/9/7

### MT48

- before: HP=17387 ATK=423 DEF=426 YK=3 BK=2 RK=0 G=3415 dmg=18498 door=47/9/7
- MT48 x11y10 fly
- MT48 x11y2 open blueDoor [BK 2->1]
- after: HP=18137 ATK=423 DEF=426 YK=3 BK=1 RK=0 G=3415 dmg=18498 door=47/10/7

### MT46

- before: HP=18137 ATK=423 DEF=426 YK=3 BK=1 RK=0 G=3415 dmg=18498 door=47/10/7
- MT46 x11y10 fly
- MT46 x6y1 shop hp [HP 18137->19637, G 3415->1295]
- after: HP=19637 ATK=423 DEF=426 YK=3 BK=1 RK=0 G=1295 dmg=18498 door=47/10/7

### MT20

- before: HP=19637 ATK=423 DEF=426 YK=3 BK=1 RK=0 G=1295 dmg=18498 door=47/10/7
- MT20 x6y2 fly
- MT20 x11y9 open yellowDoor [YK 3->2]
- MT20 x10y8 kill bat (auto: x11y7 bat, x10y8 bat)
- MT20 x10y6 open blueDoor [BK 1->0]
- MT20 x10y4 move (auto: x10y4 redPotion, x11y5 yellowKey, x11y4 bluePotion)
- after: HP=20137 ATK=423 DEF=426 YK=3 BK=0 RK=0 G=1301 dmg=18498 door=48/11/7

### MT24

- before: HP=20137 ATK=423 DEF=426 YK=3 BK=0 RK=0 G=1301 dmg=18498 door=48/11/7
- MT24 x2y11 fly
- after: HP=20137 ATK=423 DEF=426 YK=3 BK=0 RK=0 G=1301 dmg=18498 door=48/11/7

### MT50

- before: HP=20137 ATK=423 DEF=426 YK=3 BK=0 RK=0 G=1301 dmg=18498 door=48/11/7
- MT50 x6y5 kill redKing [G 1301->1801] (+500G)
- after: HP=20137 ATK=423 DEF=426 YK=3 BK=0 RK=0 G=1801 dmg=18498 door=48/11/7
