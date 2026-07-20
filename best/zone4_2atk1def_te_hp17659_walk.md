# 当前最优 Walk (zone4, auto ON)

## 说明

- 本 walk 由 Game 类 (`scripts/search/zone4_game_route.py`, auto_sweep, strict_live_model) 离线推导生成。
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone4_game_route.json --load-slot <100+> --target-click-only`（统一点击 verifier，1-4 区通用；3 区起按需 `--set-auto battle=true,item=nopotion,wall=true`）
- 源 JSON：`best/zone4_2atk1def_te_hp17659_walk.json`

## 摘要

- final: HP=17659 ATK=429 DEF=441 YK=1 BK=0 RK=0 G=520 dmg=17886 door=50/9/7 MT50 x6y5

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
- after: HP=1067 ATK=237 DEF=287 YK=14 BK=3 RK=0 G=474 dmg=3828 door=14/2/1

### MT43

- before: HP=1067 ATK=237 DEF=287 YK=14 BK=3 RK=0 G=474 dmg=3828 door=14/2/1
- MT43 x1y10 fly
- MT43 x3y6 open yellowDoor [YK 14->13]
- MT43 x5y7 kill slimelord [HP 1067->1044, G 474->514] (+40G)
- MT43 x8y6 open yellowDoor [YK 13->12]
- MT43 x11y5 open yellowDoor (auto: x10y8 yellowKey)
- MT43 x9y1 kill whiteKing [HP 1044->881, G 514->614] (+100G)
- MT43 x11y7 take redPotion [HP 881->1131]
- MT43 x11y9 open yellowDoor [YK 12->11]
- after: HP=1131 ATK=237 DEF=337 YK=11 BK=4 RK=0 G=614 dmg=4014 door=18/2/1

### MT46

- before: HP=1131 ATK=237 DEF=337 YK=11 BK=4 RK=0 G=614 dmg=4014 door=18/2/1
- MT46 x11y2 fly
- MT46 x9y11 open yellowDoor [YK 11->10]
- MT46 x6y11 open blueDoor [BK 4->3]
- MT46 x4y11 kill redSlime (auto: x4y11 redSlime, x2y11 skeleton, x1y10 bigBat, x1y8 zombie, x1y6 soldier, x3y6 swordsman, x5y6 redKnight, x5y8 slimelord)
- MT46 x4y9 kill brownWizard [HP 1131->1098, G 857->937] (+80G)
- after: HP=1098 ATK=237 DEF=337 YK=10 BK=3 RK=0 G=937 dmg=4047 door=19/3/1

### MT41

- before: HP=1098 ATK=237 DEF=337 YK=10 BK=3 RK=0 G=937 dmg=4047 door=19/3/1
- MT41 x6y10 fly
- MT41 x6y10 魔法钥匙 bigKey
- MT41 x5y6 open blueDoor [BK 3->2]
- MT41 x2y2 kill redWizard [HP 1098->1055, ATK 237->242, YK 10->13, G 937->1067] (+130G)
- MT41 x7y6 open blueDoor [BK 3->2]
- MT41 x9y5 kill brownWizard [HP 1055->1027, DEF 337->342, YK 13->16, BK 2->3, G 1067->1187] (+120G)
- MT41 x10y2 event redWizard
- MT41 x10y2 kill redWizard [HP 1027->989, G 1187->1277] (+90G)
- after: HP=989 ATK=242 DEF=342 YK=16 BK=3 RK=0 G=1277 dmg=4156 door=19/5/1

### MT40

- before: HP=989 ATK=242 DEF=342 YK=16 BK=3 RK=0 G=1277 dmg=4156 door=19/5/1
- MT40 x6y2 fly
- after: HP=989 ATK=242 DEF=342 YK=16 BK=3 RK=0 G=1277 dmg=4156 door=19/5/1

### MT41

- before: HP=989 ATK=242 DEF=342 YK=16 BK=3 RK=0 G=1277 dmg=4156 door=19/5/1
- MT41 x6y2 fly
- after: HP=989 ATK=242 DEF=342 YK=16 BK=3 RK=0 G=1277 dmg=4156 door=19/5/1

### MT42

- before: HP=989 ATK=242 DEF=342 YK=16 BK=3 RK=0 G=1277 dmg=4156 door=19/5/1
- MT42 x5y11 fly
- MT42 x6y4 kill darkKnight [HP 989->549, RK 0->1, G 1277->1397] (+120G)
- after: HP=549 ATK=242 DEF=342 YK=16 BK=3 RK=1 G=1397 dmg=4596 door=19/5/1

### MT46

- before: HP=549 ATK=242 DEF=342 YK=16 BK=3 RK=1 G=1397 dmg=4596 door=19/5/1
- MT46 x11y2 fly
- MT46 x9y1 open blueDoor [BK 3->2]
- MT46 x6y1 shop atk [ATK 242->252, G 1397->277]
- after: HP=549 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=277 dmg=4596 door=19/6/1

### MT48

- before: HP=549 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=277 dmg=4596 door=19/6/1
- MT48 x11y10 fly
- MT48 x11y11 pass downFloor
- after: HP=549 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=317 dmg=4596 door=19/6/1

### MT47

- before: HP=549 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=317 dmg=4596 door=19/6/1
- MT47 x1y10 event redWizard
- MT47 x1y11 event redWizard
- MT47 x1y11 kill redWizard [HP 549->511, G 317->407] (+90G)
- after: HP=511 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=407 dmg=4634 door=19/6/1

### MT36

- before: HP=511 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=407 dmg=4634 door=19/6/1
- MT36 x11y10 fly
- MT36 x9y1 kill redKnight (auto: x9y1 redKnight, x7y1 zombieKnight, x3y1 soldier, x1y5 redKnight, x1y3 slimeMan)
- after: HP=511 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=642 dmg=4634 door=19/6/1

### MT47

- before: HP=511 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=642 dmg=4634 door=19/6/1
- MT47 x11y10 fly
- MT47 x8y9 kill slimelord (auto: x8y9 slimelord)
- after: HP=511 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=682 dmg=4634 door=19/6/1

### MT48

- before: HP=511 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=682 dmg=4634 door=19/6/1
- MT48 x11y10 fly
- MT48 x3y5 kill slimelord (auto: x3y5 slimelord)
- after: HP=511 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=722 dmg=4634 door=19/6/1

### MT42

- before: HP=511 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=722 dmg=4634 door=19/6/1
- MT42 x1y2 fly
- MT42 x3y2 kill slimelord [G 722->762] (auto: x3y2 slimelord) (+40G)
- after: HP=511 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=762 dmg=4634 door=19/6/1

### MT41

- before: HP=511 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=762 dmg=4634 door=19/6/1
- MT41 x6y10 fly
- MT41 x3y5 kill brownWizard [HP 511->483, G 762->842] (+80G)
- MT41 x1y6 kill redBat [HP 483->435, G 842->892] (+50G)
- MT41 x11y6 kill redBat [HP 435->387, G 892->942] (+50G)
- MT41 x2y7 kill redBat [HP 387->339, G 942->992] (+50G)
- MT41 x10y7 kill redBat [HP 339->291, G 992->1042] (+50G)
- after: HP=291 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=1042 dmg=4854 door=19/6/1

### MT42

- before: HP=291 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=1042 dmg=4854 door=19/6/1
- MT42 x5y11 fly
- MT42 x9y8 kill whiteKing [HP 291->183, G 1042->1142] (+100G)
- MT42 x11y8 kill whiteKing [HP 183->75, G 1142->1242] (+100G)
- MT42 x11y4 kill redWizard [HP 75->37, G 1242->1332] (+90G)
- MT42 x9y4 kill brownWizard [HP 37->9, G 1332->1412] (+80G)
- after: HP=9 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=1412 dmg=5136 door=19/6/1

### MT46

- before: HP=9 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=1412 dmg=5136 door=19/6/1
- MT46 x11y2 fly
- MT46 x6y1 shop atk [ATK 252->262, G 1412->72]
- after: HP=9 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=72 dmg=5136 door=19/6/1

### MT37

- before: HP=9 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=72 dmg=5136 door=19/6/1
- MT37 x2y1 fly
- MT37 x7y3 take redPotion [HP 9->209]
- after: HP=209 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=72 dmg=5136 door=19/6/1

### MT43

- before: HP=209 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=72 dmg=5136 door=19/6/1
- MT43 x1y2 fly
- MT43 x6y6 take bluePotion [HP 209->1209]
- after: HP=1209 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=72 dmg=5136 door=19/6/1

### MT41

- before: HP=1209 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=72 dmg=5136 door=19/6/1
- MT41 x6y10 fly
- MT41 x1y11 take bluePotion [HP 1209->2209]
- MT41 x11y11 take bluePotion [HP 2209->3209]
- MT41 x1y1 take redPotion [HP 3209->3459]
- MT41 x11y1 take redPotion [HP 3459->3709]
- MT41 x3y9 take redPotion [HP 3709->3959]
- MT41 x9y9 take redPotion [HP 3959->4209]
- after: HP=4209 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=72 dmg=5136 door=19/6/1

### MT37

- before: HP=4209 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=72 dmg=5136 door=19/6/1
- MT37 x2y1 fly
- MT37 x7y4 take redPotion [HP 4209->4409]
- MT37 x7y9 take bluePotion [HP 4409->5209]
- MT37 x5y7 take bluePotion [HP 5209->6009]
- MT37 x8y4 take redPotion [HP 6009->6209]
- MT37 x8y3 take redPotion [HP 6209->6409]
- MT37 x3y4 take redPotion [HP 6409->6609]
- MT37 x9y4 take redPotion [HP 6609->6809]
- after: HP=6809 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=72 dmg=5136 door=19/6/1

### MT46

- before: HP=6809 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=72 dmg=5136 door=19/6/1
- MT46 x11y2 fly
- MT46 x3y1 open yellowDoor [YK 16->15]
- MT46 x2y1 kill redWizard [HP 6809->6771, ATK 262->267, G 72->162] (+90G)
- MT46 x2y4 kill brownWizard [HP 6771->6743, G 162->242] (+80G)
- after: HP=6743 ATK=267 DEF=342 YK=15 BK=2 RK=1 G=242 dmg=5202 door=20/6/1

### MT36

- before: HP=6743 ATK=267 DEF=342 YK=15 BK=2 RK=1 G=242 dmg=5202 door=20/6/1
- MT36 x11y10 fly
- MT36 x10y6 open yellowDoor [YK 15->14]
- MT36 x7y6 kill slimeMan (auto: x7y6 slimeMan, x6y5 ghostSkeleton, x5y6 slimeMan, x6y7 redKnight)
- after: HP=6743 ATK=267 DEF=342 YK=14 BK=2 RK=1 G=402 dmg=5202 door=21/6/1

### MT42

- before: HP=6743 ATK=267 DEF=342 YK=14 BK=2 RK=1 G=402 dmg=5202 door=21/6/1
- MT42 x5y11 fly
- MT42 x4y5 open yellowDoor [YK 14->13]
- MT42 x3y5 kill slimelord [G 402->442] (auto: x3y5 slimelord) (+40G)
- MT42 x1y6 open yellowDoor [YK 13->12]
- MT42 x3y8 kill redBat [HP 6743->6695, YK 12->14, G 442->492] (+50G)
- MT42 x1y9 take bluePotion [HP 6695->7695]
- MT42 x1y10 kill redBat [HP 7695->7647, DEF 342->347, YK 14->16, G 492->542] (+50G)
- after: HP=7647 ATK=267 DEF=347 YK=16 BK=2 RK=1 G=542 dmg=5298 door=23/6/1

### MT48

- before: HP=7647 ATK=267 DEF=347 YK=16 BK=2 RK=1 G=542 dmg=5298 door=23/6/1
- MT48 x11y10 fly
- MT48 x4y6 open yellowDoor [YK 16->15]
- MT48 x4y7 kill brownWizard [HP 7647->7624, ATK 267->272, G 542->622] (+80G)
- MT48 x4y9 open yellowDoor [YK 15->14]
- MT48 x4y10 kill darkKnight [HP 7624->7458, DEF 347->352, G 622->742] (+120G)
- after: HP=7458 ATK=272 DEF=352 YK=14 BK=2 RK=1 G=742 dmg=5487 door=25/6/1

### MT45

- before: HP=7458 ATK=272 DEF=352 YK=14 BK=2 RK=1 G=742 dmg=5487 door=25/6/1
- MT45 x10y1 fly
- MT45 x7y7 kill redBat [HP 7458->7420, YK 14->15, G 742->792] (+50G)
- MT45 x10y8 kill redWizard [HP 7420->7392, G 792->882] (+90G)
- after: HP=7392 ATK=272 DEF=352 YK=15 BK=2 RK=1 G=882 dmg=5553 door=25/6/1

### MT47

- before: HP=7392 ATK=272 DEF=352 YK=15 BK=2 RK=1 G=882 dmg=5553 door=25/6/1
- MT47 x11y10 fly
- MT47 x11y7 open yellowDoor [YK 15->14]
- MT47 x11y6 kill redBat [HP 7392->7354, YK 14->15, G 882->932] (+50G)
- MT47 x9y5 kill brownWizard [HP 7354->7336, G 932->1012] (+80G)
- after: HP=7336 ATK=272 DEF=352 YK=15 BK=2 RK=1 G=1012 dmg=5609 door=26/6/1

### MT48

- before: HP=7336 ATK=272 DEF=352 YK=15 BK=2 RK=1 G=1012 dmg=5609 door=26/6/1
- MT48 x11y10 fly
- MT48 x1y7 kill redBat [HP 7336->7298, G 1012->1062] (+50G)
- MT48 x1y9 kill brownWizard [HP 7298->7280, G 1062->1142] (+80G)
- after: HP=7280 ATK=272 DEF=352 YK=15 BK=2 RK=1 G=1142 dmg=5665 door=26/6/1

### MT31

- before: HP=7280 ATK=272 DEF=352 YK=15 BK=2 RK=1 G=1142 dmg=5665 door=26/6/1
- MT31 x6y10 fly
- MT31 x1y7 open yellowDoor [YK 15->14]
- MT31 x1y9 kill ghostSkeleton (auto: x1y9 ghostSkeleton, x2y9 ghostSkeleton, x4y10 redKnight)
- after: HP=7280 ATK=272 DEF=352 YK=14 BK=2 RK=1 G=1277 dmg=5665 door=27/6/1

### MT40

- before: HP=7280 ATK=272 DEF=352 YK=14 BK=2 RK=1 G=1277 dmg=5665 door=27/6/1
- MT40 x10y11 fly
- MT40 x8y11 open yellowDoor [YK 14->13]
- MT40 x4y11 open blueDoor [BK 2->1, G 1277->1337] (auto: x7y9 slimeMan, x5y9 slimeMan)
- MT40 x3y11 kill redKnight [ATK 272->276, DEF 352->356, YK 13->14, G 1337->1402] (auto: x3y11 redKnight, x1y11 redGem, x2y9 yellowKey, x1y9 blueGem) (+65G)
- after: HP=7280 ATK=276 DEF=356 YK=14 BK=1 RK=1 G=1402 dmg=5665 door=28/7/1

### MT45

- before: HP=7280 ATK=276 DEF=356 YK=14 BK=1 RK=1 G=1402 dmg=5665 door=28/7/1
- MT45 x2y1 fly
- MT45 x1y6 open blueDoor [BK 1->0]
- MT45 x3y4 kill darkKnight [HP 7280->7152, ATK 276->286, DEF 356->366, G 1402->1522] (+120G)
- after: HP=7152 ATK=286 DEF=366 YK=14 BK=0 RK=1 G=1522 dmg=5793 door=28/8/1

### MT33

- before: HP=7152 ATK=286 DEF=366 YK=14 BK=0 RK=1 G=1522 dmg=5793 door=28/8/1
- MT33 x2y1 fly
- MT33 x5y4 open yellowDoor [YK 14->13]
- MT33 x4y6 kill swordsman (auto: x6y5 zombieKnight, x4y6 swordsman, x6y7 ghostSkeleton)
- MT33 x3y7 open yellowDoor [YK 13->12]
- MT33 x2y7 kill slimeMan [G 1642->1702] (auto: x2y7 slimeMan, x1y5 slimeMan) (+60G)
- MT33 x1y8 open yellowDoor [YK 12->11]
- MT33 x3y9 kill zombieKnight (auto: x1y10 swordsman, x1y11 yellowKey, x3y9 zombieKnight, x2y11 soldier)
- after: HP=7152 ATK=286 DEF=366 YK=12 BK=0 RK=1 G=1832 dmg=5793 door=31/8/1

### MT46

- before: HP=7152 ATK=286 DEF=366 YK=12 BK=0 RK=1 G=1832 dmg=5793 door=31/8/1
- MT46 x11y2 fly
- MT46 x6y1 shop atk [ATK 286->296, G 1832->252]
- after: HP=7152 ATK=296 DEF=366 YK=12 BK=0 RK=1 G=252 dmg=5793 door=31/8/1

### MT2

- before: HP=7152 ATK=296 DEF=366 YK=12 BK=0 RK=1 G=252 dmg=5793 door=31/8/1
- MT2 x1y10 fly
- MT2 x11y7 trader specialTrader [ATK 296->305, DEF 366->377]
- after: HP=7152 ATK=305 DEF=377 YK=12 BK=0 RK=1 G=252 dmg=5793 door=31/8/1

### MT16

- before: HP=7152 ATK=305 DEF=377 YK=12 BK=0 RK=1 G=252 dmg=5793 door=31/8/1
- MT16 x6y2 fly
- MT16 x11y11 pass fakeWall2
- MT16 x11y11 老人 superPotion
- MT16 x10y11 使用 superPotion [HP 7152->12202]
- after: HP=12202 ATK=305 DEF=377 YK=12 BK=0 RK=1 G=252 dmg=5793 door=31/8/1

### MT35

- before: HP=12202 ATK=305 DEF=377 YK=12 BK=0 RK=1 G=252 dmg=5793 door=31/8/1
- MT35 x6y10 fly
- MT35 x6y7 kill magicDragon [HP 12202->6181, G 252->1052] (+800G)
- MT35 x6y6 take snow
- MT35 x5y5 take bluePotion [HP 6181->6981]
- MT35 x6y5 take bluePotion [HP 6981->7781]
- MT35 x7y5 take bluePotion [HP 7781->8581]
- after: HP=8581 ATK=305 DEF=377 YK=12 BK=0 RK=1 G=1052 dmg=11814 door=31/8/1

### MT13

- before: HP=8581 ATK=305 DEF=377 YK=12 BK=0 RK=1 G=1052 dmg=11814 door=31/8/1
- MT13 x10y11 fly
- MT13 x6y10 open yellowDoor [YK 12->11]
- MT13 x6y10 move [ATK 305->405] (auto: resource group on move) (auto: x6y9 lava, x6y8 lava, x5y9 lava, x7y9 lava, x6y7 lava, x5y8 lava, x7y8 lava, x4y9 lava, x8y9 lava, x6y6 lava, x4y8 lava, x8y8 lava, x3y9 lava, x9y9 lava, x6y5 sword5, x4y7 lava, x3y8 lava, x8y7 lava, x9y8 lava, x2y9 lava, x10y9 lava, x3y7 lava, x2y8 lava, x9y7 lava, x10y8 lava, x1y9 lava, x11y9 lava, x3y6 lava, x2y7 lava, x1y8 lava, x9y6 lava, x10y7 lava, x11y8 lava, x3y5 lava, x2y6 lava, x1y7 lava, x9y5 lava, x10y6 lava, x11y7 lava, x3y4 lava, x2y5 lava, x1y6 lava, x9y4 lava, x10y5 lava, x11y6 lava, x3y3 lava, x2y4 lava, x1y5 lava, x9y3 lava, x10y4 lava, x11y5 lava, x3y2 lava, x2y3 lava, x4y3 lava, x1y4 lava, x9y2 lava, x8y3 lava, x10y3 lava, x11y4 lava, x3y1 lava, x2y2 lava, x4y2 lava, x1y3 lava, x9y1 lava, x8y2 lava, x10y2 lava, x11y3 lava, x2y1 lava, x4y1 lava, x1y2 lava, x5y2 lava, x8y1 lava, x10y1 lava, x7y2 lava, x11y2 lava, x1y1 lava, x5y1 lava, x6y2 lava, x7y1 lava, x11y1 lava, x6y1 lava)
- after: HP=8581 ATK=405 DEF=377 YK=11 BK=0 RK=1 G=1052 dmg=11814 door=32/8/1

### MT43

- before: HP=8581 ATK=405 DEF=377 YK=11 BK=0 RK=1 G=1052 dmg=11814 door=32/8/1
- MT43 x1y2 fly
- MT43 x10y10 kill redBat (auto: x4y4 redWizard, x2y9 redBat, x6y3 darkKnight, x7y4 darkKnight, x9y7 brownWizard, x10y10 redBat)
- MT43 x8y10 open yellowDoor [YK 11->10]
- MT43 x6y9 kill darkKnight (auto: x6y9 darkKnight)
- after: HP=8581 ATK=405 DEF=377 YK=10 BK=0 RK=1 G=1682 dmg=11814 door=33/8/1

### MT45

- before: HP=8581 ATK=405 DEF=377 YK=10 BK=0 RK=1 G=1682 dmg=11814 door=33/8/1
- MT45 x2y1 fly
- MT45 x11y9 open yellowDoor [YK 10->9, G 1682->2142] (auto: x5y3 brownWizard, x7y3 redWizard, x5y5 redWizard, x7y5 brownWizard, x3y6 darkKnight)
- MT45 x9y10 open yellowDoor [YK 9->8]
- MT45 x8y9 kill whiteKing [G 2142->2242] (+100G)
- after: HP=8581 ATK=405 DEF=377 YK=8 BK=0 RK=1 G=2242 dmg=11814 door=35/8/1

### MT46

- before: HP=8581 ATK=405 DEF=377 YK=8 BK=0 RK=1 G=2242 dmg=11814 door=35/8/1
- MT46 x11y2 fly
- MT46 x6y1 shop def [DEF 377->397, G 2372->532]
- after: HP=8581 ATK=405 DEF=397 YK=8 BK=0 RK=1 G=532 dmg=11814 door=35/8/1

### MT48

- before: HP=8581 ATK=405 DEF=397 YK=8 BK=0 RK=1 G=532 dmg=11814 door=35/8/1
- MT48 x11y10 fly
- MT48 x7y3 kill whiteKing (auto: x10y7 brownWizard, x9y3 whiteKing, x9y5 whiteKing, x7y3 whiteKing, x7y5 whiteKing)
- after: HP=8581 ATK=405 DEF=397 YK=8 BK=0 RK=1 G=1012 dmg=11814 door=35/8/1

### MT47

- before: HP=8581 ATK=405 DEF=397 YK=8 BK=0 RK=1 G=1012 dmg=11814 door=35/8/1
- MT47 x2y1 fly
- MT47 x2y6 open yellowDoor [YK 8->7, G 1012->1102] (auto: x8y3 redWizard)
- MT47 x3y5 kill redBat (auto: x3y5 redBat)
- MT47 x4y4 open yellowDoor [YK 7->6]
- MT47 x5y4 kill redWizard [ATK 405->410, DEF 397->402, YK 6->7, BK 0->1, G 1152->1322] (auto: x5y4 redWizard, x6y5 brownWizard, x5y7 blueKey, x5y8 redGem, x6y7 yellowKey, x6y8 blueGem) (+170G)
- after: HP=8581 ATK=410 DEF=402 YK=7 BK=1 RK=1 G=1322 dmg=11814 door=37/8/1

### MT32

- before: HP=8581 ATK=410 DEF=402 YK=7 BK=1 RK=1 G=1322 dmg=11814 door=37/8/1
- MT32 x10y1 fly
- MT32 x5y3 open yellowDoor [YK 7->6]
- MT32 x3y4 kill slimeMan (auto: x3y4 slimeMan, x4y5 slimeMan, x1y4 soldier, x2y5 yellowKey)
- after: HP=8581 ATK=410 DEF=402 YK=7 BK=1 RK=1 G=1427 dmg=11814 door=38/8/1

### MT41

- before: HP=8581 ATK=410 DEF=402 YK=7 BK=1 RK=1 G=1427 dmg=11814 door=38/8/1
- MT41 x6y2 fly
- MT41 x5y4 kill whiteKing (auto: x5y4 whiteKing, x7y4 whiteKing)
- after: HP=8581 ATK=410 DEF=402 YK=7 BK=1 RK=1 G=1627 dmg=11814 door=38/8/1

### MT45

- before: HP=8581 ATK=410 DEF=402 YK=7 BK=1 RK=1 G=1627 dmg=11814 door=38/8/1
- MT45 x2y1 fly
- MT45 x8y11 kill whiteKing [G 1627->1727] (+100G)
- MT45 x5y9 kill darkKnight [G 1727->1847] (+120G)
- MT45 x5y11 kill darkKnight [G 1847->1967] (+120G)
- after: HP=8581 ATK=410 DEF=402 YK=7 BK=1 RK=1 G=1967 dmg=11814 door=38/8/1

### MT31

- before: HP=8581 ATK=410 DEF=402 YK=7 BK=1 RK=1 G=1967 dmg=11814 door=38/8/1
- MT31 x6y10 fly
- MT31 x11y5 open yellowDoor [YK 7->6]
- MT31 x10y3 kill ghostSkeleton (auto: x11y3 ghostSkeleton, x10y3 ghostSkeleton, x8y2 soldier)
- after: HP=8581 ATK=410 DEF=402 YK=6 BK=1 RK=1 G=2082 dmg=11814 door=39/8/1

### MT34

- before: HP=8581 ATK=410 DEF=402 YK=6 BK=1 RK=1 G=2082 dmg=11814 door=39/8/1
- MT34 x2y1 fly
- MT34 x4y2 open yellowDoor [YK 6->5]
- MT34 x5y2 kill slimeMan [YK 5->6, G 2082->2177] (auto: x5y2 slimeMan, x6y1 yellowKey, x7y2 redKnight) (+95G)
- after: HP=8581 ATK=410 DEF=402 YK=6 BK=1 RK=1 G=2177 dmg=11814 door=40/8/1

### MT46

- before: HP=8581 ATK=410 DEF=402 YK=6 BK=1 RK=1 G=2177 dmg=11814 door=40/8/1
- MT46 x11y2 fly
- MT46 x6y1 shop def [DEF 402->422, G 2177->57]
- after: HP=8581 ATK=410 DEF=422 YK=6 BK=1 RK=1 G=57 dmg=11814 door=40/8/1

### MT25

- before: HP=8581 ATK=410 DEF=422 YK=6 BK=1 RK=1 G=57 dmg=11814 door=40/8/1
- MT25 x2y11 fly
- MT25 x6y10 open redDoor [RK 1->0]
- MT25 x6y6 kill blackMagician [HP 8581->2509, G 57->1057] (+1000G)
- after: HP=2509 ATK=410 DEF=422 YK=6 BK=1 RK=4 G=1057 dmg=17886 door=40/8/2

### MT26

- before: HP=2509 ATK=410 DEF=422 YK=6 BK=1 RK=4 G=1057 dmg=17886 door=40/8/2
- MT26 x2y11 fly
- MT26 x6y10 open redDoor [RK 4->3]
- MT26 x6y9 open redDoor [RK 3->2]
- MT26 x6y8 open redDoor [RK 2->1]
- MT26 x6y6 event princess
- after: HP=2509 ATK=410 DEF=422 YK=6 BK=1 RK=1 G=1057 dmg=17886 door=40/8/5

### MT45

- before: HP=2509 ATK=410 DEF=422 YK=6 BK=1 RK=1 G=1057 dmg=17886 door=40/8/5
- MT45 x2y1 fly
- MT45 x11y5 open yellowDoor [YK 6->5]
- MT45 x11y4 kill slimelord [G 1057->1097] (auto: x11y4 slimelord) (+40G)
- MT45 x9y3 trader hp2000 [HP 2509->4509, G 1097->97]
- after: HP=4509 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=97 dmg=17886 door=41/8/5

### MT47

- before: HP=4509 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=97 dmg=17886 door=41/8/5
- MT47 x11y10 fly
- MT47 x5y11 kill brownWizard (auto: x5y11 brownWizard)
- after: HP=4509 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5

### MT48

- before: HP=4509 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5
- MT48 x11y10 fly
- MT48 x5y11 take bluePotion [HP 4509->5509]
- MT48 x5y8 take redPotion [HP 5509->5759]
- after: HP=5759 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5

### MT46

- before: HP=5759 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5
- MT46 x11y10 fly
- MT46 x1y2 take redPotion [HP 5759->6009]
- after: HP=6009 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5

### MT45

- before: HP=6009 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5
- MT45 x10y1 fly
- MT45 x11y11 take bluePotion [HP 6009->7009]
- after: HP=7009 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5

### MT43

- before: HP=7009 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5
- MT43 x1y10 fly
- MT43 x4y9 take bluePotion [HP 7009->8009]
- MT43 x4y10 take bluePotion [HP 8009->9009]
- MT43 x4y11 take bluePotion [HP 9009->10009]
- after: HP=10009 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5

### MT33

- before: HP=10009 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5
- MT33 x2y1 fly
- MT33 x2y4 take redPotion [HP 10009->10209]
- after: HP=10209 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5

### MT31

- before: HP=10209 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5
- MT31 x6y10 fly
- MT31 x10y1 take redPotion [HP 10209->10409]
- MT31 x2y11 take redPotion [HP 10409->10609]
- after: HP=10609 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5

### MT40

- before: HP=10609 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5
- MT40 x10y11 fly
- MT40 x1y10 take bluePotion [HP 10609->11409]
- after: HP=11409 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5

### MT24

- before: HP=11409 ATK=410 DEF=422 YK=5 BK=1 RK=1 G=177 dmg=17886 door=41/8/5
- MT24 x2y11 fly
- MT24 x6y8 open redDoor [RK 1->0]
- after: HP=11409 ATK=410 DEF=422 YK=5 BK=1 RK=0 G=177 dmg=17886 door=41/8/6

### MT50

- before: HP=11409 ATK=410 DEF=422 YK=5 BK=1 RK=0 G=177 dmg=17886 door=41/8/6
- MT50 x6y5 event redKing
- after: HP=11409 ATK=410 DEF=422 YK=5 BK=1 RK=0 G=177 dmg=17886 door=41/8/6

### MT49

- before: HP=11409 ATK=410 DEF=422 YK=5 BK=1 RK=0 G=177 dmg=17886 door=41/8/6
- MT49 x5y6 下楼器 downFly
- MT49 x6y6 event redKing
- MT49 x6y4 kill whiteKing [G 177->277] (+100G)
- MT49 x5y3 kill whiteKing [G 277->377] (+100G)
- MT49 x7y3 kill whiteKing [G 377->477] (+100G)
- MT49 x6y2 kill whiteKing [G 477->577] (+100G)
- MT49 x5y2 kill whiteKing [G 577->677] (+100G)
- MT49 x7y2 kill whiteKing [G 677->777] (+100G)
- MT49 x5y4 kill whiteKing [G 777->877] (+100G)
- MT49 x7y4 kill whiteKing [G 877->977] (+100G)
- MT49 x6y3 kill redKing [G 977->1477] (+500G)
- MT49 x5y5 take bluePotion [HP 11409->12409]
- MT49 x6y5 take bluePotion [HP 12409->13409]
- MT49 x7y5 take bluePotion [HP 13409->14409]
- after: HP=14409 ATK=425 DEF=437 YK=5 BK=1 RK=1 G=1477 dmg=17886 door=41/8/6

### MT48

- before: HP=14409 ATK=425 DEF=437 YK=5 BK=1 RK=1 G=1477 dmg=17886 door=41/8/6
- MT48 x1y10 fly
- MT48 x1y11 pass upFloor
- after: HP=14409 ATK=425 DEF=437 YK=5 BK=1 RK=1 G=1477 dmg=17886 door=41/8/6

### MT49

- before: HP=14409 ATK=425 DEF=437 YK=5 BK=1 RK=1 G=1477 dmg=17886 door=41/8/6
- MT49 x3y11 open redDoor [RK 1->0]
- MT49 x5y10 kill redWizard [G 1477->1567] (+90G)
- MT49 x7y10 kill redWizard [G 1567->1657] (+90G)
- MT49 x5y8 kill darkKnight [G 1657->1777] (+120G)
- MT49 x7y8 kill darkKnight [G 1777->1897] (+120G)
- after: HP=14409 ATK=425 DEF=437 YK=5 BK=1 RK=0 G=1897 dmg=17886 door=41/8/7

### MT48

- before: HP=14409 ATK=425 DEF=437 YK=5 BK=1 RK=0 G=1897 dmg=17886 door=41/8/7
- MT48 x1y10 fly
- MT48 x2y4 open blueDoor [BK 1->0]
- MT48 x2y3 kill redWizard [G 1897->1987] (auto: x2y3 redWizard) (+90G)
- after: HP=14409 ATK=425 DEF=437 YK=5 BK=0 RK=0 G=1987 dmg=17886 door=41/9/7

### MT38

- before: HP=14409 ATK=425 DEF=437 YK=5 BK=0 RK=0 G=1987 dmg=17886 door=41/9/7
- MT38 x10y1 fly
- MT38 x7y3 open yellowDoor [YK 5->4]
- MT38 x7y6 kill ghostSkeleton (auto: x7y6 ghostSkeleton, x7y7 swordsman)
- after: HP=14409 ATK=425 DEF=437 YK=4 BK=0 RK=0 G=2077 dmg=17886 door=42/9/7

### MT42

- before: HP=14409 ATK=425 DEF=437 YK=4 BK=0 RK=0 G=2077 dmg=17886 door=42/9/7
- MT42 x5y11 fly
- MT42 x11y6 kill brownWizard (auto: x11y6 brownWizard)
- after: HP=14409 ATK=425 DEF=437 YK=4 BK=0 RK=0 G=2157 dmg=17886 door=42/9/7

### MT46

- before: HP=14409 ATK=425 DEF=437 YK=4 BK=0 RK=0 G=2157 dmg=17886 door=42/9/7
- MT46 x11y2 fly
- MT46 x9y6 open yellowDoor [YK 4->3]
- MT46 x8y7 kill redWizard (auto: x8y7 redWizard)
- after: HP=14409 ATK=425 DEF=437 YK=3 BK=0 RK=0 G=2247 dmg=17886 door=43/9/7

### MT18

- before: HP=14409 ATK=425 DEF=437 YK=3 BK=0 RK=0 G=2247 dmg=17886 door=43/9/7
- MT18 x1y2 fly
- MT18 x4y8 open yellowDoor [YK 3->2]
- MT18 x4y9 kill bigBat [YK 2->3, G 2247->2295] (auto: x4y9 bigBat, x4y10 bigBat, x5y9 bigBat, x5y10 bigBat, x5y11 yellowKey) (+48G)
- after: HP=14409 ATK=425 DEF=437 YK=3 BK=0 RK=0 G=2295 dmg=17886 door=44/9/7

### MT34

- before: HP=14409 ATK=425 DEF=437 YK=3 BK=0 RK=0 G=2295 dmg=17886 door=44/9/7
- MT34 x2y1 fly
- MT34 x8y10 open yellowDoor [YK 3->2]
- MT34 x9y10 kill soldier [ATK 425->429, YK 2->3, G 2295->2340] (auto: x9y10 soldier, x10y11 yellowKey, x11y11 redGem) (+45G)
- after: HP=14409 ATK=429 DEF=437 YK=3 BK=0 RK=0 G=2340 dmg=17886 door=45/9/7

### MT18

- before: HP=14409 ATK=429 DEF=437 YK=3 BK=0 RK=0 G=2340 dmg=17886 door=45/9/7
- MT18 x1y2 fly
- MT18 x8y8 open yellowDoor [YK 3->2]
- MT18 x8y9 kill blackSlime [YK 2->3, G 2340->2372] (auto: x8y9 blackSlime, x7y9 blackSlime, x8y10 blackSlime, x7y10 blackSlime, x7y11 yellowKey) (+32G)
- after: HP=14409 ATK=429 DEF=437 YK=3 BK=0 RK=0 G=2372 dmg=17886 door=46/9/7

### MT11

- before: HP=14409 ATK=429 DEF=437 YK=3 BK=0 RK=0 G=2372 dmg=17886 door=46/9/7
- MT11 x11y10 fly
- MT11 x5y3 open yellowDoor [YK 3->2]
- MT11 x6y4 kill bigBat (auto: x5y5 zombie, x6y4 bigBat)
- after: HP=14409 ATK=429 DEF=437 YK=2 BK=0 RK=0 G=2402 dmg=17886 door=47/9/7

### MT9

- before: HP=14409 ATK=429 DEF=437 YK=2 BK=0 RK=0 G=2402 dmg=17886 door=47/9/7
- MT9 x1y10 fly
- MT9 x5y9 open yellowDoor [YK 2->1]
- MT9 x4y7 kill skeletonSoldier (auto: x5y7 yellowKey, x4y7 skeletonSoldier)
- MT9 x3y7 open yellowDoor [YK 2->1]
- MT9 x1y8 kill skeletonSoldier (auto: x1y7 yellowKey, x1y8 skeletonSoldier)
- after: HP=14409 ATK=429 DEF=437 YK=2 BK=0 RK=0 G=2418 dmg=17886 door=49/9/7

### MT12

- before: HP=14409 ATK=429 DEF=437 YK=2 BK=0 RK=0 G=2418 dmg=17886 door=49/9/7
- MT12 x10y11 fly
- MT12 x4y5 open yellowDoor [YK 2->1]
- MT12 x2y5 kill redPriest (auto: x2y5 redPriest)
- after: HP=14409 ATK=429 DEF=437 YK=1 BK=0 RK=0 G=2440 dmg=17886 door=50/9/7

### MT46

- before: HP=14409 ATK=429 DEF=437 YK=1 BK=0 RK=0 G=2440 dmg=17886 door=50/9/7
- MT46 x11y2 fly
- MT46 x6y1 shop hp [HP 14409->16009, G 2440->20]
- after: HP=16009 ATK=429 DEF=437 YK=1 BK=0 RK=0 G=20 dmg=17886 door=50/9/7

### MT38

- before: HP=16009 ATK=429 DEF=437 YK=1 BK=0 RK=0 G=20 dmg=17886 door=50/9/7
- MT38 x10y1 fly
- MT38 x6y8 take redPotion [HP 16009->16209, DEF 437->441] (auto: x5y8 blueGem)
- MT38 x5y8 move
- after: HP=16209 ATK=429 DEF=441 YK=1 BK=0 RK=0 G=20 dmg=17886 door=50/9/7

### MT48

- before: HP=16209 ATK=429 DEF=441 YK=1 BK=0 RK=0 G=20 dmg=17886 door=50/9/7
- MT48 x11y10 fly
- MT48 x2y1 take bluePotion [HP 16209->17209]
- after: HP=17209 ATK=429 DEF=441 YK=1 BK=0 RK=0 G=20 dmg=17886 door=50/9/7

### MT46

- before: HP=17209 ATK=429 DEF=441 YK=1 BK=0 RK=0 G=20 dmg=17886 door=50/9/7
- MT46 x11y10 fly
- MT46 x7y6 take redPotion [HP 17209->17459]
- after: HP=17459 ATK=429 DEF=441 YK=1 BK=0 RK=0 G=20 dmg=17886 door=50/9/7

### MT34

- before: HP=17459 ATK=429 DEF=441 YK=1 BK=0 RK=0 G=20 dmg=17886 door=50/9/7
- MT34 x6y10 fly
- MT34 x11y10 take redPotion [HP 17459->17659]
- after: HP=17659 ATK=429 DEF=441 YK=1 BK=0 RK=0 G=20 dmg=17886 door=50/9/7

### MT24

- before: HP=17659 ATK=429 DEF=441 YK=1 BK=0 RK=0 G=20 dmg=17886 door=50/9/7
- MT24 x2y11 fly
- after: HP=17659 ATK=429 DEF=441 YK=1 BK=0 RK=0 G=20 dmg=17886 door=50/9/7

### MT50

- before: HP=17659 ATK=429 DEF=441 YK=1 BK=0 RK=0 G=20 dmg=17886 door=50/9/7
- MT50 x6y5 kill redKing [G 20->520] (+500G)
- after: HP=17659 ATK=429 DEF=441 YK=1 BK=0 RK=0 G=520 dmg=17886 door=50/9/7
