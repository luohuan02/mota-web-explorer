# 当前最优 Walk (zone3, auto ON)

## 说明

- 本 walk 由 Game 类 (`scripts/search/zone3_game_route.py`, auto_sweep, strict_live_model) 离线推导生成。
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone3_game_route.json --load-slot <100+> --target-click-only`（统一点击 verifier，1-4 区通用；3 区起按需 `--set-auto battle=true,item=nopotion,wall=true`）
- 源 JSON：`best/zone3_2atk1def_preserve_pickaxe_walk.json`

## 摘要

- final: HP=45 ATK=166 DEF=166 YK=7 BK=0 RK=0 G=2423 dmg=10066 door=37/2/1 MT41 x6y2

## Walk

### MT17

- before: HP=1211 ATK=76 DEF=72 YK=4 BK=0 RK=0 G=1138 dmg=0 door=0/0/0
- MT17 x6y2 fly
- MT17 x10y10 open yellowDoor [YK 4->3]
- MT17 x9y8 kill zombie [HP 1211->1198, G 1138->1156] (+18G)
- MT17 x11y8 kill zombie [HP 1198->1185, G 1156->1174] (+18G)
- MT17 x9y5 kill zombieKnight [HP 1185->1089, G 1174->1204] (+30G)
- MT17 x11y5 kill zombieKnight [HP 1089->993, ATK 76->78, DEF 72->74, YK 3->5, G 1204->1234] (auto: x9y3 yellowKey, x11y3 yellowKey, x9y1 redGem, x11y1 blueGem) (+30G)
- MT17 x10y2 take bluePotion [HP 993->1393]
- after: HP=1393 ATK=78 DEF=74 YK=5 BK=0 RK=0 G=1234 dmg=218 door=1/0/0

### MT31

- before: HP=1393 ATK=78 DEF=74 YK=5 BK=0 RK=0 G=1234 dmg=218 door=1/0/0
- MT31 x6y2 fly
- MT31 x6y8 kill zombieKnight [HP 1393->1301, G 1234->1264] (+30G)
- MT31 x6y9 kill zombieKnight [HP 1301->1209, G 1264->1294] (+30G)
- MT31 x6y11 pass upFloor
- after: HP=1209 ATK=78 DEF=74 YK=5 BK=0 RK=0 G=1294 dmg=402 door=1/0/0

### MT32

- before: HP=1209 ATK=78 DEF=74 YK=5 BK=0 RK=0 G=1294 dmg=402 door=1/0/0
- MT32 x6y10 eventbattle yellowKnight [HP 1209->829, G 1294->1394] (auto: +100G)
- MT32 x8y11 kill ghostSkeleton [HP 829->405, G 1394->1429] (+35G)
- MT32 x10y10 shop atk [ATK 78->86, G 1429->1289]
- MT32 x10y10 shop atk [ATK 86->94, G 1289->1069]
- MT32 x10y10 shop def [DEF 74->90, G 1069->749]
- MT32 x10y10 shop def [DEF 90->106, G 749->309]
- MT32 x11y1 pass upFloor
- after: HP=405 ATK=94 DEF=106 YK=5 BK=0 RK=0 G=309 dmg=1206 door=1/0/0

### MT33

- before: HP=405 ATK=94 DEF=106 YK=5 BK=0 RK=0 G=309 dmg=1206 door=1/0/0
- MT33 x7y1 open yellowDoor [YK 5->4]
- MT33 x6y1 kill slimeMan [HP 405->269, YK 4->5, G 309->339] (+30G)
- MT33 x5y2 take redPotion [HP 269->469]
- MT33 x8y2 open yellowDoor [YK 5->4]
- MT33 x11y3 take bluePotion [HP 469->1269]
- after: HP=1269 ATK=94 DEF=106 YK=4 BK=0 RK=0 G=339 dmg=1342 door=3/0/0

### MT14

- before: HP=1269 ATK=94 DEF=106 YK=4 BK=0 RK=0 G=339 dmg=1342 door=3/0/0
- MT14 x6y10 fly
- MT14 x6y5 kill rock (auto: x3y9 redPriest, x6y5 rock, x8y5 bigBat, x11y6 zombie)
- MT14 x10y4 kill zombieKnight [HP 1269->1255, G 419->449] (+30G)
- MT14 x10y3 open yellowDoor [YK 4->7] (auto: x10y1 yellowKey, x11y2 yellowKey, x9y1 yellowKey, x11y1 yellowKey)
- MT14 x7y4 open yellowDoor [YK 7->6]
- MT14 x7y2 kill zombieKnight [HP 1255->1241, G 449->479] (+30G)
- MT14 x7y1 take redPotion [HP 1241->1341, DEF 106->108, YK 6->7, G 479->487] (auto: x6y1 yellowKey, x5y1 blueGem, x5y2 blackSlime)
- after: HP=1341 ATK=94 DEF=108 YK=7 BK=0 RK=0 G=487 dmg=1370 door=5/0/0

### MT15

- before: HP=1341 ATK=94 DEF=108 YK=7 BK=0 RK=0 G=487 dmg=1370 door=5/0/0
- MT15 x6y10 fly
- MT15 x11y6 kill redPriest (auto: x11y6 redPriest, x2y11 redPriest)
- after: HP=1341 ATK=94 DEF=108 YK=7 BK=0 RK=0 G=531 dmg=1370 door=5/0/0

### MT20

- before: HP=1341 ATK=94 DEF=108 YK=7 BK=0 RK=0 G=531 dmg=1370 door=5/0/0
- MT20 x6y10 fly
- MT20 x8y11 kill redPriest (auto: x8y11 redPriest, x10y10 rock, x2y10 rock)
- MT20 x11y11 take redPotion [HP 1341->1441]
- after: HP=1441 ATK=94 DEF=108 YK=7 BK=0 RK=0 G=609 dmg=1370 door=5/0/0

### MT18

- before: HP=1441 ATK=94 DEF=108 YK=7 BK=0 RK=0 G=609 dmg=1370 door=5/0/0
- MT18 x1y2 fly
- MT18 x10y7 kill rock (auto: x1y5 rock, x3y5 rock, x10y7 rock, x9y4 zombie)
- MT18 x11y8 open yellowDoor [DEF 108->110, G 711->733] (auto: x11y9 redPriest, x10y10 yellowKey, x10y11 blueGem)
- MT18 x11y11 take redPotion [HP 1441->1541]
- after: HP=1541 ATK=94 DEF=110 YK=7 BK=0 RK=0 G=733 dmg=1370 door=6/0/0

### MT19

- before: HP=1541 ATK=94 DEF=110 YK=7 BK=0 RK=0 G=733 dmg=1370 door=6/0/0
- MT19 x1y2 fly
- MT19 x5y6 kill rock (auto: x5y6 rock)
- MT19 x4y3 kill zombieKnight [HP 1541->1531, BK 0->1, G 761->813] (+52G)
- after: HP=1531 ATK=94 DEF=110 YK=7 BK=1 RK=0 G=813 dmg=1380 door=6/0/0

### MT14

- before: HP=1531 ATK=94 DEF=110 YK=7 BK=1 RK=0 G=813 dmg=1380 door=6/0/0
- MT14 x6y10 fly
- after: HP=1531 ATK=94 DEF=110 YK=7 BK=1 RK=0 G=813 dmg=1380 door=6/0/0

### MT18

- before: HP=1531 ATK=94 DEF=110 YK=7 BK=1 RK=0 G=813 dmg=1380 door=6/0/0
- MT18 x6y2 fly
- after: HP=1531 ATK=94 DEF=110 YK=7 BK=1 RK=0 G=813 dmg=1380 door=6/0/0

### MT19

- before: HP=1531 ATK=94 DEF=110 YK=7 BK=1 RK=0 G=813 dmg=1380 door=6/0/0
- MT19 x1y2 fly
- after: HP=1531 ATK=94 DEF=110 YK=7 BK=1 RK=0 G=813 dmg=1380 door=6/0/0

### MT20

- before: HP=1531 ATK=94 DEF=110 YK=7 BK=1 RK=0 G=813 dmg=1380 door=6/0/0
- MT20 x6y10 fly
- after: HP=1531 ATK=94 DEF=110 YK=7 BK=1 RK=0 G=813 dmg=1380 door=6/0/0

### MT18

- before: HP=1531 ATK=94 DEF=110 YK=7 BK=1 RK=0 G=813 dmg=1380 door=6/0/0
- MT18 x1y2 fly
- after: HP=1531 ATK=94 DEF=110 YK=7 BK=1 RK=0 G=813 dmg=1380 door=6/0/0

### MT32

- before: HP=1531 ATK=94 DEF=110 YK=7 BK=1 RK=0 G=813 dmg=1380 door=6/0/0
- MT32 x6y11 fly
- MT32 x10y10 shop atk [ATK 94->102, G 813->233]
- after: HP=1531 ATK=102 DEF=110 YK=7 BK=1 RK=0 G=233 dmg=1380 door=6/0/0

### MT33

- before: HP=1531 ATK=102 DEF=110 YK=7 BK=1 RK=0 G=233 dmg=1380 door=6/0/0
- MT33 x10y1 fly
- MT33 x10y5 event swordTrap
- MT33 x9y5 kill ghostSkeleton [HP 1531->1321, G 233->268] (+35G)
- MT33 x11y5 kill ghostSkeleton [HP 1321->1111, G 268->303] (+35G)
- MT33 x9y7 kill soldier [HP 1111->661, G 303->348] (+45G)
- MT33 x11y7 kill soldier [HP 661->211, G 348->393] (+45G)
- MT33 x10y10 take sword3 [ATK 102->142] (auto: x8y10 flower)
- after: HP=211 ATK=142 DEF=110 YK=7 BK=1 RK=0 G=393 dmg=2700 door=6/0/0

### MT31

- before: HP=211 ATK=142 DEF=110 YK=7 BK=1 RK=0 G=393 dmg=2700 door=6/0/0
- MT31 x6y10 fly
- after: HP=211 ATK=142 DEF=110 YK=7 BK=1 RK=0 G=393 dmg=2700 door=6/0/0

### MT33

- before: HP=211 ATK=142 DEF=110 YK=7 BK=1 RK=0 G=393 dmg=2700 door=6/0/0
- MT33 x10y1 fly
- MT33 x4y1 kill zombieKnight [HP 211->201, G 393->423] (+30G)
- MT33 x3y1 open yellowDoor [YK 7->6]
- MT33 x1y1 pass upFloor
- after: HP=201 ATK=142 DEF=110 YK=6 BK=1 RK=0 G=423 dmg=2710 door=7/0/0

### MT34

- before: HP=201 ATK=142 DEF=110 YK=6 BK=1 RK=0 G=423 dmg=2710 door=7/0/0
- MT34 x3y1 take redPotion [HP 201->401]
- after: HP=401 ATK=142 DEF=110 YK=6 BK=1 RK=0 G=423 dmg=2710 door=7/0/0

### MT32

- before: HP=401 ATK=142 DEF=110 YK=6 BK=1 RK=0 G=423 dmg=2710 door=7/0/0
- MT32 x10y1 fly
- MT32 x7y3 open yellowDoor [YK 6->5]
- MT32 x8y4 kill ghostSkeleton [HP 401->331, G 423->458] (+35G)
- MT32 x9y5 open yellowDoor [YK 5->6] (auto: x10y4 yellowKey, x11y5 yellowKey)
- MT32 x11y4 take bluePotion [HP 331->1131]
- after: HP=1131 ATK=142 DEF=110 YK=6 BK=1 RK=0 G=458 dmg=2780 door=9/0/0

### MT2

- before: HP=1131 ATK=142 DEF=110 YK=6 BK=1 RK=0 G=458 dmg=2780 door=9/0/0
- MT2 x1y10 fly
- MT2 x3y1 open blueDoor [BK 1->0]
- MT2 x6y2 kill blueGuard [HP 1131->921, G 458->508] (+50G)
- MT2 x8y2 kill blueGuard [HP 921->711, G 508->558] (+50G)
- MT2 x3y5 take yellowKey [YK 6->9] (auto: x3y4 yellowKey, x4y4 yellowKey)
- MT2 x11y4 reward oldman [G 558->1558] (auto: +1000G)
- MT2 x3y11 take bluePotion [HP 711->911]
- after: HP=911 ATK=142 DEF=110 YK=9 BK=0 RK=0 G=1558 dmg=3200 door=9/1/0

### MT31

- before: HP=911 ATK=142 DEF=110 YK=9 BK=0 RK=0 G=1558 dmg=3200 door=9/1/0
- MT31 x6y2 fly
- MT31 x10y6 kill ghostSkeleton [HP 911->841, G 1558->1593] (+35G)
- MT31 x11y7 open yellowDoor [YK 9->8]
- MT31 x10y9 kill slimeMan [HP 841->781, YK 8->12, G 1593->1623] (+30G)
- after: HP=781 ATK=142 DEF=110 YK=12 BK=0 RK=0 G=1623 dmg=3330 door=10/1/0

### MT32

- before: HP=781 ATK=142 DEF=110 YK=12 BK=0 RK=0 G=1623 dmg=3330 door=10/1/0
- MT32 x6y11 fly
- MT32 x10y10 shop hp [HP 781->1681, G 1623->883]
- after: HP=1681 ATK=142 DEF=110 YK=12 BK=0 RK=0 G=883 dmg=3330 door=10/1/0

### MT34

- before: HP=1681 ATK=142 DEF=110 YK=12 BK=0 RK=0 G=883 dmg=3330 door=10/1/0
- MT34 x2y1 fly
- MT34 x2y3 kill slimeMan [HP 1681->1621, G 883->913] (+30G)
- MT34 x2y4 open yellowDoor [YK 12->11]
- MT34 x5y5 open yellowDoor [YK 11->10, G 913->914] (auto: x5y4 greenSlime)
- MT34 x5y7 open yellowDoor [YK 10->9]
- MT34 x5y8 kill ghostSkeleton [HP 1621->1551, G 914->949] (+35G)
- MT34 x7y5 open yellowDoor [YK 9->8]
- MT34 x7y4 kill swordsman [HP 1551->981, G 949->1004] (+55G)
- MT34 x7y7 open yellowDoor [YK 8->7, G 1004->1006] (auto: x7y8 redSlime)
- MT34 x9y5 open yellowDoor [YK 7->6, G 1006->1014] (auto: x9y4 blackSlime)
- MT34 x9y7 open yellowDoor [YK 6->5]
- MT34 x11y5 open yellowDoor [YK 5->4]
- MT34 x11y4 kill soldier [HP 981->801, G 1014->1059] (+45G)
- MT34 x11y7 open yellowDoor [YK 4->3, G 1059->1062] (auto: x11y8 bat)
- MT34 x9y8 kill redKnight [HP 801->321, G 1062->1127] (+65G)
- MT34 x3y5 take yellowKey [YK 3->7, RK 0->1] (auto: x1y5 yellowKey, x2y6 redKey, x3y7 yellowKey, x1y7 yellowKey)
- after: HP=321 ATK=142 DEF=110 YK=7 BK=0 RK=1 G=1127 dmg=4690 door=19/1/0

### MT2

- before: HP=321 ATK=142 DEF=110 YK=7 BK=0 RK=1 G=1127 dmg=4690 door=19/1/0
- MT2 x1y10 fly
- MT2 x10y11 event thief
- after: HP=321 ATK=142 DEF=110 YK=7 BK=0 RK=1 G=1127 dmg=4690 door=19/1/0

### MT34

- before: HP=321 ATK=142 DEF=110 YK=7 BK=0 RK=1 G=1127 dmg=4690 door=19/1/0
- MT34 x2y1 fly
- MT34 x2y8 open yellowDoor [YK 7->6]
- MT34 x3y9 kill ghostSkeleton [HP 321->251, G 1127->1162] (+35G)
- MT34 x4y10 open yellowDoor [YK 6->5]
- MT34 x6y11 pass upFloor
- after: HP=251 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1162 dmg=4760 door=21/1/0

### MT35

- before: HP=251 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1162 dmg=4760 door=21/1/0
- MT35 x5y10 event thief
- MT35 x11y1 pass upFloor
- after: HP=251 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1162 dmg=4760 door=21/1/0

### MT34

- before: HP=251 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1162 dmg=4760 door=21/1/0
- MT34 x6y10 fly
- MT34 x2y11 kill soldier [HP 251->71, G 1162->1207] (+45G)
- MT34 x1y11 take bluePotion [HP 71->871]
- after: HP=871 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1207 dmg=4940 door=21/1/0

### MT36

- before: HP=871 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1207 dmg=4940 door=21/1/0
- MT36 x11y2 fly
- MT36 x11y3 kill slimeMan [HP 871->811, G 1207->1237] (+30G)
- MT36 x11y5 kill swordsman [HP 811->241, G 1237->1292] (+55G)
- after: HP=241 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1292 dmg=5570 door=21/1/0

### MT2

- before: HP=241 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1292 dmg=5570 door=21/1/0
- MT2 x1y10 fly
- MT2 x4y10 take bluePotion [HP 241->441]
- MT2 x3y10 take bluePotion [HP 441->641]
- after: HP=641 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1292 dmg=5570 door=21/1/0

### MT36

- before: HP=641 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1292 dmg=5570 door=21/1/0
- MT36 x11y2 fly
- MT36 x11y7 kill redKnight [HP 641->161, G 1292->1357] (+65G)
- MT36 x11y11 pass upFloor
- after: HP=161 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1357 dmg=6050 door=21/1/0

### MT2

- before: HP=161 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1357 dmg=6050 door=21/1/0
- MT2 x1y10 fly
- after: HP=161 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1357 dmg=6050 door=21/1/0

### MT32

- before: HP=161 ATK=142 DEF=110 YK=5 BK=0 RK=1 G=1357 dmg=6050 door=21/1/0
- MT32 x6y11 fly
- MT32 x10y10 shop atk [ATK 142->150, G 1357->437]
- after: HP=161 ATK=150 DEF=110 YK=5 BK=0 RK=1 G=437 dmg=6050 door=21/1/0

### MT36

- before: HP=161 ATK=150 DEF=110 YK=5 BK=0 RK=1 G=437 dmg=6050 door=21/1/0
- MT36 x11y2 fly
- MT36 x9y11 kill swordsman (auto: x9y11 swordsman)
- MT36 x7y11 kill zombieKnight [HP 161->151, YK 5->6, G 492->522] (+30G)
- after: HP=151 ATK=150 DEF=110 YK=6 BK=0 RK=1 G=522 dmg=6060 door=21/1/0

### MT19

- before: HP=151 ATK=150 DEF=110 YK=6 BK=0 RK=1 G=522 dmg=6060 door=21/1/0
- MT19 x6y10 fly
- MT19 x4y1 take redPotion [HP 151->251]
- after: HP=251 ATK=150 DEF=110 YK=6 BK=0 RK=1 G=522 dmg=6060 door=21/1/0

### MT36

- before: HP=251 ATK=150 DEF=110 YK=6 BK=0 RK=1 G=522 dmg=6060 door=21/1/0
- MT36 x11y2 fly
- MT36 x3y11 kill soldier [HP 251->71, G 522->622] (+100G)
- MT36 x1y11 take bluePotion [HP 71->871]
- after: HP=871 ATK=150 DEF=110 YK=6 BK=0 RK=1 G=622 dmg=6240 door=21/1/0

### MT14

- before: HP=871 ATK=150 DEF=110 YK=6 BK=0 RK=1 G=622 dmg=6240 door=21/1/0
- MT14 x6y10 fly
- after: HP=871 ATK=150 DEF=110 YK=6 BK=0 RK=1 G=622 dmg=6240 door=21/1/0

### MT15

- before: HP=871 ATK=150 DEF=110 YK=6 BK=0 RK=1 G=622 dmg=6240 door=21/1/0
- MT15 x6y10 fly
- MT15 x6y6 kill octopus [HP 871->241, G 622->722] (+100G)
- MT15 x6y5 take pickaxe
- MT15 x11y8 take bluePotion [HP 241->641]
- after: HP=641 ATK=150 DEF=110 YK=6 BK=0 RK=1 G=722 dmg=6870 door=21/1/0

### MT14

- before: HP=641 ATK=150 DEF=110 YK=6 BK=0 RK=1 G=722 dmg=6870 door=21/1/0
- MT14 x6y10 fly
- MT14 x9y6 take redPotion [HP 641->741]
- after: HP=741 ATK=150 DEF=110 YK=6 BK=0 RK=1 G=722 dmg=6870 door=21/1/0

### MT37

- before: HP=741 ATK=150 DEF=110 YK=6 BK=0 RK=1 G=722 dmg=6870 door=21/1/0
- MT37 x11y10 fly
- MT37 x11y9 kill redKnight [HP 741->381, G 722->842] (+120G)
- MT37 x11y3 kill redKnight [HP 381->21, G 842->907] (+65G)
- MT37 x11y1 take bluePotion [HP 21->821]
- MT37 x9y1 kill soldier [HP 821->641, G 907->952] (+45G)
- MT37 x3y1 open yellowDoor [YK 6->5]
- MT37 x1y1 pass upFloor
- after: HP=641 ATK=150 DEF=110 YK=5 BK=0 RK=1 G=952 dmg=7770 door=22/1/0

### MT14

- before: HP=641 ATK=150 DEF=110 YK=5 BK=0 RK=1 G=952 dmg=7770 door=22/1/0
- MT14 x6y10 fly
- MT14 x1y7 open yellowDoor [YK 5->4, BK 0->1, G 952->974] (auto: x1y9 redPriest, x1y11 blueKey)
- after: HP=641 ATK=150 DEF=110 YK=4 BK=1 RK=1 G=974 dmg=7770 door=23/1/0

### MT31

- before: HP=641 ATK=150 DEF=110 YK=4 BK=1 RK=1 G=974 dmg=7770 door=23/1/0
- MT31 x6y2 fly
- after: HP=641 ATK=150 DEF=110 YK=4 BK=1 RK=1 G=974 dmg=7770 door=23/1/0

### MT38

- before: HP=641 ATK=150 DEF=110 YK=4 BK=1 RK=1 G=974 dmg=7770 door=23/1/0
- MT38 x2y1 fly
- MT38 x3y1 open redDoor [RK 1->0]
- MT38 x4y1 kill slimeMan [HP 641->581, YK 4->5, G 974->1004] (+30G)
- MT38 x5y2 trader yellowKey3 [YK 5->8, G 1004->804]
- MT38 x8y1 kill slimeMan [HP 581->521, G 804->834] (+30G)
- MT38 x9y1 open yellowDoor [YK 8->7]
- MT38 x11y3 open yellowDoor [YK 7->6]
- MT38 x11y6 kill ghostSkeleton [HP 521->451, G 834->869] (+35G)
- MT38 x11y8 open yellowDoor [YK 6->5]
- MT38 x11y9 kill ghostSkeleton [HP 451->381, YK 5->6, G 869->904] (+35G)
- MT38 x9y11 kill soldier [HP 381->201, G 904->949] (+45G)
- MT38 x8y11 open yellowDoor [YK 6->5, G 949->1022] (auto: x7y11 zombie, x5y11 swordsman)
- MT38 x4y11 open yellowDoor [YK 5->4]
- MT38 x1y10 kill blueGuard [HP 201->61, G 1022->1072] (+50G)
- MT38 x11y11 take bluePotion [HP 61->861]
- MT38 x3y10 kill blueGuard [HP 861->721, G 1072->1122] (auto: x2y5 flower) (+50G)
- MT38 x2y7 take shield3 [DEF 110->150]
- MT38 x11y1 pass upFloor
- after: HP=721 ATK=150 DEF=150 YK=4 BK=1 RK=0 G=1122 dmg=8490 door=28/1/1

### MT39

- before: HP=721 ATK=150 DEF=150 YK=4 BK=1 RK=0 G=1122 dmg=8490 door=28/1/1
- MT39 x11y3 take yellowKey [YK 4->5]
- MT39 x10y4 open yellowDoor [YK 5->4, G 1122->1152] (auto: x9y6 slimeMan)
- MT39 x11y7 kill ghostSkeleton [HP 721->691, ATK 150->154, G 1152->1187] (+35G)
- after: HP=691 ATK=154 DEF=150 YK=4 BK=1 RK=0 G=1187 dmg=8520 door=29/1/1

### MT38

- before: HP=691 ATK=154 DEF=150 YK=4 BK=1 RK=0 G=1187 dmg=8520 door=29/1/1
- MT38 x10y1 fly
- MT38 x11y1 pass upFloor
- after: HP=691 ATK=154 DEF=150 YK=4 BK=1 RK=0 G=1187 dmg=8520 door=29/1/1

### MT39

- before: HP=691 ATK=154 DEF=150 YK=4 BK=1 RK=0 G=1187 dmg=8520 door=29/1/1
- MT39 x10y8 open yellowDoor [YK 4->3]
- MT39 x10y9 kill redKnight [HP 691->451, G 1187->1252] (+65G)
- MT39 x8y10 open yellowDoor [DEF 150->154, YK 3->2, G 1252->1337] (auto: x6y11 slimeMan, x5y9 swordsman, x6y9 blueGem)
- MT39 x4y10 open yellowDoor (auto: x3y11 yellowKey)
- MT39 x2y10 kill ghostSkeleton [HP 451->425, G 1337->1372] (+35G)
- MT39 x2y8 open blueDoor [BK 1->0]
- MT39 x4y2 open yellowDoor [YK 2->1]
- MT39 x6y4 open yellowDoor [YK 1->0]
- MT39 x4y4 reward centerFly3
- MT39 x4y4 take centerFly3
- after: HP=425 ATK=154 DEF=154 YK=0 BK=0 RK=0 G=1372 dmg=8786 door=34/2/1

### MT38

- before: HP=425 ATK=154 DEF=154 YK=0 BK=0 RK=0 G=1372 dmg=8786 door=34/2/1
- MT38 x10y1 fly
- MT38 x10y7 kill redKnight [HP 425->197, YK 0->3, G 1372->1437] (+65G)
- after: HP=197 ATK=154 DEF=154 YK=3 BK=0 RK=0 G=1437 dmg=9014 door=34/2/1

### MT31

- before: HP=197 ATK=154 DEF=154 YK=3 BK=0 RK=0 G=1437 dmg=9014 door=34/2/1
- MT31 x6y10 fly
- MT31 x9y8 open yellowDoor [YK 3->2]
- MT31 x8y8 take bluePotion [HP 197->997]
- after: HP=997 ATK=154 DEF=154 YK=2 BK=0 RK=0 G=1467 dmg=9014 door=35/2/1

### MT16

- before: HP=997 ATK=154 DEF=154 YK=2 BK=0 RK=0 G=1467 dmg=9014 door=35/2/1
- MT16 x6y10 fly
- MT16 x10y5 kill zombie (auto: x9y11 slimeMan, x6y6 zombieKnight, x10y5 zombie, x5y3 zombie, x3y6 rock, x2y2 redPriest, x10y11 fakeWall)
- MT16 x10y4 open yellowDoor [YK 2->1, G 1613->1633] (auto: x9y2 blackSlime, x11y1 bigBat)
- MT16 x11y3 take redPotion [HP 997->1097]
- after: HP=1097 ATK=154 DEF=154 YK=1 BK=0 RK=0 G=1633 dmg=9014 door=36/2/1

### MT39

- before: HP=1097 ATK=154 DEF=154 YK=1 BK=0 RK=0 G=1633 dmg=9014 door=36/2/1
- MT39 x11y2 fly
- MT39 x11y11 pass upFloor
- after: HP=1097 ATK=154 DEF=154 YK=1 BK=0 RK=0 G=1633 dmg=9014 door=36/2/1

### MT40

- before: HP=1097 ATK=154 DEF=154 YK=1 BK=0 RK=0 G=1633 dmg=9014 door=36/2/1
- MT40 x2y1 event centerFly3
- MT40 x2y2 kill swordsman [G 1633->1798] (auto: x3y2 swordsman, x4y2 swordsman) (+165G)
- MT40 x3y4 kill ghostSkeleton [HP 1097->1071, G 1798->1833] (+35G)
- MT40 x4y4 kill ghostSkeleton [HP 1071->1045, G 1833->1868] (+35G)
- MT40 x5y4 kill ghostSkeleton [HP 1045->1019, G 1868->1903] (+35G)
- MT40 x7y4 kill soldier [HP 1019->927, G 1903->1948] (+45G)
- MT40 x8y4 kill soldier [HP 927->835, G 1948->1993] (+45G)
- MT40 x9y4 kill soldier [HP 835->743, G 1993->2038] (+45G)
- MT40 x8y2 kill redKnight [HP 743->515, G 2038->2103] (+65G)
- MT40 x9y2 kill redKnight [HP 515->287, G 2103->2168] (+65G)
- MT40 x10y2 kill redKnight [HP 287->59, G 2168->2233] (+65G)
- MT40 x6y7 reward yellowKnight [G 2233->2333] (auto: +100G)
- MT40 x2y2 take yellowKey [ATK 154->166, DEF 154->166, YK 1->4] (auto: x3y2 yellowKey, x4y2 yellowKey, x8y2 redGem, x7y4 blueGem, x9y2 redGem, x8y4 blueGem, x10y2 redGem, x9y4 blueGem)
- MT40 x6y1 pass upFloor
- after: HP=59 ATK=166 DEF=166 YK=4 BK=0 RK=0 G=2333 dmg=10052 door=36/2/1

### MT31

- before: HP=59 ATK=166 DEF=166 YK=4 BK=0 RK=0 G=2333 dmg=10052 door=36/2/1
- MT31 x6y10 fly
- MT31 x2y6 kill ghostSkeleton [HP 59->45, G 2333->2368] (+35G)
- MT31 x1y5 open yellowDoor [YK 4->7, G 2368->2423] (auto: x1y2 swordsman, x3y2 yellowKey, x3y1 yellowKey, x4y2 yellowKey, x4y1 yellowKey)
- after: HP=45 ATK=166 DEF=166 YK=7 BK=0 RK=0 G=2423 dmg=10066 door=37/2/1

### MT41

- before: HP=45 ATK=166 DEF=166 YK=7 BK=0 RK=0 G=2423 dmg=10066 door=37/2/1
- MT41 x6y2 fly
- after: HP=45 ATK=166 DEF=166 YK=7 BK=0 RK=0 G=2423 dmg=10066 door=37/2/1
