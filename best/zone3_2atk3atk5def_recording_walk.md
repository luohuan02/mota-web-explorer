# 当前最优 Walk (zone3, auto ON)

## 说明

- 本 walk 由 Game 类 (`scripts/search/zone3_game_route.py`, auto_sweep, strict_live_model) 离线推导生成。
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone3_game_route.json --load-slot <100+> --target-click-only`（统一点击 verifier，1-4 区通用；3 区起按需 `--set-auto battle=true,item=nopotion,wall=true`）
- 源 JSON：`D:/claude/mota-web-explorer/best/zone3_2atk3atk5def_recording_walk.json`

## 摘要

- final: HP=13 ATK=166 DEF=214 YK=6 BK=1 RK=0 G=2954 dmg=4202 door=37/2/1 MT41 x6y2

## Walk

### MT31

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1320 dmg=0 door=0/0/0
- MT31 x6y2 设置自动：battle=true, item=nopotion, wall=true
- MT31 x6y8 kill zombieKnight [HP 1215->1107, G 1320->1350] (+30G)
- MT31 x6y9 kill zombieKnight [HP 1107->999, G 1350->1380] (+30G)
- MT31 x6y11 pass upFloor
- after: HP=999 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1380 dmg=216 door=0/0/0

### MT32

- before: HP=999 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1380 dmg=216 door=0/0/0
- MT32 x6y10 event yellowKnight [HP 999->579, G 1380->1480] (auto: +100G)
- MT32 x8y11 kill ghostSkeleton [HP 579->123, G 1480->1515] (+35G)
- MT32 x10y10 shop def [DEF 66->82, G 1515->1435]
- MT32 x10y10 shop def [DEF 82->98, G 1435->1295]
- MT32 x10y10 shop def [DEF 98->114, G 1295->1075]
- MT32 x10y10 shop def [DEF 114->130, G 1075->755]
- MT32 x10y10 shop def [DEF 130->146, G 755->315]
- after: HP=123 ATK=76 DEF=146 YK=5 BK=0 RK=0 G=315 dmg=1092 door=0/0/0

### MT19

- before: HP=123 ATK=76 DEF=146 YK=5 BK=0 RK=0 G=315 dmg=1092 door=0/0/0
- MT19 x6y10 fly
- MT19 x6y9 kill zombieKnight [BK 0->1, G 315->493] (auto: x8y8 zombieKnight, x7y6 rock, x4y3 zombieKnight, x8y3 zombieKnight, x11y5 blackSlime, x8y1 blueKey, x6y1 redPriest) (+178G)
- MT19 x1y1 pass downFloor
- after: HP=123 ATK=76 DEF=146 YK=5 BK=1 RK=0 G=493 dmg=1092 door=0/0/0

### MT18

- before: HP=123 ATK=76 DEF=146 YK=5 BK=1 RK=0 G=493 dmg=1092 door=0/0/0
- MT18 x9y7 move [G 493->655] (auto: x1y5 rock, x3y5 rock, x5y4 zombieKnight, x7y4 zombieKnight, x9y4 zombie, x10y7 rock)
- MT18 x11y8 open yellowDoor [YK 5->4]
- MT18 x11y8 move [DEF 146->148, YK 4->5, G 655->677] (auto: x11y9 redPriest, x10y10 yellowKey, x10y11 blueGem)
- MT18 x8y8 open yellowDoor [YK 5->4]
- MT18 x8y8 move [YK 4->5, G 677->709] (auto: x8y9 blackSlime, x7y9 blackSlime, x8y10 blackSlime, x7y10 blackSlime, x7y11 yellowKey)
- MT18 x4y8 open yellowDoor [YK 5->4]
- MT18 x4y8 move [YK 4->5, G 709->757] (auto: x4y9 bigBat, x4y10 bigBat, x5y9 bigBat, x5y10 bigBat, x5y11 yellowKey)
- MT18 x6y1 pass downFloor
- after: HP=123 ATK=76 DEF=148 YK=5 BK=1 RK=0 G=757 dmg=1092 door=3/0/0

### MT17

- before: HP=123 ATK=76 DEF=148 YK=5 BK=1 RK=0 G=757 dmg=1092 door=3/0/0
- MT17 x10y11 move [G 757->805] (auto: x5y3 zombieKnight, x5y7 zombie)
- MT17 x10y10 open yellowDoor [YK 5->4]
- MT17 x9y8 kill zombie [G 805->823] (+18G)
- MT17 x11y8 kill zombie [G 823->841] (+18G)
- MT17 x9y5 kill zombieKnight [G 841->871] (+30G)
- MT17 x11y5 kill zombieKnight [G 871->901] (+30G)
- MT17 x10y3 move [ATK 76->78, DEF 148->150, YK 4->6] (auto: x9y3 yellowKey, x11y3 yellowKey, x9y1 redGem, x11y1 blueGem)
- MT17 x10y2 take bluePotion [HP 123->523]
- MT17 x6y11 pass downFloor
- after: HP=523 ATK=78 DEF=150 YK=6 BK=1 RK=0 G=901 dmg=1092 door=4/0/0

### MT16

- before: HP=523 ATK=78 DEF=150 YK=6 BK=1 RK=0 G=901 dmg=1092 door=4/0/0
- MT16 x5y1 move [G 901->999] (auto: x6y6 zombieKnight, x5y3 zombie, x3y6 rock, x2y2 redPriest)
- MT16 x6y1 pass downFloor
- after: HP=523 ATK=78 DEF=150 YK=6 BK=1 RK=0 G=999 dmg=1092 door=4/0/0

### MT15

- before: HP=523 ATK=78 DEF=150 YK=6 BK=1 RK=0 G=999 dmg=1092 door=4/0/0
- MT15 x5y11 move [G 999->1051] (auto: x2y1 zombieKnight, x2y11 redPriest)
- MT15 x6y11 pass downFloor
- after: HP=523 ATK=78 DEF=150 YK=6 BK=1 RK=0 G=1051 dmg=1092 door=4/0/0

### MT14

- before: HP=523 ATK=78 DEF=150 YK=6 BK=1 RK=0 G=1051 dmg=1092 door=4/0/0
- MT14 x9y4 move [G 1051->1131] (auto: x3y9 redPriest, x6y5 rock, x10y4 zombieKnight)
- MT14 x10y3 open yellowDoor [YK 6->5]
- MT14 x10y2 move [YK 5->9] (auto: x10y1 yellowKey, x11y2 yellowKey, x9y1 yellowKey, x11y1 yellowKey)
- MT14 x11y11 pass downFloor
- after: HP=523 ATK=78 DEF=150 YK=9 BK=1 RK=0 G=1131 dmg=1092 door=5/0/0

### MT13

- before: HP=523 ATK=78 DEF=150 YK=9 BK=1 RK=0 G=1131 dmg=1092 door=5/0/0
- MT13 x1y11 pass downFloor
- after: HP=523 ATK=78 DEF=150 YK=9 BK=1 RK=0 G=1131 dmg=1092 door=5/0/0

### MT12

- before: HP=523 ATK=78 DEF=150 YK=9 BK=1 RK=0 G=1131 dmg=1092 door=5/0/0
- MT12 x10y11 move [G 1131->1191] (auto: x9y9 blackSlime, x11y5 bigBat, x10y3 zombie, x10y1 fakeWall, x5y3 redPriest)
- MT12 x11y11 pass downFloor
- after: HP=523 ATK=78 DEF=150 YK=9 BK=1 RK=0 G=1191 dmg=1092 door=5/0/0

### MT11

- before: HP=523 ATK=78 DEF=150 YK=9 BK=1 RK=0 G=1191 dmg=1092 door=5/0/0
- MT11 x6y10 move [G 1191->1213] (auto: x8y5 redPriest)
- MT11 x6y11 pass downFloor
- after: HP=523 ATK=78 DEF=150 YK=9 BK=1 RK=0 G=1213 dmg=1092 door=5/0/0

### MT10

- before: HP=523 ATK=78 DEF=150 YK=9 BK=1 RK=0 G=1213 dmg=1092 door=5/0/0
- MT10 x1y10 move [G 1213->1241] (auto: x3y6 skeleton, x2y7 skeletonSoldier, x10y7 skeletonSoldier, x11y6 skeleton)
- MT10 x1y11 pass downFloor
- after: HP=523 ATK=78 DEF=150 YK=9 BK=1 RK=0 G=1241 dmg=1092 door=5/0/0

### MT9

- before: HP=523 ATK=78 DEF=150 YK=9 BK=1 RK=0 G=1241 dmg=1092 door=5/0/0
- MT9 x6y1 pass downFloor
- after: HP=523 ATK=78 DEF=150 YK=9 BK=1 RK=0 G=1241 dmg=1092 door=5/0/0

### MT32

- before: HP=523 ATK=78 DEF=150 YK=9 BK=1 RK=0 G=1241 dmg=1092 door=5/0/0
- MT32 x6y11 fly
- MT32 x10y10 shop atk [ATK 78->86, G 1241->661]
- MT32 x11y1 pass upFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=661 dmg=1092 door=5/0/0

### MT33

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=661 dmg=1092 door=5/0/0
- MT33 x11y1 pass downFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=661 dmg=1092 door=5/0/0

### MT1

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=661 dmg=1092 door=5/0/0
- MT1 x2y1 fly
- MT1 x1y1 pass upFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=661 dmg=1092 door=5/0/0

### MT2

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=661 dmg=1092 door=5/0/0
- MT2 x1y11 pass upFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=661 dmg=1092 door=5/0/0

### MT3

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=661 dmg=1092 door=5/0/0
- MT3 x11y11 pass upFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=661 dmg=1092 door=5/0/0

### MT4

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=661 dmg=1092 door=5/0/0
- MT4 x1y11 pass upFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=661 dmg=1092 door=5/0/0

### MT5

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=661 dmg=1092 door=5/0/0
- MT5 x1y2 move [G 661->666] (auto: x3y5 bluePriest)
- MT5 x1y1 pass upFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=666 dmg=1092 door=5/0/0

### MT6

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=666 dmg=1092 door=5/0/0
- MT6 x11y10 move [G 666->674] (auto: x9y6 skeletonSoldier)
- MT6 x11y11 pass upFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=674 dmg=1092 door=5/0/0

### MT7

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=674 dmg=1092 door=5/0/0
- MT7 x1y1 pass upFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=674 dmg=1092 door=5/0/0

### MT8

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=674 dmg=1092 door=5/0/0
- MT8 x6y1 pass upFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=674 dmg=1092 door=5/0/0

### MT9

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=674 dmg=1092 door=5/0/0
- MT9 x1y11 pass upFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=674 dmg=1092 door=5/0/0

### MT10

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=674 dmg=1092 door=5/0/0
- MT10 x6y11 pass upFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=674 dmg=1092 door=5/0/0

### MT20

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=674 dmg=1092 door=5/0/0
- MT20 x6y10 fly
- MT20 x5y1 move [G 674->752] (auto: x8y11 redPriest, x2y10 rock, x10y10 rock)
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=752 dmg=1092 door=5/0/0

### MT33

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=752 dmg=1092 door=5/0/0
- MT33 x10y1 fly
- MT33 x11y1 pass downFloor
- after: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=752 dmg=1092 door=5/0/0

### MT32

- before: HP=523 ATK=86 DEF=150 YK=9 BK=1 RK=0 G=752 dmg=1092 door=5/0/0
- MT32 x10y10 shop atk [ATK 86->94, G 752->12]
- MT32 x11y1 pass upFloor
- after: HP=523 ATK=94 DEF=150 YK=9 BK=1 RK=0 G=12 dmg=1092 door=5/0/0

### MT33

- before: HP=523 ATK=94 DEF=150 YK=9 BK=1 RK=0 G=12 dmg=1092 door=5/0/0
- MT33 x8y2 open yellowDoor [YK 9->8]
- MT33 x11y3 take bluePotion [HP 523->1323]
- MT33 x9y5 kill ghostSkeleton [HP 1323->1233, G 12->47] (+35G)
- MT33 x11y5 kill ghostSkeleton [HP 1233->1143, G 47->82] (+35G)
- MT33 x11y7 kill soldier [HP 1143->793, G 82->127] (+45G)
- MT33 x9y7 kill soldier [HP 793->443, G 127->172] (+45G)
- MT33 x9y10 move [ATK 94->134] (auto: x10y10 sword3)
- MT33 x7y1 open yellowDoor [YK 8->7]
- MT33 x7y1 move [YK 7->8, G 172->232] (auto: x6y1 slimeMan, x4y1 zombieKnight, x6y3 yellowKey)
- MT33 x3y1 open yellowDoor [YK 8->7]
- MT33 x1y1 pass upFloor
- after: HP=443 ATK=134 DEF=150 YK=7 BK=1 RK=0 G=232 dmg=1972 door=8/0/0

### MT34

- before: HP=443 ATK=134 DEF=150 YK=7 BK=1 RK=0 G=232 dmg=1972 door=8/0/0
- MT34 x1y3 move [G 232->262] (auto: x2y3 slimeMan)
- MT34 x2y4 open yellowDoor [YK 7->6]
- MT34 x2y8 open yellowDoor [YK 6->5]
- MT34 x3y9 kill ghostSkeleton [HP 443->383, G 262->297] (+35G)
- MT34 x4y10 open yellowDoor [YK 5->4]
- MT34 x6y11 pass upFloor
- after: HP=383 ATK=134 DEF=150 YK=4 BK=1 RK=0 G=297 dmg=2032 door=11/0/0

### MT2

- before: HP=383 ATK=134 DEF=150 YK=4 BK=1 RK=0 G=297 dmg=2032 door=11/0/0
- MT2 x1y10 fly
- MT2 x3y1 open blueDoor [BK 1->0]
- MT2 x6y2 kill blueGuard [HP 383->263, G 297->347] (+50G)
- MT2 x8y2 kill blueGuard [HP 263->143, G 347->397] (+50G)
- MT2 x4y5 move [YK 4->7] (auto: x4y4 yellowKey, x3y5 yellowKey, x3y4 yellowKey)
- MT2 x11y4 event oldman [G 397->1397] (auto: +1000G)
- MT2 x10y11 event thief
- after: HP=143 ATK=134 DEF=150 YK=7 BK=0 RK=0 G=1397 dmg=2272 door=11/1/0

### MT35

- before: HP=143 ATK=134 DEF=150 YK=7 BK=0 RK=0 G=1397 dmg=2272 door=11/1/0
- MT35 x6y10 fly
- MT35 x11y1 pass upFloor
- after: HP=143 ATK=134 DEF=150 YK=7 BK=0 RK=0 G=1397 dmg=2272 door=11/1/0

### MT32

- before: HP=143 ATK=134 DEF=150 YK=7 BK=0 RK=0 G=1397 dmg=2272 door=11/1/0
- MT32 x10y1 fly
- MT32 x10y10 shop atk [ATK 134->142, G 1397->477]
- MT32 x5y3 open yellowDoor [YK 7->6]
- MT32 x4y4 move [YK 6->7, G 477->537] (auto: x3y4 slimeMan, x4y5 slimeMan, x2y5 yellowKey)
- MT32 x1y4 kill soldier [HP 143->43, G 537->582] (+45G)
- MT32 x1y3 open yellowDoor [YK 7->6]
- MT32 x1y2 move [ATK 142->146, DEF 150->154] (auto: x1y1 blueGem, x2y2 redGem)
- MT32 x5y11 pass downFloor
- after: HP=43 ATK=146 DEF=154 YK=6 BK=0 RK=0 G=582 dmg=2372 door=13/1/0

### MT33

- before: HP=43 ATK=146 DEF=154 YK=6 BK=0 RK=0 G=582 dmg=2372 door=13/1/0
- MT33 x10y1 fly
- MT33 x5y2 take redPotion [HP 43->243]
- MT33 x1y1 pass upFloor
- after: HP=243 ATK=146 DEF=154 YK=6 BK=0 RK=0 G=582 dmg=2372 door=13/1/0

### MT34

- before: HP=243 ATK=146 DEF=154 YK=6 BK=0 RK=0 G=582 dmg=2372 door=13/1/0
- MT34 x8y10 open yellowDoor [YK 6->5]
- MT34 x9y10 kill soldier [HP 243->151, ATK 146->150, YK 5->6, G 582->682] (auto: x10y11 yellowKey, x11y11 redGem, x1y10 swordsman) (+100G)
- MT34 x6y11 pass upFloor
- after: HP=151 ATK=150 DEF=154 YK=6 BK=0 RK=0 G=682 dmg=2464 door=14/1/0

### MT35

- before: HP=151 ATK=150 DEF=154 YK=6 BK=0 RK=0 G=682 dmg=2464 door=14/1/0
- MT35 x11y1 pass upFloor
- after: HP=151 ATK=150 DEF=154 YK=6 BK=0 RK=0 G=682 dmg=2464 door=14/1/0

### MT34

- before: HP=151 ATK=150 DEF=154 YK=6 BK=0 RK=0 G=682 dmg=2464 door=14/1/0
- MT34 x6y10 fly
- MT34 x1y11 take bluePotion [HP 151->951]
- after: HP=951 ATK=150 DEF=154 YK=6 BK=0 RK=0 G=682 dmg=2464 door=14/1/0

### MT36

- before: HP=951 ATK=150 DEF=154 YK=6 BK=0 RK=0 G=682 dmg=2464 door=14/1/0
- MT36 x11y2 fly
- MT36 x11y3 kill slimeMan [G 682->767] (auto: x11y5 swordsman) (+85G)
- MT36 x11y7 kill redKnight [HP 951->723, YK 6->7, G 767->917] (auto: x9y11 swordsman, x7y11 zombieKnight, x5y11 yellowKey) (+150G)
- MT36 x11y11 pass upFloor
- after: HP=723 ATK=150 DEF=154 YK=7 BK=0 RK=0 G=917 dmg=2692 door=14/1/0

### MT37

- before: HP=723 ATK=150 DEF=154 YK=7 BK=0 RK=0 G=917 dmg=2692 door=14/1/0
- MT37 x11y9 kill redKnight [HP 723->495, G 917->1037] (auto: x11y6 swordsman) (+120G)
- MT37 x11y3 kill redKnight [HP 495->267, G 1037->1102] (+65G)
- MT37 x9y1 kill soldier [HP 267->175, G 1102->1147] (+45G)
- MT37 x3y1 open yellowDoor [YK 7->6]
- MT37 x1y1 pass upFloor
- after: HP=175 ATK=150 DEF=154 YK=6 BK=0 RK=0 G=1147 dmg=3240 door=15/1/0

### MT34

- before: HP=175 ATK=150 DEF=154 YK=6 BK=0 RK=0 G=1147 dmg=3240 door=15/1/0
- MT34 x6y10 fly
- MT34 x3y1 take redPotion [HP 175->375]
- MT34 x5y5 open yellowDoor [YK 6->5]
- MT34 x5y5 move [G 1147->1148] (auto: x5y4 greenSlime)
- after: HP=375 ATK=150 DEF=154 YK=5 BK=0 RK=0 G=1148 dmg=3240 door=16/1/0

### MT31

- before: HP=375 ATK=150 DEF=154 YK=5 BK=0 RK=0 G=1148 dmg=3240 door=16/1/0
- MT31 x6y10 fly
- MT31 x2y6 kill ghostSkeleton [HP 375->349, G 1148->1183] (+35G)
- MT31 x1y5 open yellowDoor [YK 5->4]
- MT31 x1y3 move [YK 4->8, G 1183->1238] (auto: x1y2 swordsman, x3y2 yellowKey, x3y1 yellowKey, x4y2 yellowKey, x4y1 yellowKey)
- MT31 x3y4 open yellowDoor [YK 8->7]
- MT31 x3y4 move [BK 0->1] (auto: x4y4 blueKey)
- MT31 x6y11 pass upFloor
- after: HP=349 ATK=150 DEF=154 YK=7 BK=1 RK=0 G=1238 dmg=3266 door=18/1/0

### MT34

- before: HP=349 ATK=150 DEF=154 YK=7 BK=1 RK=0 G=1238 dmg=3266 door=18/1/0
- MT34 x2y1 fly
- MT34 x5y7 open yellowDoor [YK 7->6]
- MT34 x5y8 kill ghostSkeleton [HP 349->323, G 1238->1273] (+35G)
- MT34 x7y5 open yellowDoor [YK 6->5]
- MT34 x7y5 move [G 1273->1328] (auto: x7y4 swordsman)
- MT34 x7y7 open yellowDoor [YK 5->4]
- MT34 x7y7 move [G 1328->1330] (auto: x7y8 redSlime)
- MT34 x9y5 open yellowDoor [YK 4->3]
- MT34 x9y5 move [G 1330->1338] (auto: x9y4 blackSlime)
- MT34 x9y7 open yellowDoor [YK 3->2]
- MT34 x9y8 kill redKnight [HP 323->95, G 1338->1403] (+65G)
- MT34 x11y5 open yellowDoor [YK 2->1]
- MT34 x11y4 kill soldier [HP 95->3, G 1403->1448] (+45G)
- MT34 x11y7 open yellowDoor [YK 1->0]
- MT34 x11y7 move [G 1448->1451] (auto: x11y8 bat)
- MT34 x11y8 move [YK 0->4, RK 0->1] (auto: x3y5 yellowKey, x2y6 redKey, x3y7 yellowKey, x1y5 yellowKey, x1y7 yellowKey)
- MT34 x6y11 pass upFloor
- after: HP=3 ATK=150 DEF=154 YK=4 BK=1 RK=1 G=1451 dmg=3612 door=25/1/0

### MT35

- before: HP=3 ATK=150 DEF=154 YK=4 BK=1 RK=1 G=1451 dmg=3612 door=25/1/0
- MT35 x11y1 pass upFloor
- after: HP=3 ATK=150 DEF=154 YK=4 BK=1 RK=1 G=1451 dmg=3612 door=25/1/0

### MT36

- before: HP=3 ATK=150 DEF=154 YK=4 BK=1 RK=1 G=1451 dmg=3612 door=25/1/0
- MT36 x11y11 pass upFloor
- after: HP=3 ATK=150 DEF=154 YK=4 BK=1 RK=1 G=1451 dmg=3612 door=25/1/0

### MT37

- before: HP=3 ATK=150 DEF=154 YK=4 BK=1 RK=1 G=1451 dmg=3612 door=25/1/0
- MT37 x1y1 pass upFloor
- after: HP=3 ATK=150 DEF=154 YK=4 BK=1 RK=1 G=1451 dmg=3612 door=25/1/0

### MT38

- before: HP=3 ATK=150 DEF=154 YK=4 BK=1 RK=1 G=1451 dmg=3612 door=25/1/0
- MT38 x3y1 open redDoor [RK 1->0]
- MT38 x3y1 move [YK 4->5, G 1451->1511] (auto: x4y1 slimeMan, x6y2 yellowKey, x8y1 slimeMan)
- MT38 x5y2 trader yellowKey3 [YK 5->8, G 1511->1311]
- after: HP=3 ATK=150 DEF=154 YK=8 BK=1 RK=0 G=1311 dmg=3612 door=25/1/1

### MT34

- before: HP=3 ATK=150 DEF=154 YK=8 BK=1 RK=0 G=1311 dmg=3612 door=25/1/1
- MT34 x6y10 fly
- MT34 x11y10 take redPotion [HP 3->203]
- after: HP=203 ATK=150 DEF=154 YK=8 BK=1 RK=0 G=1311 dmg=3612 door=25/1/1

### MT38

- before: HP=203 ATK=150 DEF=154 YK=8 BK=1 RK=0 G=1311 dmg=3612 door=25/1/1
- MT38 x2y1 fly
- MT38 x7y3 open yellowDoor [YK 8->7]
- MT38 x7y6 kill ghostSkeleton [HP 203->177, G 1311->1401] (auto: x7y7 swordsman) (+90G)
- MT38 x6y8 take redPotion [HP 177->377, DEF 154->158] (auto: x5y8 blueGem)
- MT38 x9y1 open yellowDoor [YK 7->6]
- MT38 x11y1 pass upFloor
- after: HP=377 ATK=150 DEF=158 YK=6 BK=1 RK=0 G=1401 dmg=3638 door=27/1/1

### MT39

- before: HP=377 ATK=150 DEF=158 YK=6 BK=1 RK=0 G=1401 dmg=3638 door=27/1/1
- MT39 x11y1 pass downFloor
- after: HP=377 ATK=150 DEF=158 YK=6 BK=1 RK=0 G=1401 dmg=3638 door=27/1/1

### MT38

- before: HP=377 ATK=150 DEF=158 YK=6 BK=1 RK=0 G=1401 dmg=3638 door=27/1/1
- MT38 x11y3 open yellowDoor [YK 6->5]
- MT38 x11y6 kill ghostSkeleton [HP 377->355, G 1401->1436] (+35G)
- MT38 x11y8 open yellowDoor [YK 5->4]
- MT38 x11y9 kill ghostSkeleton [HP 355->333, YK 4->5, G 1436->1471] (auto: x9y9 yellowKey) (+35G)
- MT38 x9y11 kill soldier [HP 333->249, G 1471->1516] (+45G)
- MT38 x8y11 open yellowDoor [YK 5->4]
- MT38 x8y11 move [G 1516->1589] (auto: x7y11 zombie, x5y11 swordsman)
- MT38 x4y11 open yellowDoor [YK 4->3]
- MT38 x3y10 kill blueGuard [HP 249->205, G 1589->1639] (+50G)
- MT38 x1y10 kill blueGuard [HP 205->161, G 1639->1689] (+50G)
- MT38 x1y7 move [DEF 158->198, G 1689->1724] (auto: x2y7 shield3, x1y3 ghostSkeleton, x2y5 flower)
- MT38 x11y1 pass upFloor
- after: HP=161 ATK=150 DEF=198 YK=3 BK=1 RK=0 G=1724 dmg=3854 door=31/1/1

### MT39

- before: HP=161 ATK=150 DEF=198 YK=3 BK=1 RK=0 G=1724 dmg=3854 door=31/1/1
- MT39 x10y3 move [YK 3->4] (auto: x11y3 yellowKey)
- MT39 x10y4 open yellowDoor [YK 4->3]
- MT39 x9y5 move [ATK 150->154, G 1724->1789] (auto: x9y6 slimeMan, x11y7 ghostSkeleton, x11y6 redGem)
- MT39 x10y8 open yellowDoor [YK 3->2]
- MT39 x10y9 kill redKnight [HP 161->65, G 1789->1854] (+65G)
- MT39 x8y10 open yellowDoor [YK 2->1]
- MT39 x7y11 move [DEF 198->202, G 1854->1984] (auto: x6y11 slimeMan, x5y9 swordsman, x6y9 blueGem, x11y5 soldier)
- MT39 x4y10 open yellowDoor [YK 1->0]
- MT39 x3y10 move [YK 0->1, G 1984->2054] (auto: x3y9 ghostSkeleton, x2y10 ghostSkeleton, x3y11 yellowKey)
- MT39 x2y8 open blueDoor [BK 1->0]
- after: HP=65 ATK=154 DEF=202 YK=1 BK=0 RK=0 G=2054 dmg=3950 door=35/2/1

### MT32

- before: HP=65 ATK=154 DEF=202 YK=1 BK=0 RK=0 G=2054 dmg=3950 door=35/2/1
- MT32 x10y1 fly
- MT32 x3y10 kill blueGuard [G 2054->2104] (+50G)
- MT32 x1y10 kill blueGuard [G 2104->2154] (+50G)
- MT32 x2y9 move [YK 1->5, BK 0->1] (auto: x2y7 yellowKey, x1y7 yellowKey, x3y7 yellowKey, x4y8 blueKey, x4y7 yellowKey)
- after: HP=65 ATK=154 DEF=202 YK=5 BK=1 RK=0 G=2154 dmg=3950 door=35/2/1

### MT39

- before: HP=65 ATK=154 DEF=202 YK=5 BK=1 RK=0 G=2154 dmg=3950 door=35/2/1
- MT39 x11y2 fly
- MT39 x4y2 open yellowDoor [YK 5->4]
- MT39 x6y4 open yellowDoor [YK 4->3]
- MT39 x4y4 take centerFly3
- MT39 x11y11 pass upFloor
- after: HP=65 ATK=154 DEF=202 YK=3 BK=1 RK=0 G=2154 dmg=3950 door=37/2/1

### MT40

- before: HP=65 ATK=154 DEF=202 YK=3 BK=1 RK=0 G=2154 dmg=3950 door=37/2/1
- MT40 x9y11 move [G 2154->2254] (auto: x9y10 soldier, x10y9 swordsman)
- MT40 x9y9 take redPotion [HP 65->265]
- MT40 x2y1 中心飞行 centerFly
- MT40 x2y2 kill swordsman [G 2254->2659] (auto: x3y2 swordsman, x4y2 swordsman, x3y4 ghostSkeleton, x4y4 ghostSkeleton, x5y4 ghostSkeleton, x7y4 soldier, x8y4 soldier, x9y4 soldier) (+405G)
- MT40 x8y2 kill redKnight [HP 265->181, G 2659->2724] (+65G)
- MT40 x9y2 kill redKnight [HP 181->97, G 2724->2789] (+65G)
- MT40 x10y2 kill redKnight [HP 97->13, G 2789->2854] (+65G)
- MT40 x6y1 kill yellowKnight [G 2854->2954] (+100G)
- MT40 x5y1 move [ATK 154->166, DEF 202->214, YK 3->6] (auto: x7y4 blueGem, x8y4 blueGem, x9y4 blueGem, x4y2 yellowKey, x8y2 redGem, x3y2 yellowKey, x9y2 redGem, x2y2 yellowKey, x10y2 redGem)
- MT40 x6y1 pass upFloor
- after: HP=13 ATK=166 DEF=214 YK=6 BK=1 RK=0 G=2954 dmg=4202 door=37/2/1
