# 当前最优 Walk (zone4, auto ON)

## 说明

- 本 walk 由 Game 类 (`scripts/search/zone4_game_route.py`, auto_sweep, strict_live_model) 离线推导生成。
- auto 配置：battle=true, item=nopotion, wall=true。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk best/zone4_2atk1def_te_hp18277_walk.json --load-slot 150 --target-click-only --set-auto battle=true,item=nopotion,wall=true --out-json best/zone4_2atk1def_te_hp18277_live_verify.json`
- 源 JSON：`outputs/results/zone4_dynamic_auto_terminal_closure_v2.json`

## 摘要

- final: HP=18277 ATK=439 DEF=425 YK=3 BK=1 RK=0 G=2346 dmg=17418 door=49/10/7 MT50 x6y5

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

### MT43

- before: HP=1067 ATK=237 DEF=287 YK=14 BK=3 RK=0 G=474 dmg=3828 door=14/2/1
- MT43 x1y10 fly
- MT43 x3y6 open yellowDoor [YK 14->13]
- MT43 x5y7 kill slimelord [HP 1067->2044, G 474->514] (+40G)
- MT43 x8y6 open yellowDoor [YK 13->12]
- MT43 x11y5 open yellowDoor [HP 2044->2294] (auto: x10y8 yellowKey, x11y7 redPotion)
- MT43 x9y1 kill whiteKing [HP 2294->2131, G 514->614] (+100G)
- MT43 x11y9 open yellowDoor [YK 12->11]
- after: HP=2131 ATK=237 DEF=337 YK=11 BK=4 RK=0 G=614 dmg=4014 door=18/2/1

### MT46

- before: HP=2131 ATK=237 DEF=337 YK=11 BK=4 RK=0 G=614 dmg=4014 door=18/2/1
- MT46 x11y2 fly
- MT46 x9y11 open yellowDoor [YK 11->10]
- MT46 x6y11 open blueDoor [BK 4->3]
- MT46 x4y11 kill redSlime (auto: x4y11 redSlime, x2y11 skeleton, x1y10 bigBat, x1y8 zombie, x1y6 soldier, x3y6 swordsman, x5y6 redKnight, x5y8 slimelord)
- MT46 x4y9 kill brownWizard [HP 2131->2098, G 857->937] (+80G)
- after: HP=2098 ATK=237 DEF=337 YK=10 BK=3 RK=0 G=937 dmg=4047 door=19/3/1

### MT41

- before: HP=2098 ATK=237 DEF=337 YK=10 BK=3 RK=0 G=937 dmg=4047 door=19/3/1
- MT41 x6y10 fly
- MT41 x6y10 魔法钥匙 bigKey
- MT41 x5y6 open blueDoor [BK 3->2]
- MT41 x2y2 kill redWizard [HP 2098->2555, ATK 237->242, YK 10->13, G 937->1067] (+130G)
- MT41 x7y6 open blueDoor [BK 3->2]
- MT41 x9y5 kill brownWizard [HP 2555->3027, DEF 337->342, YK 13->16, BK 2->3, G 1067->1187] (+120G)
- MT41 x10y2 event redWizard
- MT41 x10y2 kill redWizard [HP 3027->2989, G 1187->1277] (+90G)
- after: HP=2989 ATK=242 DEF=342 YK=16 BK=3 RK=0 G=1277 dmg=4156 door=19/5/1

### MT40

- before: HP=2989 ATK=242 DEF=342 YK=16 BK=3 RK=0 G=1277 dmg=4156 door=19/5/1
- MT40 x6y2 fly
- after: HP=2989 ATK=242 DEF=342 YK=16 BK=3 RK=0 G=1277 dmg=4156 door=19/5/1

### MT41

- before: HP=2989 ATK=242 DEF=342 YK=16 BK=3 RK=0 G=1277 dmg=4156 door=19/5/1
- MT41 x6y2 fly
- after: HP=2989 ATK=242 DEF=342 YK=16 BK=3 RK=0 G=1277 dmg=4156 door=19/5/1

### MT42

- before: HP=2989 ATK=242 DEF=342 YK=16 BK=3 RK=0 G=1277 dmg=4156 door=19/5/1
- MT42 x5y11 fly
- MT42 x6y4 kill darkKnight [HP 2989->2549, RK 0->1, G 1277->1397] (+120G)
- after: HP=2549 ATK=242 DEF=342 YK=16 BK=3 RK=1 G=1397 dmg=4596 door=19/5/1

### MT46

- before: HP=2549 ATK=242 DEF=342 YK=16 BK=3 RK=1 G=1397 dmg=4596 door=19/5/1
- MT46 x11y2 fly
- MT46 x9y1 open blueDoor [BK 3->2]
- MT46 x6y1 shop atk [ATK 242->252, G 1397->277]
- after: HP=2549 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=277 dmg=4596 door=19/6/1

### MT36

- before: HP=2549 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=277 dmg=4596 door=19/6/1
- MT36 x11y10 fly
- MT36 x9y1 kill redKnight (auto: x9y1 redKnight, x7y1 zombieKnight, x3y1 soldier, x1y5 redKnight, x1y3 slimeMan)
- after: HP=2549 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=512 dmg=4596 door=19/6/1

### MT41

- before: HP=2549 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=512 dmg=4596 door=19/6/1
- MT41 x6y2 fly
- MT41 x5y4 kill whiteKing [HP 2549->2441, G 512->612] (+100G)
- MT41 x7y4 kill whiteKing [HP 2441->2333, G 612->712] (+100G)
- after: HP=2333 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=712 dmg=4812 door=19/6/1

### MT42

- before: HP=2333 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=712 dmg=4812 door=19/6/1
- MT42 x5y11 fly
- MT42 x9y8 kill whiteKing [HP 2333->2225, G 712->812] (+100G)
- MT42 x11y8 kill whiteKing [HP 2225->2117, G 812->912] (+100G)
- MT42 x11y4 kill redWizard [HP 2117->2079, G 912->1002] (+90G)
- MT42 x9y4 kill brownWizard [HP 2079->2051, G 1002->1082] (+80G)
- MT42 x11y6 kill brownWizard [HP 2051->2023, G 1082->1162] (+80G)
- after: HP=2023 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=1162 dmg=5122 door=19/6/1

### MT43

- before: HP=2023 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=1162 dmg=5122 door=19/6/1
- MT43 x1y2 fly
- MT43 x6y3 kill darkKnight [HP 2023->1671, G 1162->1282] (+120G)
- MT43 x7y4 kill darkKnight [HP 1671->1319, G 1282->1402] (+120G)
- after: HP=1319 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=1402 dmg=5826 door=19/6/1

### MT46

- before: HP=1319 ATK=252 DEF=342 YK=16 BK=2 RK=1 G=1402 dmg=5826 door=19/6/1
- MT46 x11y2 fly
- MT46 x6y1 shop atk [ATK 252->262, G 1402->62]
- after: HP=1319 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=62 dmg=5826 door=19/6/1

### MT41

- before: HP=1319 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=62 dmg=5826 door=19/6/1
- MT41 x6y10 fly
- MT41 x1y6 kill redBat [HP 1319->2271, G 62->112] (+50G)
- MT41 x11y6 kill redBat [HP 2271->3223, G 112->162] (+50G)
- MT41 x3y5 kill brownWizard [HP 3223->3195, G 162->242] (+80G)
- MT41 x2y7 kill redBat [HP 3195->3147, G 242->292] (+50G)
- MT41 x10y7 kill redBat [HP 3147->3099, G 292->342] (+50G)
- after: HP=3099 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=342 dmg=6046 door=19/6/1

### MT43

- before: HP=3099 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=342 dmg=6046 door=19/6/1
- MT43 x1y2 fly
- MT43 x4y4 kill redWizard [HP 3099->3061, G 342->432] (+90G)
- MT43 x9y7 kill brownWizard [HP 3061->3033, G 432->512] (+80G)
- MT43 x2y9 kill redBat [HP 3033->2985, G 512->562] (+50G)
- MT43 x10y10 kill redBat [HP 2985->2937, G 562->612] (+50G)
- after: HP=2937 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=612 dmg=6208 door=19/6/1

### MT45

- before: HP=2937 ATK=262 DEF=342 YK=16 BK=2 RK=1 G=612 dmg=6208 door=19/6/1
- MT45 x2y1 fly
- MT45 x3y6 kill darkKnight [HP 2937->2673, DEF 342->352, G 612->732] (+120G)
- MT45 x3y4 kill darkKnight [HP 2673->2439, ATK 262->272, G 732->852] (+120G)
- MT45 x7y3 kill redWizard [HP 2439->2411, G 852->942] (+90G)
- MT45 x5y5 kill redWizard [HP 2411->2383, G 942->1032] (+90G)
- MT45 x5y3 kill brownWizard [HP 2383->2365, G 1032->1112] (+80G)
- MT45 x7y5 kill brownWizard [HP 2365->2347, G 1112->1192] (+80G)
- MT45 x7y7 kill redBat [HP 2347->2309, YK 16->17, G 1192->1242] (+50G)
- MT45 x10y8 kill redWizard [HP 2309->2281, G 1242->1332] (+90G)
- after: HP=2281 ATK=272 DEF=352 YK=17 BK=2 RK=1 G=1332 dmg=6864 door=19/6/1

### MT46

- before: HP=2281 ATK=272 DEF=352 YK=17 BK=2 RK=1 G=1332 dmg=6864 door=19/6/1
- MT46 x11y2 fly
- MT46 x10y9 kill brownWizard [HP 2281->2263, G 1332->1412] (+80G)
- MT46 x9y4 kill redBat [HP 2263->2225, G 1412->1462] (+50G)
- after: HP=2225 ATK=272 DEF=352 YK=17 BK=2 RK=1 G=1462 dmg=6920 door=19/6/1

### MT47

- before: HP=2225 ATK=272 DEF=352 YK=17 BK=2 RK=1 G=1462 dmg=6920 door=19/6/1
- MT47 x11y10 fly
- MT47 x5y11 kill brownWizard [HP 2225->2207, G 1462->1582] (+120G)
- after: HP=2207 ATK=272 DEF=352 YK=17 BK=2 RK=1 G=1582 dmg=6938 door=19/6/1

### MT46

- before: HP=2207 ATK=272 DEF=352 YK=17 BK=2 RK=1 G=1582 dmg=6938 door=19/6/1
- MT46 x11y10 fly
- MT46 x6y1 shop atk [ATK 272->282, G 1582->2]
- after: HP=2207 ATK=282 DEF=352 YK=17 BK=2 RK=1 G=2 dmg=6938 door=19/6/1

### MT48

- before: HP=2207 ATK=282 DEF=352 YK=17 BK=2 RK=1 G=2 dmg=6938 door=19/6/1
- MT48 x11y10 fly
- MT48 x11y11 pass downFloor
- after: HP=2207 ATK=282 DEF=352 YK=17 BK=2 RK=1 G=42 dmg=6938 door=19/6/1

### MT47

- before: HP=2207 ATK=282 DEF=352 YK=17 BK=2 RK=1 G=42 dmg=6938 door=19/6/1
- MT47 x1y10 event redWizard
- MT47 x1y11 event redWizard
- MT47 x1y11 kill redWizard [HP 2207->2179, G 42->132] (+90G)
- after: HP=2179 ATK=282 DEF=352 YK=17 BK=2 RK=1 G=132 dmg=6966 door=19/6/1

### MT42

- before: HP=2179 ATK=282 DEF=352 YK=17 BK=2 RK=1 G=132 dmg=6966 door=19/6/1
- MT42 x1y2 fly
- MT42 x3y2 kill slimelord [G 132->172] (auto: x3y2 slimelord) (+40G)
- after: HP=2179 ATK=282 DEF=352 YK=17 BK=2 RK=1 G=172 dmg=6966 door=19/6/1

### MT48

- before: HP=2179 ATK=282 DEF=352 YK=17 BK=2 RK=1 G=172 dmg=6966 door=19/6/1
- MT48 x11y10 fly
- MT48 x3y5 kill slimelord (auto: x3y5 slimelord)
- after: HP=2179 ATK=282 DEF=352 YK=17 BK=2 RK=1 G=212 dmg=6966 door=19/6/1

### MT37

- before: HP=2179 ATK=282 DEF=352 YK=17 BK=2 RK=1 G=212 dmg=6966 door=19/6/1
- MT37 x2y1 fly
- after: HP=4979 ATK=282 DEF=352 YK=17 BK=2 RK=1 G=212 dmg=6966 door=19/6/1

### MT42

- before: HP=4979 ATK=282 DEF=352 YK=17 BK=2 RK=1 G=212 dmg=6966 door=19/6/1
- MT42 x5y11 fly
- MT42 x4y5 open yellowDoor [YK 17->16]
- MT42 x3y5 kill slimelord [G 212->252] (auto: x3y5 slimelord) (+40G)
- MT42 x1y6 open yellowDoor [YK 16->15]
- MT42 x3y8 kill redBat [HP 4979->5941, YK 15->17, G 252->302] (+50G)
- MT42 x1y10 kill redBat [HP 5941->5903, DEF 352->357, YK 17->19, G 302->352] (+50G)
- after: HP=5903 ATK=282 DEF=357 YK=19 BK=2 RK=1 G=352 dmg=7042 door=21/6/1

### MT34

- before: HP=5903 ATK=282 DEF=357 YK=19 BK=2 RK=1 G=352 dmg=7042 door=21/6/1
- MT34 x6y10 fly
- MT34 x4y2 open yellowDoor [YK 19->18]
- MT34 x5y2 kill slimeMan [YK 18->19, G 352->447] (auto: x5y2 slimeMan, x6y1 yellowKey, x7y2 redKnight) (+95G)
- MT34 x8y2 open yellowDoor [YK 19->18]
- MT34 x9y1 move (auto: x9y1 yellowKey, x10y2 yellowKey, x10y1 yellowKey, x11y2 redPotion, x11y1 blueGem)
- MT34 x8y10 open yellowDoor [YK 21->20]
- MT34 x9y10 kill soldier [HP 6103->6303, ATK 282->286, YK 20->21, G 447->492] (auto: x9y10 soldier, x10y11 yellowKey, x11y10 redPotion, x11y11 redGem) (+45G)
- after: HP=6303 ATK=286 DEF=361 YK=21 BK=2 RK=1 G=492 dmg=7042 door=24/6/1

### MT48

- before: HP=6303 ATK=286 DEF=361 YK=21 BK=2 RK=1 G=492 dmg=7042 door=24/6/1
- MT48 x11y10 fly
- MT48 x4y6 open yellowDoor [YK 21->20]
- MT48 x4y7 kill brownWizard [HP 6303->6544, ATK 286->291, G 492->622] (+130G)
- MT48 x4y9 open yellowDoor [YK 20->19]
- MT48 x4y10 kill darkKnight [HP 6544->7406, DEF 361->366, G 622->742] (+120G)
- after: HP=7406 ATK=291 DEF=366 YK=19 BK=2 RK=1 G=742 dmg=7189 door=26/6/1

### MT36

- before: HP=7406 ATK=291 DEF=366 YK=19 BK=2 RK=1 G=742 dmg=7189 door=26/6/1
- MT36 x11y10 fly
- MT36 x10y6 open yellowDoor [YK 19->18]
- MT36 x7y6 kill slimeMan (auto: x7y6 slimeMan, x6y5 ghostSkeleton, x5y6 slimeMan, x6y7 redKnight)
- after: HP=7406 ATK=291 DEF=366 YK=18 BK=2 RK=1 G=902 dmg=7189 door=27/6/1

### MT47

- before: HP=7406 ATK=291 DEF=366 YK=18 BK=2 RK=1 G=902 dmg=7189 door=27/6/1
- MT47 x11y10 fly
- MT47 x11y7 open yellowDoor [YK 18->17]
- MT47 x11y6 kill redBat [YK 17->18, G 902->952] (auto: x11y6 redBat, x8y6 yellowKey) (+50G)
- MT47 x9y5 kill brownWizard [HP 7406->7402, G 952->1032] (+80G)
- after: HP=7402 ATK=291 DEF=366 YK=18 BK=2 RK=1 G=1032 dmg=7193 door=28/6/1

### MT31

- before: HP=7402 ATK=291 DEF=366 YK=18 BK=2 RK=1 G=1032 dmg=7193 door=28/6/1
- MT31 x6y10 fly
- MT31 x1y7 open yellowDoor [YK 18->17]
- MT31 x1y9 kill ghostSkeleton (auto: x1y9 ghostSkeleton, x2y9 ghostSkeleton, x2y11 redPotion, x4y10 redKnight)
- after: HP=7602 ATK=291 DEF=366 YK=17 BK=2 RK=1 G=1167 dmg=7193 door=29/6/1

### MT40

- before: HP=7602 ATK=291 DEF=366 YK=17 BK=2 RK=1 G=1167 dmg=7193 door=29/6/1
- MT40 x10y11 fly
- MT40 x8y11 open yellowDoor [YK 17->16]
- MT40 x4y11 open blueDoor [BK 2->1, G 1167->1227] (auto: x7y9 slimeMan, x5y9 slimeMan)
- MT40 x3y11 kill redKnight [HP 7602->8402, ATK 291->295, DEF 366->370, YK 16->17, G 1227->1292] (auto: x3y11 redKnight, x1y11 redGem, x2y9 yellowKey, x1y10 bluePotion, x1y9 blueGem) (+65G)
- after: HP=8402 ATK=295 DEF=370 YK=17 BK=1 RK=1 G=1292 dmg=7193 door=30/7/1

### MT48

- before: HP=8402 ATK=295 DEF=370 YK=17 BK=1 RK=1 G=1292 dmg=7193 door=30/7/1
- MT48 x11y10 fly
- MT48 x7y3 kill whiteKing [HP 8402->8322, G 1292->1552] (+260G)
- after: HP=8322 ATK=295 DEF=370 YK=17 BK=1 RK=1 G=1552 dmg=7273 door=30/7/1

### MT47

- before: HP=8322 ATK=295 DEF=370 YK=17 BK=1 RK=1 G=1552 dmg=7273 door=30/7/1
- MT47 x2y1 fly
- MT47 x2y6 open yellowDoor [YK 17->16]
- MT47 x3y5 kill redBat (auto: x3y5 redBat)
- MT47 x4y4 open yellowDoor [YK 16->15]
- MT47 x5y4 kill redWizard [HP 8322->8312, ATK 295->300, DEF 370->375, YK 15->16, BK 1->2, G 1602->1772] (+170G)
- after: HP=8312 ATK=300 DEF=375 YK=16 BK=2 RK=1 G=1772 dmg=7283 door=32/7/1

### MT46

- before: HP=8312 ATK=300 DEF=375 YK=16 BK=2 RK=1 G=1772 dmg=7283 door=32/7/1
- MT46 x11y10 fly
- MT46 x3y1 open yellowDoor [YK 16->15]
- MT46 x2y1 kill redWizard [HP 8312->8557, ATK 300->305, G 1772->1942] (+170G)
- MT46 x6y1 shop atk [ATK 305->315, G 1942->102]
- after: HP=8557 ATK=315 DEF=375 YK=15 BK=2 RK=1 G=102 dmg=7288 door=33/7/1

### MT2

- before: HP=8557 ATK=315 DEF=375 YK=15 BK=2 RK=1 G=102 dmg=7288 door=33/7/1
- MT2 x1y10 fly
- MT2 x11y7 trader specialTrader [ATK 315->324, DEF 375->386]
- after: HP=8557 ATK=324 DEF=386 YK=15 BK=2 RK=1 G=102 dmg=7288 door=33/7/1

### MT16

- before: HP=8557 ATK=324 DEF=386 YK=15 BK=2 RK=1 G=102 dmg=7288 door=33/7/1
- MT16 x6y2 fly
- MT16 x11y11 pass fakeWall2
- MT16 x11y11 老人 superPotion
- MT16 x10y11 使用 superPotion [HP 8557->13807]
- after: HP=13807 ATK=324 DEF=386 YK=15 BK=2 RK=1 G=102 dmg=7288 door=33/7/1

### MT35

- before: HP=13807 ATK=324 DEF=386 YK=15 BK=2 RK=1 G=102 dmg=7288 door=33/7/1
- MT35 x6y10 fly
- MT35 x6y7 kill magicDragon [HP 13807->9527, G 102->902] (+800G)
- MT35 x6y6 take snow [HP 9527->11927] (auto: x6y5 bluePotion, x5y5 bluePotion, x7y5 bluePotion)
- after: HP=11927 ATK=324 DEF=386 YK=15 BK=2 RK=1 G=902 dmg=11568 door=33/7/1

### MT13

- before: HP=11927 ATK=324 DEF=386 YK=15 BK=2 RK=1 G=902 dmg=11568 door=33/7/1
- MT13 x10y11 fly
- MT13 x6y10 open yellowDoor [YK 15->14]
- MT13 x6y10 move [ATK 324->424] (auto: resource group on move) (auto: x6y9 lava, x6y8 lava, x5y9 lava, x7y9 lava, x6y7 lava, x5y8 lava, x7y8 lava, x4y9 lava, x8y9 lava, x6y6 lava, x4y8 lava, x8y8 lava, x3y9 lava, x9y9 lava, x6y5 sword5, x4y7 lava, x3y8 lava, x8y7 lava, x9y8 lava, x2y9 lava, x10y9 lava, x3y7 lava, x2y8 lava, x9y7 lava, x10y8 lava, x1y9 lava, x11y9 lava, x3y6 lava, x2y7 lava, x1y8 lava, x9y6 lava, x10y7 lava, x11y8 lava, x3y5 lava, x2y6 lava, x1y7 lava, x9y5 lava, x10y6 lava, x11y7 lava, x3y4 lava, x2y5 lava, x1y6 lava, x9y4 lava, x10y5 lava, x11y6 lava, x3y3 lava, x2y4 lava, x1y5 lava, x9y3 lava, x10y4 lava, x11y5 lava, x3y2 lava, x2y3 lava, x4y3 lava, x1y4 lava, x9y2 lava, x8y3 lava, x10y3 lava, x11y4 lava, x3y1 lava, x2y2 lava, x4y2 lava, x1y3 lava, x9y1 lava, x8y2 lava, x10y2 lava, x11y3 lava, x2y1 lava, x4y1 lava, x1y2 lava, x5y2 lava, x8y1 lava, x10y1 lava, x7y2 lava, x11y2 lava, x1y1 lava, x5y1 lava, x6y2 lava, x7y1 lava, x11y1 lava, x6y1 lava)
- after: HP=11927 ATK=424 DEF=386 YK=14 BK=2 RK=1 G=902 dmg=11568 door=34/7/1

### MT48

- before: HP=11927 ATK=424 DEF=386 YK=14 BK=2 RK=1 G=902 dmg=11568 door=34/7/1
- MT48 x11y10 fly
- MT48 x2y4 open blueDoor [BK 2->1, G 902->1202] (auto: x9y3 whiteKing, x9y5 whiteKing, x7y5 whiteKing)
- MT48 x2y3 kill redWizard [HP 11927->12927, G 1202->1292] (auto: x2y3 redWizard, x2y1 bluePotion) (+90G)
- after: HP=12927 ATK=424 DEF=386 YK=14 BK=1 RK=1 G=1292 dmg=11568 door=34/8/1

### MT32

- before: HP=12927 ATK=424 DEF=386 YK=14 BK=1 RK=1 G=1292 dmg=11568 door=34/8/1
- MT32 x10y1 fly
- MT32 x5y3 open yellowDoor [YK 14->13]
- MT32 x3y4 kill slimeMan (auto: x3y4 slimeMan, x4y5 slimeMan, x1y4 soldier, x2y5 yellowKey)
- after: HP=12927 ATK=424 DEF=386 YK=14 BK=1 RK=1 G=1397 dmg=11568 door=35/8/1

### MT33

- before: HP=12927 ATK=424 DEF=386 YK=14 BK=1 RK=1 G=1397 dmg=11568 door=35/8/1
- MT33 x10y1 fly
- MT33 x5y4 open yellowDoor [YK 14->13]
- MT33 x6y5 kill zombieKnight (auto: x6y5 zombieKnight, x4y6 swordsman, x6y7 ghostSkeleton)
- after: HP=12927 ATK=424 DEF=386 YK=13 BK=1 RK=1 G=1517 dmg=11568 door=36/8/1

### MT43

- before: HP=12927 ATK=424 DEF=386 YK=13 BK=1 RK=1 G=1517 dmg=11568 door=36/8/1
- MT43 x1y2 fly
- MT43 x8y10 open yellowDoor [YK 13->12]
- MT43 x6y9 kill darkKnight (auto: x6y9 darkKnight, x4y9 bluePotion, x4y10 bluePotion, x4y11 bluePotion)
- after: HP=15927 ATK=424 DEF=386 YK=12 BK=1 RK=1 G=1637 dmg=11568 door=37/8/1

### MT31

- before: HP=15927 ATK=424 DEF=386 YK=12 BK=1 RK=1 G=1637 dmg=11568 door=37/8/1
- MT31 x6y10 fly
- MT31 x11y5 open yellowDoor [YK 12->11]
- MT31 x10y3 kill ghostSkeleton (auto: x11y3 ghostSkeleton, x10y3 ghostSkeleton, x10y1 redPotion, x8y2 soldier)
- after: HP=16127 ATK=424 DEF=386 YK=11 BK=1 RK=1 G=1752 dmg=11568 door=38/8/1

### MT38

- before: HP=16127 ATK=424 DEF=386 YK=11 BK=1 RK=1 G=1752 dmg=11568 door=38/8/1
- MT38 x2y1 fly
- MT38 x7y3 open yellowDoor [YK 11->10]
- MT38 x7y6 kill ghostSkeleton (auto: x7y6 ghostSkeleton, x7y7 swordsman, x6y8 redPotion, x5y8 blueGem)
- after: HP=16327 ATK=424 DEF=390 YK=10 BK=1 RK=1 G=1842 dmg=11568 door=39/8/1

### MT46

- before: HP=16327 ATK=424 DEF=390 YK=10 BK=1 RK=1 G=1842 dmg=11568 door=39/8/1
- MT46 x11y2 fly
- MT46 x9y6 open yellowDoor [YK 10->9]
- MT46 x8y7 kill redWizard (auto: x7y6 redPotion, x8y7 redWizard)
- after: HP=16577 ATK=424 DEF=390 YK=9 BK=1 RK=1 G=1932 dmg=11568 door=40/8/1

### MT45

- before: HP=16577 ATK=424 DEF=390 YK=9 BK=1 RK=1 G=1932 dmg=11568 door=40/8/1
- MT45 x10y1 fly
- MT45 x11y9 open yellowDoor [YK 9->8]
- MT45 x9y10 open yellowDoor [HP 16577->17577, YK 8->7] (auto: x11y11 bluePotion)
- MT45 x8y9 kill whiteKing [G 1932->2032] (+100G)
- MT45 x8y11 kill whiteKing [G 2032->2132] (+100G)
- after: HP=17577 ATK=424 DEF=390 YK=7 BK=1 RK=1 G=2132 dmg=11568 door=42/8/1

### MT46

- before: HP=17577 ATK=424 DEF=390 YK=7 BK=1 RK=1 G=2132 dmg=11568 door=42/8/1
- MT46 x11y2 fly
- MT46 x6y1 shop def [DEF 390->410, G 2132->12]
- after: HP=17577 ATK=424 DEF=410 YK=7 BK=1 RK=1 G=12 dmg=11568 door=42/8/1

### MT25

- before: HP=17577 ATK=424 DEF=410 YK=7 BK=1 RK=1 G=12 dmg=11568 door=42/8/1
- MT25 x2y11 fly
- MT25 x6y10 open redDoor [RK 1->0]
- MT25 x6y6 kill blackMagician [HP 17577->11727, G 12->1012] (+1000G)
- after: HP=11727 ATK=424 DEF=410 YK=7 BK=1 RK=4 G=1012 dmg=17418 door=42/8/2

### MT26

- before: HP=11727 ATK=424 DEF=410 YK=7 BK=1 RK=4 G=1012 dmg=17418 door=42/8/2
- MT26 x2y11 fly
- MT26 x6y10 open redDoor [RK 4->3]
- MT26 x6y9 open redDoor [RK 3->2]
- MT26 x6y8 open redDoor [RK 2->1]
- MT26 x6y6 event princess
- after: HP=11727 ATK=424 DEF=410 YK=7 BK=1 RK=1 G=1012 dmg=17418 door=42/8/5

### MT45

- before: HP=11727 ATK=424 DEF=410 YK=7 BK=1 RK=1 G=1012 dmg=17418 door=42/8/5
- MT45 x2y1 fly
- MT45 x11y5 open yellowDoor [YK 7->6]
- MT45 x11y4 kill slimelord [G 1012->1052] (auto: x11y4 slimelord) (+40G)
- MT45 x9y3 trader hp2000 [HP 11727->13727, G 1052->52]
- MT45 x5y9 kill darkKnight [G 52->172] (+120G)
- MT45 x5y11 kill darkKnight [G 172->292] (+120G)
- after: HP=13727 ATK=424 DEF=410 YK=6 BK=1 RK=1 G=292 dmg=17418 door=43/8/5

### MT24

- before: HP=13727 ATK=424 DEF=410 YK=6 BK=1 RK=1 G=292 dmg=17418 door=43/8/5
- MT24 x2y11 fly
- MT24 x6y8 open redDoor [RK 1->0]
- after: HP=13727 ATK=424 DEF=410 YK=6 BK=1 RK=0 G=292 dmg=17418 door=43/8/6

### MT50

- before: HP=13727 ATK=424 DEF=410 YK=6 BK=1 RK=0 G=292 dmg=17418 door=43/8/6
- MT50 x6y5 event redKing
- after: HP=13727 ATK=424 DEF=410 YK=6 BK=1 RK=0 G=292 dmg=17418 door=43/8/6

### MT49

- before: HP=13727 ATK=424 DEF=410 YK=6 BK=1 RK=0 G=292 dmg=17418 door=43/8/6
- MT49 x5y6 下楼器 downFly
- MT49 x6y6 event redKing
- MT49 x6y4 kill whiteKing [G 292->392] (+100G)
- MT49 x5y3 kill whiteKing [G 392->492] (+100G)
- MT49 x7y3 kill whiteKing [G 492->592] (+100G)
- MT49 x6y2 kill whiteKing [G 592->692] (+100G)
- MT49 x5y2 kill whiteKing [G 692->792] (+100G)
- MT49 x7y2 kill whiteKing [G 792->892] (+100G)
- MT49 x5y4 kill whiteKing [G 892->992] (+100G)
- MT49 x7y4 kill whiteKing [G 992->1092] (+100G)
- MT49 x6y3 kill redKing [G 1092->1592] (+500G)
- after: HP=16727 ATK=439 DEF=425 YK=6 BK=1 RK=1 G=1592 dmg=17418 door=43/8/6

### MT48

- before: HP=16727 ATK=439 DEF=425 YK=6 BK=1 RK=1 G=1592 dmg=17418 door=43/8/6
- MT48 x1y10 fly
- MT48 x1y11 pass upFloor
- after: HP=16727 ATK=439 DEF=425 YK=6 BK=1 RK=1 G=1592 dmg=17418 door=43/8/6

### MT49

- before: HP=16727 ATK=439 DEF=425 YK=6 BK=1 RK=1 G=1592 dmg=17418 door=43/8/6
- MT49 x3y11 open redDoor [RK 1->0]
- MT49 x5y10 kill redWizard [G 1592->1682] (+90G)
- after: HP=16727 ATK=439 DEF=425 YK=6 BK=1 RK=0 G=1682 dmg=17418 door=43/8/7

### MT48

- before: HP=16727 ATK=439 DEF=425 YK=6 BK=1 RK=0 G=1682 dmg=17418 door=43/8/7
- MT48 x1y10 fly
- MT48 x11y11 pass downFloor
- MT48 x11y10 fly
- MT48 x11y2 open blueDoor [BK 1->0]
- MT48 x7y1 move (auto: x9y1 redPotion, x8y1 redPotion, x7y1 redPotion)
- after: HP=17477 ATK=439 DEF=425 YK=6 BK=0 RK=0 G=1772 dmg=17418 door=43/9/7

### MT33

- before: HP=17477 ATK=439 DEF=425 YK=6 BK=0 RK=0 G=1772 dmg=17418 door=43/9/7
- MT33 x2y1 fly
- MT33 x3y7 open yellowDoor [YK 6->5]
- MT33 x2y7 kill slimeMan [HP 17477->17677, G 1772->1832] (auto: x2y7 slimeMan, x2y4 redPotion, x1y5 slimeMan) (+60G)
- after: HP=17677 ATK=439 DEF=425 YK=5 BK=0 RK=0 G=1832 dmg=17418 door=44/9/7

### MT3

- before: HP=17677 ATK=439 DEF=425 YK=5 BK=0 RK=0 G=1832 dmg=17418 door=44/9/7
- MT3 x10y11 fly
- MT3 x9y2 open yellowDoor [YK 5->4]
- MT3 x10y2 kill bat [HP 17677->17727, G 1832->1835] (auto: x10y2 bat, x11y1 redPotion) (+3G)
- after: HP=17727 ATK=439 DEF=425 YK=4 BK=0 RK=0 G=1835 dmg=17418 door=45/9/7

### MT8

- before: HP=17727 ATK=439 DEF=425 YK=4 BK=0 RK=0 G=1835 dmg=17418 door=45/9/7
- MT8 x1y2 fly
- MT8 x1y3 open yellowDoor [YK 4->3]
- MT8 x1y5 move (auto: x1y5 redPotion, x2y6 redSlime, x3y6 greenSlime, x4y6 redSlime)
- after: HP=17777 ATK=439 DEF=425 YK=3 BK=0 RK=0 G=1840 dmg=17418 door=46/9/7

### MT32

- before: HP=17777 ATK=439 DEF=425 YK=3 BK=0 RK=0 G=1840 dmg=17418 door=46/9/7
- MT32 x6y11 fly
- MT32 x9y8 open yellowDoor [YK 3->2]
- MT32 x10y7 move (auto: x10y7 yellowKey, x11y8 yellowKey, x11y7 blueKey)
- after: HP=17777 ATK=439 DEF=425 YK=4 BK=1 RK=0 G=1840 dmg=17418 door=47/9/7

### MT31

- before: HP=17777 ATK=439 DEF=425 YK=4 BK=1 RK=0 G=1840 dmg=17418 door=47/9/7
- MT31 x6y10 fly
- MT31 x3y4 open yellowDoor [YK 4->3]
- MT31 x4y4 move (auto: x4y4 blueKey)
- after: HP=17777 ATK=439 DEF=425 YK=3 BK=2 RK=0 G=1840 dmg=17418 door=48/9/7

### MT20

- before: HP=17777 ATK=439 DEF=425 YK=3 BK=2 RK=0 G=1840 dmg=17418 door=48/9/7
- MT20 x6y2 fly
- MT20 x11y9 open yellowDoor [YK 3->2]
- MT20 x10y8 kill bat (auto: x11y7 bat, x10y8 bat)
- MT20 x10y6 open blueDoor [BK 2->1]
- MT20 x10y4 move (auto: x10y4 redPotion, x11y5 yellowKey, x11y4 bluePotion)
- after: HP=18277 ATK=439 DEF=425 YK=3 BK=1 RK=0 G=1846 dmg=17418 door=49/10/7

### MT24

- before: HP=18277 ATK=439 DEF=425 YK=3 BK=1 RK=0 G=1846 dmg=17418 door=49/10/7
- MT24 x2y11 fly
- after: HP=18277 ATK=439 DEF=425 YK=3 BK=1 RK=0 G=1846 dmg=17418 door=49/10/7

### MT50

- before: HP=18277 ATK=439 DEF=425 YK=3 BK=1 RK=0 G=1846 dmg=17418 door=49/10/7
- MT50 x6y5 kill redKing [G 1846->2346] (+500G)
- after: HP=18277 ATK=439 DEF=425 YK=3 BK=1 RK=0 G=2346 dmg=17418 door=49/10/7
