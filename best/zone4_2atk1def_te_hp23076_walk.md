# 当前最优 Walk (zone4, auto ON)

## 说明

- 本 walk 由 Game 类 (`scripts/search/zone4_game_route.py`, auto_sweep, strict_live_model) 离线推导生成。
- auto 配置：battle=true, item=nopotion, wall=true。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone4_game_route.json --load-slot <100+> --target-click-only`（统一点击 verifier，1-4 区通用；3 区起按需 `--set-auto battle=true,item=nopotion,wall=true`）
- 源 JSON：`best/zone4_2atk1def_te_hp23076_walk.json`

## 摘要

- final: HP=23076 ATK=417 DEF=475 YK=5 BK=1 RK=0 G=906 dmg=14479 door=51/11/7 MT50 x6y5

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
- MT31 x1y7 open yellowDoor [YK 12->11]
- MT31 x2y9 kill ghostSkeleton (auto: x1y9 ghostSkeleton, x2y9 ghostSkeleton, x2y11 redPotion, x4y10 redKnight)
- MT31 x4y9 open yellowDoor [YK 11->10]
- MT31 x4y8 move (auto: x4y8 blueGem)
- after: HP=1467 ATK=241 DEF=291 YK=10 BK=3 RK=0 G=724 dmg=3828 door=18/2/1

### MT32

- before: HP=1467 ATK=241 DEF=291 YK=10 BK=3 RK=0 G=724 dmg=3828 door=18/2/1
- MT32 x6y11 fly
- MT32 x3y1 open blueDoor [BK 3->2]
- MT32 x1y1 move (auto: x1y1 blueGem, x2y2 redGem)
- after: HP=1467 ATK=245 DEF=295 YK=10 BK=2 RK=0 G=724 dmg=3828 door=18/3/1

### MT43

- before: HP=1467 ATK=245 DEF=295 YK=10 BK=2 RK=0 G=724 dmg=3828 door=18/3/1
- MT43 x1y2 fly
- MT43 x3y6 open yellowDoor [YK 10->9]
- MT43 x5y7 kill slimelord [HP 1467->2452, G 724->764] (+40G)
- MT43 x8y6 open yellowDoor [YK 9->8]
- MT43 x11y5 open yellowDoor [HP 2452->2702] (auto: x10y8 yellowKey, x11y7 redPotion)
- MT43 x9y1 kill whiteKing [HP 2702->2547, G 764->864] (+100G)
- MT43 x11y9 open yellowDoor [YK 8->7]
- after: HP=2547 ATK=245 DEF=345 YK=7 BK=3 RK=0 G=864 dmg=3998 door=22/3/1

### MT46

- before: HP=2547 ATK=245 DEF=345 YK=7 BK=3 RK=0 G=864 dmg=3998 door=22/3/1
- MT46 x11y2 fly
- MT46 x9y11 open yellowDoor [YK 7->6]
- MT46 x6y11 open blueDoor [BK 3->2]
- MT46 x4y11 kill redSlime (auto: x4y11 redSlime, x2y11 skeleton, x1y10 bigBat, x1y8 zombie, x1y6 soldier, x3y6 swordsman, x5y6 redKnight, x5y8 slimelord)
- MT46 x4y9 kill brownWizard [HP 2547->2522, G 1107->1187] (+80G)
- after: HP=2522 ATK=245 DEF=345 YK=6 BK=2 RK=0 G=1187 dmg=4023 door=23/4/1

### MT41

- before: HP=2522 ATK=245 DEF=345 YK=6 BK=2 RK=0 G=1187 dmg=4023 door=23/4/1
- MT41 x6y10 fly
- MT41 x6y10 魔法钥匙 bigKey
- MT41 x5y6 open blueDoor [BK 2->1]
- MT41 x2y2 kill redWizard [HP 2522->2987, ATK 245->250, YK 6->9, G 1187->1317] (+130G)
- MT41 x7y6 open blueDoor [BK 2->1]
- MT41 x9y5 kill brownWizard [HP 2987->3467, DEF 345->350, YK 9->12, BK 1->2, G 1317->1437] (+120G)
- MT41 x10y2 event redWizard
- MT41 x10y2 kill redWizard [HP 3467->3437, G 1437->1527] (+90G)
- after: HP=3437 ATK=250 DEF=350 YK=12 BK=2 RK=0 G=1527 dmg=4108 door=23/6/1

### MT40

- before: HP=3437 ATK=250 DEF=350 YK=12 BK=2 RK=0 G=1527 dmg=4108 door=23/6/1
- MT40 x6y2 fly
- after: HP=3437 ATK=250 DEF=350 YK=12 BK=2 RK=0 G=1527 dmg=4108 door=23/6/1

### MT41

- before: HP=3437 ATK=250 DEF=350 YK=12 BK=2 RK=0 G=1527 dmg=4108 door=23/6/1
- MT41 x6y2 fly
- after: HP=3437 ATK=250 DEF=350 YK=12 BK=2 RK=0 G=1527 dmg=4108 door=23/6/1

### MT42

- before: HP=3437 ATK=250 DEF=350 YK=12 BK=2 RK=0 G=1527 dmg=4108 door=23/6/1
- MT42 x5y11 fly
- MT42 x6y4 kill darkKnight [HP 3437->3117, RK 0->1, G 1527->1647] (+120G)
- after: HP=3117 ATK=250 DEF=350 YK=12 BK=2 RK=1 G=1647 dmg=4428 door=23/6/1

### MT46

- before: HP=3117 ATK=250 DEF=350 YK=12 BK=2 RK=1 G=1647 dmg=4428 door=23/6/1
- MT46 x11y2 fly
- MT46 x9y1 open blueDoor [BK 2->1]
- MT46 x6y1 shop def [DEF 350->370, G 1647->527]
- after: HP=3117 ATK=250 DEF=370 YK=12 BK=1 RK=1 G=527 dmg=4428 door=23/7/1

### MT36

- before: HP=3117 ATK=250 DEF=370 YK=12 BK=1 RK=1 G=527 dmg=4428 door=23/7/1
- MT36 x11y10 fly
- MT36 x9y1 kill redKnight (auto: x9y1 redKnight, x7y1 zombieKnight, x3y1 soldier, x1y5 redKnight, x1y3 slimeMan)
- after: HP=3117 ATK=250 DEF=370 YK=12 BK=1 RK=1 G=762 dmg=4428 door=23/7/1

### MT41

- before: HP=3117 ATK=250 DEF=370 YK=12 BK=1 RK=1 G=762 dmg=4428 door=23/7/1
- MT41 x6y2 fly
- MT41 x5y4 kill whiteKing [HP 3117->3037, G 762->862] (+100G)
- MT41 x7y4 kill whiteKing [HP 3037->2957, G 862->962] (+100G)
- after: HP=2957 ATK=250 DEF=370 YK=12 BK=1 RK=1 G=962 dmg=4588 door=23/7/1

### MT42

- before: HP=2957 ATK=250 DEF=370 YK=12 BK=1 RK=1 G=962 dmg=4588 door=23/7/1
- MT42 x5y11 fly
- MT42 x9y8 kill whiteKing [HP 2957->2877, G 962->1222] (+260G)
- MT42 x11y8 kill whiteKing [HP 2877->2797, G 1222->1322] (+100G)
- MT42 x11y4 kill redWizard [HP 2797->2787, G 1322->1412] (+90G)
- after: HP=2787 ATK=250 DEF=370 YK=12 BK=1 RK=1 G=1412 dmg=4758 door=23/7/1

### MT46

- before: HP=2787 ATK=250 DEF=370 YK=12 BK=1 RK=1 G=1412 dmg=4758 door=23/7/1
- MT46 x11y2 fly
- MT46 x6y1 shop def [DEF 370->390, G 1492->152]
- after: HP=2787 ATK=250 DEF=390 YK=12 BK=1 RK=1 G=152 dmg=4758 door=23/7/1

### MT41

- before: HP=2787 ATK=250 DEF=390 YK=12 BK=1 RK=1 G=152 dmg=4758 door=23/7/1
- MT41 x6y10 fly
- MT41 x3y5 kill brownWizard (auto: x2y7 redBat, x10y7 redBat, x3y5 brownWizard, x1y6 redBat, x11y6 redBat, x1y11 bluePotion, x11y11 bluePotion)
- after: HP=4787 ATK=250 DEF=390 YK=12 BK=1 RK=1 G=432 dmg=4758 door=23/7/1

### MT43

- before: HP=4787 ATK=250 DEF=390 YK=12 BK=1 RK=1 G=432 dmg=4758 door=23/7/1
- MT43 x1y2 fly
- MT43 x6y3 kill darkKnight [HP 4787->4627, G 432->822] (+390G)
- MT43 x7y4 kill darkKnight [HP 4627->4467, G 822->942] (+120G)
- after: HP=4467 ATK=250 DEF=390 YK=12 BK=1 RK=1 G=942 dmg=5078 door=23/7/1

### MT45

- before: HP=4467 ATK=250 DEF=390 YK=12 BK=1 RK=1 G=942 dmg=5078 door=23/7/1
- MT45 x2y1 fly
- MT45 x3y6 kill darkKnight [HP 4467->4307, DEF 390->400, YK 12->13, G 942->1542] (+600G)
- MT45 x3y4 kill darkKnight [HP 4307->4187, ATK 250->260, G 1542->1662] (+120G)
- after: HP=4187 ATK=260 DEF=400 YK=13 BK=1 RK=1 G=1662 dmg=5358 door=23/7/1

### MT46

- before: HP=4187 ATK=260 DEF=400 YK=13 BK=1 RK=1 G=1662 dmg=5358 door=23/7/1
- MT46 x11y2 fly
- MT46 x6y1 shop def [DEF 400->420, G 1712->132]
- after: HP=4187 ATK=260 DEF=420 YK=13 BK=1 RK=1 G=132 dmg=5358 door=23/7/1

### MT48

- before: HP=4187 ATK=260 DEF=420 YK=13 BK=1 RK=1 G=132 dmg=5358 door=23/7/1
- MT48 x11y10 fly
- MT48 x11y11 pass downFloor
- after: HP=4187 ATK=260 DEF=420 YK=13 BK=1 RK=1 G=262 dmg=5358 door=23/7/1

### MT47

- before: HP=4187 ATK=260 DEF=420 YK=13 BK=1 RK=1 G=262 dmg=5358 door=23/7/1
- MT47 x1y10 event redWizard
- MT47 x1y11 event redWizard
- MT47 x1y10 move [G 262->352] (auto: resource group on move) (auto: x1y11 redWizard)
- after: HP=4187 ATK=260 DEF=420 YK=13 BK=1 RK=1 G=352 dmg=5358 door=23/7/1

### MT42

- before: HP=4187 ATK=260 DEF=420 YK=13 BK=1 RK=1 G=352 dmg=5358 door=23/7/1
- MT42 x1y2 fly
- MT42 x3y2 kill slimelord [G 352->392] (auto: x3y2 slimelord) (+40G)
- after: HP=4187 ATK=260 DEF=420 YK=13 BK=1 RK=1 G=392 dmg=5358 door=23/7/1

### MT47

- before: HP=4187 ATK=260 DEF=420 YK=13 BK=1 RK=1 G=392 dmg=5358 door=23/7/1
- MT47 x11y10 fly
- MT47 x8y9 kill slimelord (auto: x8y9 slimelord, x5y11 brownWizard)
- after: HP=4187 ATK=260 DEF=420 YK=13 BK=1 RK=1 G=512 dmg=5358 door=23/7/1

### MT48

- before: HP=4187 ATK=260 DEF=420 YK=13 BK=1 RK=1 G=512 dmg=5358 door=23/7/1
- MT48 x11y10 fly
- MT48 x3y5 kill slimelord (auto: x10y7 brownWizard, x3y5 slimelord, x1y7 redBat, x1y9 brownWizard)
- MT48 x7y3 kill whiteKing [HP 4187->4157, G 762->862] (+100G)
- MT48 x9y3 kill whiteKing [HP 4157->4127, G 862->962] (+100G)
- MT48 x7y5 kill whiteKing [HP 4127->4097, G 962->1062] (+100G)
- after: HP=4097 ATK=260 DEF=420 YK=13 BK=1 RK=1 G=1062 dmg=5448 door=23/7/1

### MT45

- before: HP=4097 ATK=260 DEF=420 YK=13 BK=1 RK=1 G=1062 dmg=5448 door=23/7/1
- MT45 x10y1 fly
- MT45 x11y5 open yellowDoor [YK 13->12]
- MT45 x11y4 kill slimelord [G 1062->1102] (auto: x11y4 slimelord) (+40G)
- MT45 x9y3 trader hp2000 [HP 4097->6097, G 1102->102]
- after: HP=6097 ATK=260 DEF=420 YK=12 BK=1 RK=1 G=102 dmg=5448 door=24/7/1

### MT37

- before: HP=6097 ATK=260 DEF=420 YK=12 BK=1 RK=1 G=102 dmg=5448 door=24/7/1
- MT37 x2y1 fly
- after: HP=8897 ATK=260 DEF=420 YK=12 BK=1 RK=1 G=102 dmg=5448 door=24/7/1

### MT42

- before: HP=8897 ATK=260 DEF=420 YK=12 BK=1 RK=1 G=102 dmg=5448 door=24/7/1
- MT42 x5y11 fly
- MT42 x4y5 open yellowDoor [YK 12->11]
- MT42 x3y5 kill slimelord [G 102->142] (auto: x3y5 slimelord) (+40G)
- MT42 x1y6 open yellowDoor [YK 11->10]
- MT42 x3y8 kill redBat (auto: x3y8 redBat, x3y9 yellowKey, x2y9 yellowKey, x1y9 bluePotion, x1y10 redBat, x1y11 yellowKey, x2y11 yellowKey, x3y11 blueGem)
- after: HP=9897 ATK=260 DEF=425 YK=14 BK=1 RK=1 G=242 dmg=5448 door=26/7/1

### MT34

- before: HP=9897 ATK=260 DEF=425 YK=14 BK=1 RK=1 G=242 dmg=5448 door=26/7/1
- MT34 x6y10 fly
- MT34 x4y2 open yellowDoor [YK 14->13]
- MT34 x5y2 kill slimeMan [YK 13->14, G 242->337] (auto: x5y2 slimeMan, x6y1 yellowKey, x7y2 redKnight) (+95G)
- MT34 x8y2 open yellowDoor [YK 14->13]
- MT34 x9y1 move (auto: x9y1 yellowKey, x10y2 yellowKey, x10y1 yellowKey, x11y2 redPotion, x11y1 blueGem)
- MT34 x8y10 open yellowDoor [YK 16->15]
- MT34 x9y10 kill soldier [HP 10097->10297, ATK 260->264, YK 15->16, G 337->382] (auto: x9y10 soldier, x10y11 yellowKey, x11y10 redPotion, x11y11 redGem) (+45G)
- after: HP=10297 ATK=264 DEF=429 YK=16 BK=1 RK=1 G=382 dmg=5448 door=29/7/1

### MT47

- before: HP=10297 ATK=264 DEF=429 YK=16 BK=1 RK=1 G=382 dmg=5448 door=29/7/1
- MT47 x11y10 fly
- MT47 x3y11 open yellowDoor [YK 16->15]
- MT47 x2y6 open yellowDoor [YK 15->14]
- MT47 x3y5 kill redBat (auto: x3y5 redBat)
- MT47 x4y4 open yellowDoor [YK 14->13]
- MT47 x5y4 kill redWizard [ATK 264->269, DEF 429->434, YK 13->14, BK 1->2, G 432->602] (auto: x5y4 redWizard, x6y5 brownWizard, x5y7 blueKey, x5y8 redGem, x6y7 yellowKey, x6y8 blueGem) (+170G)
- after: HP=10297 ATK=269 DEF=434 YK=14 BK=2 RK=1 G=602 dmg=5448 door=32/7/1

### MT48

- before: HP=10297 ATK=269 DEF=434 YK=14 BK=2 RK=1 G=602 dmg=5448 door=32/7/1
- MT48 x11y10 fly
- MT48 x4y6 open yellowDoor [YK 14->13]
- MT48 x4y7 kill brownWizard [HP 10297->10547, ATK 269->274, G 602->682] (auto: x4y7 brownWizard, x3y8 redGem, x5y8 redPotion) (+80G)
- MT48 x4y9 open yellowDoor [YK 13->12]
- MT48 x4y10 kill darkKnight [HP 10547->11547, DEF 434->439, G 682->802] (auto: x4y10 darkKnight, x3y11 blueGem, x5y11 bluePotion) (+120G)
- after: HP=11547 ATK=274 DEF=439 YK=12 BK=2 RK=1 G=802 dmg=5448 door=34/7/1

### MT46

- before: HP=11547 ATK=274 DEF=439 YK=12 BK=2 RK=1 G=802 dmg=5448 door=34/7/1
- MT46 x11y10 fly
- MT46 x3y1 open yellowDoor [YK 12->11]
- MT46 x2y1 kill redWizard [HP 11547->11797, ATK 274->279, G 802->972] (auto: x2y1 redWizard, x1y2 redPotion, x1y3 redGem, x2y4 brownWizard) (+170G)
- after: HP=11797 ATK=279 DEF=439 YK=11 BK=2 RK=1 G=972 dmg=5448 door=35/7/1

### MT36

- before: HP=11797 ATK=279 DEF=439 YK=11 BK=2 RK=1 G=972 dmg=5448 door=35/7/1
- MT36 x11y10 fly
- MT36 x10y6 open yellowDoor [YK 11->10]
- MT36 x7y6 kill slimeMan (auto: x7y6 slimeMan, x6y5 ghostSkeleton, x5y6 slimeMan, x6y7 redKnight)
- after: HP=11797 ATK=279 DEF=439 YK=10 BK=2 RK=1 G=1132 dmg=5448 door=36/7/1

### MT47

- before: HP=11797 ATK=279 DEF=439 YK=10 BK=2 RK=1 G=1132 dmg=5448 door=36/7/1
- MT47 x11y10 fly
- MT47 x11y7 open yellowDoor [YK 10->9]
- MT47 x11y6 kill redBat [YK 9->10, G 1132->1262] (auto: x11y6 redBat, x9y5 brownWizard, x8y6 yellowKey) (+130G)
- after: HP=11797 ATK=279 DEF=439 YK=10 BK=2 RK=1 G=1262 dmg=5448 door=37/7/1

### MT32

- before: HP=11797 ATK=279 DEF=439 YK=10 BK=2 RK=1 G=1262 dmg=5448 door=37/7/1
- MT32 x10y1 fly
- MT32 x1y3 open yellowDoor [YK 10->9]
- MT32 x1y4 kill soldier [YK 9->10, G 1262->1367] (auto: x1y4 soldier, x2y5 yellowKey, x3y4 slimeMan, x4y5 slimeMan) (+105G)
- after: HP=11797 ATK=279 DEF=439 YK=10 BK=2 RK=1 G=1367 dmg=5448 door=38/7/1

### MT40

- before: HP=11797 ATK=279 DEF=439 YK=10 BK=2 RK=1 G=1367 dmg=5448 door=38/7/1
- MT40 x10y11 fly
- MT40 x8y11 open yellowDoor [YK 10->9]
- MT40 x4y11 open blueDoor [BK 2->1, G 1367->1427] (auto: x7y9 slimeMan, x5y9 slimeMan)
- MT40 x3y11 kill redKnight [HP 11797->12597, ATK 279->283, DEF 439->443, YK 9->10, G 1427->1492] (auto: x3y11 redKnight, x1y11 redGem, x2y9 yellowKey, x1y10 bluePotion, x1y9 blueGem) (+65G)
- after: HP=12597 ATK=283 DEF=443 YK=10 BK=1 RK=1 G=1492 dmg=5448 door=39/8/1

### MT33

- before: HP=12597 ATK=283 DEF=443 YK=10 BK=1 RK=1 G=1492 dmg=5448 door=39/8/1
- MT33 x2y1 fly
- MT33 x5y4 open yellowDoor [YK 10->9]
- MT33 x6y5 kill zombieKnight (auto: x6y5 zombieKnight, x4y6 swordsman, x6y7 ghostSkeleton)
- after: HP=12597 ATK=283 DEF=443 YK=9 BK=1 RK=1 G=1612 dmg=5448 door=40/8/1

### MT43

- before: HP=12597 ATK=283 DEF=443 YK=9 BK=1 RK=1 G=1612 dmg=5448 door=40/8/1
- MT43 x1y2 fly
- MT43 x8y10 open yellowDoor [YK 9->8]
- MT43 x6y9 kill darkKnight (auto: x6y9 darkKnight, x4y9 bluePotion, x4y10 bluePotion, x4y11 bluePotion)
- after: HP=15597 ATK=283 DEF=443 YK=8 BK=1 RK=1 G=1732 dmg=5448 door=41/8/1

### MT48

- before: HP=15597 ATK=283 DEF=443 YK=8 BK=1 RK=1 G=1732 dmg=5448 door=41/8/1
- MT48 x11y10 fly
- MT48 x9y5 kill whiteKing [HP 15597->15590, G 1732->1832] (+100G)
- MT48 x2y4 open blueDoor [BK 1->0]
- MT48 x2y3 kill redWizard [HP 15590->16590, G 1832->1922] (auto: x2y3 redWizard, x2y1 bluePotion) (+90G)
- after: HP=16590 ATK=283 DEF=443 YK=8 BK=0 RK=1 G=1922 dmg=5455 door=41/9/1

### MT46

- before: HP=16590 ATK=283 DEF=443 YK=8 BK=0 RK=1 G=1922 dmg=5455 door=41/9/1
- MT46 x11y10 fly
- MT46 x6y1 shop atk [ATK 283->293, G 1922->82]
- after: HP=16590 ATK=293 DEF=443 YK=8 BK=0 RK=1 G=82 dmg=5455 door=41/9/1

### MT2

- before: HP=16590 ATK=293 DEF=443 YK=8 BK=0 RK=1 G=82 dmg=5455 door=41/9/1
- MT2 x1y10 fly
- MT2 x11y7 trader specialTrader [ATK 293->302, DEF 443->456]
- after: HP=16590 ATK=302 DEF=456 YK=8 BK=0 RK=1 G=82 dmg=5455 door=41/9/1

### MT16

- before: HP=16590 ATK=302 DEF=456 YK=8 BK=0 RK=1 G=82 dmg=5455 door=41/9/1
- MT16 x6y2 fly
- MT16 x11y11 pass fakeWall2
- MT16 x11y11 老人 superPotion
- MT16 x10y11 使用 superPotion [HP 16590->22200]
- after: HP=22200 ATK=302 DEF=456 YK=8 BK=0 RK=1 G=82 dmg=5455 door=41/9/1

### MT35

- before: HP=22200 ATK=302 DEF=456 YK=8 BK=0 RK=1 G=82 dmg=5455 door=41/9/1
- MT35 x6y10 fly
- MT35 x6y7 kill magicDragon [HP 22200->18168, G 82->882] (+800G)
- MT35 x6y6 take snow [HP 18168->20568] (auto: x6y5 bluePotion, x5y5 bluePotion, x7y5 bluePotion)
- after: HP=20568 ATK=302 DEF=456 YK=8 BK=0 RK=1 G=882 dmg=9487 door=41/9/1

### MT13

- before: HP=20568 ATK=302 DEF=456 YK=8 BK=0 RK=1 G=882 dmg=9487 door=41/9/1
- MT13 x10y11 fly
- MT13 x6y10 open yellowDoor [YK 8->7]
- MT13 x6y10 move [ATK 302->402] (auto: resource group on move) (auto: x6y9 lava, x6y8 lava, x5y9 lava, x7y9 lava, x6y7 lava, x5y8 lava, x7y8 lava, x4y9 lava, x8y9 lava, x6y6 lava, x4y8 lava, x8y8 lava, x3y9 lava, x9y9 lava, x6y5 sword5, x4y7 lava, x3y8 lava, x8y7 lava, x9y8 lava, x2y9 lava, x10y9 lava, x3y7 lava, x2y8 lava, x9y7 lava, x10y8 lava, x1y9 lava, x11y9 lava, x3y6 lava, x2y7 lava, x1y8 lava, x9y6 lava, x10y7 lava, x11y8 lava, x3y5 lava, x2y6 lava, x1y7 lava, x9y5 lava, x10y6 lava, x11y7 lava, x3y4 lava, x2y5 lava, x1y6 lava, x9y4 lava, x10y5 lava, x11y6 lava, x3y3 lava, x2y4 lava, x1y5 lava, x9y3 lava, x10y4 lava, x11y5 lava, x3y2 lava, x2y3 lava, x4y3 lava, x1y4 lava, x9y2 lava, x8y3 lava, x10y3 lava, x11y4 lava, x3y1 lava, x2y2 lava, x4y2 lava, x1y3 lava, x9y1 lava, x8y2 lava, x10y2 lava, x11y3 lava, x2y1 lava, x4y1 lava, x1y2 lava, x5y2 lava, x8y1 lava, x10y1 lava, x7y2 lava, x11y2 lava, x1y1 lava, x5y1 lava, x6y2 lava, x7y1 lava, x11y1 lava, x6y1 lava)
- after: HP=20568 ATK=402 DEF=456 YK=7 BK=0 RK=1 G=882 dmg=9487 door=42/9/1

### MT25

- before: HP=20568 ATK=402 DEF=456 YK=7 BK=0 RK=1 G=882 dmg=9487 door=42/9/1
- MT25 x2y11 fly
- MT25 x6y10 open redDoor [RK 1->0]
- MT25 x6y6 kill blackMagician [HP 20568->15576, G 882->1882] (+1000G)
- after: HP=15576 ATK=402 DEF=456 YK=7 BK=0 RK=4 G=1882 dmg=14479 door=42/9/2

### MT26

- before: HP=15576 ATK=402 DEF=456 YK=7 BK=0 RK=4 G=1882 dmg=14479 door=42/9/2
- MT26 x2y11 fly
- MT26 x6y10 open redDoor [RK 4->3]
- MT26 x6y9 open redDoor [RK 3->2]
- MT26 x6y8 open redDoor [RK 2->1]
- MT26 x6y6 event princess
- after: HP=15576 ATK=402 DEF=456 YK=7 BK=0 RK=1 G=1882 dmg=14479 door=42/9/5

### MT31

- before: HP=15576 ATK=402 DEF=456 YK=7 BK=0 RK=1 G=1882 dmg=14479 door=42/9/5
- MT31 x6y2 fly
- MT31 x1y11 trader keyBundle31 [YK 7->11, BK 0->1, G 1882->882]
- after: HP=15576 ATK=402 DEF=456 YK=11 BK=1 RK=1 G=882 dmg=14479 door=42/9/5

### MT20

- before: HP=15576 ATK=402 DEF=456 YK=11 BK=1 RK=1 G=882 dmg=14479 door=42/9/5
- MT20 x6y2 fly
- MT20 x11y9 open yellowDoor [YK 11->10]
- MT20 x10y8 kill bat (auto: x11y7 bat, x10y8 bat)
- MT20 x10y6 open blueDoor [BK 1->0]
- after: HP=16076 ATK=402 DEF=456 YK=11 BK=0 RK=1 G=888 dmg=14479 door=43/10/5

### MT24

- before: HP=16076 ATK=402 DEF=456 YK=11 BK=0 RK=1 G=888 dmg=14479 door=43/10/5
- MT24 x2y11 fly
- MT24 x6y8 open redDoor [RK 1->0]
- after: HP=16076 ATK=402 DEF=456 YK=11 BK=0 RK=0 G=888 dmg=14479 door=43/10/6

### MT50

- before: HP=16076 ATK=402 DEF=456 YK=11 BK=0 RK=0 G=888 dmg=14479 door=43/10/6
- MT50 x6y5 event redKing
- after: HP=16076 ATK=402 DEF=456 YK=11 BK=0 RK=0 G=888 dmg=14479 door=43/10/6

### MT49

- before: HP=16076 ATK=402 DEF=456 YK=11 BK=0 RK=0 G=888 dmg=14479 door=43/10/6
- MT49 x5y6 下楼器 downFly
- MT49 x6y6 event redKing
- MT49 x6y4 kill whiteKing [G 888->988] (+100G)
- MT49 x5y3 kill whiteKing [G 988->1088] (+100G)
- MT49 x7y3 kill whiteKing [G 1088->1188] (+100G)
- MT49 x6y2 kill whiteKing [G 1188->1288] (+100G)
- MT49 x5y2 kill whiteKing [G 1288->1388] (+100G)
- MT49 x7y2 kill whiteKing [G 1388->1488] (+100G)
- MT49 x5y4 kill whiteKing [G 1488->1588] (+100G)
- MT49 x7y4 kill whiteKing [G 1588->1688] (+100G)
- MT49 x6y3 kill redKing [G 1688->2188] (+500G)
- after: HP=19076 ATK=417 DEF=471 YK=11 BK=0 RK=1 G=2188 dmg=14479 door=43/10/6

### MT48

- before: HP=19076 ATK=417 DEF=471 YK=11 BK=0 RK=1 G=2188 dmg=14479 door=43/10/6
- MT48 x1y10 fly
- MT48 x1y11 pass upFloor
- after: HP=19076 ATK=417 DEF=471 YK=11 BK=0 RK=1 G=2188 dmg=14479 door=43/10/6

### MT49

- before: HP=19076 ATK=417 DEF=471 YK=11 BK=0 RK=1 G=2188 dmg=14479 door=43/10/6
- MT49 x3y11 open redDoor [RK 1->0]
- MT49 x5y10 kill redWizard [G 2188->2278] (+90G)
- after: HP=19076 ATK=417 DEF=471 YK=11 BK=0 RK=0 G=2278 dmg=14479 door=43/10/7

### MT45

- before: HP=19076 ATK=417 DEF=471 YK=11 BK=0 RK=0 G=2278 dmg=14479 door=43/10/7
- MT45 x10y1 fly
- MT45 x11y9 open yellowDoor [YK 11->10]
- MT45 x11y11 move (auto: x11y11 bluePotion)
- after: HP=20076 ATK=417 DEF=471 YK=10 BK=0 RK=0 G=2278 dmg=14479 door=44/10/7

### MT46

- before: HP=20076 ATK=417 DEF=471 YK=10 BK=0 RK=0 G=2278 dmg=14479 door=44/10/7
- MT46 x11y2 fly
- MT46 x9y6 open yellowDoor [YK 10->9]
- MT46 x7y6 move (auto: x7y6 redPotion, x8y7 redWizard)
- after: HP=20326 ATK=417 DEF=471 YK=9 BK=0 RK=0 G=2368 dmg=14479 door=45/10/7

### MT38

- before: HP=20326 ATK=417 DEF=471 YK=9 BK=0 RK=0 G=2368 dmg=14479 door=45/10/7
- MT38 x10y1 fly
- MT38 x7y3 open yellowDoor [YK 9->8]
- MT38 x7y6 kill ghostSkeleton (auto: x7y6 ghostSkeleton, x7y7 swordsman, x6y8 redPotion, x5y8 blueGem)
- after: HP=20526 ATK=417 DEF=475 YK=8 BK=0 RK=0 G=2458 dmg=14479 door=46/10/7

### MT33

- before: HP=20526 ATK=417 DEF=475 YK=8 BK=0 RK=0 G=2458 dmg=14479 door=46/10/7
- MT33 x2y1 fly
- MT33 x3y7 open yellowDoor [YK 8->7]
- MT33 x2y7 kill slimeMan [HP 20526->20726, G 2458->2518] (auto: x2y7 slimeMan, x2y4 redPotion, x1y5 slimeMan) (+60G)
- after: HP=20726 ATK=417 DEF=475 YK=7 BK=0 RK=0 G=2518 dmg=14479 door=47/10/7

### MT3

- before: HP=20726 ATK=417 DEF=475 YK=7 BK=0 RK=0 G=2518 dmg=14479 door=47/10/7
- MT3 x10y11 fly
- MT3 x9y2 open yellowDoor [YK 7->6]
- MT3 x10y2 kill bat [HP 20726->20776, G 2518->2521] (auto: x10y2 bat, x11y1 redPotion) (+3G)
- after: HP=20776 ATK=417 DEF=475 YK=6 BK=0 RK=0 G=2521 dmg=14479 door=48/10/7

### MT8

- before: HP=20776 ATK=417 DEF=475 YK=6 BK=0 RK=0 G=2521 dmg=14479 door=48/10/7
- MT8 x1y2 fly
- MT8 x1y3 open yellowDoor [YK 6->5]
- MT8 x1y5 move (auto: x1y5 redPotion, x2y6 redSlime, x3y6 greenSlime, x4y6 redSlime)
- after: HP=20826 ATK=417 DEF=475 YK=5 BK=0 RK=0 G=2526 dmg=14479 door=49/10/7

### MT32

- before: HP=20826 ATK=417 DEF=475 YK=5 BK=0 RK=0 G=2526 dmg=14479 door=49/10/7
- MT32 x6y11 fly
- MT32 x9y8 open yellowDoor [YK 5->4]
- MT32 x10y7 move (auto: x10y7 yellowKey, x11y8 yellowKey, x11y7 blueKey)
- after: HP=20826 ATK=417 DEF=475 YK=6 BK=1 RK=0 G=2526 dmg=14479 door=50/10/7

### MT31

- before: HP=20826 ATK=417 DEF=475 YK=6 BK=1 RK=0 G=2526 dmg=14479 door=50/10/7
- MT31 x6y10 fly
- MT31 x3y4 open yellowDoor [YK 6->5]
- MT31 x4y4 move (auto: x4y4 blueKey)
- after: HP=20826 ATK=417 DEF=475 YK=5 BK=2 RK=0 G=2526 dmg=14479 door=51/10/7

### MT48

- before: HP=20826 ATK=417 DEF=475 YK=5 BK=2 RK=0 G=2526 dmg=14479 door=51/10/7
- MT48 x11y10 fly
- MT48 x11y2 open blueDoor [BK 2->1]
- after: HP=21576 ATK=417 DEF=475 YK=5 BK=1 RK=0 G=2526 dmg=14479 door=51/11/7

### MT46

- before: HP=21576 ATK=417 DEF=475 YK=5 BK=1 RK=0 G=2526 dmg=14479 door=51/11/7
- MT46 x11y10 fly
- MT46 x6y1 shop hp [HP 21576->23076, G 2526->406]
- after: HP=23076 ATK=417 DEF=475 YK=5 BK=1 RK=0 G=406 dmg=14479 door=51/11/7

### MT24

- before: HP=23076 ATK=417 DEF=475 YK=5 BK=1 RK=0 G=406 dmg=14479 door=51/11/7
- MT24 x2y11 fly
- after: HP=23076 ATK=417 DEF=475 YK=5 BK=1 RK=0 G=406 dmg=14479 door=51/11/7

### MT50

- before: HP=23076 ATK=417 DEF=475 YK=5 BK=1 RK=0 G=406 dmg=14479 door=51/11/7
- MT50 x6y5 kill redKing [G 406->906] (+500G)
- after: HP=23076 ATK=417 DEF=475 YK=5 BK=1 RK=0 G=906 dmg=14479 door=51/11/7
