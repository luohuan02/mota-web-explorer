# 当前最优 Walk (zone4, auto ON)

## 说明

- 全防录像（2区2攻+买800rk+全防 2120）经 recording_seed_to_game.py 转换。MT50 redKing 走位步由 converter 根因修复（_coalesce_redundant_arrivals 保留 redKing 键盘触发前定位 到达，免手动重插）
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk best/zone12_2atk6def_39944_walk.json --load-slot 1 --target-click-only --set-auto battle=false,item=false,wall=false`
- 源 JSON：`best/zone12_2atk6def_39944_walk.json`

## 摘要

- final: HP=39944 ATK=374 DEF=607 YK=1 BK=0 RK=1 G=1707 dmg=13342 door=182/23/10 MT50 x6y5

## Walk

### MT4

- before: HP=926 ATK=10 DEF=10 YK=4 BK=1 RK=0 G=7 dmg=0 door=0/0/0
- MT4 x11y10 设置自动：battle=false, item=false, wall=false
- MT4 x11y10 设置自动：battle=true, item=true, wall=true
- MT4 x11y8 open yellowDoor [YK 4->3]
- MT4 x3y7 kill greenSlime [HP 926->902, G 7->8] (+1G)
- MT4 x1y7 kill redSlime [HP 902->852, G 8->10] (+2G)
- MT4 x1y8 open yellowDoor [YK 3->2]
- MT4 x1y11 pass upFloor
- after: HP=852 ATK=10 DEF=10 YK=2 BK=1 RK=0 G=10 dmg=74 door=2/0/0

### MT5

- before: HP=852 ATK=10 DEF=10 YK=2 BK=1 RK=0 G=10 dmg=74 door=2/0/0
- MT5 x6y8 kill greenSlime [HP 852->828, G 10->11] (+1G)
- MT5 x7y6 kill greenSlime [HP 828->804, G 11->12] (+1G)
- MT5 x11y7 kill redSlime [HP 804->754, G 12->14] (+2G)
- MT5 x8y9 open yellowDoor [YK 2->1]
- MT5 x8y11 move [ATK 10->20] (auto: x9y11 fakeWall, x11y11 sword1)
- MT5 x11y2 kill redSlime [HP 754->734, G 14->16] (+2G)
- MT5 x10y1 open yellowDoor [YK 1->0]
- MT5 x8y2 kill greenSlime [HP 734->726, YK 0->4, G 16->17] (auto: x8y3 yellowKey, x8y4 yellowKey, x9y3 yellowKey, x9y4 yellowKey) (+1G)
- MT5 x1y11 pass downFloor
- after: HP=726 ATK=20 DEF=10 YK=4 BK=1 RK=0 G=17 dmg=200 door=4/0/0

### MT4

- before: HP=726 ATK=20 DEF=10 YK=4 BK=1 RK=0 G=17 dmg=200 door=4/0/0
- MT4 x8y8 open yellowDoor [YK 4->3]
- MT4 x8y9 kill bluePriest [HP 726->688, ATK 20->21, G 17->22] (auto: x7y10 redGem, x9y10 redPotion) (+5G)
- MT4 x4y8 open yellowDoor [YK 3->2]
- MT4 x4y9 kill bat [HP 688->660, YK 2->4, G 22->25] (auto: x5y10 yellowKey, x5y11 yellowKey) (+3G)
- MT4 x3y10 kill greenSlime [HP 660->652, YK 4->5, G 25->26] (auto: x3y11 yellowKey) (+1G)
- MT4 x1y11 pass upFloor
- after: HP=652 ATK=21 DEF=10 YK=5 BK=1 RK=0 G=26 dmg=324 door=6/0/0

### MT5

- before: HP=652 ATK=21 DEF=10 YK=5 BK=1 RK=0 G=26 dmg=324 door=6/0/0
- MT5 x6y4 kill bat [HP 652->624, YK 5->6, G 26->29] (auto: x6y2 yellowKey) (+3G)
- MT5 x5y1 open yellowDoor [YK 6->5]
- MT5 x4y1 kill redSlime [HP 624->604, G 29->31] (+2G)
- MT5 x4y4 open yellowDoor [YK 5->4]
- MT5 x4y6 kill bat [HP 604->576, YK 4->6, G 31->34] (auto: x1y6 yellowKey, x1y5 yellowKey) (+3G)
- MT5 x3y3 kill bat [HP 576->548, G 34->37] (+3G)
- MT5 x2y3 open yellowDoor [YK 6->5]
- MT5 x1y1 pass upFloor
- after: HP=548 ATK=21 DEF=10 YK=5 BK=1 RK=0 G=37 dmg=428 door=9/0/0

### MT6

- before: HP=548 ATK=21 DEF=10 YK=5 BK=1 RK=0 G=37 dmg=428 door=9/0/0
- MT6 x3y6 kill redSlime [HP 548->528, G 37->39] (+2G)
- MT6 x4y6 kill bluePriest [HP 528->440, YK 5->6, G 39->44] (auto: x6y6 yellowKey) (+5G)
- MT6 x5y4 open yellowDoor [YK 6->5]
- MT6 x4y3 kill redSlime [HP 440->420, YK 5->9, G 44->46] (auto: x4y2 yellowKey, x4y1 yellowKey, x3y2 yellowKey, x3y1 yellowKey) (+2G)
- MT6 x7y8 open yellowDoor [YK 9->8]
- MT6 x8y8 open yellowDoor [YK 8->7]
- MT6 x10y8 open yellowDoor [YK 7->6]
- MT6 x11y9 kill redSlime [HP 420->400, G 46->48] (+2G)
- MT6 x11y11 pass upFloor
- after: HP=400 ATK=21 DEF=10 YK=6 BK=1 RK=0 G=48 dmg=576 door=13/0/0

### MT7

- before: HP=400 ATK=21 DEF=10 YK=6 BK=1 RK=0 G=48 dmg=576 door=13/0/0
- MT7 x11y7 open yellowDoor [YK 6->5]
- MT7 x4y6 kill bluePriest [HP 400->312, G 48->53] (+5G)
- MT7 x3y5 open yellowDoor [YK 5->4]
- MT7 x3y3 kill bat [HP 312->334, ATK 21->22, G 53->56] (auto: x3y2 redPotion, x3y1 redGem) (+3G)
- MT7 x2y6 kill skeletonSoldier [HP 334->124, G 56->64] (+8G)
- MT7 x1y5 open yellowDoor [YK 4->3]
- MT7 x1y1 pass upFloor
- after: HP=124 ATK=22 DEF=10 YK=3 BK=1 RK=0 G=64 dmg=902 door=16/0/0

### MT8

- before: HP=124 ATK=22 DEF=10 YK=3 BK=1 RK=0 G=64 dmg=902 door=16/0/0
- MT8 x3y1 open yellowDoor [YK 3->2]
- MT8 x4y1 open yellowDoor [YK 2->1]
- MT8 x6y3 open yellowDoor [YK 1->0]
- MT8 x6y1 pass upFloor
- after: HP=124 ATK=22 DEF=10 YK=0 BK=1 RK=0 G=64 dmg=902 door=19/0/0

### MT9

- before: HP=124 ATK=22 DEF=10 YK=0 BK=1 RK=0 G=64 dmg=902 door=19/0/0
- MT9 x6y1 pass downFloor
- after: HP=124 ATK=22 DEF=10 YK=0 BK=1 RK=0 G=64 dmg=902 door=19/0/0

### MT8

- before: HP=124 ATK=22 DEF=10 YK=0 BK=1 RK=0 G=64 dmg=902 door=19/0/0
- MT8 x6y4 move [YK 0->3] (auto: x5y4 yellowKey, x4y4 yellowKey, x3y4 yellowKey)
- MT8 x6y1 pass upFloor
- after: HP=124 ATK=22 DEF=10 YK=3 BK=1 RK=0 G=64 dmg=902 door=19/0/0

### MT9

- before: HP=124 ATK=22 DEF=10 YK=3 BK=1 RK=0 G=64 dmg=902 door=19/0/0
- MT9 x8y1 open yellowDoor [YK 3->2]
- MT9 x9y1 kill greenSlime [HP 124->166, DEF 10->20, G 64->65] (auto: x11y1 redPotion, x10y5 fakeWall, x9y7 shield1) (+1G)
- MT9 x10y4 move [G 65->66] (auto: x10y2 greenSlime)
- MT9 x9y4 open yellowDoor [YK 2->1]
- MT9 x8y4 open yellowDoor [YK 1->0]
- MT9 x8y4 move [ATK 22->23, YK 0->2, G 66->68] (auto: x7y4 yellowKey, x5y4 yellowKey, x6y5 redGem, x7y6 redSlime)
- MT9 x4y5 open yellowDoor [YK 2->1]
- MT9 x3y5 kill bat [HP 166->148, DEF 20->21, YK 1->2, G 68->71] (auto: x2y4 yellowKey, x1y5 blueGem) (+3G)
- after: HP=148 ATK=23 DEF=21 YK=2 BK=1 RK=0 G=71 dmg=928 door=23/0/0

### MT6

- before: HP=148 ATK=23 DEF=21 YK=2 BK=1 RK=0 G=71 dmg=928 door=23/0/0
- MT6 x11y10 fly
- MT6 x6y11 move [HP 148->248, G 71->73] (auto: x9y9 redSlime, x9y11 redPotion, x8y11 redPotion)
- MT6 x5y11 kill skeleton [HP 248->206, G 73->80] (auto: x2y11 greenSlime) (+7G)
- MT6 x1y10 open yellowDoor [YK 2->1]
- MT6 x2y9 kill bat [HP 206->189, DEF 21->22, G 80->83] (auto: x4y9 blueGem) (+3G)
- after: HP=189 ATK=23 DEF=22 YK=1 BK=1 RK=0 G=83 dmg=987 door=24/0/0

### MT3

- before: HP=189 ATK=23 DEF=22 YK=1 BK=1 RK=0 G=83 dmg=987 door=24/0/0
- MT3 x10y11 fly
- MT3 x3y5 kill bat [HP 189->173, G 83->86] (+3G)
- MT3 x1y4 open yellowDoor [YK 1->0]
- MT3 x1y3 kill bluePriest [HP 173->193, DEF 22->23, YK 0->1, G 86->91] (auto: x1y1 yellowKey, x2y2 redPotion, x2y1 blueGem) (+5G)
- after: HP=193 ATK=23 DEF=23 YK=1 BK=1 RK=0 G=91 dmg=1033 door=25/0/0

### MT8

- before: HP=193 ATK=23 DEF=23 YK=1 BK=1 RK=0 G=91 dmg=1033 door=25/0/0
- MT8 x1y2 fly
- MT8 x7y4 move [G 91->92] (auto: x7y2 greenSlime)
- MT8 x7y5 kill bluePriest [HP 193->166, G 92->97] (+5G)
- MT8 x7y7 kill bat [HP 166->151, G 97->100] (+3G)
- MT8 x6y8 kill skeleton [HP 151->113, G 100->106] (+6G)
- MT8 x4y8 kill bat [HP 113->98, G 106->109] (+3G)
- MT8 x1y9 open yellowDoor [YK 1->0]
- MT8 x1y9 move [G 109->110] (auto: x1y10 greenSlime)
- MT8 x2y11 kill bat [HP 98->83, G 110->113] (+3G)
- MT8 x3y11 open blueDoor [BK 1->0]
- MT8 x3y11 move [ATK 23->24, DEF 23->24, YK 0->2] (auto: x4y11 yellowKey, x4y10 redGem, x5y11 blueGem, x5y10 yellowKey)
- after: HP=83 ATK=24 DEF=24 YK=2 BK=0 RK=0 G=113 dmg=1143 door=26/1/0

### MT1

- before: HP=83 ATK=24 DEF=24 YK=2 BK=0 RK=0 G=113 dmg=1143 door=26/1/0
- MT1 x2y1 fly
- MT1 x6y6 open yellowDoor [YK 2->1]
- MT1 x7y6 kill bat [HP 83->69, G 113->116] (+3G)
- MT1 x8y6 kill bluePriest [HP 69->45, G 116->121] (+5G)
- MT1 x9y6 kill bat [HP 45->31, G 121->124] (+3G)
- MT1 x9y5 open yellowDoor [YK 1->0]
- MT1 x9y4 move [HP 31->81, ATK 24->25, DEF 24->25, YK 0->1] (auto: x8y4 redPotion, x8y3 yellowKey, x7y4 blueGem, x7y3 redGem)
- after: HP=81 ATK=25 DEF=25 YK=1 BK=0 RK=0 G=124 dmg=1195 door=28/1/0

### MT3

- before: HP=81 ATK=25 DEF=25 YK=1 BK=0 RK=0 G=124 dmg=1195 door=28/1/0
- MT3 x2y11 fly
- MT3 x1y6 open yellowDoor [YK 1->0]
- MT3 x1y7 kill skeleton [HP 81->97, ATK 25->26, YK 0->1, G 124->130] (auto: x1y9 redPotion, x2y8 yellowKey, x2y9 redGem) (+6G)
- after: HP=97 ATK=26 DEF=25 YK=1 BK=0 RK=0 G=130 dmg=1229 door=29/1/0

### MT5

- before: HP=97 ATK=26 DEF=25 YK=1 BK=0 RK=0 G=130 dmg=1229 door=29/1/0
- MT5 x2y11 fly
- MT5 x2y6 move [G 130->131] (auto: x9y2 greenSlime)
- MT5 x2y7 kill skeletonSoldier [HP 97->66, DEF 25->26, YK 1->2, G 131->139] (auto: x2y9 yellowKey, x1y9 blueGem, x3y9 redPotion, x4y9 wand) (+8G)
- MT5 x1y11 pass downFloor
- after: HP=66 ATK=26 DEF=26 YK=2 BK=0 RK=0 G=139 dmg=1310 door=29/1/0

### MT4

- before: HP=66 ATK=26 DEF=26 YK=2 BK=0 RK=0 G=139 dmg=1310 door=29/1/0
- MT4 x1y5 move [G 139->141] (auto: x4y11 greenSlime, x8y11 greenSlime)
- MT4 x2y5 kill bluePriest [HP 66->48, G 141->146] (+5G)
- MT4 x2y4 open yellowDoor [YK 2->1]
- MT4 x2y2 move [HP 48->98, YK 1->2, BK 0->1] (auto: x2y1 blueKey, x1y2 redPotion, x3y2 yellowKey)
- after: HP=98 ATK=26 DEF=26 YK=2 BK=1 RK=0 G=146 dmg=1328 door=30/1/0

### MT9

- before: HP=98 ATK=26 DEF=26 YK=2 BK=1 RK=0 G=146 dmg=1328 door=30/1/0
- MT9 x6y2 fly
- MT9 x7y10 kill bat [HP 98->86, G 146->149] (+3G)
- MT9 x6y11 open yellowDoor [YK 2->1]
- MT9 x3y11 open blueDoor [BK 1->0]
- MT9 x2y11 move [HP 86->136] (auto: x2y10 redPotion)
- MT9 x1y11 pass upFloor
- after: HP=136 ATK=26 DEF=26 YK=1 BK=0 RK=0 G=149 dmg=1340 door=31/2/0

### MT10

- before: HP=136 ATK=26 DEF=26 YK=1 BK=0 RK=0 G=149 dmg=1340 door=31/2/0
- MT10 x1y9 open yellowDoor [YK 1->0]
- MT10 x1y6 kill skeleton [HP 136->104, DEF 26->27, G 149->155] (auto: x2y6 blueGem) (+6G)
- after: HP=104 ATK=26 DEF=27 YK=0 BK=0 RK=0 G=155 dmg=1372 door=32/2/0

### MT7

- before: HP=104 ATK=26 DEF=27 YK=0 BK=0 RK=0 G=155 dmg=1372 door=32/2/0
- MT7 x1y2 fly
- MT7 x9y5 kill skeleton [HP 104->124, YK 0->2, G 155->161] (auto: x9y3 redPotion, x9y2 yellowKey, x9y1 yellowKey) (+6G)
- MT7 x5y7 open yellowDoor [YK 2->1]
- MT7 x5y9 kill bat [HP 124->113, YK 1->3, G 161->164] (auto: x5y10 yellowKey, x5y11 yellowKey) (+3G)
- MT7 x9y7 kill skeletonSoldier [HP 113->238, YK 3->5, G 164->172] (auto: x9y9 bluePotion, x9y10 yellowKey, x9y11 yellowKey) (+8G)
- after: HP=238 ATK=26 DEF=27 YK=5 BK=0 RK=0 G=172 dmg=1488 door=33/2/0

### MT10

- before: HP=238 ATK=26 DEF=27 YK=5 BK=0 RK=0 G=172 dmg=1488 door=33/2/0
- MT10 x1y10 fly
- MT10 x3y9 open yellowDoor [YK 5->4]
- MT10 x4y11 kill bluePriest [HP 238->223, G 172->177] (+5G)
- MT10 x8y11 kill bluePriest [HP 223->208, G 177->182] (+5G)
- MT10 x9y9 open yellowDoor [YK 4->3]
- MT10 x9y6 kill skeleton [HP 208->178, ATK 26->27, G 182->188] (auto: x10y6 redGem) (+6G)
- MT10 x11y9 open yellowDoor [YK 3->2]
- MT10 x11y9 move [HP 178->378] (auto: x11y11 bluePotion)
- after: HP=378 ATK=27 DEF=27 YK=2 BK=0 RK=0 G=188 dmg=1548 door=36/2/0

### MT7

- before: HP=378 ATK=27 DEF=27 YK=2 BK=0 RK=0 G=188 dmg=1548 door=36/2/0
- MT7 x1y2 fly
- MT7 x7y7 open yellowDoor [YK 2->1]
- MT7 x7y8 move [G 188->190] (auto: x7y9 redSlime)
- MT7 x7y10 kill bluePriest [HP 378->563, G 190->195] (auto: x7y11 bluePotion) (+5G)
- MT7 x1y1 pass upFloor
- after: HP=563 ATK=27 DEF=27 YK=1 BK=0 RK=0 G=195 dmg=1563 door=37/2/0

### MT8

- before: HP=563 ATK=27 DEF=27 YK=1 BK=0 RK=0 G=195 dmg=1563 door=37/2/0
- MT8 x8y8 kill bluePriest [HP 563->548, G 195->200] (+5G)
- MT8 x10y7 open yellowDoor [YK 1->0]
- MT8 x9y5 kill yellowGuard [HP 548->359, G 200->212] (+12G)
- MT8 x11y5 kill yellowGuard [HP 359->170, G 212->224] (+12G)
- MT8 x10y3 move [HP 170->420, YK 0->2, RK 0->1] (auto: x10y2 redKey, x9y3 bluePotion, x11y3 redPotion, x9y1 yellowKey, x11y1 yellowKey)
- after: HP=420 ATK=27 DEF=27 YK=2 BK=0 RK=1 G=224 dmg=1956 door=38/2/0

### MT1

- before: HP=420 ATK=27 DEF=27 YK=2 BK=0 RK=1 G=224 dmg=1956 door=38/2/0
- MT1 x2y1 fly
- MT1 x10y9 open yellowDoor [YK 2->1]
- MT1 x10y10 kill bat [HP 420->609, G 224->229] (auto: x10y11 bluePotion, x9y11 greenSlime, x11y11 greenSlime) (+5G)
- MT1 x4y3 open yellowDoor [YK 1->0]
- MT1 x2y3 move [HP 609->659] (auto: x1y3 redPotion)
- after: HP=659 ATK=27 DEF=27 YK=0 BK=0 RK=1 G=229 dmg=1967 door=40/2/0

### MT10

- before: HP=659 ATK=27 DEF=27 YK=0 BK=0 RK=1 G=229 dmg=1967 door=40/2/0
- MT10 x1y10 fly
- MT10 x6y9 open redDoor [RK 1->0]
- MT10 x6y4 kill skeletonSoldier [HP 659->584, G 229->237] (+8G)
- MT10 x5y4 kill skeleton [HP 584->554, G 237->243] (+6G)
- MT10 x5y5 kill skeleton [HP 554->524, G 243->249] (+6G)
- MT10 x5y6 kill skeleton [HP 524->494, G 249->255] (+6G)
- MT10 x6y6 kill skeletonSoldier [HP 494->419, G 255->263] (+8G)
- MT10 x7y6 kill skeleton [HP 419->389, G 263->269] (+6G)
- MT10 x7y5 kill skeleton [HP 389->359, G 269->275] (+6G)
- MT10 x7y4 kill skeleton [HP 359->329, G 275->281] (+6G)
- MT10 x6y1 kill skeletonCaptain [HP 329->25, G 281->311] (+30G)
- MT10 x6y8 move [HP 25->625, ATK 27->30, DEF 27->30, YK 0->3] (auto: x3y4 bluePotion, x9y4 yellowKey, x3y3 redGem, x2y4 bluePotion, x9y3 blueGem, x10y4 yellowKey, x2y3 redGem, x1y4 bluePotion, x10y3 blueGem, x11y4 yellowKey, x1y3 redGem, x11y3 blueGem)
- MT10 x6y11 pass upFloor
- after: HP=625 ATK=30 DEF=30 YK=3 BK=0 RK=0 G=311 dmg=2601 door=40/2/1

### MT11

- before: HP=625 ATK=30 DEF=30 YK=3 BK=0 RK=0 G=311 dmg=2601 door=40/2/1
- MT11 x10y9 kill bat [HP 625->617, G 311->314] (+3G)
- MT11 x11y11 pass upFloor
- after: HP=617 ATK=30 DEF=30 YK=3 BK=0 RK=0 G=314 dmg=2609 door=40/2/1

### MT12

- before: HP=617 ATK=30 DEF=30 YK=3 BK=0 RK=0 G=314 dmg=2609 door=40/2/1
- MT12 x8y11 kill bat [HP 617->809, G 314->317] (auto: x7y10 redPotion, x5y10 redPotion) (+3G)
- MT12 x6y9 shop atk [ATK 30->34, G 317->297]
- MT12 x6y9 shop atk [ATK 34->38, G 297->257]
- MT12 x5y11 move [G 257->260] (auto: x4y11 bat)
- MT12 x1y11 pass upFloor
- after: HP=809 ATK=38 DEF=30 YK=3 BK=0 RK=0 G=260 dmg=2617 door=40/2/1

### MT13

- before: HP=809 ATK=38 DEF=30 YK=3 BK=0 RK=0 G=260 dmg=2617 door=40/2/1
- MT13 x11y11 pass upFloor
- after: HP=809 ATK=38 DEF=30 YK=3 BK=0 RK=0 G=260 dmg=2617 door=40/2/1

### MT14

- before: HP=809 ATK=38 DEF=30 YK=3 BK=0 RK=0 G=260 dmg=2617 door=40/2/1
- MT14 x9y9 open yellowDoor [YK 3->2]
- MT14 x8y8 kill blackSlime [HP 809->719, G 260->268] (+8G)
- MT14 x6y8 open yellowDoor [YK 2->1]
- MT14 x6y8 move [HP 719->819] (auto: x6y9 fakeWall, x5y10 redPotion)
- MT14 x6y11 pass upFloor
- after: HP=819 ATK=38 DEF=30 YK=1 BK=0 RK=0 G=268 dmg=2707 door=42/2/1

### MT7

- before: HP=819 ATK=38 DEF=30 YK=1 BK=0 RK=0 G=268 dmg=2707 door=42/2/1
- MT7 x1y2 fly
- MT7 x7y5 open yellowDoor [YK 1->0]
- MT7 x7y3 kill skeletonSoldier [HP 819->775, G 268->278] (auto: x5y3 redSlime) (+10G)
- MT7 x6y1 trader yellowKey5 [YK 0->5, G 278->228]
- after: HP=775 ATK=38 DEF=30 YK=5 BK=0 RK=0 G=228 dmg=2751 door=43/2/1

### MT15

- before: HP=775 ATK=38 DEF=30 YK=5 BK=0 RK=0 G=228 dmg=2751 door=43/2/1
- MT15 x6y10 fly
- MT15 x8y11 open yellowDoor [YK 5->4]
- MT15 x8y11 move [G 228->234] (auto: x9y11 bat, x10y10 bat)
- MT15 x11y11 trader blueKey1_15 [BK 0->1, G 234->34]
- MT15 x9y9 open yellowDoor [YK 4->3]
- MT15 x9y6 open yellowDoor [YK 3->2]
- MT15 x9y4 kill bigBat [HP 775->705, G 34->46] (+12G)
- MT15 x11y3 open yellowDoor [YK 2->1]
- MT15 x11y2 kill blackSlime [HP 705->615, G 46->54] (+8G)
- MT15 x9y1 event thief
- MT15 x6y1 pass upFloor
- after: HP=615 ATK=38 DEF=30 YK=1 BK=1 RK=0 G=54 dmg=2911 door=47/2/1

### MT16

- before: HP=615 ATK=38 DEF=30 YK=1 BK=1 RK=0 G=54 dmg=2911 door=47/2/1
- MT16 x6y3 move [YK 1->2] (auto: x7y3 yellowKey)
- MT16 x6y4 open blueDoor [BK 1->0]
- MT16 x6y5 move [HP 615->715, YK 2->3] (auto: x5y5 redPotion, x7y7 yellowKey)
- MT16 x6y8 open yellowDoor [YK 3->2]
- MT16 x4y10 open yellowDoor [YK 2->1]
- MT16 x2y9 kill blackSlime [HP 715->725, ATK 38->40, DEF 30->32, YK 1->3, G 54->62] (auto: x2y8 fakeWall, x2y7 yellowKey, x1y7 blueGem, x2y5 yellowKey, x1y6 redPotion, x1y5 redGem) (+8G)
- MT16 x6y11 pass upFloor
- after: HP=725 ATK=40 DEF=32 YK=3 BK=0 RK=0 G=62 dmg=3001 door=49/3/1

### MT17

- before: HP=725 ATK=40 DEF=32 YK=3 BK=0 RK=0 G=62 dmg=3001 door=49/3/1
- MT17 x4y11 kill bigBat [HP 725->757, G 62->74] (auto: x1y11 redPotion) (+12G)
- MT17 x2y10 open yellowDoor [YK 3->2]
- MT17 x1y8 kill yellowGuard [HP 757->725, G 74->86] (+12G)
- MT17 x3y8 kill yellowGuard [HP 725->693, G 86->98] (+12G)
- MT17 x1y5 kill yellowGuard [HP 693->661, G 98->110] (+12G)
- MT17 x3y5 kill yellowGuard [HP 661->629, G 110->122] (+12G)
- MT17 x1y2 move [ATK 40->60] (auto: x2y2 sword2)
- after: HP=629 ATK=60 DEF=32 YK=2 BK=0 RK=0 G=122 dmg=3197 door=50/3/1

### MT6

- before: HP=629 ATK=60 DEF=32 YK=2 BK=0 RK=0 G=122 dmg=3197 door=50/3/1
- MT6 x11y10 fly
- MT6 x6y1 move [YK 2->3, G 122->139] (auto: x7y1 bluePriest, x9y1 yellowKey, x10y1 greenSlime, x8y6 skeleton, x1y8 bluePriest)
- MT6 x11y2 open yellowDoor [YK 3->2]
- MT6 x11y3 move [HP 629->679, G 139->148] (auto: x10y3 skeleton, x11y4 bat, x8y3 redPotion)
- MT6 x8y4 trader blueKey1 [BK 0->1, G 148->98]
- after: HP=679 ATK=60 DEF=32 YK=2 BK=1 RK=0 G=98 dmg=3197 door=51/3/1

### MT11

- before: HP=679 ATK=60 DEF=32 YK=2 BK=1 RK=0 G=98 dmg=3197 door=51/3/1
- MT11 x6y10 fly
- MT11 x5y9 open yellowDoor [YK 2->1]
- MT11 x4y9 kill blackSlime [HP 679->623, YK 1->6, G 98->106] (auto: x4y11 yellowKey, x3y11 yellowKey, x1y10 yellowKey, x2y11 yellowKey, x1y11 yellowKey) (+8G)
- MT11 x2y9 kill bigBat [HP 623->555, G 106->118] (+12G)
- MT11 x2y8 open blueDoor [BK 1->0]
- MT11 x1y6 move [HP 555->955] (auto: x1y7 bluePotion)
- MT11 x1y5 kill redPriest [HP 955->766, G 118->140] (+22G)
- MT11 x3y5 kill redPriest [HP 766->577, G 140->162] (+22G)
- MT11 x1y2 move [DEF 32->52] (auto: x2y2 shield2)
- after: HP=577 ATK=60 DEF=52 YK=6 BK=0 RK=0 G=162 dmg=3699 door=52/4/1

### MT9

- before: HP=577 ATK=60 DEF=52 YK=6 BK=0 RK=0 G=162 dmg=3699 door=52/4/1
- MT9 x1y10 fly
- MT9 x1y4 move [YK 6->7, G 162->190] (auto: x1y3 skeletonSoldier, x2y2 yellowKey, x3y1 skeleton, x11y6 skeletonSoldier, x5y10 skeleton)
- MT9 x1y9 open yellowDoor [YK 7->6]
- MT9 x1y9 move [YK 6->7, G 190->198] (auto: x1y8 skeletonSoldier, x1y7 yellowKey)
- MT9 x3y7 open yellowDoor [YK 7->6]
- MT9 x3y7 move [YK 6->7, G 198->206] (auto: x4y7 skeletonSoldier, x5y7 yellowKey)
- after: HP=577 ATK=60 DEF=52 YK=7 BK=0 RK=0 G=206 dmg=3699 door=54/4/1

### MT8

- before: HP=577 ATK=60 DEF=52 YK=7 BK=0 RK=0 G=206 dmg=3699 door=54/4/1
- MT8 x6y2 fly
- MT8 x11y9 open yellowDoor [YK 7->6]
- MT8 x11y9 move [G 206->220] (auto: x11y10 skeleton, x10y11 skeletonSoldier)
- MT8 x9y11 open yellowDoor [YK 6->5]
- MT8 x1y2 move [HP 577->627, YK 5->6, BK 0->1] (auto: x8y10 redPotion, x7y11 yellowKey, x7y10 blueKey)
- MT8 x1y1 pass downFloor
- after: HP=627 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=220 dmg=3699 door=56/4/1

### MT7

- before: HP=627 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=220 dmg=3699 door=56/4/1
- MT7 x11y11 pass downFloor
- after: HP=627 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=220 dmg=3699 door=56/4/1

### MT6

- before: HP=627 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=220 dmg=3699 door=56/4/1
- MT6 x8y3 move [G 220->228] (auto: x9y6 skeletonSoldier)
- MT6 x1y1 pass downFloor
- after: HP=627 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=228 dmg=3699 door=56/4/1

### MT5

- before: HP=627 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=228 dmg=3699 door=56/4/1
- MT5 x2y11 move [G 228->233] (auto: x3y5 bluePriest)
- MT5 x1y11 pass downFloor
- after: HP=627 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=233 dmg=3699 door=56/4/1

### MT4

- before: HP=627 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=233 dmg=3699 door=56/4/1
- MT4 x4y5 open yellowDoor [YK 6->5]
- MT4 x5y5 move [G 233->241] (auto: x6y5 redSlime, x9y5 skeleton)
- MT4 x10y4 open yellowDoor [YK 5->4]
- MT4 x10y4 move [HP 627->827, YK 4->5, G 241->249] (auto: x10y3 skeletonSoldier, x9y2 yellowKey, x11y2 bluePotion)
- after: HP=827 ATK=60 DEF=52 YK=5 BK=1 RK=0 G=249 dmg=3699 door=58/4/1

### MT1

- before: HP=827 ATK=60 DEF=52 YK=5 BK=1 RK=0 G=249 dmg=3699 door=58/4/1
- MT1 x2y1 fly
- MT1 x1y4 move [G 249->255] (auto: x2y4 skeleton)
- MT1 x2y5 open yellowDoor [YK 5->4]
- MT1 x2y6 move [YK 4->5, G 255->263] (auto: x1y6 yellowKey, x2y7 skeletonSoldier)
- MT1 x2y8 open yellowDoor [YK 5->4]
- MT1 x2y10 move [HP 827->927, YK 4->6] (auto: x1y10 redPotion, x2y11 fly, x3y10 yellowKey, x1y11 redPotion, x3y11 yellowKey)
- after: HP=927 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=263 dmg=3699 door=60/4/1

### MT15

- before: HP=927 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=263 dmg=3699 door=60/4/1
- MT15 x6y10 fly
- MT15 x4y1 open yellowDoor [YK 6->5]
- MT15 x1y2 kill zombie [HP 927->795, DEF 52->54, G 263->281] (auto: x1y1 blueGem) (+18G)
- after: HP=795 ATK=60 DEF=54 YK=5 BK=1 RK=0 G=281 dmg=3831 door=61/4/1

### MT12

- before: HP=795 ATK=60 DEF=54 YK=5 BK=1 RK=0 G=281 dmg=3831 door=61/4/1
- MT12 x2y11 fly
- MT12 x11y9 kill zombie [HP 795->671, G 281->299] (+18G)
- MT12 x11y8 open yellowDoor [YK 5->4]
- MT12 x11y7 kill blackSlime [HP 671->759, DEF 54->56, YK 4->5, G 299->307] (auto: x10y6 blueGem, x9y7 yellowKey, x9y5 redPotion) (+8G)
- MT12 x8y6 open yellowDoor [YK 5->4]
- MT12 x7y6 kill redPriest [HP 759->1042, G 307->329] (auto: x6y7 bluePotion) (+22G)
- MT12 x6y5 kill zombie [HP 1042->926, G 329->347] (+18G)
- MT12 x6y4 open yellowDoor [YK 4->3]
- MT12 x7y3 kill redPriest [HP 926->809, ATK 60->62, YK 3->5, G 347->369] (auto: x7y1 yellowKey, x6y1 redGem, x5y1 yellowKey) (+22G)
- MT12 x11y11 pass downFloor
- after: HP=809 ATK=62 DEF=56 YK=5 BK=1 RK=0 G=369 dmg=4317 door=64/4/1

### MT11

- before: HP=809 ATK=62 DEF=56 YK=5 BK=1 RK=0 G=369 dmg=4317 door=64/4/1
- MT11 x11y8 kill bigBat [HP 809->765, G 369->381] (+12G)
- MT11 x11y4 kill blackSlime [HP 765->857, YK 5->6, G 381->389] (auto: x11y1 yellowKey, x10y1 redPotion) (+8G)
- MT11 x9y3 open yellowDoor [YK 6->5]
- MT11 x8y2 kill zombie [HP 857->741, G 389->407] (+18G)
- MT11 x7y1 open yellowDoor [YK 5->4]
- MT11 x6y1 move [ATK 62->64, G 407->410] (auto: x5y1 redGem, x6y2 bat)
- after: HP=741 ATK=64 DEF=56 YK=4 BK=1 RK=0 G=410 dmg=4485 door=66/4/1

### MT17

- before: HP=741 ATK=64 DEF=56 YK=4 BK=1 RK=0 G=410 dmg=4485 door=66/4/1
- MT17 x5y11 fly
- MT17 x6y9 kill redPriest [HP 741->663, G 410->432] (+22G)
- MT17 x7y7 kill blackSlime [HP 663->655, G 432->440] (+8G)
- MT17 x7y5 open blueDoor [BK 1->0]
- MT17 x7y3 kill bigBat [HP 655->611, G 440->452] (+12G)
- MT17 x6y1 pass upFloor
- after: HP=611 ATK=64 DEF=56 YK=4 BK=0 RK=0 G=452 dmg=4615 door=66/5/1

### MT18

- before: HP=611 ATK=64 DEF=56 YK=4 BK=0 RK=0 G=452 dmg=4615 door=66/5/1
- MT18 x8y1 open yellowDoor [YK 4->3]
- MT18 x9y1 kill redPriest [HP 611->533, YK 3->7, BK 0->1, G 452->474] (auto: x11y1 yellowKey, x11y2 yellowKey, x11y3 blueKey, x11y4 yellowKey, x11y5 yellowKey) (+22G)
- MT18 x5y4 kill zombieKnight [HP 533->149, G 474->504] (+30G)
- MT18 x4y4 open yellowDoor [YK 7->6]
- MT18 x3y4 move [HP 149->249] (auto: x2y4 redPotion)
- MT18 x1y3 open yellowDoor [YK 6->5]
- MT18 x1y1 pass upFloor
- after: HP=249 ATK=64 DEF=56 YK=5 BK=1 RK=0 G=504 dmg=5077 door=69/5/1

### MT19

- before: HP=249 ATK=64 DEF=56 YK=5 BK=1 RK=0 G=504 dmg=5077 door=69/5/1
- MT19 x1y3 open yellowDoor [YK 5->4]
- MT19 x1y3 move [G 504->507] (auto: x1y4 bat)
- MT19 x1y6 open yellowDoor [YK 4->3]
- MT19 x1y7 kill bigBat [HP 249->205, G 507->519] (+12G)
- MT19 x1y9 open yellowDoor [YK 3->2]
- MT19 x1y11 kill blackSlime [HP 205->197, G 519->527] (+8G)
- MT19 x3y11 kill bigBat [HP 197->153, G 527->539] (+12G)
- MT19 x4y10 open yellowDoor [YK 2->1]
- MT19 x4y10 move [YK 1->3] (auto: x5y10 yellowKey, x7y10 yellowKey)
- MT19 x6y11 pass upFloor
- after: HP=153 ATK=64 DEF=56 YK=3 BK=1 RK=0 G=539 dmg=5173 door=73/5/1

### MT20

- before: HP=153 ATK=64 DEF=56 YK=3 BK=1 RK=0 G=539 dmg=5173 door=73/5/1
- MT20 x4y11 kill redPriest [HP 153->175, G 539->561] (auto: x1y11 redPotion) (+22G)
- MT20 x1y9 open yellowDoor [YK 3->2]
- MT20 x1y8 move [G 561->567] (auto: x1y7 bat, x2y8 bat)
- MT20 x2y6 open blueDoor [BK 1->0]
- MT20 x2y6 move [ATK 64->66, DEF 56->58, YK 2->3] (auto: x2y4 blueGem, x1y5 yellowKey, x1y4 redGem)
- after: HP=175 ATK=66 DEF=58 YK=3 BK=0 RK=0 G=567 dmg=5251 door=74/6/1

### MT16

- before: HP=175 ATK=66 DEF=58 YK=3 BK=0 RK=0 G=567 dmg=5251 door=74/6/1
- MT16 x6y10 fly
- after: HP=175 ATK=66 DEF=58 YK=3 BK=0 RK=0 G=567 dmg=5251 door=74/6/1

### MT15

- before: HP=175 ATK=66 DEF=58 YK=3 BK=0 RK=0 G=567 dmg=5251 door=74/6/1
- MT15 x6y2 fly
- MT15 x1y4 open yellowDoor [YK 3->2]
- MT15 x1y7 kill blackSlime [HP 175->171, G 567->575] (+8G)
- MT15 x2y9 open yellowDoor [YK 2->1]
- MT15 x2y9 move [YK 1->3, BK 0->1] (auto: x3y7 yellowKey, x3y6 blueKey, x3y5 yellowKey)
- after: HP=171 ATK=66 DEF=58 YK=3 BK=1 RK=0 G=575 dmg=5255 door=76/6/1

### MT18

- before: HP=171 ATK=66 DEF=58 YK=3 BK=1 RK=0 G=575 dmg=5255 door=76/6/1
- MT18 x6y2 fly
- MT18 x6y6 open blueDoor [BK 1->0]
- MT18 x2y7 kill zombie [HP 171->63, G 575->593] (+18G)
- MT18 x1y8 open yellowDoor [YK 3->2]
- after: HP=63 ATK=66 DEF=58 YK=2 BK=0 RK=0 G=593 dmg=5363 door=77/7/1

### MT9

- before: HP=63 ATK=66 DEF=58 YK=2 BK=0 RK=0 G=593 dmg=5363 door=77/7/1
- MT9 x1y10 fly
- MT9 x8y11 open yellowDoor [YK 2->1]
- MT9 x8y11 move [HP 63->113, YK 1->2, G 593->609] (auto: x9y11 bluePriest, x9y9 yellowKey, x10y10 skeleton, x11y11 redPotion, x11y9 bluePriest)
- after: HP=113 ATK=66 DEF=58 YK=2 BK=0 RK=0 G=609 dmg=5363 door=78/7/1

### MT18

- before: HP=113 ATK=66 DEF=58 YK=2 BK=0 RK=0 G=609 dmg=5363 door=78/7/1
- MT18 x6y2 fly
- MT18 x1y9 kill redPriest [HP 113->139, ATK 66->68, YK 2->3, G 609->643] (auto: x1y11 redPotion, x2y10 yellowKey, x2y11 redGem, x10y5 bigBat) (+34G)
- after: HP=139 ATK=68 DEF=58 YK=3 BK=0 RK=0 G=643 dmg=5437 door=78/7/1

### MT19

- before: HP=139 ATK=68 DEF=58 YK=3 BK=0 RK=0 G=643 dmg=5437 door=78/7/1
- MT19 x1y2 fly
- MT19 x8y11 open yellowDoor [YK 3->2]
- MT19 x9y11 move [HP 139->239, YK 2->3, G 643->658] (auto: x10y11 bat, x11y10 bigBat, x10y9 yellowKey, x9y9 redPotion)
- MT19 x11y8 kill zombie [HP 239->131, G 658->676] (+18G)
- MT19 x11y7 open yellowDoor [YK 3->2]
- MT19 x10y5 kill blackSlime [HP 131->129, G 676->684] (+8G)
- MT19 x10y3 open yellowDoor [YK 2->1]
- MT19 x10y3 move [ATK 68->70, YK 1->2, G 684->696] (auto: x10y2 bigBat, x10y1 yellowKey, x11y1 redGem)
- after: HP=129 ATK=70 DEF=58 YK=2 BK=0 RK=0 G=696 dmg=5547 door=81/7/1

### MT16

- before: HP=129 ATK=70 DEF=58 YK=2 BK=0 RK=0 G=696 dmg=5547 door=81/7/1
- MT16 x6y10 fly
- MT16 x5y2 move [G 696->720] (auto: x5y9 bigBat, x7y9 bigBat)
- MT16 x4y2 open yellowDoor [YK 2->1]
- MT16 x3y1 move [YK 1->4, G 720->744] (auto: x2y1 bigBat, x1y1 yellowKey, x1y2 yellowKey, x2y3 bigBat, x1y3 yellowKey)
- after: HP=129 ATK=70 DEF=58 YK=4 BK=0 RK=0 G=744 dmg=5547 door=82/7/1

### MT11

- before: HP=129 ATK=70 DEF=58 YK=4 BK=0 RK=0 G=744 dmg=5547 door=82/7/1
- MT11 x11y10 fly
- MT11 x9y9 move [G 744->756] (auto: x4y7 bigBat)
- MT11 x9y10 open yellowDoor [YK 4->3]
- MT11 x9y10 move [HP 129->529, G 756->768] (auto: x9y11 bigBat, x8y11 bluePotion)
- after: HP=529 ATK=70 DEF=58 YK=3 BK=0 RK=0 G=768 dmg=5547 door=83/7/1

### MT15

- before: HP=529 ATK=70 DEF=58 YK=3 BK=0 RK=0 G=768 dmg=5547 door=83/7/1
- MT15 x6y10 fly
- MT15 x10y11 move [G 768->804] (auto: x10y5 bigBat, x1y10 bigBat, x3y10 bigBat)
- after: HP=529 ATK=70 DEF=58 YK=3 BK=0 RK=0 G=804 dmg=5547 door=83/7/1

### MT16

- before: HP=529 ATK=70 DEF=58 YK=3 BK=0 RK=0 G=804 dmg=5547 door=83/7/1
- MT16 x6y2 fly
- after: HP=529 ATK=70 DEF=58 YK=3 BK=0 RK=0 G=804 dmg=5547 door=83/7/1

### MT12

- before: HP=529 ATK=70 DEF=58 YK=3 BK=0 RK=0 G=804 dmg=5547 door=83/7/1
- MT12 x2y11 fly
- MT12 x3y11 move [G 804->816] (auto: x11y5 bigBat)
- MT12 x3y10 open yellowDoor [YK 3->2]
- MT12 x3y9 kill zombie [HP 529->448, YK 2->5, BK 0->1, G 816->834] (auto: x2y8 blueKey, x2y7 yellowKey, x1y8 yellowKey, x1y7 yellowKey) (+18G)
- after: HP=448 ATK=70 DEF=58 YK=5 BK=1 RK=0 G=834 dmg=5628 door=84/7/1

### MT19

- before: HP=448 ATK=70 DEF=58 YK=5 BK=1 RK=0 G=834 dmg=5628 door=84/7/1
- MT19 x1y2 fly
- MT19 x3y8 kill blackSlime [HP 448->446, G 834->842] (+8G)
- MT19 x6y7 open blueDoor [BK 1->0]
- MT19 x7y6 kill rock [HP 446->68, YK 5->7, G 842->870] (auto: x8y5 yellowKey, x6y4 fakeWall, x4y5 yellowKey) (+28G)
- MT19 x6y3 pass fakeWall2
- after: HP=68 ATK=70 DEF=58 YK=7 BK=0 RK=0 G=870 dmg=6008 door=84/8/1

### MT17

- before: HP=68 ATK=70 DEF=58 YK=7 BK=0 RK=0 G=870 dmg=6008 door=84/8/1
- MT17 x6y2 fly
- MT17 x7y11 move [HP 68->168, G 870->882] (auto: x8y11 bigBat, x11y11 redPotion)
- after: HP=168 ATK=70 DEF=58 YK=7 BK=0 RK=0 G=882 dmg=6008 door=84/8/1

### MT16

- before: HP=168 ATK=70 DEF=58 YK=7 BK=0 RK=0 G=882 dmg=6008 door=84/8/1
- MT16 x6y10 fly
- MT16 x8y2 open yellowDoor [YK 7->6]
- MT16 x9y2 kill blackSlime [HP 168->266, G 882->902] (auto: x11y1 bigBat, x11y3 redPotion) (+20G)
- after: HP=266 ATK=70 DEF=58 YK=6 BK=0 RK=0 G=902 dmg=6010 door=85/8/1

### MT15

- before: HP=266 ATK=70 DEF=58 YK=6 BK=0 RK=0 G=902 dmg=6010 door=85/8/1
- MT15 x6y2 fly
- MT15 x11y6 kill redPriest [HP 266->592, G 902->924] (auto: x11y8 bluePotion) (+22G)
- after: HP=592 ATK=70 DEF=58 YK=6 BK=0 RK=0 G=924 dmg=6084 door=85/8/1

### MT11

- before: HP=592 ATK=70 DEF=58 YK=6 BK=0 RK=0 G=924 dmg=6084 door=85/8/1
- MT11 x11y10 fly
- MT11 x7y7 open yellowDoor [YK 6->5]
- MT11 x8y7 kill blackSlime [HP 592->690, G 924->932] (auto: x9y6 redPotion) (+8G)
- after: HP=690 ATK=70 DEF=58 YK=5 BK=0 RK=0 G=932 dmg=6086 door=86/8/1

### MT3

- before: HP=690 ATK=70 DEF=58 YK=5 BK=0 RK=0 G=932 dmg=6086 door=86/8/1
- MT3 x10y11 fly
- MT3 x9y8 open yellowDoor [YK 5->4]
- MT3 x9y8 move [HP 690->740, YK 4->5, G 932->937] (auto: x10y8 bluePriest, x11y8 yellowKey, x11y7 redPotion)
- after: HP=740 ATK=70 DEF=58 YK=5 BK=0 RK=0 G=937 dmg=6086 door=87/8/1

### MT20

- before: HP=740 ATK=70 DEF=58 YK=5 BK=0 RK=0 G=937 dmg=6086 door=87/8/1
- MT20 x6y10 fly
- after: HP=740 ATK=70 DEF=58 YK=5 BK=0 RK=0 G=937 dmg=6086 door=87/8/1

### MT12

- before: HP=740 ATK=70 DEF=58 YK=5 BK=0 RK=0 G=937 dmg=6086 door=87/8/1
- MT12 x2y11 fly
- MT12 x4y5 open yellowDoor [YK 5->4]
- MT12 x2y5 kill redPriest [HP 740->666, G 937->959] (+22G)
- MT12 x1y4 open yellowDoor [YK 4->3]
- MT12 x3y3 move [G 959->971] (auto: x3y2 bigBat, x2y1 fakeWall)
- MT12 x1y1 trader redKey1 [RK 0->1, G 971->171]
- after: HP=666 ATK=70 DEF=58 YK=3 BK=0 RK=1 G=171 dmg=6160 door=89/8/1

### MT14

- before: HP=666 ATK=70 DEF=58 YK=3 BK=0 RK=1 G=171 dmg=6160 door=89/8/1
- MT14 x11y10 fly
- MT14 x10y8 kill blackSlime [HP 666->664, G 171->179] (+8G)
- MT14 x11y7 open yellowDoor [YK 3->2]
- MT14 x11y6 kill zombie [HP 664->737, G 179->209] (auto: x9y6 redPotion, x8y5 bigBat) (+30G)
- after: HP=737 ATK=70 DEF=58 YK=2 BK=0 RK=1 G=209 dmg=6189 door=90/8/1

### MT20

- before: HP=737 ATK=70 DEF=58 YK=2 BK=0 RK=1 G=209 dmg=6189 door=90/8/1
- MT20 x6y10 fly
- MT20 x6y9 open redDoor [RK 1->0]
- MT20 x6y8 pass
- MT20 x6y6 kill vampire [HP 737->32, G 209->353] (+144G)
- MT20 x6y5 move [HP 32->1232, ATK 70->76, DEF 58->64, YK 2->5] (auto: x6y4 yellowKey, x5y4 yellowKey, x7y4 yellowKey, x4y5 redGem, x8y5 blueGem, x4y6 redGem, x6y8 bluePotion, x8y6 blueGem, x4y7 redGem, x5y8 bluePotion, x7y8 bluePotion, x8y7 blueGem)
- MT20 x6y1 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2

### MT21

- before: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2
- MT21 x6y11 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2

### MT22

- before: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2
- MT22 x6y6 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2

### MT23

- before: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2
- MT23 x11y1 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2

### MT24

- before: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2
- MT24 x2y10 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2

### MT25

- before: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2
- MT25 x1y11 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2

### MT26

- before: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2
- MT26 x2y10 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2

### MT27

- before: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2
- MT27 x11y11 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2

### MT28

- before: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2
- MT28 x1y11 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2

### MT29

- before: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2
- MT29 x6y2 event thief
- MT29 x6y11 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2

### MT30

- before: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=353 dmg=6894 door=90/8/2
- MT30 x5y5 kill greenSlime [G 353->354] (+1G)
- MT30 x4y5 kill redSlime [G 354->356] (+2G)
- MT30 x3y5 kill blackSlime [G 356->364] (+8G)
- MT30 x7y5 kill greenSlime [G 364->365] (+1G)
- MT30 x8y5 kill redSlime [G 365->367] (+2G)
- MT30 x9y5 kill blackSlime [G 367->375] (+8G)
- MT30 x6y1 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=375 dmg=6894 door=90/8/2

### MT31

- before: HP=1232 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=375 dmg=6894 door=90/8/2
- MT31 x6y2 设置自动：battle=true, item=nopotion, wall=true
- MT31 x6y8 kill zombieKnight [HP 1232->1120, G 375->405] (+30G)
- MT31 x6y9 kill zombieKnight [HP 1120->1008, G 405->435] (+30G)
- MT31 x6y11 pass upFloor
- after: HP=1008 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=435 dmg=7118 door=90/8/2

### MT32

- before: HP=1008 ATK=76 DEF=64 YK=5 BK=0 RK=0 G=435 dmg=7118 door=90/8/2
- MT32 x6y10 pass [HP 1008->578, G 435->535] (auto: +100G)
- MT32 x8y11 kill ghostSkeleton [HP 578->114, G 535->570] (+35G)
- MT32 x10y10 shop def [DEF 64->80, G 570->490]
- MT32 x10y10 shop def [DEF 80->96, G 490->350]
- MT32 x10y10 shop def [DEF 96->112, G 350->130]
- after: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=130 dmg=8012 door=90/8/2

### MT20

- before: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=130 dmg=8012 door=90/8/2
- MT20 x6y2 fly
- MT20 x5y11 move [G 130->208] (auto: x2y10 rock, x8y11 redPriest, x10y10 rock)
- MT20 x6y11 pass downFloor
- after: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=208 dmg=8012 door=90/8/2

### MT19

- before: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=208 dmg=8012 door=90/8/2
- MT19 x1y2 move [G 208->244] (auto: x5y6 rock, x11y5 blackSlime)
- MT19 x1y1 pass downFloor
- after: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=244 dmg=8012 door=90/8/2

### MT18

- before: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=244 dmg=8012 door=90/8/2
- MT18 x4y7 move [G 244->354] (auto: x10y7 rock, x3y5 rock, x1y5 rock, x10y2 blackSlime, x9y4 zombie)
- MT18 x4y8 open yellowDoor [YK 5->4]
- MT18 x8y7 move [YK 4->5, G 354->402] (auto: x4y9 bigBat, x4y10 bigBat, x5y9 bigBat, x5y10 bigBat, x5y11 yellowKey)
- MT18 x8y8 open yellowDoor [YK 5->4]
- MT18 x11y7 move [YK 4->5, G 402->434] (auto: x8y9 blackSlime, x7y9 blackSlime, x8y10 blackSlime, x7y10 blackSlime, x7y11 yellowKey)
- MT18 x11y8 open yellowDoor [YK 5->4]
- MT18 x5y1 move [DEF 112->114, YK 4->5, G 434->456] (auto: x11y9 redPriest, x10y10 yellowKey, x10y11 blueGem)
- MT18 x6y1 pass downFloor
- after: HP=114 ATK=76 DEF=114 YK=5 BK=0 RK=0 G=456 dmg=8012 door=93/8/2

### MT17

- before: HP=114 ATK=76 DEF=114 YK=5 BK=0 RK=0 G=456 dmg=8012 door=93/8/2
- MT17 x5y11 move [G 456->474] (auto: x5y7 zombie)
- MT17 x6y11 pass downFloor
- after: HP=114 ATK=76 DEF=114 YK=5 BK=0 RK=0 G=474 dmg=8012 door=93/8/2

### MT16

- before: HP=114 ATK=76 DEF=114 YK=5 BK=0 RK=0 G=474 dmg=8012 door=93/8/2
- MT16 x7y10 move [G 474->542] (auto: x3y6 rock, x5y3 zombie, x2y2 redPriest)
- MT16 x8y10 open yellowDoor [YK 5->4]
- MT16 x9y9 move [G 542->564] (auto: x10y9 redPriest)
- MT16 x10y8 open yellowDoor [YK 4->3]
- MT16 x5y1 move [BK 0->1, G 564->594] (auto: x9y7 bigBat, x11y7 blueKey, x10y5 zombie)
- MT16 x6y1 pass downFloor
- after: HP=114 ATK=76 DEF=114 YK=3 BK=1 RK=0 G=594 dmg=8012 door=95/8/2

### MT15

- before: HP=114 ATK=76 DEF=114 YK=3 BK=1 RK=0 G=594 dmg=8012 door=95/8/2
- MT15 x5y11 move [G 594->624] (auto: x3y3 blackSlime, x2y11 redPriest)
- MT15 x6y11 pass downFloor
- after: HP=114 ATK=76 DEF=114 YK=3 BK=1 RK=0 G=624 dmg=8012 door=95/8/2

### MT14

- before: HP=114 ATK=76 DEF=114 YK=3 BK=1 RK=0 G=624 dmg=8012 door=95/8/2
- MT14 x7y5 move [G 624->712] (auto: x6y5 rock, x4y5 bigBat, x2y6 blackSlime, x4y8 zombie, x3y9 redPriest)
- MT14 x1y7 open yellowDoor [YK 3->2]
- MT14 x1y8 move [BK 1->2, G 712->734] (auto: x1y9 redPriest, x1y11 blueKey)
- MT14 x11y11 pass downFloor
- after: HP=114 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=734 dmg=8012 door=96/8/2

### MT13

- before: HP=114 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=734 dmg=8012 door=96/8/2
- MT13 x1y11 pass downFloor
- after: HP=114 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=734 dmg=8012 door=96/8/2

### MT12

- before: HP=114 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=734 dmg=8012 door=96/8/2
- MT12 x10y11 move [G 734->782] (auto: x9y9 blackSlime, x10y3 zombie, x10y1 fakeWall, x5y3 redPriest)
- MT12 x11y11 pass downFloor
- after: HP=114 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=782 dmg=8012 door=96/8/2

### MT11

- before: HP=114 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=782 dmg=8012 door=96/8/2
- MT11 x6y10 move [G 782->804] (auto: x8y5 redPriest)
- MT11 x6y11 pass downFloor
- after: HP=114 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=804 dmg=8012 door=96/8/2

### MT10

- before: HP=114 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=804 dmg=8012 door=96/8/2
- MT10 x1y10 move [G 804->832] (auto: x2y7 skeletonSoldier, x3y6 skeleton, x10y7 skeletonSoldier, x11y6 skeleton)
- MT10 x1y11 pass downFloor
- after: HP=114 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=832 dmg=8012 door=96/8/2

### MT32

- before: HP=114 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=832 dmg=8012 door=96/8/2
- MT32 x6y11 fly
- MT32 x10y10 shop def [DEF 114->130, G 832->512]
- MT32 x10y10 shop def [DEF 130->146, G 512->72]
- MT32 x5y3 open yellowDoor [YK 2->1]
- MT32 x10y1 move [YK 1->2, G 72->132] (auto: x3y4 slimeMan, x4y5 slimeMan, x2y5 yellowKey)
- MT32 x11y1 pass upFloor
- after: HP=114 ATK=76 DEF=146 YK=2 BK=2 RK=0 G=132 dmg=8012 door=97/8/2

### MT33

- before: HP=114 ATK=76 DEF=146 YK=2 BK=2 RK=0 G=132 dmg=8012 door=97/8/2
- MT33 x7y1 open yellowDoor [YK 2->1]
- MT33 x7y1 move [YK 1->2, G 132->192] (auto: x6y1 slimeMan, x4y1 zombieKnight, x6y3 yellowKey)
- after: HP=114 ATK=76 DEF=146 YK=2 BK=2 RK=0 G=192 dmg=8012 door=98/8/2

### MT20

- before: HP=114 ATK=76 DEF=146 YK=2 BK=2 RK=0 G=192 dmg=8012 door=98/8/2
- MT20 x6y2 fly
- MT20 x6y11 pass downFloor
- after: HP=114 ATK=76 DEF=146 YK=2 BK=2 RK=0 G=192 dmg=8012 door=98/8/2

### MT19

- before: HP=114 ATK=76 DEF=146 YK=2 BK=2 RK=0 G=192 dmg=8012 door=98/8/2
- MT19 x1y2 move [BK 2->3, G 192->334] (auto: x6y9 zombieKnight, x8y8 zombieKnight, x4y3 zombieKnight, x8y3 zombieKnight, x8y1 blueKey, x6y1 redPriest)
- MT19 x1y1 pass downFloor
- after: HP=114 ATK=76 DEF=146 YK=2 BK=3 RK=0 G=334 dmg=8012 door=98/8/2

### MT18

- before: HP=114 ATK=76 DEF=146 YK=2 BK=3 RK=0 G=334 dmg=8012 door=98/8/2
- MT18 x5y1 move [G 334->364] (auto: x7y4 zombieKnight)
- MT18 x6y1 pass downFloor
- after: HP=114 ATK=76 DEF=146 YK=2 BK=3 RK=0 G=364 dmg=8012 door=98/8/2

### MT17

- before: HP=114 ATK=76 DEF=146 YK=2 BK=3 RK=0 G=364 dmg=8012 door=98/8/2
- MT17 x10y11 move [G 364->394] (auto: x5y3 zombieKnight)
- MT17 x10y10 open yellowDoor [YK 2->1]
- MT17 x9y8 kill zombie [G 394->412] (+18G)
- MT17 x11y8 kill zombie [G 412->430] (+18G)
- MT17 x9y5 kill zombieKnight [G 430->460] (+30G)
- MT17 x11y5 kill zombieKnight [G 460->490] (+30G)
- MT17 x10y3 move [ATK 76->78, DEF 146->148, YK 1->3] (auto: x9y3 yellowKey, x11y3 yellowKey, x9y1 redGem, x11y1 blueGem)
- MT17 x10y2 take bluePotion [HP 114->514]
- MT17 x6y11 pass downFloor
- after: HP=514 ATK=78 DEF=148 YK=3 BK=3 RK=0 G=490 dmg=8012 door=99/8/2

### MT16

- before: HP=514 ATK=78 DEF=148 YK=3 BK=3 RK=0 G=490 dmg=8012 door=99/8/2
- MT16 x9y10 move [G 490->550] (auto: x9y11 slimeMan, x10y11 fakeWall, x6y6 zombieKnight)
- MT16 x11y11 pass fakeWall2
- MT16 x11y11 event superPotion
- MT16 x6y1 pass downFloor
- after: HP=514 ATK=78 DEF=148 YK=3 BK=3 RK=0 G=550 dmg=8012 door=99/8/2

### MT15

- before: HP=514 ATK=78 DEF=148 YK=3 BK=3 RK=0 G=550 dmg=8012 door=99/8/2
- MT15 x5y11 move [G 550->580] (auto: x2y1 zombieKnight)
- MT15 x6y11 pass downFloor
- after: HP=514 ATK=78 DEF=148 YK=3 BK=3 RK=0 G=580 dmg=8012 door=99/8/2

### MT14

- before: HP=514 ATK=78 DEF=148 YK=3 BK=3 RK=0 G=580 dmg=8012 door=99/8/2
- MT14 x7y5 move [G 580->610] (auto: x10y4 zombieKnight)
- MT14 x7y4 open yellowDoor [YK 3->2]
- MT14 x10y4 move [G 610->640] (auto: x7y2 zombieKnight)
- MT14 x10y3 open yellowDoor [YK 2->1]
- MT14 x7y2 move [YK 1->5] (auto: x10y1 yellowKey, x11y2 yellowKey, x9y1 yellowKey, x11y1 yellowKey)
- MT14 x7y1 take redPotion [HP 514->614, DEF 148->150, YK 5->6, G 640->648] (auto: x6y1 yellowKey, x5y1 blueGem, x5y2 blackSlime)
- MT14 x2y4 open blueDoor [BK 3->2]
- MT14 x2y3 move [G 648->738] (auto: x2y2 zombieKnight, x1y1 zombieKnight, x3y1 zombieKnight)
- MT14 x2y2 move [RK 0->1] (auto: x1y3 redKey)
- after: HP=614 ATK=78 DEF=150 YK=6 BK=2 RK=1 G=738 dmg=8012 door=101/9/2

### MT32

- before: HP=614 ATK=78 DEF=150 YK=6 BK=2 RK=1 G=738 dmg=8012 door=101/9/2
- MT32 x6y11 fly
- MT32 x10y10 shop def [DEF 150->166, G 738->158]
- MT32 x11y1 pass upFloor
- after: HP=614 ATK=78 DEF=166 YK=6 BK=2 RK=1 G=158 dmg=8012 door=101/9/2

### MT33

- before: HP=614 ATK=78 DEF=166 YK=6 BK=2 RK=1 G=158 dmg=8012 door=101/9/2
- MT33 x3y1 open yellowDoor [YK 6->5]
- MT33 x1y1 pass upFloor
- after: HP=614 ATK=78 DEF=166 YK=5 BK=2 RK=1 G=158 dmg=8012 door=102/9/2

### MT34

- before: HP=614 ATK=78 DEF=166 YK=5 BK=2 RK=1 G=158 dmg=8012 door=102/9/2
- MT34 x3y2 move [G 158->188] (auto: x2y3 slimeMan)
- MT34 x4y2 open yellowDoor [YK 5->4]
- MT34 x4y2 move [YK 4->5, G 188->218] (auto: x5y2 slimeMan, x6y1 yellowKey)
- MT34 x1y1 pass downFloor
- after: HP=614 ATK=78 DEF=166 YK=5 BK=2 RK=1 G=218 dmg=8012 door=103/9/2

### MT33

- before: HP=614 ATK=78 DEF=166 YK=5 BK=2 RK=1 G=218 dmg=8012 door=103/9/2
- MT33 x11y1 pass downFloor
- after: HP=614 ATK=78 DEF=166 YK=5 BK=2 RK=1 G=218 dmg=8012 door=103/9/2

### MT32

- before: HP=614 ATK=78 DEF=166 YK=5 BK=2 RK=1 G=218 dmg=8012 door=103/9/2
- MT32 x3y1 open blueDoor [BK 2->1]
- MT32 x3y1 move [ATK 78->82, DEF 166->170] (auto: x1y1 blueGem, x2y2 redGem)
- MT32 x5y11 pass downFloor
- after: HP=614 ATK=82 DEF=170 YK=5 BK=1 RK=1 G=218 dmg=8012 door=103/10/2

### MT31

- before: HP=614 ATK=82 DEF=170 YK=5 BK=1 RK=1 G=218 dmg=8012 door=103/10/2
- MT31 x10y6 kill ghostSkeleton [HP 614->574, G 218->253] (+35G)
- MT31 x11y7 open yellowDoor [YK 5->4]
- MT31 x10y8 move [YK 4->8, G 253->313] (auto: x10y9 slimeMan, x9y10 yellowKey, x11y10 slimeMan, x8y10 yellowKey, x9y11 yellowKey, x8y11 yellowKey)
- after: HP=574 ATK=82 DEF=170 YK=8 BK=1 RK=1 G=313 dmg=8052 door=104/10/2

### MT33

- before: HP=574 ATK=82 DEF=170 YK=8 BK=1 RK=1 G=313 dmg=8052 door=104/10/2
- MT33 x10y1 fly
- MT33 x11y1 pass downFloor
- after: HP=574 ATK=82 DEF=170 YK=8 BK=1 RK=1 G=313 dmg=8052 door=104/10/2

### MT28

- before: HP=574 ATK=82 DEF=170 YK=8 BK=1 RK=1 G=313 dmg=8052 door=104/10/2
- MT28 x2y11 fly
- MT28 x8y4 trader specialTrader [YK 8->7, G 313->413] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 7->6, G 413->513] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 6->5, G 513->613] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 5->4, G 613->713] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 4->3, G 713->813] (auto: +100G)
- after: HP=574 ATK=82 DEF=170 YK=3 BK=1 RK=1 G=813 dmg=8052 door=104/10/2

### MT32

- before: HP=574 ATK=82 DEF=170 YK=3 BK=1 RK=1 G=813 dmg=8052 door=104/10/2
- MT32 x6y11 fly
- MT32 x10y10 shop def [DEF 170->186, G 813->73]
- after: HP=574 ATK=82 DEF=186 YK=3 BK=1 RK=1 G=73 dmg=8052 door=104/10/2

### MT33

- before: HP=574 ATK=82 DEF=186 YK=3 BK=1 RK=1 G=73 dmg=8052 door=104/10/2
- MT33 x10y1 fly
- MT33 x1y1 pass upFloor
- after: HP=574 ATK=82 DEF=186 YK=3 BK=1 RK=1 G=73 dmg=8052 door=104/10/2

### MT34

- before: HP=574 ATK=82 DEF=186 YK=3 BK=1 RK=1 G=73 dmg=8052 door=104/10/2
- MT34 x1y1 pass downFloor
- after: HP=574 ATK=82 DEF=186 YK=3 BK=1 RK=1 G=73 dmg=8052 door=104/10/2

### MT33

- before: HP=574 ATK=82 DEF=186 YK=3 BK=1 RK=1 G=73 dmg=8052 door=104/10/2
- MT33 x8y2 open yellowDoor [YK 3->2]
- MT33 x10y5 pass
- MT33 x11y5 kill ghostSkeleton [G 73->143] (auto: x9y5 ghostSkeleton) (+70G)
- MT33 x9y7 kill soldier [HP 574->406, G 143->188] (+45G)
- MT33 x11y7 kill soldier [HP 406->238, G 188->233] (+45G)
- MT33 x9y10 move [ATK 82->122] (auto: x10y10 sword3)
- MT33 x11y1 pass downFloor
- after: HP=238 ATK=122 DEF=186 YK=2 BK=1 RK=1 G=233 dmg=8388 door=105/10/2

### MT32

- before: HP=238 ATK=122 DEF=186 YK=2 BK=1 RK=1 G=233 dmg=8388 door=105/10/2
- MT32 x3y10 kill blueGuard [G 233->283] (+50G)
- MT32 x1y10 kill blueGuard [G 283->333] (+50G)
- MT32 x3y8 move [YK 2->6, BK 1->2] (auto: x2y7 yellowKey, x1y7 yellowKey, x3y7 yellowKey, x4y8 blueKey, x4y7 yellowKey)
- after: HP=238 ATK=122 DEF=186 YK=6 BK=2 RK=1 G=333 dmg=8388 door=105/10/2

### MT2

- before: HP=238 ATK=122 DEF=186 YK=6 BK=2 RK=1 G=333 dmg=8388 door=105/10/2
- MT2 x1y10 fly
- MT2 x3y1 open blueDoor [BK 2->1]
- MT2 x6y2 kill blueGuard [G 333->383] (+50G)
- MT2 x8y2 kill blueGuard [G 383->433] (+50G)
- MT2 x10y4 move [YK 6->9] (auto: x4y4 yellowKey, x3y5 yellowKey, x3y4 yellowKey)
- MT2 x11y4 event oldman [G 433->1433] (auto: +1000G)
- MT2 x10y11 event thief
- after: HP=238 ATK=122 DEF=186 YK=9 BK=1 RK=1 G=1433 dmg=8388 door=105/11/2

### MT15

- before: HP=238 ATK=122 DEF=186 YK=9 BK=1 RK=1 G=1433 dmg=8388 door=105/11/2
- MT15 x6y10 fly
- MT15 x6y6 kill octopus [G 1433->1533] (+100G)
- MT15 x6y5 take pickaxe
- after: HP=238 ATK=122 DEF=186 YK=9 BK=1 RK=1 G=1533 dmg=8388 door=105/11/2

### MT33

- before: HP=238 ATK=122 DEF=186 YK=9 BK=1 RK=1 G=1533 dmg=8388 door=105/11/2
- MT33 x10y1 fly
- MT33 x1y1 pass upFloor
- after: HP=238 ATK=122 DEF=186 YK=9 BK=1 RK=1 G=1533 dmg=8388 door=105/11/2

### MT34

- before: HP=238 ATK=122 DEF=186 YK=9 BK=1 RK=1 G=1533 dmg=8388 door=105/11/2
- MT34 x2y4 open yellowDoor [YK 9->8]
- MT34 x2y8 open yellowDoor [YK 8->7]
- MT34 x2y9 move [G 1533->1568] (auto: x3y9 ghostSkeleton)
- MT34 x4y10 open yellowDoor [YK 7->6]
- MT34 x6y11 pass upFloor
- after: HP=238 ATK=122 DEF=186 YK=6 BK=1 RK=1 G=1568 dmg=8388 door=108/11/2

### MT35

- before: HP=238 ATK=122 DEF=186 YK=6 BK=1 RK=1 G=1568 dmg=8388 door=108/11/2
- MT35 x5y10 pass thief
- MT35 x11y1 pass upFloor
- after: HP=238 ATK=122 DEF=186 YK=6 BK=1 RK=1 G=1568 dmg=8388 door=108/11/2

### MT32

- before: HP=238 ATK=122 DEF=186 YK=6 BK=1 RK=1 G=1568 dmg=8388 door=108/11/2
- MT32 x10y1 fly
- MT32 x10y10 shop def [DEF 186->202, G 1568->648]
- MT32 x10y1 move [G 648->693] (auto: x1y4 soldier)
- MT32 x11y1 pass upFloor
- after: HP=238 ATK=122 DEF=202 YK=6 BK=1 RK=1 G=693 dmg=8388 door=108/11/2

### MT33

- before: HP=238 ATK=122 DEF=202 YK=6 BK=1 RK=1 G=693 dmg=8388 door=108/11/2
- MT33 x1y1 pass upFloor
- after: HP=238 ATK=122 DEF=202 YK=6 BK=1 RK=1 G=693 dmg=8388 door=108/11/2

### MT34

- before: HP=238 ATK=122 DEF=202 YK=6 BK=1 RK=1 G=693 dmg=8388 door=108/11/2
- MT34 x7y10 move [G 693->738] (auto: x2y11 soldier)
- MT34 x8y10 open yellowDoor [YK 6->5]
- MT34 x8y10 move [ATK 122->126, YK 5->6, G 738->783] (auto: x9y10 soldier, x10y11 yellowKey, x11y11 redGem)
- after: HP=238 ATK=126 DEF=202 YK=6 BK=1 RK=1 G=783 dmg=8388 door=109/11/2

### MT31

- before: HP=238 ATK=126 DEF=202 YK=6 BK=1 RK=1 G=783 dmg=8388 door=109/11/2
- MT31 x6y10 fly
- MT31 x11y6 move [G 783->818] (auto: x2y6 ghostSkeleton)
- MT31 x11y5 open yellowDoor [YK 6->5]
- MT31 x10y4 move [G 818->933] (auto: x10y3 ghostSkeleton, x11y3 ghostSkeleton, x8y2 soldier)
- MT31 x8y3 open yellowDoor [YK 5->4]
- MT31 x1y6 move [ATK 126->130] (auto: x8y4 redGem)
- MT31 x1y5 open yellowDoor [YK 4->3]
- MT31 x2y4 move [YK 3->7, G 933->978] (auto: x2y3 soldier, x3y2 yellowKey, x3y1 yellowKey, x4y2 yellowKey, x4y1 yellowKey)
- MT31 x3y4 open yellowDoor [YK 7->6]
- MT31 x3y4 move [BK 1->2] (auto: x4y4 blueKey)
- after: HP=238 ATK=130 DEF=202 YK=6 BK=2 RK=1 G=978 dmg=8388 door=113/11/2

### MT36

- before: HP=238 ATK=130 DEF=202 YK=6 BK=2 RK=1 G=978 dmg=8388 door=113/11/2
- MT36 x11y2 fly
- MT36 x10y1 move [G 978->1008] (auto: x11y3 slimeMan)
- MT36 x9y1 kill redKnight [HP 238->70, G 1008->1178] (auto: x7y1 zombieKnight, x3y1 soldier, x1y3 slimeMan) (+170G)
- MT36 x6y2 open yellowDoor [YK 6->5]
- MT36 x6y4 move [G 1178->1273] (auto: x6y5 ghostSkeleton, x5y6 slimeMan, x7y6 slimeMan)
- MT36 x10y6 open yellowDoor [YK 5->4]
- after: HP=70 ATK=130 DEF=202 YK=4 BK=2 RK=1 G=1273 dmg=8556 door=115/11/2

### MT34

- before: HP=70 ATK=130 DEF=202 YK=4 BK=2 RK=1 G=1273 dmg=8556 door=115/11/2
- MT34 x6y10 fly
- MT34 x3y1 take redPotion [HP 70->270]
- after: HP=270 ATK=130 DEF=202 YK=4 BK=2 RK=1 G=1273 dmg=8556 door=115/11/2

### MT36

- before: HP=270 ATK=130 DEF=202 YK=4 BK=2 RK=1 G=1273 dmg=8556 door=115/11/2
- MT36 x11y2 fly
- MT36 x11y7 kill redKnight [HP 270->102, G 1273->1338] (+65G)
- MT36 x11y11 pass upFloor
- after: HP=102 ATK=130 DEF=202 YK=4 BK=2 RK=1 G=1338 dmg=8724 door=115/11/2

### MT37

- before: HP=102 ATK=130 DEF=202 YK=4 BK=2 RK=1 G=1338 dmg=8724 door=115/11/2
- MT37 x10y11 move [G 1338->1448] (auto: x9y11 ghostSkeleton, x3y11 slimeMan, x1y9 soldier)
- MT37 x1y6 take redPotion [HP 102->302]
- MT37 x1y3 open blueDoor [BK 2->1]
- MT37 x1y1 pass upFloor
- after: HP=302 ATK=130 DEF=202 YK=4 BK=1 RK=1 G=1448 dmg=8724 door=115/12/2

### MT38

- before: HP=302 ATK=130 DEF=202 YK=4 BK=1 RK=1 G=1448 dmg=8724 door=115/12/2
- MT38 x3y1 open redDoor [RK 1->0]
- MT38 x3y1 move [YK 4->5, G 1448->1633] (auto: x4y1 slimeMan, x1y3 ghostSkeleton, x6y2 yellowKey, x8y1 slimeMan, x3y4 soldier, x4y4 soldier)
- MT38 x5y2 trader yellowKey3 [YK 5->8, G 1633->1433]
- MT38 x9y1 open yellowDoor [YK 8->7]
- MT38 x11y1 pass upFloor
- after: HP=302 ATK=130 DEF=202 YK=7 BK=1 RK=0 G=1433 dmg=8724 door=116/12/3

### MT39

- before: HP=302 ATK=130 DEF=202 YK=7 BK=1 RK=0 G=1433 dmg=8724 door=116/12/3
- MT39 x10y3 move [YK 7->8] (auto: x11y3 yellowKey)
- MT39 x10y4 open yellowDoor [YK 8->7]
- MT39 x9y5 move [ATK 130->134, G 1433->1543] (auto: x9y6 slimeMan, x11y5 soldier, x11y6 redGem, x11y7 ghostSkeleton)
- MT39 x11y1 pass downFloor
- after: HP=302 ATK=134 DEF=202 YK=7 BK=1 RK=0 G=1543 dmg=8724 door=117/12/3

### MT38

- before: HP=302 ATK=134 DEF=202 YK=7 BK=1 RK=0 G=1543 dmg=8724 door=117/12/3
- MT38 x11y3 open yellowDoor [YK 7->6]
- MT38 x11y5 move [G 1543->1578] (auto: x11y6 ghostSkeleton)
- MT38 x11y8 open yellowDoor [YK 6->5]
- MT38 x11y8 move [YK 5->6, G 1578->1658] (auto: x11y9 ghostSkeleton, x9y9 yellowKey, x9y11 soldier)
- MT38 x8y11 open yellowDoor [YK 6->5]
- MT38 x8y11 move [G 1658->1676] (auto: x7y11 zombie)
- after: HP=302 ATK=134 DEF=202 YK=5 BK=1 RK=0 G=1676 dmg=8724 door=120/12/3

### MT34

- before: HP=302 ATK=134 DEF=202 YK=5 BK=1 RK=0 G=1676 dmg=8724 door=120/12/3
- MT34 x6y10 fly
- MT34 x11y10 take redPotion [HP 302->502]
- after: HP=502 ATK=134 DEF=202 YK=5 BK=1 RK=0 G=1676 dmg=8724 door=120/12/3

### MT39

- before: HP=502 ATK=134 DEF=202 YK=5 BK=1 RK=0 G=1676 dmg=8724 door=120/12/3
- MT39 x11y2 fly
- MT39 x11y1 pass downFloor
- after: HP=502 ATK=134 DEF=202 YK=5 BK=1 RK=0 G=1676 dmg=8724 door=120/12/3

### MT38

- before: HP=502 ATK=134 DEF=202 YK=5 BK=1 RK=0 G=1676 dmg=8724 door=120/12/3
- MT38 x5y11 kill swordsman [HP 502->24, G 1676->1731] (+55G)
- MT38 x4y11 open yellowDoor [YK 5->4]
- MT38 x3y10 kill blueGuard [G 1731->1781] (+50G)
- MT38 x1y10 kill blueGuard [G 1781->1831] (+50G)
- MT38 x1y7 move [DEF 202->242, YK 4->7, G 1831->1961] (auto: x2y7 shield3, x10y10 redKnight, x10y7 redKnight, x9y6 yellowKey, x9y5 yellowKey, x9y4 yellowKey)
- MT38 x11y1 pass upFloor
- after: HP=24 ATK=134 DEF=242 YK=7 BK=1 RK=0 G=1961 dmg=9202 door=121/12/3

### MT39

- before: HP=24 ATK=134 DEF=242 YK=7 BK=1 RK=0 G=1961 dmg=9202 door=121/12/3
- MT39 x10y8 open yellowDoor [YK 7->6]
- MT39 x10y8 move [G 1961->2026] (auto: x10y9 redKnight)
- MT39 x8y10 open yellowDoor [YK 6->5]
- MT39 x7y11 move [DEF 242->246, G 2026->2121] (auto: x6y11 slimeMan, x7y9 redKnight, x6y9 blueGem)
- MT39 x4y10 open yellowDoor [YK 5->4]
- MT39 x3y10 move [YK 4->5, G 2121->2191] (auto: x3y9 ghostSkeleton, x2y10 ghostSkeleton, x3y11 yellowKey)
- MT39 x2y8 open blueDoor [BK 1->0]
- MT39 x4y2 open yellowDoor [YK 5->4]
- MT39 x6y4 open yellowDoor [YK 4->3]
- MT39 x4y4 take centerFly3
- MT39 x11y11 pass upFloor
- after: HP=24 ATK=134 DEF=246 YK=3 BK=0 RK=0 G=2191 dmg=9202 door=126/13/3

### MT34

- before: HP=24 ATK=134 DEF=246 YK=3 BK=0 RK=0 G=2191 dmg=9202 door=126/13/3
- MT34 x6y10 fly
- MT34 x6y2 move [G 2191->2256] (auto: x7y2 redKnight)
- MT34 x8y2 open yellowDoor [YK 3->2]
- MT34 x9y2 move [DEF 246->250, YK 2->5] (auto: x9y1 yellowKey, x10y2 yellowKey, x10y1 yellowKey, x11y1 blueGem)
- after: HP=24 ATK=134 DEF=250 YK=5 BK=0 RK=0 G=2256 dmg=9202 door=127/13/3

### MT32

- before: HP=24 ATK=134 DEF=250 YK=5 BK=0 RK=0 G=2256 dmg=9202 door=127/13/3
- MT32 x10y1 fly
- MT32 x7y3 open yellowDoor [YK 5->4]
- MT32 x8y3 move [G 2256->2356] (auto: x8y4 ghostSkeleton, x8y7 redKnight)
- MT32 x9y5 open yellowDoor [YK 4->3]
- MT32 x8y8 move [YK 3->5] (auto: x10y4 yellowKey, x11y5 yellowKey)
- MT32 x9y8 open yellowDoor [YK 5->4]
- MT32 x4y11 move [YK 4->6, BK 0->1] (auto: x10y7 yellowKey, x11y8 yellowKey, x11y7 blueKey)
- MT32 x5y11 pass downFloor
- after: HP=24 ATK=134 DEF=250 YK=6 BK=1 RK=0 G=2356 dmg=9202 door=130/13/3

### MT31

- before: HP=24 ATK=134 DEF=250 YK=6 BK=1 RK=0 G=2356 dmg=9202 door=130/13/3
- MT31 x1y7 open yellowDoor [YK 6->5]
- MT31 x2y8 move [G 2356->2491] (auto: x2y9 ghostSkeleton, x1y9 ghostSkeleton, x4y10 redKnight)
- MT31 x4y9 open yellowDoor [YK 5->4]
- MT31 x4y9 move [DEF 250->254] (auto: x4y8 blueGem)
- after: HP=24 ATK=134 DEF=254 YK=4 BK=1 RK=0 G=2491 dmg=9202 door=132/13/3

### MT38

- before: HP=24 ATK=134 DEF=254 YK=4 BK=1 RK=0 G=2491 dmg=9202 door=132/13/3
- MT38 x2y1 fly
- MT38 x11y11 take bluePotion [HP 24->824]
- after: HP=824 ATK=134 DEF=254 YK=4 BK=1 RK=0 G=2491 dmg=9202 door=132/13/3

### MT2

- before: HP=824 ATK=134 DEF=254 YK=4 BK=1 RK=0 G=2491 dmg=9202 door=132/13/3
- MT2 x1y10 fly
- MT2 x4y10 take bluePotion [HP 824->1024]
- MT2 x3y10 take bluePotion [HP 1024->1224]
- after: HP=1224 ATK=134 DEF=254 YK=4 BK=1 RK=0 G=2491 dmg=9202 door=132/13/3

### MT14

- before: HP=1224 ATK=134 DEF=254 YK=4 BK=1 RK=0 G=2491 dmg=9202 door=132/13/3
- MT14 x11y10 fly
- MT14 x1y5 take redPotion [HP 1224->1324]
- after: HP=1324 ATK=134 DEF=254 YK=4 BK=1 RK=0 G=2491 dmg=9202 door=132/13/3

### MT40

- before: HP=1324 ATK=134 DEF=254 YK=4 BK=1 RK=0 G=2491 dmg=9202 door=132/13/3
- MT40 x10y11 fly
- MT40 x2y1 中心飞行 centerFly
- MT40 x2y2 kill swordsman [HP 1324->898, G 2491->2981] (auto: x3y4 ghostSkeleton, x4y4 ghostSkeleton, x5y4 ghostSkeleton, x7y4 soldier, x8y2 redKnight, x8y4 soldier, x9y2 redKnight, x9y4 soldier, x10y2 redKnight) (+490G)
- MT40 x3y2 kill swordsman [HP 898->472, G 2981->3036] (+55G)
- MT40 x4y2 kill swordsman [HP 472->46, G 3036->3091] (+55G)
- MT40 x6y1 kill yellowKnight [G 3091->3191] (+100G)
- MT40 x6y7 pass
- MT40 x5y1 move [ATK 134->146, DEF 254->266, YK 4->7] (auto: x4y2 yellowKey, x3y2 yellowKey, x2y2 yellowKey, x8y2 redGem, x7y4 blueGem, x9y2 redGem, x8y4 blueGem, x10y2 redGem, x9y4 blueGem)
- MT40 x6y1 pass upFloor
- after: HP=46 ATK=146 DEF=266 YK=7 BK=1 RK=0 G=3191 dmg=10480 door=132/13/3

### MT41

- before: HP=46 ATK=146 DEF=266 YK=7 BK=1 RK=0 G=3191 dmg=10480 door=132/13/3
- MT41 x6y4 地图伤害 checkBlock [HP 46->23]
- MT41 x6y7 open yellowDoor [YK 7->6]
- MT41 x6y8 open yellowDoor [YK 6->5]
- MT41 x6y9 open yellowDoor [YK 5->4]
- MT41 x6y11 pass upFloor
- after: HP=23 ATK=146 DEF=266 YK=4 BK=1 RK=0 G=3191 dmg=10503 door=135/13/3

### MT42

- before: HP=23 ATK=146 DEF=266 YK=4 BK=1 RK=0 G=3191 dmg=10503 door=135/13/3
- MT42 x5y10 pass
- MT42 x5y10 event yellowKnightEscape
- after: HP=23 ATK=146 DEF=266 YK=4 BK=1 RK=0 G=3191 dmg=10503 door=135/13/3

### MT39

- before: HP=23 ATK=146 DEF=266 YK=4 BK=1 RK=0 G=3191 dmg=10503 door=135/13/3
- MT39 x11y10 fly
- MT39 x9y11 take redPotion [HP 23->223]
- after: HP=223 ATK=146 DEF=266 YK=4 BK=1 RK=0 G=3191 dmg=10503 door=135/13/3

### MT42

- before: HP=223 ATK=146 DEF=266 YK=4 BK=1 RK=0 G=3191 dmg=10503 door=135/13/3
- MT42 x5y11 fly
- MT42 x8y5 open yellowDoor [YK 4->3]
- MT42 x9y5 地图伤害 checkBlock [HP 223->123]
- MT42 x10y6 地图伤害 checkBlock [HP 123->23]
- MT42 x10y8 地图伤害 checkBlock [HP 23->12]
- MT42 x10y9 move [YK 3->8, BK 1->2] (auto: x10y10 yellowKey, x9y10 yellowKey, x10y11 blueKey, x11y10 yellowKey, x9y11 yellowKey, x11y11 yellowKey)
- MT42 x2y2 中心飞行 centerFly
- MT42 x1y1 pass upFloor
- after: HP=12 ATK=146 DEF=266 YK=8 BK=2 RK=0 G=3191 dmg=10714 door=136/13/3

### MT43

- before: HP=12 ATK=146 DEF=266 YK=8 BK=2 RK=0 G=3191 dmg=10714 door=136/13/3
- MT43 x1y4 open blueDoor [BK 2->1]
- MT43 x1y8 open yellowDoor [YK 8->7]
- MT43 x1y11 pass upFloor
- after: HP=12 ATK=146 DEF=266 YK=7 BK=1 RK=0 G=3191 dmg=10714 door=137/14/3

### MT45

- before: HP=12 ATK=146 DEF=266 YK=7 BK=1 RK=0 G=3191 dmg=10714 door=137/14/3
- MT45 x11y1 pass upFloor
- after: HP=12 ATK=146 DEF=266 YK=7 BK=1 RK=0 G=3191 dmg=10714 door=137/14/3

### MT46

- before: HP=12 ATK=146 DEF=266 YK=7 BK=1 RK=0 G=3191 dmg=10714 door=137/14/3
- MT46 x11y2 设置自动：battle=true, item=true, wall=true
- after: HP=12 ATK=146 DEF=266 YK=7 BK=1 RK=0 G=3191 dmg=10714 door=137/14/3

### MT40

- before: HP=12 ATK=146 DEF=266 YK=7 BK=1 RK=0 G=3191 dmg=10714 door=137/14/3
- MT40 x6y2 fly
- MT40 x5y3 move [HP 12->2412] (auto: x5y4 bluePotion, x4y4 bluePotion, x3y4 bluePotion)
- after: HP=2412 ATK=146 DEF=266 YK=7 BK=1 RK=0 G=3191 dmg=10714 door=137/14/3

### MT46

- before: HP=2412 ATK=146 DEF=266 YK=7 BK=1 RK=0 G=3191 dmg=10714 door=137/14/3
- MT46 x11y2 fly
- MT46 x11y3 open yellowDoor [YK 7->6]
- MT46 x11y5 open yellowDoor [YK 6->5]
- MT46 x11y8 open yellowDoor [YK 5->4]
- MT46 x11y9 地图伤害 checkBlock [HP 2412->2312]
- MT46 x11y11 pass upFloor
- after: HP=2312 ATK=146 DEF=266 YK=4 BK=1 RK=0 G=3191 dmg=10814 door=140/14/3

### MT47

- before: HP=2312 ATK=146 DEF=266 YK=4 BK=1 RK=0 G=3191 dmg=10814 door=140/14/3
- MT47 x1y2 中心飞行 centerFly
- MT47 x3y1 open blueDoor [BK 1->0]
- MT47 x1y1 pass upFloor
- after: HP=2312 ATK=146 DEF=266 YK=4 BK=0 RK=0 G=3191 dmg=10814 door=140/15/3

### MT39

- before: HP=2312 ATK=146 DEF=266 YK=4 BK=0 RK=0 G=3191 dmg=10814 door=140/15/3
- MT39 x11y10 fly
- MT39 x11y11 pass upFloor
- after: HP=2312 ATK=146 DEF=266 YK=4 BK=0 RK=0 G=3191 dmg=10814 door=140/15/3

### MT40

- before: HP=2312 ATK=146 DEF=266 YK=4 BK=0 RK=0 G=3191 dmg=10814 door=140/15/3
- MT40 x9y11 move [HP 2312->2512, G 3191->3236] (auto: x9y10 soldier, x9y9 redPotion)
- MT40 x8y11 open yellowDoor [YK 4->3]
- MT40 x6y9 move [G 3236->3296] (auto: x5y9 slimeMan, x7y9 slimeMan)
- after: HP=2512 ATK=146 DEF=266 YK=3 BK=0 RK=0 G=3296 dmg=10814 door=141/15/3

### MT38

- before: HP=2512 ATK=146 DEF=266 YK=3 BK=0 RK=0 G=3296 dmg=10814 door=141/15/3
- MT38 x10y1 fly
- MT38 x7y3 open yellowDoor [YK 3->2]
- MT38 x4y2 move [G 3296->3331] (auto: x7y6 ghostSkeleton)
- MT38 x1y1 pass downFloor
- after: HP=2512 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3331 dmg=10814 door=142/15/3

### MT37

- before: HP=2512 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3331 dmg=10814 door=142/15/3
- MT37 x10y11 move [G 3331->3396] (auto: x11y9 redKnight)
- MT37 x11y11 pass downFloor
- after: HP=2512 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3396 dmg=10814 door=142/15/3

### MT36

- before: HP=2512 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3396 dmg=10814 door=142/15/3
- MT36 x1y2 move [G 3396->3526] (auto: x1y5 redKnight, x6y7 redKnight)
- MT36 x11y1 pass downFloor
- after: HP=2512 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3

### MT35

- before: HP=2512 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3
- MT35 x6y11 pass downFloor
- after: HP=2512 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3

### MT34

- before: HP=2512 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3
- MT34 x1y2 move [HP 2512->3512] (auto: x11y2 redPotion, x1y11 bluePotion)
- MT34 x1y1 pass downFloor
- after: HP=3512 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3

### MT33

- before: HP=3512 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3
- MT33 x10y1 move [HP 3512->4512] (auto: x5y2 redPotion, x11y3 bluePotion)
- MT33 x11y1 pass downFloor
- after: HP=4512 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3

### MT32

- before: HP=4512 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3
- MT32 x4y11 move [HP 4512->5312] (auto: x11y4 bluePotion)
- MT32 x5y11 pass downFloor
- after: HP=5312 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3

### MT48

- before: HP=5312 ATK=146 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3
- MT48 x11y10 fly
- MT48 x10y10 使用镐 pickaxe
- MT48 x8y10 take sword4 [ATK 146->196]
- after: HP=5312 ATK=196 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3

### MT40

- before: HP=5312 ATK=196 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3
- MT40 x6y2 fly
- after: HP=5312 ATK=196 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3

### MT39

- before: HP=5312 ATK=196 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3
- MT39 x11y10 fly
- MT39 x11y11 pass upFloor
- after: HP=5312 ATK=196 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3

### MT40

- before: HP=5312 ATK=196 DEF=266 YK=2 BK=0 RK=0 G=3526 dmg=10814 door=142/15/3
- MT40 x9y9 move [G 3526->3581] (auto: x10y9 swordsman)
- MT40 x11y11 pass downFloor
- after: HP=5312 ATK=196 DEF=266 YK=2 BK=0 RK=0 G=3581 dmg=10814 door=142/15/3

### MT39

- before: HP=5312 ATK=196 DEF=266 YK=2 BK=0 RK=0 G=3581 dmg=10814 door=142/15/3
- MT39 x10y1 move [G 3581->3636] (auto: x5y9 swordsman)
- MT39 x11y1 pass downFloor
- after: HP=5312 ATK=196 DEF=266 YK=2 BK=0 RK=0 G=3636 dmg=10814 door=142/15/3

### MT38

- before: HP=5312 ATK=196 DEF=266 YK=2 BK=0 RK=0 G=3636 dmg=10814 door=142/15/3
- MT38 x1y2 move [HP 5312->5512, DEF 266->270, G 3636->3691] (auto: x7y7 swordsman, x6y8 redPotion, x5y8 blueGem)
- MT38 x1y1 pass downFloor
- after: HP=5512 ATK=196 DEF=270 YK=2 BK=0 RK=0 G=3691 dmg=10814 door=142/15/3

### MT37

- before: HP=5512 ATK=196 DEF=270 YK=2 BK=0 RK=0 G=3691 dmg=10814 door=142/15/3
- MT37 x10y11 move [HP 5512->6312, G 3691->3856] (auto: x11y6 swordsman, x11y3 redKnight, x11y1 bluePotion, x9y1 soldier)
- MT37 x11y11 pass downFloor
- after: HP=6312 ATK=196 DEF=270 YK=2 BK=0 RK=0 G=3856 dmg=10814 door=142/15/3

### MT36

- before: HP=6312 ATK=196 DEF=270 YK=2 BK=0 RK=0 G=3856 dmg=10814 door=142/15/3
- MT36 x10y1 move [HP 6312->7112, YK 2->3, G 3856->4096] (auto: x11y5 swordsman, x9y11 swordsman, x7y11 zombieKnight, x1y9 swordsman, x5y11 yellowKey, x1y11 bluePotion, x3y11 soldier)
- MT36 x11y1 pass downFloor
- after: HP=7112 ATK=196 DEF=270 YK=3 BK=0 RK=0 G=4096 dmg=10814 door=142/15/3

### MT35

- before: HP=7112 ATK=196 DEF=270 YK=3 BK=0 RK=0 G=4096 dmg=10814 door=142/15/3
- MT35 x6y11 pass downFloor
- after: HP=7112 ATK=196 DEF=270 YK=3 BK=0 RK=0 G=4096 dmg=10814 door=142/15/3

### MT34

- before: HP=7112 ATK=196 DEF=270 YK=3 BK=0 RK=0 G=4096 dmg=10814 door=142/15/3
- MT34 x1y2 move [G 4096->4151] (auto: x1y10 swordsman)
- MT34 x1y1 pass downFloor
- after: HP=7112 ATK=196 DEF=270 YK=3 BK=0 RK=0 G=4151 dmg=10814 door=142/15/3

### MT47

- before: HP=7112 ATK=196 DEF=270 YK=3 BK=0 RK=0 G=4151 dmg=10814 door=142/15/3
- MT47 x11y10 fly
- after: HP=7112 ATK=196 DEF=270 YK=3 BK=0 RK=0 G=4151 dmg=10814 door=142/15/3

### MT48

- before: HP=7112 ATK=196 DEF=270 YK=3 BK=0 RK=0 G=4151 dmg=10814 door=142/15/3
- MT48 x11y10 fly
- MT48 x11y11 pass downFloor
- after: HP=7112 ATK=196 DEF=270 YK=3 BK=0 RK=0 G=4151 dmg=10814 door=142/15/3

### MT47

- before: HP=7112 ATK=196 DEF=270 YK=3 BK=0 RK=0 G=4151 dmg=10814 door=142/15/3
- MT47 x5y2 trader earthquake [G 4151->151]
- after: HP=7112 ATK=196 DEF=270 YK=3 BK=0 RK=0 G=151 dmg=10814 door=142/15/3

### MT37

- before: HP=7112 ATK=196 DEF=270 YK=3 BK=0 RK=0 G=151 dmg=10814 door=142/15/3
- MT37 x2y1 fly
- MT37 x2y1 地震卷轴 earthquake
- MT37 x2y3 move [HP 7112->10512, ATK 196->212, DEF 270->286, YK 3->12, BK 0->2, RK 0->1] (auto: x3y4 redPotion, x4y3 redPotion, x3y5 yellowKey, x4y4 redPotion, x5y3 redPotion, x4y5 yellowKey, x5y4 yellowKey, x3y7 blueGem, x5y5 bomb, x7y3 redPotion, x3y8 yellowKey, x4y7 redGem, x7y4 redPotion, x8y3 redPotion, x4y8 yellowKey, x5y7 bluePotion, x7y5 redKey, x8y4 redPotion, x4y9 blueKey, x5y8 yellowKey, x8y5 yellowKey, x9y4 redPotion, x5y9 blueKey, x7y7 redGem, x9y5 yellowKey, x7y8 blueGem, x8y7 redGem, x7y9 bluePotion, x8y8 blueGem, x9y7 redGem, x8y9 yellowKey, x9y8 blueGem)
- after: HP=10512 ATK=212 DEF=286 YK=12 BK=2 RK=1 G=151 dmg=10814 door=142/15/3

### MT40

- before: HP=10512 ATK=212 DEF=286 YK=12 BK=2 RK=1 G=151 dmg=10814 door=142/15/3
- MT40 x10y11 fly
- MT40 x4y11 open blueDoor [BK 2->1]
- MT40 x4y11 move [HP 10512->11312, ATK 212->216, DEF 286->290, YK 12->13, G 151->216] (auto: x3y11 redKnight, x1y11 redGem, x2y9 yellowKey, x1y10 bluePotion, x1y9 blueGem)
- after: HP=11312 ATK=216 DEF=290 YK=13 BK=1 RK=1 G=216 dmg=10814 door=142/16/3

### MT34

- before: HP=11312 ATK=216 DEF=290 YK=13 BK=1 RK=1 G=216 dmg=10814 door=142/16/3
- MT34 x6y10 fly
- after: HP=11312 ATK=216 DEF=290 YK=13 BK=1 RK=1 G=216 dmg=10814 door=142/16/3

### MT45

- before: HP=11312 ATK=216 DEF=290 YK=13 BK=1 RK=1 G=216 dmg=10814 door=142/16/3
- MT45 x2y1 fly
- MT45 x6y2 open yellowDoor [YK 13->12]
- MT45 x6y3 地图伤害 checkBlock [HP 11312->11012]
- MT45 x6y5 地图伤害 checkBlock [HP 11012->10712]
- MT45 x6y6 open yellowDoor [YK 12->11]
- MT45 x4y7 open yellowDoor [YK 11->10]
- MT45 x2y8 open redDoor [RK 1->0]
- MT45 x6y5 地图伤害 checkBlock [HP 10712->10412]
- MT45 x6y3 地图伤害 checkBlock [HP 10412->10112]
- after: HP=10112 ATK=216 DEF=290 YK=10 BK=1 RK=0 G=216 dmg=12014 door=145/16/4

### MT43

- before: HP=10112 ATK=216 DEF=290 YK=10 BK=1 RK=0 G=216 dmg=12014 door=145/16/4
- MT43 x1y10 fly
- after: HP=10112 ATK=216 DEF=290 YK=10 BK=1 RK=0 G=216 dmg=12014 door=145/16/4

### MT44

- before: HP=10112 ATK=216 DEF=290 YK=10 BK=1 RK=0 G=216 dmg=12014 door=145/16/4
- MT44 x1y10 上楼器 upFly
- MT44 x6y9 炸弹 bomb [G 216->616] (auto: +400G)
- MT44 x6y8 move [HP 10112->11112, DEF 290->390] (auto: x6y7 redPotion, x6y6 shield5, x6y5 redPotion, x5y6 redPotion, x7y6 redPotion)
- after: HP=11112 ATK=216 DEF=390 YK=10 BK=1 RK=0 G=616 dmg=12014 door=145/16/4

### MT41

- before: HP=11112 ATK=216 DEF=390 YK=10 BK=1 RK=0 G=616 dmg=12014 door=145/16/4
- MT41 x6y10 fly
- MT41 x6y11 pass upFloor
- after: HP=11112 ATK=216 DEF=390 YK=10 BK=1 RK=0 G=616 dmg=12014 door=145/16/4

### MT42

- before: HP=11112 ATK=216 DEF=390 YK=10 BK=1 RK=0 G=616 dmg=12014 door=145/16/4
- MT42 x10y4 move [YK 10->15, BK 1->2, G 616->866] (auto: x9y4 brownWizard, x11y4 redWizard, x10y2 yellowKey, x10y1 blueKey, x9y2 yellowKey, x11y2 yellowKey, x11y6 brownWizard, x9y1 yellowKey, x11y1 yellowKey)
- after: HP=11112 ATK=216 DEF=390 YK=15 BK=2 RK=0 G=866 dmg=12014 door=145/16/4

### MT43

- before: HP=11112 ATK=216 DEF=390 YK=15 BK=2 RK=0 G=866 dmg=12014 door=145/16/4
- MT43 x1y2 fly
- MT43 x1y1 pass downFloor
- after: HP=11112 ATK=216 DEF=390 YK=15 BK=2 RK=0 G=866 dmg=12014 door=145/16/4

### MT42

- before: HP=11112 ATK=216 DEF=390 YK=15 BK=2 RK=0 G=866 dmg=12014 door=145/16/4
- MT42 x2y2 move [G 866->906] (auto: x3y2 slimelord)
- MT42 x3y3 open yellowDoor [YK 15->14]
- MT42 x2y5 move [G 906->946] (auto: x3y5 slimelord)
- MT42 x1y6 open yellowDoor [YK 14->13]
- MT42 x3y7 move [HP 11112->12112, DEF 390->395, YK 13->17, G 946->1046] (auto: x3y8 redBat, x3y9 yellowKey, x2y9 yellowKey, x1y9 bluePotion, x1y10 redBat, x1y11 yellowKey, x2y11 yellowKey, x3y11 blueGem)
- MT42 x1y1 pass upFloor
- after: HP=12112 ATK=216 DEF=395 YK=17 BK=2 RK=0 G=1046 dmg=12014 door=147/16/4

### MT46

- before: HP=12112 ATK=216 DEF=395 YK=17 BK=2 RK=0 G=1046 dmg=12014 door=147/16/4
- MT46 x11y2 fly
- MT46 x10y11 move [G 1046->1216] (auto: x10y9 brownWizard, x10y6 slimelord, x9y4 redBat)
- MT46 x9y11 open yellowDoor [YK 17->16]
- MT46 x9y6 open yellowDoor [YK 16->15]
- MT46 x7y11 move [HP 12112->12362, G 1216->1306] (auto: x7y6 redPotion, x8y7 redWizard)
- MT46 x6y11 open blueDoor [BK 2->1]
- MT46 x4y4 move [G 1306->1629] (auto: x4y11 redSlime, x2y11 skeleton, x1y10 bigBat, x1y8 zombie, x1y6 soldier, x3y6 swordsman, x5y6 redKnight, x5y8 slimelord, x4y9 brownWizard, x3y8 bigKey)
- MT46 x3y4 open yellowDoor [YK 15->14]
- MT46 x3y4 move [HP 12362->12612, ATK 216->221, G 1629->1799] (auto: x2y4 brownWizard, x1y3 redGem, x2y1 redWizard, x1y2 redPotion)
- MT46 x3y1 open yellowDoor [YK 14->13]
- MT46 x6y1 shop def [DEF 395->415, G 1799->679]
- after: HP=12612 ATK=221 DEF=415 YK=13 BK=1 RK=0 G=679 dmg=12014 door=151/17/4

### MT47

- before: HP=12612 ATK=221 DEF=415 YK=13 BK=1 RK=0 G=679 dmg=12014 door=151/17/4
- MT47 x11y10 fly
- MT47 x8y11 move [G 679->719] (auto: x8y9 slimelord)
- MT47 x7y11 open yellowDoor [YK 13->12]
- MT47 x11y8 move [HP 12612->12862, ATK 221->226, G 719->799] (auto: x6y10 redGem, x5y11 brownWizard, x4y10 redPotion)
- MT47 x11y7 open yellowDoor [YK 12->11]
- MT47 x11y7 move [YK 11->12, G 799->929] (auto: x11y6 redBat, x9y5 brownWizard, x8y6 yellowKey)
- MT47 x8y4 open yellowDoor [YK 12->11]
- MT47 x8y3 move [DEF 415->420, YK 11->13, G 929->1059] (auto: x9y3 slimelord, x11y3 yellowKey, x11y2 blueGem, x11y1 yellowKey, x8y1 redWizard)
- after: HP=12862 ATK=226 DEF=420 YK=13 BK=1 RK=0 G=1059 dmg=12014 door=154/17/4

### MT48

- before: HP=12862 ATK=226 DEF=420 YK=13 BK=1 RK=0 G=1059 dmg=12014 door=154/17/4
- MT48 x11y10 fly
- MT48 x11y11 pass downFloor
- after: HP=12862 ATK=226 DEF=420 YK=13 BK=1 RK=0 G=1059 dmg=12014 door=154/17/4

### MT47

- before: HP=12862 ATK=226 DEF=420 YK=13 BK=1 RK=0 G=1059 dmg=12014 door=154/17/4
- MT47 x2y6 open yellowDoor [YK 13->12]
- MT47 x3y6 move [G 1059->1109] (auto: x3y5 redBat)
- MT47 x4y4 open yellowDoor [YK 12->11]
- MT47 x1y7 move [ATK 226->231, DEF 420->425, YK 11->12, BK 1->2, G 1109->1279] (auto: x5y4 redWizard, x6y5 brownWizard, x5y7 blueKey, x5y8 redGem, x6y7 yellowKey, x6y8 blueGem)
- MT47 x1y10 move [G 1279->1369] (auto: x1y11 redWizard)
- MT47 x1y1 pass upFloor
- after: HP=12862 ATK=231 DEF=425 YK=12 BK=2 RK=0 G=1369 dmg=12014 door=156/17/4

### MT48

- before: HP=12862 ATK=231 DEF=425 YK=12 BK=2 RK=0 G=1369 dmg=12014 door=156/17/4
- MT48 x4y5 move [G 1369->1619] (auto: x3y5 slimelord, x1y7 redBat, x1y9 brownWizard, x10y7 brownWizard)
- MT48 x4y6 open yellowDoor [YK 12->11]
- MT48 x4y6 move [HP 12862->13112, ATK 231->236, G 1619->1699] (auto: x4y7 brownWizard, x3y8 redGem, x5y8 redPotion)
- MT48 x2y4 open blueDoor [BK 2->1]
- MT48 x2y4 move [HP 13112->14112, G 1699->1789] (auto: x2y3 redWizard, x2y1 bluePotion)
- after: HP=14112 ATK=236 DEF=425 YK=11 BK=1 RK=0 G=1789 dmg=12014 door=157/18/4

### MT46

- before: HP=14112 ATK=236 DEF=425 YK=11 BK=1 RK=0 G=1789 dmg=12014 door=157/18/4
- MT46 x11y10 fly
- MT46 x6y1 shop def [DEF 425->445, G 1789->449]
- after: HP=14112 ATK=236 DEF=445 YK=11 BK=1 RK=0 G=449 dmg=12014 door=157/18/4

### MT48

- before: HP=14112 ATK=236 DEF=445 YK=11 BK=1 RK=0 G=449 dmg=12014 door=157/18/4
- MT48 x11y10 fly
- MT48 x1y11 pass upFloor
- after: HP=14112 ATK=236 DEF=445 YK=11 BK=1 RK=0 G=449 dmg=12014 door=157/18/4

### MT49

- before: HP=14112 ATK=236 DEF=445 YK=11 BK=1 RK=0 G=449 dmg=12014 door=157/18/4
- MT49 x1y11 pass downFloor
- after: HP=14112 ATK=236 DEF=445 YK=11 BK=1 RK=0 G=449 dmg=12014 door=157/18/4

### MT48

- before: HP=14112 ATK=236 DEF=445 YK=11 BK=1 RK=0 G=449 dmg=12014 door=157/18/4
- MT48 x4y9 open yellowDoor [YK 11->10]
- MT48 x4y9 move [HP 14112->15112, DEF 445->450, G 449->969] (auto: x4y10 darkKnight, x3y11 blueGem, x5y11 bluePotion, x7y3 whiteKing, x7y5 whiteKing, x9y3 whiteKing, x9y5 whiteKing)
- MT48 x11y11 pass downFloor
- after: HP=15112 ATK=236 DEF=450 YK=10 BK=1 RK=0 G=969 dmg=12014 door=158/18/4

### MT45

- before: HP=15112 ATK=236 DEF=450 YK=10 BK=1 RK=0 G=969 dmg=12014 door=158/18/4
- MT45 x10y1 fly
- MT45 x6y7 move [ATK 236->246, DEF 450->460, YK 10->11, G 969->1689] (auto: x7y7 redBat, x5y5 redWizard, x7y5 brownWizard, x3y6 darkKnight, x5y3 brownWizard, x7y3 redWizard, x10y8 redWizard, x11y7 yellowKey, x3y4 darkKnight, x2y5 blueGem, x1y5 blueGem, x2y3 redGem, x1y3 redGem)
- MT45 x11y9 open yellowDoor [YK 11->10]
- MT45 x10y10 move [HP 15112->16112] (auto: x11y11 bluePotion)
- MT45 x9y10 open yellowDoor [YK 10->9]
- MT45 x8y11 kill whiteKing [G 1689->1789] (+100G)
- MT45 x8y9 kill whiteKing [G 1789->1889] (+100G)
- MT45 x5y9 kill darkKnight [G 1889->2009] (+120G)
- MT45 x5y11 kill darkKnight [G 2009->2129] (+120G)
- after: HP=16112 ATK=246 DEF=460 YK=9 BK=1 RK=0 G=2129 dmg=12014 door=160/18/4

### MT43

- before: HP=16112 ATK=246 DEF=460 YK=9 BK=1 RK=0 G=2129 dmg=12014 door=160/18/4
- MT43 x1y10 fly
- MT43 x1y5 move [G 2129->2309] (auto: x2y9 redBat, x2y5 slimelord, x4y4 redWizard)
- MT43 x3y6 open yellowDoor [YK 9->8]
- MT43 x4y7 move [HP 16112->17112, G 2309->2349] (auto: x5y7 slimelord, x6y6 bluePotion)
- MT43 x8y6 open yellowDoor [YK 8->7]
- MT43 x11y6 move [HP 17112->17362, YK 7->8, G 2349->2429] (auto: x11y7 redPotion, x9y7 brownWizard, x10y8 yellowKey)
- MT43 x11y5 open yellowDoor [YK 8->7]
- MT43 x9y1 kill whiteKing [G 2429->2529] (+100G)
- MT43 x8y4 move [DEF 460->510, G 2529->2809] (auto: x9y4 shield4, x7y4 darkKnight, x6y3 darkKnight, x5y1 slimelord)
- MT43 x11y9 open yellowDoor [YK 7->6]
- MT43 x11y10 move [BK 1->2, G 2809->2859] (auto: x10y10 redBat, x11y11 blueKey)
- MT43 x8y10 open yellowDoor [YK 6->5]
- MT43 x7y9 move [HP 17362->20362, G 2859->2979] (auto: x6y9 darkKnight, x4y9 bluePotion, x4y10 bluePotion, x4y11 bluePotion)
- MT43 x1y1 pass downFloor
- after: HP=20362 ATK=246 DEF=510 YK=5 BK=2 RK=0 G=2979 dmg=12014 door=165/18/4

### MT41

- before: HP=20362 ATK=246 DEF=510 YK=5 BK=2 RK=0 G=2979 dmg=12014 door=165/18/4
- MT41 x6y10 fly
- MT41 x6y11 pass upFloor
- after: HP=20362 ATK=246 DEF=510 YK=5 BK=2 RK=0 G=2979 dmg=12014 door=165/18/4

### MT42

- before: HP=20362 ATK=246 DEF=510 YK=5 BK=2 RK=0 G=2979 dmg=12014 door=165/18/4
- MT42 x6y8 move [RK 0->1, G 2979->3299] (auto: x6y4 darkKnight, x7y1 redKey, x9y8 whiteKing, x11y8 whiteKing)
- MT42 x6y11 pass downFloor
- after: HP=20362 ATK=246 DEF=510 YK=5 BK=2 RK=1 G=3299 dmg=12014 door=165/18/4

### MT41

- before: HP=20362 ATK=246 DEF=510 YK=5 BK=2 RK=1 G=3299 dmg=12014 door=165/18/4
- MT41 x6y10 魔法钥匙 bigKey
- MT41 x6y6 move [G 3299->3499] (auto: x5y4 whiteKing, x7y4 whiteKing)
- MT41 x5y6 open blueDoor [BK 2->1]
- MT41 x7y6 open blueDoor [BK 1->0]
- MT41 x1y2 move [HP 20362->23362, ATK 246->251, DEF 510->515, YK 5->11, BK 0->2, G 3499->3939] (auto: x1y1 redPotion, x1y6 redBat, x3y5 brownWizard, x2y7 redBat, x4y7 slimelord, x1y11 bluePotion, x4y1 blueKey, x3y9 redPotion, x4y10 yellowKey, x3y10 yellowKey, x4y11 redGem, x8y7 slimelord, x3y11 yellowKey, x9y5 brownWizard, x10y7 redBat, x11y6 redBat, x8y10 yellowKey, x9y9 redPotion, x8y11 blueGem, x9y10 yellowKey, x9y11 yellowKey, x8y1 blueKey, x11y11 bluePotion, x11y1 redPotion)
- MT41 x2y2 kill redWizard [G 3939->4029] (+90G)
- MT41 x10y2 event redWizard
- MT41 x10y2 kill redWizard [G 4029->4119] (+90G)
- after: HP=23362 ATK=251 DEF=515 YK=11 BK=2 RK=1 G=4119 dmg=12014 door=165/20/4

### MT40

- before: HP=23362 ATK=251 DEF=515 YK=11 BK=2 RK=1 G=4119 dmg=12014 door=165/20/4
- MT40 x6y2 fly
- MT40 x6y1 pass upFloor
- after: HP=23362 ATK=251 DEF=515 YK=11 BK=2 RK=1 G=4119 dmg=12014 door=165/20/4

### MT2

- before: HP=23362 ATK=251 DEF=515 YK=11 BK=2 RK=1 G=4119 dmg=12014 door=165/20/4
- MT2 x1y10 fly
- MT2 x3y10 move [HP 23362->23562] (auto: x3y11 bluePotion)
- after: HP=23562 ATK=251 DEF=515 YK=11 BK=2 RK=1 G=4119 dmg=12014 door=165/20/4

### MT13

- before: HP=23562 ATK=251 DEF=515 YK=11 BK=2 RK=1 G=4119 dmg=12014 door=165/20/4
- MT13 x2y11 fly
- MT13 x6y10 open yellowDoor [YK 11->10]
- after: HP=23562 ATK=251 DEF=515 YK=10 BK=2 RK=1 G=4119 dmg=12014 door=166/20/4

### MT18

- before: HP=23562 ATK=251 DEF=515 YK=10 BK=2 RK=1 G=4119 dmg=12014 door=166/20/4
- MT18 x6y2 fly
- MT18 x1y2 move [HP 23562->23662] (auto: x11y11 redPotion)
- MT18 x1y1 pass upFloor
- after: HP=23662 ATK=251 DEF=515 YK=10 BK=2 RK=1 G=4119 dmg=12014 door=166/20/4

### MT19

- before: HP=23662 ATK=251 DEF=515 YK=10 BK=2 RK=1 G=4119 dmg=12014 door=166/20/4
- MT19 x5y11 move [HP 23662->23762] (auto: x4y1 redPotion)
- MT19 x6y11 pass upFloor
- after: HP=23762 ATK=251 DEF=515 YK=10 BK=2 RK=1 G=4119 dmg=12014 door=166/20/4

### MT31

- before: HP=23762 ATK=251 DEF=515 YK=10 BK=2 RK=1 G=4119 dmg=12014 door=166/20/4
- MT31 x6y2 fly
- MT31 x6y10 move [HP 23762->24162, G 4119->4174] (auto: x1y2 swordsman, x2y11 redPotion, x10y1 redPotion)
- MT31 x6y11 pass upFloor
- after: HP=24162 ATK=251 DEF=515 YK=10 BK=2 RK=1 G=4174 dmg=12014 door=166/20/4

### MT33

- before: HP=24162 ATK=251 DEF=515 YK=10 BK=2 RK=1 G=4174 dmg=12014 door=166/20/4
- MT33 x10y1 fly
- MT33 x5y4 open yellowDoor [YK 10->9]
- MT33 x4y5 move [G 4174->4294] (auto: x4y6 swordsman, x6y5 zombieKnight, x6y7 ghostSkeleton)
- MT33 x3y7 open yellowDoor [YK 9->8]
- MT33 x3y7 move [HP 24162->24362, G 4294->4354] (auto: x2y7 slimeMan, x2y4 redPotion, x1y5 slimeMan)
- MT33 x1y8 open yellowDoor [YK 8->7]
- MT33 x2y9 move [YK 7->8, G 4354->4484] (auto: x3y9 zombieKnight, x1y10 swordsman, x1y11 yellowKey, x2y11 soldier)
- MT33 x4y11 open blueDoor [BK 2->1]
- MT33 x5y11 move [YK 8->9, G 4484->4559] (auto: x5y10 yellowKey, x6y9 soldier, x7y10 slimeMan)
- after: HP=24362 ATK=251 DEF=515 YK=9 BK=1 RK=1 G=4559 dmg=12014 door=169/21/4

### MT46

- before: HP=24362 ATK=251 DEF=515 YK=9 BK=1 RK=1 G=4559 dmg=12014 door=169/21/4
- MT46 x11y2 fly
- MT46 x6y1 shop def [DEF 515->535, G 4559->2979]
- MT46 x6y1 shop def [DEF 535->555, G 2979->1139]
- after: HP=24362 ATK=251 DEF=555 YK=9 BK=1 RK=1 G=1139 dmg=12014 door=169/21/4

### MT34

- before: HP=24362 ATK=251 DEF=555 YK=9 BK=1 RK=1 G=1139 dmg=12014 door=169/21/4
- MT34 x6y10 fly
- MT34 x11y7 open yellowDoor [YK 9->8]
- MT34 x11y5 open yellowDoor [YK 8->7]
- MT34 x9y6 move [G 1139->1187] (auto: x11y4 soldier, x11y8 bat)
- MT34 x9y5 open yellowDoor [YK 7->6]
- MT34 x7y6 move [G 1187->1195] (auto: x9y4 blackSlime)
- MT34 x7y5 open yellowDoor [YK 6->5]
- MT34 x5y6 move [G 1195->1250] (auto: x7y4 swordsman)
- MT34 x5y5 open yellowDoor [YK 5->4]
- MT34 x3y7 move [G 1250->1251] (auto: x5y4 greenSlime)
- MT34 x7y7 open yellowDoor [YK 4->3]
- MT34 x9y6 move [G 1251->1253] (auto: x7y8 redSlime)
- MT34 x9y7 open yellowDoor [YK 3->2]
- MT34 x5y6 move [G 1253->1318] (auto: x9y8 redKnight)
- MT34 x5y7 open yellowDoor [YK 2->1]
- MT34 x3y6 move [G 1318->1353] (auto: x5y8 ghostSkeleton)
- MT34 x2y6 take redKey [YK 1->5, RK 1->2] (auto: x1y5 yellowKey, x3y5 yellowKey, x1y7 yellowKey, x3y7 yellowKey)
- after: HP=24362 ATK=251 DEF=555 YK=5 BK=1 RK=2 G=1353 dmg=12014 door=177/21/4

### MT49

- before: HP=24362 ATK=251 DEF=555 YK=5 BK=1 RK=2 G=1353 dmg=12014 door=177/21/4
- MT49 x2y11 fly
- MT49 x3y11 open redDoor [RK 2->1]
- MT49 x5y10 kill redWizard [G 1353->1443] (+90G)
- MT49 x7y10 kill redWizard [G 1443->1533] (+90G)
- MT49 x5y8 kill darkKnight [G 1533->1653] (+120G)
- MT49 x7y8 kill darkKnight [G 1653->1773] (+120G)
- MT49 x1y11 pass downFloor
- after: HP=24362 ATK=251 DEF=555 YK=5 BK=1 RK=1 G=1773 dmg=12014 door=177/21/5

### MT28

- before: HP=24362 ATK=251 DEF=555 YK=5 BK=1 RK=1 G=1773 dmg=12014 door=177/21/5
- MT28 x2y11 fly
- MT28 x8y4 trader specialTrader [YK 5->4, G 1773->1873] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 4->3, G 1873->1973] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 3->2, G 1973->2073] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 2->1, G 2073->2173] (auto: +100G)
- after: HP=24362 ATK=251 DEF=555 YK=1 BK=1 RK=1 G=2173 dmg=12014 door=177/21/5

### MT46

- before: HP=24362 ATK=251 DEF=555 YK=1 BK=1 RK=1 G=2173 dmg=12014 door=177/21/5
- MT46 x11y2 fly
- MT46 x6y1 shop def [DEF 555->575, G 2173->53]
- after: HP=24362 ATK=251 DEF=575 YK=1 BK=1 RK=1 G=53 dmg=12014 door=177/21/5

### MT2

- before: HP=24362 ATK=251 DEF=575 YK=1 BK=1 RK=1 G=53 dmg=12014 door=177/21/5
- MT2 x1y10 fly
- MT2 x11y7 event specialTrader [ATK 251->259, DEF 575->592]
- after: HP=24362 ATK=259 DEF=592 YK=1 BK=1 RK=1 G=53 dmg=12014 door=177/21/5

### MT35

- before: HP=24362 ATK=259 DEF=592 YK=1 BK=1 RK=1 G=53 dmg=12014 door=177/21/5
- MT35 x6y10 fly
- MT35 x6y7 kill magicDragon [HP 24362->23034, G 53->853] (+800G)
- MT35 x6y6 take snow [HP 23034->25434] (auto: x6y5 bluePotion, x5y5 bluePotion, x7y5 bluePotion)
- after: HP=25434 ATK=259 DEF=592 YK=1 BK=1 RK=1 G=853 dmg=13342 door=177/21/5

### MT13

- before: HP=25434 ATK=259 DEF=592 YK=1 BK=1 RK=1 G=853 dmg=13342 door=177/21/5
- MT13 x10y11 fly
- MT13 x6y10 move [ATK 259->359] (auto: x6y9 lava, x6y8 lava, x5y9 lava, x7y9 lava, x6y7 lava, x5y8 lava, x7y8 lava, x4y9 lava, x8y9 lava, x6y6 lava, x4y8 lava, x8y8 lava, x3y9 lava, x9y9 lava, x6y5 sword5, x4y7 lava, x3y8 lava, x8y7 lava, x9y8 lava, x2y9 lava, x10y9 lava, x3y7 lava, x2y8 lava, x9y7 lava, x10y8 lava, x1y9 lava, x11y9 lava, x3y6 lava, x2y7 lava, x1y8 lava, x9y6 lava, x10y7 lava, x11y8 lava, x3y5 lava, x2y6 lava, x1y7 lava, x9y5 lava, x10y6 lava, x11y7 lava, x3y4 lava, x2y5 lava, x1y6 lava, x9y4 lava, x10y5 lava, x11y6 lava, x3y3 lava, x2y4 lava, x1y5 lava, x9y3 lava, x10y4 lava, x11y5 lava, x3y2 lava, x2y3 lava, x4y3 lava, x1y4 lava, x9y2 lava, x8y3 lava, x10y3 lava, x11y4 lava, x3y1 lava, x2y2 lava, x4y2 lava, x1y3 lava, x9y1 lava, x8y2 lava, x10y2 lava, x11y3 lava, x2y1 lava, x4y1 lava, x1y2 lava, x5y2 lava, x8y1 lava, x10y1 lava, x7y2 lava, x11y2 lava, x1y1 lava, x5y1 lava, x6y2 lava, x7y1 lava, x11y1 lava, x6y1 lava)
- after: HP=25434 ATK=359 DEF=592 YK=1 BK=1 RK=1 G=853 dmg=13342 door=177/21/5

### MT25

- before: HP=25434 ATK=359 DEF=592 YK=1 BK=1 RK=1 G=853 dmg=13342 door=177/21/5
- MT25 x2y11 fly
- MT25 x6y10 open redDoor [RK 1->0]
- MT25 x6y9 pass
- MT25 x6y6 kill blackMagician [G 853->1853] (+1000G)
- MT25 x1y10 move [RK 0->4] (auto: x5y8 redKey, x7y8 redKey, x4y8 redKey, x8y8 redKey)
- MT25 x1y11 pass upFloor
- after: HP=25434 ATK=359 DEF=592 YK=1 BK=1 RK=4 G=1853 dmg=13342 door=177/21/6

### MT26

- before: HP=25434 ATK=359 DEF=592 YK=1 BK=1 RK=4 G=1853 dmg=13342 door=177/21/6
- MT26 x6y10 open redDoor [RK 4->3]
- MT26 x6y9 open redDoor [RK 3->2]
- MT26 x6y8 open redDoor [RK 2->1]
- MT26 x6y6 event princess
- MT26 x1y11 pass downFloor
- after: HP=25434 ATK=359 DEF=592 YK=1 BK=1 RK=1 G=1853 dmg=13342 door=177/21/9

### MT25

- before: HP=25434 ATK=359 DEF=592 YK=1 BK=1 RK=1 G=1853 dmg=13342 door=177/21/9
- MT25 x2y10 pass downFloor
- after: HP=25434 ATK=359 DEF=592 YK=1 BK=1 RK=1 G=1853 dmg=13342 door=177/21/9

### MT24

- before: HP=25434 ATK=359 DEF=592 YK=1 BK=1 RK=1 G=1853 dmg=13342 door=177/21/9
- MT24 x6y8 open redDoor [RK 1->0]
- MT24 x6y2 pass
- after: HP=25434 ATK=359 DEF=592 YK=1 BK=1 RK=0 G=1853 dmg=13342 door=177/21/10

### MT50

- before: HP=25434 ATK=359 DEF=592 YK=1 BK=1 RK=0 G=1853 dmg=13342 door=177/21/10
- MT50 x6y5 event redKing
- MT50 x6y5 event thief
- after: HP=25434 ATK=359 DEF=592 YK=1 BK=1 RK=0 G=1853 dmg=13342 door=177/21/10

### MT49

- before: HP=25434 ATK=359 DEF=592 YK=1 BK=1 RK=0 G=1853 dmg=13342 door=177/21/10
- MT49 x5y5 下楼器 downFly
- MT49 x6y6 pass
- MT49 x6y6 event redKing
- MT49 x6y4 kill whiteKing [G 1853->1953] (+100G)
- MT49 x7y3 kill whiteKing [G 1953->2053] (+100G)
- MT49 x6y2 kill whiteKing [G 2053->2153] (+100G)
- MT49 x5y3 kill whiteKing [G 2153->2253] (+100G)
- MT49 x5y4 kill whiteKing [G 2253->2353] (+100G)
- MT49 x5y2 kill whiteKing [G 2353->2453] (+100G)
- MT49 x7y2 kill whiteKing [G 2453->2553] (+100G)
- MT49 x7y4 kill whiteKing [G 2553->2653] (+100G)
- MT49 x6y3 kill redKing [G 2653->3153] (+500G)
- MT49 x6y4 move [HP 25434->28434, ATK 359->374, DEF 592->607, RK 0->1] (auto: x5y2 redKey, x7y2 knife, x6y5 bluePotion, x4y4 redGem, x5y5 bluePotion, x7y5 bluePotion, x8y4 blueGem, x3y4 redGem, x9y4 blueGem, x2y4 redGem, x10y4 blueGem)
- after: HP=28434 ATK=374 DEF=607 YK=1 BK=1 RK=1 G=3153 dmg=13342 door=177/21/10

### MT48

- before: HP=28434 ATK=374 DEF=607 YK=1 BK=1 RK=1 G=3153 dmg=13342 door=177/21/10
- MT48 x1y10 fly
- MT48 x5y2 open blueDoor [BK 1->0]
- MT48 x6y1 move [HP 28434->29184] (auto: x7y1 redPotion, x8y1 redPotion, x9y1 redPotion)
- after: HP=29184 ATK=374 DEF=607 YK=1 BK=0 RK=1 G=3153 dmg=13342 door=177/22/10

### MT46

- before: HP=29184 ATK=374 DEF=607 YK=1 BK=0 RK=1 G=3153 dmg=13342 door=177/22/10
- MT46 x11y10 fly
- after: HP=29184 ATK=374 DEF=607 YK=1 BK=0 RK=1 G=3153 dmg=13342 door=177/22/10

### MT45

- before: HP=29184 ATK=374 DEF=607 YK=1 BK=0 RK=1 G=3153 dmg=13342 door=177/22/10
- MT45 x10y1 fly
- MT45 x11y5 open yellowDoor [YK 1->0]
- MT45 x11y5 move [G 3153->3193] (auto: x11y4 slimelord)
- MT45 x9y3 trader hp2000 [HP 29184->31184, G 3193->2193]
- after: HP=31184 ATK=374 DEF=607 YK=0 BK=0 RK=1 G=2193 dmg=13342 door=178/22/10

### MT31

- before: HP=31184 ATK=374 DEF=607 YK=0 BK=0 RK=1 G=2193 dmg=13342 door=178/22/10
- MT31 x6y10 fly
- MT31 x1y11 trader keyBundle31 [YK 0->4, BK 0->1, G 2193->1193]
- MT31 x9y8 open yellowDoor [YK 4->3]
- MT31 x9y8 move [HP 31184->31984] (auto: x8y8 bluePotion)
- after: HP=31984 ATK=374 DEF=607 YK=3 BK=1 RK=1 G=1193 dmg=13342 door=179/22/10

### MT45

- before: HP=31984 ATK=374 DEF=607 YK=3 BK=1 RK=1 G=1193 dmg=13342 door=179/22/10
- MT45 x2y1 fly
- after: HP=31984 ATK=374 DEF=607 YK=3 BK=1 RK=1 G=1193 dmg=13342 door=179/22/10

### MT20

- before: HP=31984 ATK=374 DEF=607 YK=3 BK=1 RK=1 G=1193 dmg=13342 door=179/22/10
- MT20 x6y2 fly
- MT20 x10y11 move [HP 31984->32084] (auto: x11y11 redPotion)
- MT20 x11y9 open yellowDoor [YK 3->2]
- MT20 x11y8 move [G 1193->1199] (auto: x11y7 bat, x10y8 bat)
- MT20 x10y6 open blueDoor [BK 1->0]
- MT20 x10y5 move [HP 32084->32584, YK 2->3] (auto: x10y4 redPotion, x11y5 yellowKey, x11y4 bluePotion)
- after: HP=32584 ATK=374 DEF=607 YK=3 BK=0 RK=1 G=1199 dmg=13342 door=180/23/10

### MT8

- before: HP=32584 ATK=374 DEF=607 YK=3 BK=0 RK=1 G=1199 dmg=13342 door=180/23/10
- MT8 x6y2 fly
- MT8 x1y3 open yellowDoor [YK 3->2]
- MT8 x1y4 move [HP 32584->32634, G 1199->1204] (auto: x1y5 redPotion, x2y6 redSlime, x3y6 greenSlime, x4y6 redSlime)
- MT8 x1y1 pass downFloor
- after: HP=32634 ATK=374 DEF=607 YK=2 BK=0 RK=1 G=1204 dmg=13342 door=181/23/10

### MT7

- before: HP=32634 ATK=374 DEF=607 YK=2 BK=0 RK=1 G=1204 dmg=13342 door=181/23/10
- MT7 x11y11 pass downFloor
- after: HP=32634 ATK=374 DEF=607 YK=2 BK=0 RK=1 G=1204 dmg=13342 door=181/23/10

### MT6

- before: HP=32634 ATK=374 DEF=607 YK=2 BK=0 RK=1 G=1204 dmg=13342 door=181/23/10
- MT6 x1y1 pass downFloor
- after: HP=32634 ATK=374 DEF=607 YK=2 BK=0 RK=1 G=1204 dmg=13342 door=181/23/10

### MT5

- before: HP=32634 ATK=374 DEF=607 YK=2 BK=0 RK=1 G=1204 dmg=13342 door=181/23/10
- MT5 x1y11 pass downFloor
- after: HP=32634 ATK=374 DEF=607 YK=2 BK=0 RK=1 G=1204 dmg=13342 door=181/23/10

### MT4

- before: HP=32634 ATK=374 DEF=607 YK=2 BK=0 RK=1 G=1204 dmg=13342 door=181/23/10
- MT4 x11y11 pass downFloor
- after: HP=32634 ATK=374 DEF=607 YK=2 BK=0 RK=1 G=1204 dmg=13342 door=181/23/10

### MT3

- before: HP=32634 ATK=374 DEF=607 YK=2 BK=0 RK=1 G=1204 dmg=13342 door=181/23/10
- MT3 x9y2 open yellowDoor [YK 2->1]
- MT3 x9y2 move [HP 32634->32684, G 1204->1207] (auto: x10y2 bat, x11y1 redPotion)
- MT3 x10y2 使用 superPotion [HP 32684->39944]
- after: HP=39944 ATK=374 DEF=607 YK=1 BK=0 RK=1 G=1207 dmg=13342 door=182/23/10

### MT24

- before: HP=39944 ATK=374 DEF=607 YK=1 BK=0 RK=1 G=1207 dmg=13342 door=182/23/10
- MT24 x2y11 fly
- MT24 x6y2 pass
- after: HP=39944 ATK=374 DEF=607 YK=1 BK=0 RK=1 G=1207 dmg=13342 door=182/23/10

### MT50

- before: HP=39944 ATK=374 DEF=607 YK=1 BK=0 RK=1 G=1207 dmg=13342 door=182/23/10
- MT50 x6y5 kill redKing [G 1207->1707] (+500G)
- after: HP=39944 ATK=374 DEF=607 YK=1 BK=0 RK=1 G=1707 dmg=13342 door=182/23/10
