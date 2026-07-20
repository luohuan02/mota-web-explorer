# 当前最优 Walk (zone3, auto ON)

## 说明

- 本 walk 是 `best/zone3_2atk1def_game_route_walk.json` (HP=125) 的 **minhp 派生版**：用 `scripts/build/minimize_strict_walk_hp.py` 在固定动作序列下做“最低存活 HP 压缩”，删除 1 瓶 +100 红血瓶，约束每步 `after.hp > 0`；再由 `scripts/search/zone3_game_route.py` 通用 Game (strict_live_model + auto_sweep, item=nopotion) 全程合法回放重新生成 before/after。
- `removed_potions` 记录被压掉的血瓶（含本版新删的 MT19 x4y1 redPotion +100，以及 HP=125 版已删的 4 瓶；后者声明为 blocked_items 以匹配实机 item=nopotion 的“路径上不拾血瓶”语义，避免离线 go_to 路过拾取导致 +800 发散）。
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证（2026-07-12 通过，201 entry 0 mismatch，终态精确一致 HP=25）：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk best/zone3_2atk1def_minhp_walk.json --load-slot 59 --set-auto battle=true,item=nopotion,wall=true --target-click-only`
- 用途：4 区半血陷阱（special 16，HP 减半）前控血。本版把 3 区末 HP 从 125 压到 25（少拣 MT19 x4y1 红血瓶 +100）；后续可在 4 区半血陷阱之后用飞行器回 19F 补拾该血瓶拿满 +100。
- 源 JSON：`outputs/results/zone3_2atk1def_minhp_walk.json`

## 摘要

- final: HP=25 ATK=174 DEF=166 YK=4 BK=0 RK=0 G=1828 dmg=8086 door=27/2/1 MT41 x6y2

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
- MT2 x10y11 event thief
- after: HP=711 ATK=142 DEF=110 YK=9 BK=0 RK=0 G=1558 dmg=3200 door=9/1/0

### MT34

- before: HP=711 ATK=142 DEF=110 YK=9 BK=0 RK=0 G=1558 dmg=3200 door=9/1/0
- MT34 x2y1 fly
- MT34 x2y3 kill slimeMan [HP 711->651, G 1558->1588] (+30G)
- MT34 x2y4 open yellowDoor [YK 9->8]
- MT34 x2y8 open yellowDoor [YK 8->7]
- MT34 x3y9 kill ghostSkeleton [HP 651->581, G 1588->1623] (+35G)
- MT34 x4y10 open yellowDoor [YK 7->6]
- MT34 x6y11 pass upFloor
- after: HP=581 ATK=142 DEF=110 YK=6 BK=0 RK=0 G=1623 dmg=3330 door=12/1/0

### MT35

- before: HP=581 ATK=142 DEF=110 YK=6 BK=0 RK=0 G=1623 dmg=3330 door=12/1/0
- MT35 x5y10 event thief
- MT35 x11y1 pass upFloor
- after: HP=581 ATK=142 DEF=110 YK=6 BK=0 RK=0 G=1623 dmg=3330 door=12/1/0

### MT34

- before: HP=581 ATK=142 DEF=110 YK=6 BK=0 RK=0 G=1623 dmg=3330 door=12/1/0
- MT34 x6y10 fly
- MT34 x2y11 kill soldier [HP 581->401, G 1623->1668] (+45G)
- MT34 x1y11 take bluePotion [HP 401->1201]
- after: HP=1201 ATK=142 DEF=110 YK=6 BK=0 RK=0 G=1668 dmg=3510 door=12/1/0

### MT31

- before: HP=1201 ATK=142 DEF=110 YK=6 BK=0 RK=0 G=1668 dmg=3510 door=12/1/0
- MT31 x6y10 fly
- MT31 x10y6 kill ghostSkeleton [HP 1201->1131, G 1668->1703] (+35G)
- MT31 x11y7 open yellowDoor [YK 6->5]
- MT31 x9y8 open yellowDoor [YK 5->4]
- MT31 x8y8 take bluePotion [HP 1131->1931]
- after: HP=1931 ATK=142 DEF=110 YK=4 BK=0 RK=0 G=1703 dmg=3580 door=14/1/0

### MT36

- before: HP=1931 ATK=142 DEF=110 YK=4 BK=0 RK=0 G=1703 dmg=3580 door=14/1/0
- MT36 x11y2 fly
- MT36 x11y3 kill slimeMan [HP 1931->1871, G 1703->1733] (+30G)
- MT36 x11y5 kill swordsman [HP 1871->1301, G 1733->1788] (+55G)
- MT36 x11y7 kill redKnight [HP 1301->821, G 1788->1853] (+65G)
- MT36 x11y11 pass upFloor
- after: HP=821 ATK=142 DEF=110 YK=4 BK=0 RK=0 G=1853 dmg=4690 door=14/1/0

### MT2

- before: HP=821 ATK=142 DEF=110 YK=4 BK=0 RK=0 G=1853 dmg=4690 door=14/1/0
- MT2 x1y10 fly
- MT2 x4y10 take bluePotion [HP 821->1021]
- MT2 x3y10 take bluePotion [HP 1021->1221]
- MT2 x3y11 take bluePotion [HP 1221->1421]
- after: HP=1421 ATK=142 DEF=110 YK=4 BK=0 RK=0 G=1853 dmg=4690 door=14/1/0

### MT32

- before: HP=1421 ATK=142 DEF=110 YK=4 BK=0 RK=0 G=1853 dmg=4690 door=14/1/0
- MT32 x6y11 fly
- MT32 x10y10 shop atk [ATK 142->150, G 1853->1113]
- MT32 x10y10 shop atk [ATK 150->158, G 1113->193]
- after: HP=1421 ATK=158 DEF=110 YK=4 BK=0 RK=0 G=193 dmg=4690 door=14/1/0

### MT36

- before: HP=1421 ATK=158 DEF=110 YK=4 BK=0 RK=0 G=193 dmg=4690 door=14/1/0
- MT36 x11y2 fly
- MT36 x9y11 kill swordsman (auto: x9y11 swordsman)
- MT36 x7y11 kill zombieKnight [HP 1421->1411, YK 4->5, G 248->278] (+30G)
- MT36 x3y11 kill soldier [HP 1411->1231, G 278->378] (+100G)
- MT36 x1y11 take bluePotion [HP 1231->2031]
- after: HP=2031 ATK=158 DEF=110 YK=5 BK=0 RK=0 G=378 dmg=4880 door=14/1/0

### MT14

- before: HP=2031 ATK=158 DEF=110 YK=5 BK=0 RK=0 G=378 dmg=4880 door=14/1/0
- MT14 x6y10 fly
- after: HP=2031 ATK=158 DEF=110 YK=5 BK=0 RK=0 G=378 dmg=4880 door=14/1/0

### MT15

- before: HP=2031 ATK=158 DEF=110 YK=5 BK=0 RK=0 G=378 dmg=4880 door=14/1/0
- MT15 x6y10 fly
- MT15 x6y6 kill octopus [HP 2031->1471, G 378->478] (+100G)
- MT15 x6y5 take pickaxe
- after: HP=1471 ATK=158 DEF=110 YK=5 BK=0 RK=0 G=478 dmg=5440 door=14/1/0

### MT37

- before: HP=1471 ATK=158 DEF=110 YK=5 BK=0 RK=0 G=478 dmg=5440 door=14/1/0
- MT37 x11y10 fly
- MT37 x11y9 kill redKnight [HP 1471->1111, G 478->598] (+120G)
- MT37 x10y5 使用镐 pickaxe
- MT37 x9y5 take yellowKey [YK 5->7, RK 0->1] (auto: x8y5 yellowKey, x7y5 redKey)
- MT37 x11y3 kill redKnight [HP 1111->751, G 598->663] (+65G)
- MT37 x11y1 take bluePotion [HP 751->1551]
- MT37 x9y1 kill soldier [HP 1551->1371, G 663->708] (+45G)
- MT37 x3y1 open yellowDoor [YK 7->6]
- MT37 x1y1 pass upFloor
- MT37 x2y1 fly
- MT37 x7y4 take redPotion [HP 1371->1571]
- MT37 x7y3 take redPotion [HP 1571->1771]
- after: HP=1771 ATK=158 DEF=110 YK=6 BK=0 RK=1 G=708 dmg=6340 door=15/1/0

### MT14

- before: HP=1771 ATK=158 DEF=110 YK=6 BK=0 RK=1 G=708 dmg=6340 door=15/1/0
- MT14 x6y10 fly
- MT14 x1y7 open yellowDoor [YK 6->5, BK 0->1, G 708->730] (auto: x1y9 redPriest, x1y11 blueKey)
- after: HP=1771 ATK=158 DEF=110 YK=5 BK=1 RK=1 G=730 dmg=6340 door=16/1/0

### MT31

- before: HP=1771 ATK=158 DEF=110 YK=5 BK=1 RK=1 G=730 dmg=6340 door=16/1/0
- MT31 x6y2 fly
- after: HP=1771 ATK=158 DEF=110 YK=5 BK=1 RK=1 G=730 dmg=6340 door=16/1/0

### MT38

- before: HP=1771 ATK=158 DEF=110 YK=5 BK=1 RK=1 G=730 dmg=6340 door=16/1/0
- MT38 x2y1 fly
- MT38 x3y1 open redDoor [RK 1->0]
- MT38 x4y1 kill slimeMan [HP 1771->1711, YK 5->6, G 730->760] (+30G)
- MT38 x5y2 trader yellowKey3 [YK 6->9, G 760->560]
- MT38 x8y1 kill slimeMan [HP 1711->1651, G 560->590] (+30G)
- MT38 x9y1 open yellowDoor [YK 9->8]
- MT38 x11y3 open yellowDoor [YK 8->7]
- MT38 x11y6 kill ghostSkeleton [HP 1651->1581, G 590->625] (+35G)
- MT38 x11y8 open yellowDoor [YK 7->6]
- MT38 x11y9 kill ghostSkeleton [HP 1581->1511, YK 6->7, G 625->660] (+35G)
- MT38 x9y11 kill soldier [HP 1511->1331, G 660->705] (+45G)
- MT38 x8y11 open yellowDoor [YK 7->6, G 705->778] (auto: x7y11 zombie, x5y11 swordsman)
- MT38 x4y11 open yellowDoor [YK 6->5]
- MT38 x1y10 kill blueGuard [HP 1331->1191, G 778->828] (+50G)
- MT38 x3y10 kill blueGuard [HP 1191->1051, G 828->878] (auto: x2y5 flower) (+50G)
- MT38 x2y7 take shield3 [DEF 110->150]
- MT38 x11y1 pass upFloor
- after: HP=1051 ATK=158 DEF=150 YK=5 BK=1 RK=0 G=878 dmg=7060 door=21/1/1

### MT39

- before: HP=1051 ATK=158 DEF=150 YK=5 BK=1 RK=0 G=878 dmg=7060 door=21/1/1
- MT39 x11y3 take yellowKey [YK 5->6]
- MT39 x10y4 open yellowDoor [YK 6->5, G 878->908] (auto: x9y6 slimeMan)
- MT39 x11y7 kill ghostSkeleton [HP 1051->1021, ATK 158->162, G 908->943] (+35G)
- after: HP=1021 ATK=162 DEF=150 YK=5 BK=1 RK=0 G=943 dmg=7090 door=22/1/1

### MT38

- before: HP=1021 ATK=162 DEF=150 YK=5 BK=1 RK=0 G=943 dmg=7090 door=22/1/1
- MT38 x10y1 fly
- MT38 x11y1 pass upFloor
- after: HP=1021 ATK=162 DEF=150 YK=5 BK=1 RK=0 G=943 dmg=7090 door=22/1/1

### MT39

- before: HP=1021 ATK=162 DEF=150 YK=5 BK=1 RK=0 G=943 dmg=7090 door=22/1/1
- MT39 x10y8 open yellowDoor [YK 5->4]
- MT39 x10y9 kill redKnight [HP 1021->861, G 943->1008] (+65G)
- MT39 x8y10 open yellowDoor [DEF 150->154, YK 4->3, G 1008->1093] (auto: x6y11 slimeMan, x5y9 swordsman, x6y9 blueGem)
- MT39 x4y10 open yellowDoor (auto: x3y11 yellowKey)
- MT39 x2y10 kill ghostSkeleton [HP 861->835, G 1093->1128] (+35G)
- MT39 x2y8 open blueDoor [BK 1->0]
- MT39 x4y2 open yellowDoor [YK 3->2]
- MT39 x6y4 open yellowDoor [YK 2->1]
- MT39 x4y4 reward centerFly3
- MT39 x4y4 take centerFly3
- MT39 x11y11 pass upFloor
- after: HP=835 ATK=162 DEF=154 YK=1 BK=0 RK=0 G=1128 dmg=7276 door=27/2/1

### MT40

- before: HP=835 ATK=162 DEF=154 YK=1 BK=0 RK=0 G=1128 dmg=7276 door=27/2/1
- MT40 x2y1 event centerFly3
- MT40 x2y2 kill swordsman [G 1128->1293] (auto: x3y2 swordsman, x4y2 swordsman) (+165G)
- MT40 x3y4 kill ghostSkeleton [HP 835->809, G 1293->1328] (+35G)
- MT40 x4y4 kill ghostSkeleton [HP 809->783, G 1328->1363] (+35G)
- MT40 x5y4 kill ghostSkeleton [HP 783->757, G 1363->1398] (+35G)
- MT40 x7y4 kill soldier [HP 757->665, G 1398->1443] (+45G)
- MT40 x8y4 kill soldier [HP 665->573, G 1443->1488] (+45G)
- MT40 x9y4 kill soldier [HP 573->481, G 1488->1533] (+45G)
- MT40 x8y2 kill redKnight [HP 481->329, G 1533->1598] (+65G)
- MT40 x9y2 kill redKnight [HP 329->177, G 1598->1663] (+65G)
- MT40 x10y2 kill redKnight [HP 177->25, G 1663->1728] (+65G)
- MT40 x6y7 reward yellowKnight [G 1728->1828] (auto: +100G)
- MT40 x2y2 take yellowKey [ATK 162->174, DEF 154->166, YK 1->4] (auto: x3y2 yellowKey, x4y2 yellowKey, x8y2 redGem, x7y4 blueGem, x9y2 redGem, x8y4 blueGem, x10y2 redGem, x9y4 blueGem)
- MT40 x6y1 pass upFloor
- after: HP=25 ATK=174 DEF=166 YK=4 BK=0 RK=0 G=1828 dmg=8086 door=27/2/1
