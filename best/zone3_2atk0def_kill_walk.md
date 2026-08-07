# 当前最优 Walk (zone3, auto ON)

## 说明

- 本 walk 由 Game 类 (`scripts/search/zone3_game_route.py`, auto_sweep, strict_live_model) 离线推导生成。
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone3_game_route.json --load-slot <100+> --target-click-only`（统一点击 verifier，1-4 区通用；3 区起按需 `--set-auto battle=true,item=nopotion,wall=true`）
- 源 JSON：`best/zone3_2atk0def_kill_walk.json`

## 摘要

- final: HP=609 ATK=166 DEF=174 YK=9 BK=0 RK=0 G=2285 dmg=8806 door=35/2/1 MT41 x6y2

## Walk

### MT20

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0
- MT20 x6y1 pass upFloor
- after: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0

### MT21

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0
- MT21 x6y11 pass upFloor
- after: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0

### MT22

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0
- MT22 x6y6 pass upFloor
- after: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0

### MT23

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0
- MT23 x11y1 pass upFloor
- after: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0

### MT24

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0
- MT24 x2y10 pass upFloor
- after: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0

### MT25

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0
- MT25 x1y11 pass upFloor
- after: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0

### MT26

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0
- MT26 x2y10 pass upFloor
- after: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0

### MT27

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0
- MT27 x11y11 pass upFloor
- after: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0

### MT28

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0
- MT28 x1y11 pass upFloor
- after: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0

### MT29

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0
- MT29 x6y2 event thief
- MT29 x6y11 pass upFloor
- after: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0

### MT30

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=0 door=0/0/0
- MT30 x3y5 kill blackSlime [G 1298->1306] (+8G)
- MT30 x4y5 kill redSlime [G 1306->1308] (+2G)
- MT30 x5y5 kill greenSlime [G 1308->1309] (+1G)
- MT30 x7y5 kill greenSlime [G 1309->1310] (+1G)
- MT30 x8y5 kill redSlime [G 1310->1312] (+2G)
- MT30 x9y5 kill blackSlime [G 1312->1320] (+8G)
- MT30 x6y1 pass upFloor
- after: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1320 dmg=0 door=0/0/0

### MT17

- before: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1320 dmg=0 door=0/0/0
- MT17 x6y2 fly
- MT17 x10y10 open yellowDoor [YK 5->4]
- MT17 x9y8 kill zombie [HP 1215->1196, G 1320->1338] (+18G)
- MT17 x11y8 kill zombie [HP 1196->1177, G 1338->1356] (+18G)
- MT17 x9y5 kill zombieKnight [HP 1177->1069, G 1356->1386] (+30G)
- MT17 x11y5 kill zombieKnight [HP 1069->961, G 1386->1416] (+30G)
- MT17 x10y2 take bluePotion [HP 961->1361, ATK 76->78, DEF 66->68, YK 4->6] (auto: x9y3 yellowKey, x11y3 yellowKey, x9y1 redGem, x11y1 blueGem)
- after: HP=1361 ATK=78 DEF=68 YK=6 BK=0 RK=0 G=1416 dmg=254 door=1/0/0

### MT31

- before: HP=1361 ATK=78 DEF=68 YK=6 BK=0 RK=0 G=1416 dmg=254 door=1/0/0
- MT31 x6y2 fly
- MT31 x6y8 kill zombieKnight [HP 1361->1257, G 1416->1446] (+30G)
- MT31 x6y9 kill zombieKnight [HP 1257->1153, G 1446->1476] (+30G)
- MT31 x6y11 pass upFloor
- after: HP=1153 ATK=78 DEF=68 YK=6 BK=0 RK=0 G=1476 dmg=462 door=1/0/0

### MT32

- before: HP=1153 ATK=78 DEF=68 YK=6 BK=0 RK=0 G=1476 dmg=462 door=1/0/0
- MT32 x6y10 eventbattle yellowKnight [HP 1153->743, G 1476->1576] (auto: +100G)
- MT32 x8y11 kill ghostSkeleton [HP 743->295, G 1576->1611] (+35G)
- MT32 x10y10 shop atk [ATK 78->86, G 1611->1531]
- MT32 x10y10 shop atk [ATK 86->94, G 1531->1391]
- MT32 x10y10 shop def [DEF 68->84, G 1391->1171]
- MT32 x10y10 shop def [DEF 84->100, G 1171->851]
- MT32 x10y10 shop def [DEF 100->116, G 851->411]
- MT32 x11y1 pass upFloor
- after: HP=295 ATK=94 DEF=116 YK=6 BK=0 RK=0 G=411 dmg=1320 door=1/0/0

### MT33

- before: HP=295 ATK=94 DEF=116 YK=6 BK=0 RK=0 G=411 dmg=1320 door=1/0/0
- MT33 x7y1 open yellowDoor [YK 6->5]
- MT33 x6y1 kill slimeMan [HP 295->199, YK 5->6, G 411->441] (auto: x6y3 yellowKey) (+30G)
- MT33 x5y2 take redPotion [HP 199->399]
- MT33 x8y2 open yellowDoor [YK 6->5]
- MT33 x11y3 take bluePotion [HP 399->1199]
- after: HP=1199 ATK=94 DEF=116 YK=5 BK=0 RK=0 G=441 dmg=1416 door=3/0/0

### MT14

- before: HP=1199 ATK=94 DEF=116 YK=5 BK=0 RK=0 G=441 dmg=1416 door=3/0/0
- MT14 x6y10 fly
- MT14 x6y5 kill rock [G 441->491] (auto: x3y9 redPriest) (+50G)
- MT14 x10y4 kill zombieKnight [HP 1199->1195, G 491->521] (+30G)
- MT14 x10y3 open yellowDoor [YK 5->4]
- MT14 x10y1 move [YK 4->8] (auto: x10y1 yellowKey, x11y2 yellowKey, x9y1 yellowKey, x11y1 yellowKey)
- after: HP=1195 ATK=94 DEF=116 YK=8 BK=0 RK=0 G=521 dmg=1420 door=4/0/0

### MT15

- before: HP=1195 ATK=94 DEF=116 YK=8 BK=0 RK=0 G=521 dmg=1420 door=4/0/0
- MT15 x6y10 fly
- after: HP=1195 ATK=94 DEF=116 YK=8 BK=0 RK=0 G=521 dmg=1420 door=4/0/0

### MT20

- before: HP=1195 ATK=94 DEF=116 YK=8 BK=0 RK=0 G=521 dmg=1420 door=4/0/0
- MT20 x6y10 fly
- MT20 x8y11 kill redPriest [G 521->599] (auto: x10y10 rock, x2y10 rock) (+78G)
- MT20 x11y11 take redPotion [HP 1195->1295]
- after: HP=1295 ATK=94 DEF=116 YK=8 BK=0 RK=0 G=599 dmg=1420 door=4/0/0

### MT18

- before: HP=1295 ATK=94 DEF=116 YK=8 BK=0 RK=0 G=599 dmg=1420 door=4/0/0
- MT18 x1y2 fly
- MT18 x10y7 kill rock [G 599->701] (auto: x1y5 rock, x3y5 rock, x9y4 zombie) (+102G)
- MT18 x11y8 open yellowDoor [YK 8->7]
- MT18 x11y9 kill redPriest [DEF 116->118, YK 7->8, G 701->723] (auto: x10y10 yellowKey, x10y11 blueGem) (+22G)
- MT18 x11y11 take redPotion [HP 1295->1395]
- after: HP=1395 ATK=94 DEF=118 YK=8 BK=0 RK=0 G=723 dmg=1420 door=5/0/0

### MT19

- before: HP=1395 ATK=94 DEF=118 YK=8 BK=0 RK=0 G=723 dmg=1420 door=5/0/0
- MT19 x1y2 fly
- MT19 x4y3 kill zombieKnight [HP 1395->1393, BK 0->1, G 723->811] (auto: x7y6 rock, x11y5 blackSlime, x6y1 redPriest, x8y1 blueKey) (+88G)
- after: HP=1393 ATK=94 DEF=118 YK=8 BK=1 RK=0 G=811 dmg=1422 door=5/0/0

### MT14

- before: HP=1393 ATK=94 DEF=118 YK=8 BK=1 RK=0 G=811 dmg=1422 door=5/0/0
- MT14 x6y10 fly
- after: HP=1393 ATK=94 DEF=118 YK=8 BK=1 RK=0 G=811 dmg=1422 door=5/0/0

### MT18

- before: HP=1393 ATK=94 DEF=118 YK=8 BK=1 RK=0 G=811 dmg=1422 door=5/0/0
- MT18 x6y2 fly
- after: HP=1393 ATK=94 DEF=118 YK=8 BK=1 RK=0 G=811 dmg=1422 door=5/0/0

### MT19

- before: HP=1393 ATK=94 DEF=118 YK=8 BK=1 RK=0 G=811 dmg=1422 door=5/0/0
- MT19 x1y2 fly
- after: HP=1393 ATK=94 DEF=118 YK=8 BK=1 RK=0 G=811 dmg=1422 door=5/0/0

### MT20

- before: HP=1393 ATK=94 DEF=118 YK=8 BK=1 RK=0 G=811 dmg=1422 door=5/0/0
- MT20 x6y10 fly
- after: HP=1393 ATK=94 DEF=118 YK=8 BK=1 RK=0 G=811 dmg=1422 door=5/0/0

### MT18

- before: HP=1393 ATK=94 DEF=118 YK=8 BK=1 RK=0 G=811 dmg=1422 door=5/0/0
- MT18 x1y2 fly
- after: HP=1393 ATK=94 DEF=118 YK=8 BK=1 RK=0 G=811 dmg=1422 door=5/0/0

### MT32

- before: HP=1393 ATK=94 DEF=118 YK=8 BK=1 RK=0 G=811 dmg=1422 door=5/0/0
- MT32 x6y11 fly
- MT32 x10y10 shop atk [ATK 94->102, G 811->231]
- after: HP=1393 ATK=102 DEF=118 YK=8 BK=1 RK=0 G=231 dmg=1422 door=5/0/0

### MT33

- before: HP=1393 ATK=102 DEF=118 YK=8 BK=1 RK=0 G=231 dmg=1422 door=5/0/0
- MT33 x10y1 fly
- MT33 x10y5 event swordTrap
- MT33 x9y5 kill ghostSkeleton [HP 1393->1207, G 231->266] (+35G)
- MT33 x11y5 kill ghostSkeleton [HP 1207->1021, G 266->301] (+35G)
- MT33 x9y7 kill soldier [HP 1021->611, G 301->346] (+45G)
- MT33 x11y7 kill soldier [HP 611->201, G 346->391] (+45G)
- MT33 x10y10 move [ATK 102->142] (auto: x10y10 sword3)
- after: HP=201 ATK=142 DEF=118 YK=8 BK=1 RK=0 G=391 dmg=2614 door=5/0/0

### MT31

- before: HP=201 ATK=142 DEF=118 YK=8 BK=1 RK=0 G=391 dmg=2614 door=5/0/0
- MT31 x6y10 fly
- after: HP=201 ATK=142 DEF=118 YK=8 BK=1 RK=0 G=391 dmg=2614 door=5/0/0

### MT33

- before: HP=201 ATK=142 DEF=118 YK=8 BK=1 RK=0 G=391 dmg=2614 door=5/0/0
- MT33 x10y1 fly
- MT33 x4y1 kill zombieKnight [HP 201->199, G 391->421] (+30G)
- MT33 x3y1 open yellowDoor [YK 8->7]
- MT33 x1y1 pass upFloor
- after: HP=199 ATK=142 DEF=118 YK=7 BK=1 RK=0 G=421 dmg=2616 door=6/0/0

### MT34

- before: HP=199 ATK=142 DEF=118 YK=7 BK=1 RK=0 G=421 dmg=2616 door=6/0/0
- MT34 x3y1 take redPotion [HP 199->399]
- after: HP=399 ATK=142 DEF=118 YK=7 BK=1 RK=0 G=421 dmg=2616 door=6/0/0

### MT32

- before: HP=399 ATK=142 DEF=118 YK=7 BK=1 RK=0 G=421 dmg=2616 door=6/0/0
- MT32 x10y1 fly
- MT32 x7y3 open yellowDoor [YK 7->6]
- MT32 x8y4 kill ghostSkeleton [HP 399->337, G 421->456] (+35G)
- MT32 x9y5 open yellowDoor [YK 6->5]
- MT32 x11y4 take bluePotion [HP 337->1137, YK 5->7] (auto: x10y4 yellowKey, x11y5 yellowKey)
- after: HP=1137 ATK=142 DEF=118 YK=7 BK=1 RK=0 G=456 dmg=2678 door=8/0/0

### MT2

- before: HP=1137 ATK=142 DEF=118 YK=7 BK=1 RK=0 G=456 dmg=2678 door=8/0/0
- MT2 x1y10 fly
- MT2 x3y1 open blueDoor [BK 1->0]
- MT2 x6y2 kill blueGuard [HP 1137->951, G 456->506] (+50G)
- MT2 x8y2 kill blueGuard [HP 951->765, G 506->556] (+50G)
- MT2 x3y5 move [YK 7->10] (auto: x4y4 yellowKey, x3y5 yellowKey, x3y4 yellowKey)
- MT2 x11y4 reward oldman [G 556->1556] (auto: +1000G)
- MT2 x3y11 take bluePotion [HP 765->965]
- after: HP=965 ATK=142 DEF=118 YK=10 BK=0 RK=0 G=1556 dmg=3050 door=8/1/0

### MT31

- before: HP=965 ATK=142 DEF=118 YK=10 BK=0 RK=0 G=1556 dmg=3050 door=8/1/0
- MT31 x6y2 fly
- MT31 x10y6 kill ghostSkeleton [HP 965->903, G 1556->1591] (+35G)
- MT31 x11y7 open yellowDoor [YK 10->9]
- MT31 x10y9 kill slimeMan [HP 903->859, YK 9->13, G 1591->1621] (auto: x9y10 yellowKey, x8y10 yellowKey, x9y11 yellowKey, x8y11 yellowKey) (+30G)
- after: HP=859 ATK=142 DEF=118 YK=13 BK=0 RK=0 G=1621 dmg=3156 door=9/1/0

### MT32

- before: HP=859 ATK=142 DEF=118 YK=13 BK=0 RK=0 G=1621 dmg=3156 door=9/1/0
- MT32 x6y11 fly
- MT32 x10y10 shop hp [HP 859->1759, G 1621->881]
- after: HP=1759 ATK=142 DEF=118 YK=13 BK=0 RK=0 G=881 dmg=3156 door=9/1/0

### MT34

- before: HP=1759 ATK=142 DEF=118 YK=13 BK=0 RK=0 G=881 dmg=3156 door=9/1/0
- MT34 x2y1 fly
- MT34 x2y3 kill slimeMan [HP 1759->1715, G 881->911] (+30G)
- MT34 x2y4 open yellowDoor [YK 13->12]
- MT34 x5y5 open yellowDoor [YK 12->11]
- MT34 x5y7 open yellowDoor [YK 11->10]
- MT34 x5y8 kill ghostSkeleton [HP 1715->1653, G 911->947] (auto: x5y4 greenSlime) (+36G)
- MT34 x7y5 open yellowDoor [YK 10->9]
- MT34 x7y4 kill swordsman [HP 1653->1091, G 947->1002] (+55G)
- MT34 x7y7 open yellowDoor [YK 9->8]
- MT34 x9y5 open yellowDoor [YK 8->7, G 1002->1004] (auto: x7y8 redSlime)
- MT34 x9y7 open yellowDoor [YK 7->6]
- MT34 x11y5 open yellowDoor [YK 6->5, G 1004->1012] (auto: x9y4 blackSlime)
- MT34 x11y4 kill soldier [HP 1091->927, G 1012->1057] (+45G)
- MT34 x11y7 open yellowDoor [YK 5->4]
- MT34 x9y8 kill redKnight [HP 927->479, G 1057->1125] (auto: x11y8 bat) (+68G)
- MT34 x3y5 move [YK 4->8, RK 0->1] (auto: x3y5 yellowKey, x2y6 redKey, x3y7 yellowKey, x1y5 yellowKey, x1y7 yellowKey)
- after: HP=479 ATK=142 DEF=118 YK=8 BK=0 RK=1 G=1125 dmg=4436 door=18/1/0

### MT2

- before: HP=479 ATK=142 DEF=118 YK=8 BK=0 RK=1 G=1125 dmg=4436 door=18/1/0
- MT2 x1y10 fly
- MT2 x10y11 event thief
- after: HP=479 ATK=142 DEF=118 YK=8 BK=0 RK=1 G=1125 dmg=4436 door=18/1/0

### MT34

- before: HP=479 ATK=142 DEF=118 YK=8 BK=0 RK=1 G=1125 dmg=4436 door=18/1/0
- MT34 x2y1 fly
- MT34 x2y8 open yellowDoor [YK 8->7]
- MT34 x3y9 kill ghostSkeleton [HP 479->417, G 1125->1160] (+35G)
- MT34 x4y10 open yellowDoor [YK 7->6]
- MT34 x6y11 pass upFloor
- after: HP=417 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1160 dmg=4498 door=20/1/0

### MT35

- before: HP=417 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1160 dmg=4498 door=20/1/0
- MT35 x5y10 event thief
- MT35 x11y1 pass upFloor
- after: HP=417 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1160 dmg=4498 door=20/1/0

### MT34

- before: HP=417 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1160 dmg=4498 door=20/1/0
- MT34 x6y10 fly
- MT34 x2y11 kill soldier [HP 417->253, G 1160->1205] (+45G)
- MT34 x1y11 take bluePotion [HP 253->1053]
- after: HP=1053 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1205 dmg=4662 door=20/1/0

### MT36

- before: HP=1053 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1205 dmg=4662 door=20/1/0
- MT36 x11y2 fly
- MT36 x11y3 kill slimeMan [HP 1053->1009, G 1205->1235] (+30G)
- MT36 x11y5 kill swordsman [HP 1009->447, G 1235->1290] (+55G)
- after: HP=447 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1290 dmg=5268 door=20/1/0

### MT2

- before: HP=447 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1290 dmg=5268 door=20/1/0
- MT2 x1y10 fly
- MT2 x4y10 take bluePotion [HP 447->647]
- MT2 x3y10 take bluePotion [HP 647->847]
- after: HP=847 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1290 dmg=5268 door=20/1/0

### MT36

- before: HP=847 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1290 dmg=5268 door=20/1/0
- MT36 x11y2 fly
- MT36 x11y7 kill redKnight [HP 847->399, G 1290->1355] (+65G)
- MT36 x11y11 pass upFloor
- after: HP=399 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1355 dmg=5716 door=20/1/0

### MT2

- before: HP=399 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1355 dmg=5716 door=20/1/0
- MT2 x1y10 fly
- after: HP=399 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1355 dmg=5716 door=20/1/0

### MT32

- before: HP=399 ATK=142 DEF=118 YK=6 BK=0 RK=1 G=1355 dmg=5716 door=20/1/0
- MT32 x6y11 fly
- MT32 x10y10 shop atk [ATK 142->150, G 1355->435]
- after: HP=399 ATK=150 DEF=118 YK=6 BK=0 RK=1 G=435 dmg=5716 door=20/1/0

### MT36

- before: HP=399 ATK=150 DEF=118 YK=6 BK=0 RK=1 G=435 dmg=5716 door=20/1/0
- MT36 x11y2 fly
- MT36 x9y11 kill swordsman [G 435->490] (+55G)
- MT36 x7y11 kill zombieKnight [HP 399->397, YK 6->7, G 490->520] (auto: x5y11 yellowKey) (+30G)
- after: HP=397 ATK=150 DEF=118 YK=7 BK=0 RK=1 G=520 dmg=5718 door=20/1/0

### MT19

- before: HP=397 ATK=150 DEF=118 YK=7 BK=0 RK=1 G=520 dmg=5718 door=20/1/0
- MT19 x6y10 fly
- MT19 x4y1 take redPotion [HP 397->497]
- after: HP=497 ATK=150 DEF=118 YK=7 BK=0 RK=1 G=520 dmg=5718 door=20/1/0

### MT36

- before: HP=497 ATK=150 DEF=118 YK=7 BK=0 RK=1 G=520 dmg=5718 door=20/1/0
- MT36 x11y2 fly
- MT36 x3y11 kill soldier [HP 497->333, G 520->620] (auto: x1y9 swordsman) (+100G)
- MT36 x1y11 take bluePotion [HP 333->1133]
- after: HP=1133 ATK=150 DEF=118 YK=7 BK=0 RK=1 G=620 dmg=5882 door=20/1/0

### MT14

- before: HP=1133 ATK=150 DEF=118 YK=7 BK=0 RK=1 G=620 dmg=5882 door=20/1/0
- MT14 x6y10 fly
- after: HP=1133 ATK=150 DEF=118 YK=7 BK=0 RK=1 G=620 dmg=5882 door=20/1/0

### MT15

- before: HP=1133 ATK=150 DEF=118 YK=7 BK=0 RK=1 G=620 dmg=5882 door=20/1/0
- MT15 x6y10 fly
- after: HP=1133 ATK=150 DEF=118 YK=7 BK=0 RK=1 G=620 dmg=5882 door=20/1/0

### MT14

- before: HP=1133 ATK=150 DEF=118 YK=7 BK=0 RK=1 G=620 dmg=5882 door=20/1/0
- MT14 x6y10 fly
- after: HP=1133 ATK=150 DEF=118 YK=7 BK=0 RK=1 G=620 dmg=5882 door=20/1/0

### MT37

- before: HP=1133 ATK=150 DEF=118 YK=7 BK=0 RK=1 G=620 dmg=5882 door=20/1/0
- MT37 x11y10 fly
- MT37 x11y9 kill redKnight [HP 1133->797, G 620->740] (auto: x11y6 swordsman) (+120G)
- MT37 x11y3 kill redKnight [HP 797->461, G 740->805] (+65G)
- MT37 x11y1 take bluePotion [HP 461->1261]
- MT37 x9y1 kill soldier [HP 1261->1097, G 805->850] (+45G)
- MT37 x3y1 open yellowDoor [YK 7->6]
- MT37 x1y1 pass upFloor
- after: HP=1097 ATK=150 DEF=118 YK=6 BK=0 RK=1 G=850 dmg=6718 door=21/1/0

### MT31

- before: HP=1097 ATK=150 DEF=118 YK=6 BK=0 RK=1 G=850 dmg=6718 door=21/1/0
- MT31 x6y10 fly
- MT31 x2y6 kill ghostSkeleton [HP 1097->1035, G 850->885] (+35G)
- MT31 x1y5 open yellowDoor [YK 6->5]
- MT31 x3y4 open yellowDoor [YK 5->8, G 885->940] (auto: x1y2 swordsman, x3y2 yellowKey, x3y1 yellowKey, x4y2 yellowKey, x4y1 yellowKey)
- MT31 x4y4 move [BK 0->1] (auto: x4y4 blueKey)
- after: HP=1035 ATK=150 DEF=118 YK=8 BK=1 RK=1 G=940 dmg=6780 door=23/1/0

### MT38

- before: HP=1035 ATK=150 DEF=118 YK=8 BK=1 RK=1 G=940 dmg=6780 door=23/1/0
- MT38 x2y1 fly
- MT38 x3y1 open redDoor [RK 1->0]
- MT38 x4y1 kill slimeMan [HP 1035->991, YK 8->9, G 940->970] (auto: x6y2 yellowKey) (+30G)
- MT38 x5y2 trader yellowKey3 [YK 9->12, G 970->770]
- MT38 x8y1 kill slimeMan [HP 991->947, G 770->800] (+30G)
- MT38 x9y1 open yellowDoor [YK 12->11]
- MT38 x11y3 open yellowDoor [YK 11->10]
- MT38 x11y6 kill ghostSkeleton [HP 947->885, G 800->835] (+35G)
- MT38 x11y8 open yellowDoor [YK 10->9]
- MT38 x11y9 kill ghostSkeleton [HP 885->823, YK 9->10, G 835->870] (auto: x9y9 yellowKey) (+35G)
- MT38 x9y11 kill soldier [HP 823->659, G 870->915] (+45G)
- MT38 x8y11 open yellowDoor [YK 10->9]
- MT38 x7y11 kill zombie [G 915->988] (auto: x5y11 swordsman) (+73G)
- MT38 x4y11 open yellowDoor [YK 9->8]
- MT38 x1y10 kill blueGuard [HP 659->535, G 988->1038] (+50G)
- MT38 x11y11 take bluePotion [HP 535->1335]
- MT38 x3y10 kill blueGuard [HP 1335->1211, G 1038->1088] (+50G)
- MT38 x2y7 move [DEF 118->158] (auto: x2y7 shield3)
- MT38 x11y1 pass upFloor
- after: HP=1211 ATK=150 DEF=158 YK=8 BK=1 RK=0 G=1088 dmg=7404 door=28/1/1

### MT39

- before: HP=1211 ATK=150 DEF=158 YK=8 BK=1 RK=0 G=1088 dmg=7404 door=28/1/1
- MT39 x11y3 take yellowKey [YK 8->9]
- MT39 x10y4 open yellowDoor [YK 9->8]
- MT39 x9y6 kill slimeMan [G 1088->1118] (+30G)
- MT39 x11y7 kill ghostSkeleton [HP 1211->1189, ATK 150->154, G 1118->1153] (auto: x11y6 redGem) (+35G)
- after: HP=1189 ATK=154 DEF=158 YK=8 BK=1 RK=0 G=1153 dmg=7426 door=29/1/1

### MT38

- before: HP=1189 ATK=154 DEF=158 YK=8 BK=1 RK=0 G=1153 dmg=7426 door=29/1/1
- MT38 x10y1 fly
- MT38 x11y1 pass upFloor
- after: HP=1189 ATK=154 DEF=158 YK=8 BK=1 RK=0 G=1153 dmg=7426 door=29/1/1

### MT39

- before: HP=1189 ATK=154 DEF=158 YK=8 BK=1 RK=0 G=1153 dmg=7426 door=29/1/1
- MT39 x10y8 open yellowDoor [YK 8->7]
- MT39 x10y9 kill redKnight [HP 1189->973, G 1153->1218] (+65G)
- MT39 x8y10 open yellowDoor [YK 7->6]
- MT39 x6y11 kill slimeMan [DEF 158->162, G 1218->1303] (auto: x5y9 swordsman, x6y9 blueGem) (+85G)
- MT39 x4y10 open yellowDoor [YK 6->5]
- MT39 x2y10 kill ghostSkeleton [HP 973->955, YK 5->6, G 1303->1338] (auto: x3y11 yellowKey) (+35G)
- MT39 x2y8 open blueDoor [BK 1->0]
- MT39 x4y2 open yellowDoor [YK 6->5]
- MT39 x6y4 open yellowDoor [YK 5->4]
- MT39 x4y4 reward centerFly3
- after: HP=955 ATK=154 DEF=162 YK=4 BK=0 RK=0 G=1338 dmg=7660 door=34/2/1

### MT38

- before: HP=955 ATK=154 DEF=162 YK=4 BK=0 RK=0 G=1338 dmg=7660 door=34/2/1
- MT38 x10y1 fly
- MT38 x10y7 kill redKnight [HP 955->751, YK 4->7, G 1338->1403] (auto: x9y6 yellowKey, x9y5 yellowKey, x9y4 yellowKey) (+65G)
- after: HP=751 ATK=154 DEF=162 YK=7 BK=0 RK=0 G=1403 dmg=7864 door=34/2/1

### MT31

- before: HP=751 ATK=154 DEF=162 YK=7 BK=0 RK=0 G=1403 dmg=7864 door=34/2/1
- MT31 x6y10 fly
- MT31 x9y8 open yellowDoor [YK 7->6, G 1403->1433] (auto: x11y10 slimeMan)
- MT31 x8y8 take bluePotion [HP 751->1551]
- after: HP=1551 ATK=154 DEF=162 YK=6 BK=0 RK=0 G=1433 dmg=7864 door=35/2/1

### MT16

- before: HP=1551 ATK=154 DEF=162 YK=6 BK=0 RK=0 G=1433 dmg=7864 door=35/2/1
- MT16 x6y10 fly
- after: HP=1551 ATK=154 DEF=162 YK=6 BK=0 RK=0 G=1433 dmg=7864 door=35/2/1

### MT39

- before: HP=1551 ATK=154 DEF=162 YK=6 BK=0 RK=0 G=1433 dmg=7864 door=35/2/1
- MT39 x11y2 fly
- MT39 x11y11 pass upFloor
- after: HP=1551 ATK=154 DEF=162 YK=6 BK=0 RK=0 G=1433 dmg=7864 door=35/2/1

### MT40

- before: HP=1551 ATK=154 DEF=162 YK=6 BK=0 RK=0 G=1433 dmg=7864 door=35/2/1
- MT40 x2y1 event centerFly3
- MT40 x2y2 kill swordsman [G 1433->1598] (auto: x3y2 swordsman, x4y2 swordsman) (+165G)
- MT40 x3y4 kill ghostSkeleton [HP 1551->1533, G 1598->1633] (+35G)
- MT40 x4y4 kill ghostSkeleton [HP 1533->1515, G 1633->1668] (+35G)
- MT40 x5y4 kill ghostSkeleton [HP 1515->1497, G 1668->1703] (+35G)
- MT40 x7y4 kill soldier [HP 1497->1421, G 1703->1748] (+45G)
- MT40 x8y4 kill soldier [HP 1421->1345, G 1748->1793] (+45G)
- MT40 x9y4 kill soldier [HP 1345->1269, G 1793->1838] (+45G)
- MT40 x8y2 kill redKnight [HP 1269->1065, G 1838->1903] (+65G)
- MT40 x9y2 kill redKnight [HP 1065->861, G 1903->1968] (+65G)
- MT40 x10y2 kill redKnight [HP 861->657, G 1968->2033] (+65G)
- MT40 x6y7 reward yellowKnight [G 2033->2133] (auto: +100G)
- MT40 x2y2 move [ATK 154->166, DEF 162->174, YK 6->9] (auto: x7y4 blueGem, x4y2 yellowKey, x8y4 blueGem, x3y2 yellowKey, x9y4 blueGem, x2y2 yellowKey, x8y2 redGem, x9y2 redGem, x10y2 redGem)
- MT40 x6y1 pass upFloor
- after: HP=657 ATK=166 DEF=174 YK=9 BK=0 RK=0 G=2133 dmg=8758 door=35/2/1

### MT31

- before: HP=657 ATK=166 DEF=174 YK=9 BK=0 RK=0 G=2133 dmg=8758 door=35/2/1
- MT31 x6y10 fly
- after: HP=657 ATK=166 DEF=174 YK=9 BK=0 RK=0 G=2133 dmg=8758 door=35/2/1

### MT15

- before: HP=657 ATK=166 DEF=174 YK=9 BK=0 RK=0 G=2133 dmg=8758 door=35/2/1
- MT15 x6y2 fly
- MT15 x6y6 kill octopus [HP 657->609, G 2133->2285] (auto: x2y1 zombieKnight, x2y11 redPriest) (+152G)
- MT15 x6y5 take pickaxe
- after: HP=609 ATK=166 DEF=174 YK=9 BK=0 RK=0 G=2285 dmg=8806 door=35/2/1

### MT31

- before: HP=609 ATK=166 DEF=174 YK=9 BK=0 RK=0 G=2285 dmg=8806 door=35/2/1
- MT31 x6y2 fly
- after: HP=609 ATK=166 DEF=174 YK=9 BK=0 RK=0 G=2285 dmg=8806 door=35/2/1

### MT41

- before: HP=609 ATK=166 DEF=174 YK=9 BK=0 RK=0 G=2285 dmg=8806 door=35/2/1
- MT41 x6y2 fly
- after: HP=609 ATK=166 DEF=174 YK=9 BK=0 RK=0 G=2285 dmg=8806 door=35/2/1
