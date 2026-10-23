# 当前最优 Walk (zone4, auto ON)

## 说明

- 本 walk 由 Game 类 (`scripts/search/zone4_game_route.py`, auto_sweep, strict_live_model) 离线推导生成。
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone4_game_route.json --load-slot <100+> --target-click-only`（统一点击 verifier，1-4 区通用；3 区起按需 `--set-auto battle=true,item=nopotion,wall=true`）
- 源 JSON：`best/zone12_2atk6def_38624_walk.json`

## 摘要

- final: HP=38624 ATK=390 DEF=574 YK=0 BK=0 RK=0 G=159 dmg=13982 door=168/22/10 MT45 x9y4

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

### MT10

- before: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=130 dmg=8012 door=90/8/2
- MT10 x6y10 fly
- MT10 x5y10 move [G 130->158] (auto: x3y6 skeleton, x2y7 skeletonSoldier, x10y7 skeletonSoldier, x11y6 skeleton)
- MT10 x6y11 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=158 dmg=8012 door=90/8/2

### MT11

- before: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=158 dmg=8012 door=90/8/2
- MT11 x11y10 move [G 158->180] (auto: x8y5 redPriest)
- MT11 x11y11 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=180 dmg=8012 door=90/8/2

### MT12

- before: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=180 dmg=8012 door=90/8/2
- MT12 x2y11 move [G 180->228] (auto: x9y9 blackSlime, x10y3 zombie, x10y1 fakeWall, x5y3 redPriest)
- MT12 x1y11 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=228 dmg=8012 door=90/8/2

### MT13

- before: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=228 dmg=8012 door=90/8/2
- MT13 x11y11 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=228 dmg=8012 door=90/8/2

### MT14

- before: HP=114 ATK=76 DEF=112 YK=5 BK=0 RK=0 G=228 dmg=8012 door=90/8/2
- MT14 x7y5 move [G 228->316] (auto: x6y5 rock, x4y5 bigBat, x2y6 blackSlime, x4y8 zombie, x3y9 redPriest)
- MT14 x1y7 open yellowDoor [YK 5->4]
- MT14 x1y8 move [BK 0->1, G 316->338] (auto: x1y9 redPriest, x1y11 blueKey)
- MT14 x6y11 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=4 BK=1 RK=0 G=338 dmg=8012 door=91/8/2

### MT15

- before: HP=114 ATK=76 DEF=112 YK=4 BK=1 RK=0 G=338 dmg=8012 door=91/8/2
- MT15 x5y1 move [G 338->368] (auto: x3y3 blackSlime, x2y11 redPriest)
- MT15 x6y1 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=4 BK=1 RK=0 G=368 dmg=8012 door=91/8/2

### MT16

- before: HP=114 ATK=76 DEF=112 YK=4 BK=1 RK=0 G=368 dmg=8012 door=91/8/2
- MT16 x10y3 move [G 368->436] (auto: x5y3 zombie, x2y2 redPriest, x3y6 rock)
- MT16 x10y4 open yellowDoor [YK 4->3]
- MT16 x10y4 move [BK 1->2, G 436->466] (auto: x10y5 zombie, x9y7 bigBat, x11y7 blueKey)
- after: HP=114 ATK=76 DEF=112 YK=3 BK=2 RK=0 G=466 dmg=8012 door=92/8/2

### MT32

- before: HP=114 ATK=76 DEF=112 YK=3 BK=2 RK=0 G=466 dmg=8012 door=92/8/2
- MT32 x6y11 fly
- MT32 x10y10 shop def [DEF 112->128, G 466->146]
- MT32 x3y1 open blueDoor [BK 2->1]
- MT32 x2y1 move [ATK 76->80, DEF 128->132] (auto: x1y1 blueGem, x2y2 redGem)
- after: HP=114 ATK=80 DEF=132 YK=3 BK=1 RK=0 G=146 dmg=8012 door=92/9/2

### MT14

- before: HP=114 ATK=80 DEF=132 YK=3 BK=1 RK=0 G=146 dmg=8012 door=92/9/2
- MT14 x6y10 fly
- MT14 x7y5 move [G 146->176] (auto: x10y4 zombieKnight)
- MT14 x7y4 open yellowDoor [YK 3->2]
- MT14 x10y4 move [G 176->206] (auto: x7y2 zombieKnight)
- MT14 x10y3 open yellowDoor [YK 2->1]
- MT14 x10y2 move [YK 1->5] (auto: x10y1 yellowKey, x11y2 yellowKey, x9y1 yellowKey, x11y1 yellowKey)
- MT14 x7y1 take redPotion [HP 114->214, DEF 132->134, YK 5->6, G 206->214] (auto: x6y1 yellowKey, x5y1 blueGem, x5y2 blackSlime)
- MT14 x6y11 pass upFloor
- after: HP=214 ATK=80 DEF=134 YK=6 BK=1 RK=0 G=214 dmg=8012 door=94/9/2

### MT15

- before: HP=214 ATK=80 DEF=134 YK=6 BK=1 RK=0 G=214 dmg=8012 door=94/9/2
- MT15 x5y1 move [G 214->244] (auto: x2y1 zombieKnight)
- MT15 x6y1 pass upFloor
- after: HP=214 ATK=80 DEF=134 YK=6 BK=1 RK=0 G=244 dmg=8012 door=94/9/2

### MT16

- before: HP=214 ATK=80 DEF=134 YK=6 BK=1 RK=0 G=244 dmg=8012 door=94/9/2
- MT16 x5y11 move [G 244->274] (auto: x6y6 zombieKnight)
- MT16 x6y11 pass upFloor
- after: HP=214 ATK=80 DEF=134 YK=6 BK=1 RK=0 G=274 dmg=8012 door=94/9/2

### MT17

- before: HP=214 ATK=80 DEF=134 YK=6 BK=1 RK=0 G=274 dmg=8012 door=94/9/2
- MT17 x10y11 move [G 274->322] (auto: x5y7 zombie, x5y3 zombieKnight)
- MT17 x10y10 open yellowDoor [YK 6->5]
- MT17 x9y8 kill zombie [G 322->340] (+18G)
- MT17 x11y8 kill zombie [G 340->358] (+18G)
- MT17 x9y5 kill zombieKnight [G 358->388] (+30G)
- MT17 x11y5 kill zombieKnight [G 388->418] (+30G)
- MT17 x10y2 take bluePotion [HP 214->614, ATK 80->82, DEF 134->136, YK 5->7]
- MT17 x6y1 pass upFloor
- after: HP=614 ATK=82 DEF=136 YK=7 BK=1 RK=0 G=418 dmg=8012 door=95/9/2

### MT18

- before: HP=614 ATK=82 DEF=136 YK=7 BK=1 RK=0 G=418 dmg=8012 door=95/9/2
- MT18 x4y7 move [G 418->558] (auto: x7y4 zombieKnight, x10y7 rock, x3y5 rock, x1y5 rock, x10y2 blackSlime, x9y4 zombie)
- MT18 x4y8 open yellowDoor [YK 7->6]
- MT18 x4y8 move [YK 6->7, G 558->606] (auto: x4y9 bigBat, x4y10 bigBat, x5y9 bigBat, x5y10 bigBat, x5y11 yellowKey)
- MT18 x8y8 open yellowDoor [YK 7->6]
- MT18 x11y7 move [YK 6->7, G 606->638] (auto: x8y9 blackSlime, x7y9 blackSlime, x8y10 blackSlime, x7y10 blackSlime, x7y11 yellowKey)
- MT18 x11y8 open yellowDoor [YK 7->6]
- MT18 x11y8 move [DEF 136->138, YK 6->7, G 638->660] (auto: x11y9 redPriest, x10y10 yellowKey, x10y11 blueGem)
- MT18 x1y1 pass upFloor
- after: HP=614 ATK=82 DEF=138 YK=7 BK=1 RK=0 G=660 dmg=8012 door=98/9/2

### MT19

- before: HP=614 ATK=82 DEF=138 YK=7 BK=1 RK=0 G=660 dmg=8012 door=98/9/2
- MT19 x5y11 move [BK 1->2, G 660->838] (auto: x6y9 zombieKnight, x8y8 zombieKnight, x5y6 rock, x4y3 zombieKnight, x8y3 zombieKnight, x11y5 blackSlime, x8y1 blueKey, x6y1 redPriest)
- MT19 x6y11 pass upFloor
- after: HP=614 ATK=82 DEF=138 YK=7 BK=2 RK=0 G=838 dmg=8012 door=98/9/2

### MT20

- before: HP=614 ATK=82 DEF=138 YK=7 BK=2 RK=0 G=838 dmg=8012 door=98/9/2
- MT20 x7y11 move [G 838->916] (auto: x8y11 redPriest, x10y10 rock, x2y10 rock)
- after: HP=614 ATK=82 DEF=138 YK=7 BK=2 RK=0 G=916 dmg=8012 door=98/9/2

### MT32

- before: HP=614 ATK=82 DEF=138 YK=7 BK=2 RK=0 G=916 dmg=8012 door=98/9/2
- MT32 x6y11 fly
- MT32 x10y10 shop def [DEF 138->154, G 916->476]
- MT32 x5y3 open yellowDoor [YK 7->6]
- MT32 x5y3 move [YK 6->7, G 476->536] (auto: x3y4 slimeMan, x4y5 slimeMan, x2y5 yellowKey)
- MT32 x11y1 pass upFloor
- after: HP=614 ATK=82 DEF=154 YK=7 BK=2 RK=0 G=536 dmg=8012 door=99/9/2

### MT33

- before: HP=614 ATK=82 DEF=154 YK=7 BK=2 RK=0 G=536 dmg=8012 door=99/9/2
- MT33 x7y1 open yellowDoor [YK 7->6]
- MT33 x7y1 move [YK 6->7, G 536->596] (auto: x6y1 slimeMan, x4y1 zombieKnight, x6y3 yellowKey)
- after: HP=614 ATK=82 DEF=154 YK=7 BK=2 RK=0 G=596 dmg=8012 door=100/9/2

### MT16

- before: HP=614 ATK=82 DEF=154 YK=7 BK=2 RK=0 G=596 dmg=8012 door=100/9/2
- MT16 x6y10 fly
- MT16 x8y10 open yellowDoor [YK 7->6]
- MT16 x9y10 move [G 596->648] (auto: x9y11 slimeMan, x10y9 redPriest, x10y11 fakeWall)
- MT16 x11y11 pass fakeWall2
- MT16 x11y11 event superPotion
- after: HP=614 ATK=82 DEF=154 YK=6 BK=2 RK=0 G=648 dmg=8012 door=101/9/2

### MT32

- before: HP=614 ATK=82 DEF=154 YK=6 BK=2 RK=0 G=648 dmg=8012 door=101/9/2
- MT32 x6y11 fly
- MT32 x10y10 shop def [DEF 154->170, G 648->68]
- MT32 x11y1 pass upFloor
- after: HP=614 ATK=82 DEF=170 YK=6 BK=2 RK=0 G=68 dmg=8012 door=101/9/2

### MT33

- before: HP=614 ATK=82 DEF=170 YK=6 BK=2 RK=0 G=68 dmg=8012 door=101/9/2
- MT33 x8y2 open yellowDoor [YK 6->5]
- MT33 x5y2 take redPotion [HP 614->814]
- MT33 x10y5 pass
- MT33 x9y5 kill ghostSkeleton [HP 814->774, G 68->103] (+35G)
- MT33 x11y5 kill ghostSkeleton [HP 774->734, G 103->138] (+35G)
- MT33 x11y7 kill soldier [HP 734->374, G 138->183] (+45G)
- MT33 x9y7 kill soldier [HP 374->14, G 183->228] (+45G)
- MT33 x9y10 move [ATK 82->122] (auto: x10y10 sword3)
- MT33 x3y1 open yellowDoor [YK 5->4]
- MT33 x1y1 pass upFloor
- after: HP=14 ATK=122 DEF=170 YK=4 BK=2 RK=0 G=228 dmg=8812 door=103/9/2

### MT34

- before: HP=14 ATK=122 DEF=170 YK=4 BK=2 RK=0 G=228 dmg=8812 door=103/9/2
- MT34 x3y1 take redPotion [HP 14->214, G 228->258] (auto: x2y3 slimeMan)
- MT34 x4y2 open yellowDoor [YK 4->3]
- MT34 x2y3 move [YK 3->4, G 258->288] (auto: x5y2 slimeMan, x6y1 yellowKey)
- MT34 x2y4 open yellowDoor [YK 4->3]
- MT34 x2y8 open yellowDoor [YK 3->2]
- MT34 x3y9 kill ghostSkeleton [HP 214->194, G 288->323] (+35G)
- MT34 x4y10 open yellowDoor [YK 2->1]
- MT34 x6y11 pass upFloor
- after: HP=194 ATK=122 DEF=170 YK=1 BK=2 RK=0 G=323 dmg=8832 door=107/9/2

### MT15

- before: HP=194 ATK=122 DEF=170 YK=1 BK=2 RK=0 G=323 dmg=8832 door=107/9/2
- MT15 x6y2 fly
- after: HP=194 ATK=122 DEF=170 YK=1 BK=2 RK=0 G=323 dmg=8832 door=107/9/2

### MT2

- before: HP=194 ATK=122 DEF=170 YK=1 BK=2 RK=0 G=323 dmg=8832 door=107/9/2
- MT2 x1y10 fly
- MT2 x3y1 open blueDoor [BK 2->1]
- after: HP=194 ATK=122 DEF=170 YK=1 BK=1 RK=0 G=323 dmg=8832 door=107/10/2

### MT31

- before: HP=194 ATK=122 DEF=170 YK=1 BK=1 RK=0 G=323 dmg=8832 door=107/10/2
- MT31 x6y2 fly
- MT31 x10y6 kill ghostSkeleton [HP 194->174, G 323->358] (+35G)
- MT31 x11y7 open yellowDoor [YK 1->0]
- MT31 x10y8 move [YK 0->4, G 358->418] (auto: x10y9 slimeMan, x9y10 yellowKey, x11y10 slimeMan, x8y10 yellowKey, x9y11 yellowKey, x8y11 yellowKey)
- MT31 x6y11 pass upFloor
- after: HP=174 ATK=122 DEF=170 YK=4 BK=1 RK=0 G=418 dmg=8852 door=108/10/2

### MT28

- before: HP=174 ATK=122 DEF=170 YK=4 BK=1 RK=0 G=418 dmg=8852 door=108/10/2
- MT28 x2y11 fly
- MT28 x8y4 trader specialTrader [YK 4->3, G 418->518] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 3->2, G 518->618] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 2->1, G 618->718] (auto: +100G)
- after: HP=174 ATK=122 DEF=170 YK=1 BK=1 RK=0 G=718 dmg=8852 door=108/10/2

### MT32

- before: HP=174 ATK=122 DEF=170 YK=1 BK=1 RK=0 G=718 dmg=8852 door=108/10/2
- MT32 x6y11 fly
- after: HP=174 ATK=122 DEF=170 YK=1 BK=1 RK=0 G=718 dmg=8852 door=108/10/2

### MT14

- before: HP=174 ATK=122 DEF=170 YK=1 BK=1 RK=0 G=718 dmg=8852 door=108/10/2
- MT14 x6y10 fly
- MT14 x2y4 open blueDoor [BK 1->0]
- MT14 x2y3 move [G 718->808] (auto: x2y2 zombieKnight, x1y1 zombieKnight, x3y1 zombieKnight)
- MT14 x2y2 move [RK 0->1] (auto: x1y3 redKey)
- after: HP=174 ATK=122 DEF=170 YK=1 BK=0 RK=1 G=808 dmg=8852 door=108/11/2

### MT32

- before: HP=174 ATK=122 DEF=170 YK=1 BK=0 RK=1 G=808 dmg=8852 door=108/11/2
- MT32 x6y11 fly
- MT32 x10y10 shop atk [ATK 122->130, G 808->68]
- after: HP=174 ATK=130 DEF=170 YK=1 BK=0 RK=1 G=68 dmg=8852 door=108/11/2

### MT2

- before: HP=174 ATK=130 DEF=170 YK=1 BK=0 RK=1 G=68 dmg=8852 door=108/11/2
- MT2 x1y10 fly
- MT2 x6y2 kill blueGuard [HP 174->134, G 68->118] (+50G)
- MT2 x8y2 kill blueGuard [HP 134->94, G 118->168] (+50G)
- MT2 x10y4 move [YK 1->4] (auto: x4y4 yellowKey, x3y5 yellowKey, x3y4 yellowKey)
- MT2 x11y4 event oldman [G 168->1168] (auto: +1000G)
- MT2 x10y11 event thief
- after: HP=94 ATK=130 DEF=170 YK=4 BK=0 RK=1 G=1168 dmg=8932 door=108/11/2

### MT35

- before: HP=94 ATK=130 DEF=170 YK=4 BK=0 RK=1 G=1168 dmg=8932 door=108/11/2
- MT35 x6y10 fly
- MT35 x5y10 pass thief
- after: HP=94 ATK=130 DEF=170 YK=4 BK=0 RK=1 G=1168 dmg=8932 door=108/11/2

### MT32

- before: HP=94 ATK=130 DEF=170 YK=4 BK=0 RK=1 G=1168 dmg=8932 door=108/11/2
- MT32 x10y1 fly
- MT32 x10y10 shop atk [ATK 130->138, G 1168->248]
- after: HP=94 ATK=138 DEF=170 YK=4 BK=0 RK=1 G=248 dmg=8932 door=108/11/2

### MT35

- before: HP=94 ATK=138 DEF=170 YK=4 BK=0 RK=1 G=248 dmg=8932 door=108/11/2
- MT35 x6y10 fly
- MT35 x11y1 pass upFloor
- after: HP=94 ATK=138 DEF=170 YK=4 BK=0 RK=1 G=248 dmg=8932 door=108/11/2

### MT34

- before: HP=94 ATK=138 DEF=170 YK=4 BK=0 RK=1 G=248 dmg=8932 door=108/11/2
- MT34 x6y10 fly
- MT34 x8y10 open yellowDoor [YK 4->3]
- MT34 x9y10 kill soldier [HP 94->34, ATK 138->142, YK 3->4, G 248->293] (auto: x10y11 yellowKey, x11y11 redGem) (+45G)
- MT34 x11y10 take redPotion [HP 34->234]
- after: HP=234 ATK=142 DEF=170 YK=4 BK=0 RK=1 G=293 dmg=8992 door=109/11/2

### MT31

- before: HP=234 ATK=142 DEF=170 YK=4 BK=0 RK=1 G=293 dmg=8992 door=109/11/2
- MT31 x6y10 fly
- MT31 x11y5 open yellowDoor [YK 4->3]
- MT31 x10y3 kill ghostSkeleton [HP 234->224, G 293->328] (+35G)
- MT31 x8y2 kill soldier [HP 224->164, G 328->373] (+45G)
- MT31 x8y3 open yellowDoor [YK 3->2]
- MT31 x8y3 move [ATK 142->146] (auto: x8y4 redGem)
- after: HP=164 ATK=146 DEF=170 YK=2 BK=0 RK=1 G=373 dmg=9062 door=111/11/2

### MT2

- before: HP=164 ATK=146 DEF=170 YK=2 BK=0 RK=1 G=373 dmg=9062 door=111/11/2
- MT2 x1y10 fly
- MT2 x4y10 take bluePotion [HP 164->364]
- after: HP=364 ATK=146 DEF=170 YK=2 BK=0 RK=1 G=373 dmg=9062 door=111/11/2

### MT14

- before: HP=364 ATK=146 DEF=170 YK=2 BK=0 RK=1 G=373 dmg=9062 door=111/11/2
- MT14 x11y10 fly
- MT14 x1y5 take redPotion [HP 364->464]
- after: HP=464 ATK=146 DEF=170 YK=2 BK=0 RK=1 G=373 dmg=9062 door=111/11/2

### MT36

- before: HP=464 ATK=146 DEF=170 YK=2 BK=0 RK=1 G=373 dmg=9062 door=111/11/2
- MT36 x11y2 fly
- MT36 x10y1 move [G 373->403] (auto: x11y3 slimeMan)
- MT36 x9y1 kill redKnight [HP 464->284, G 403->498] (auto: x7y1 zombieKnight) (+95G)
- MT36 x6y2 open yellowDoor [YK 2->1]
- MT36 x6y5 kill ghostSkeleton [HP 284->274, G 498->593] (auto: x5y6 slimeMan, x7y6 slimeMan) (+95G)
- MT36 x10y6 open yellowDoor [YK 1->0]
- MT36 x11y7 kill redKnight [HP 274->94, G 593->658] (+65G)
- MT36 x11y11 pass upFloor
- after: HP=94 ATK=146 DEF=170 YK=0 BK=0 RK=1 G=658 dmg=9432 door=113/11/2

### MT37

- before: HP=94 ATK=146 DEF=170 YK=0 BK=0 RK=1 G=658 dmg=9432 door=113/11/2
- MT37 x9y11 kill ghostSkeleton [HP 94->84, G 658->723] (auto: x3y11 slimeMan) (+65G)
- MT37 x1y9 kill soldier [HP 84->24, G 723->768] (+45G)
- MT37 x1y6 take redPotion [HP 24->224]
- after: HP=224 ATK=146 DEF=170 YK=0 BK=0 RK=1 G=768 dmg=9502 door=113/11/2

### MT32

- before: HP=224 ATK=146 DEF=170 YK=0 BK=0 RK=1 G=768 dmg=9502 door=113/11/2
- MT32 x10y1 fly
- MT32 x1y10 kill blueGuard [HP 224->204, G 768->818] (+50G)
- MT32 x3y10 kill blueGuard [HP 204->184, G 818->868] (+50G)
- MT32 x3y8 move [YK 0->4, BK 0->1] (auto: x3y7 yellowKey, x4y8 blueKey, x2y7 yellowKey, x4y7 yellowKey, x1y7 yellowKey)
- after: HP=184 ATK=146 DEF=170 YK=4 BK=1 RK=1 G=868 dmg=9542 door=113/11/2

### MT37

- before: HP=184 ATK=146 DEF=170 YK=4 BK=1 RK=1 G=868 dmg=9542 door=113/11/2
- MT37 x11y10 fly
- MT37 x1y3 open blueDoor [BK 1->0]
- MT37 x1y1 pass upFloor
- after: HP=184 ATK=146 DEF=170 YK=4 BK=0 RK=1 G=868 dmg=9542 door=113/12/2

### MT38

- before: HP=184 ATK=146 DEF=170 YK=4 BK=0 RK=1 G=868 dmg=9542 door=113/12/2
- MT38 x3y1 open redDoor [RK 1->0]
- MT38 x3y1 move [YK 4->5, G 868->928] (auto: x4y1 slimeMan, x6y2 yellowKey, x8y1 slimeMan)
- MT38 x5y2 trader yellowKey3 [YK 5->8, G 928->728]
- MT38 x9y1 open yellowDoor [YK 8->7]
- MT38 x11y1 pass upFloor
- after: HP=184 ATK=146 DEF=170 YK=7 BK=0 RK=0 G=728 dmg=9542 door=114/12/3

### MT39

- before: HP=184 ATK=146 DEF=170 YK=7 BK=0 RK=0 G=728 dmg=9542 door=114/12/3
- MT39 x10y3 move [YK 7->8] (auto: x11y3 yellowKey)
- MT39 x10y4 open yellowDoor [YK 8->7]
- MT39 x9y5 move [G 728->758] (auto: x9y6 slimeMan)
- MT39 x11y7 kill ghostSkeleton [HP 184->174, ATK 146->150, G 758->793] (auto: x11y6 redGem) (+35G)
- MT39 x11y1 pass downFloor
- after: HP=174 ATK=150 DEF=170 YK=7 BK=0 RK=0 G=793 dmg=9552 door=115/12/3

### MT38

- before: HP=174 ATK=150 DEF=170 YK=7 BK=0 RK=0 G=793 dmg=9552 door=115/12/3
- MT38 x7y3 open yellowDoor [YK 7->6]
- MT38 x7y6 kill ghostSkeleton [HP 174->164, G 793->883] (auto: x7y7 swordsman) (+90G)
- MT38 x6y8 take redPotion [HP 164->364, DEF 170->174] (auto: x5y8 blueGem)
- MT38 x11y3 open yellowDoor [YK 6->5]
- MT38 x11y6 kill ghostSkeleton [HP 364->358, G 883->918] (+35G)
- MT38 x11y8 open yellowDoor [YK 5->4]
- MT38 x11y9 kill ghostSkeleton [HP 358->352, YK 4->5, G 918->953] (auto: x9y9 yellowKey) (+35G)
- MT38 x9y11 kill soldier [HP 352->300, G 953->998] (+45G)
- MT38 x8y11 open yellowDoor [YK 5->4]
- MT38 x8y11 move [G 998->1071] (auto: x7y11 zombie, x5y11 swordsman)
- MT38 x4y11 open yellowDoor [YK 4->3]
- MT38 x3y10 kill blueGuard [HP 300->288, G 1071->1121] (+50G)
- MT38 x1y10 kill blueGuard [HP 288->276, G 1121->1171] (+50G)
- MT38 x2y7 take shield3 [DEF 174->214, G 1171->1296] (auto: x1y3 ghostSkeleton, x2y5 flower, x3y4 soldier, x4y4 soldier)
- after: HP=276 ATK=150 DEF=214 YK=3 BK=0 RK=0 G=1296 dmg=9650 door=120/12/3

### MT39

- before: HP=276 ATK=150 DEF=214 YK=3 BK=0 RK=0 G=1296 dmg=9650 door=120/12/3
- MT39 x11y2 fly
- MT39 x10y7 move [G 1296->1341] (auto: x11y5 soldier)
- MT39 x10y8 open yellowDoor [YK 3->2]
- MT39 x10y9 kill redKnight [HP 276->228, G 1341->1406] (+65G)
- MT39 x8y10 open yellowDoor [YK 2->1]
- MT39 x7y11 move [DEF 214->218, G 1406->1491] (auto: x6y11 slimeMan, x5y9 swordsman, x6y9 blueGem)
- MT39 x4y10 open yellowDoor [YK 1->0]
- MT39 x3y10 move [YK 0->1, G 1491->1561] (auto: x3y9 ghostSkeleton, x2y10 ghostSkeleton, x3y11 yellowKey)
- MT39 x11y11 pass upFloor
- after: HP=228 ATK=150 DEF=218 YK=1 BK=0 RK=0 G=1561 dmg=9698 door=123/12/3

### MT31

- before: HP=228 ATK=150 DEF=218 YK=1 BK=0 RK=0 G=1561 dmg=9698 door=123/12/3
- MT31 x6y10 fly
- MT31 x3y6 move [G 1561->1631] (auto: x2y6 ghostSkeleton, x11y3 ghostSkeleton)
- MT31 x1y5 open yellowDoor [YK 1->0]
- MT31 x2y4 move [YK 0->4, G 1631->1731] (auto: x2y3 soldier, x1y2 swordsman, x3y2 yellowKey, x3y1 yellowKey, x4y2 yellowKey, x4y1 yellowKey)
- MT31 x3y4 open yellowDoor [YK 4->3]
- MT31 x3y4 move [BK 0->1] (auto: x4y4 blueKey)
- MT31 x1y7 open yellowDoor [YK 3->2]
- MT31 x1y8 move [G 1731->1801] (auto: x1y9 ghostSkeleton, x2y9 ghostSkeleton)
- MT31 x4y10 kill redKnight [HP 228->192, G 1801->1866] (+65G)
- MT31 x4y9 open yellowDoor [YK 2->1]
- MT31 x4y9 move [DEF 218->222] (auto: x4y8 blueGem)
- after: HP=192 ATK=150 DEF=222 YK=1 BK=1 RK=0 G=1866 dmg=9734 door=127/12/3

### MT34

- before: HP=192 ATK=150 DEF=222 YK=1 BK=1 RK=0 G=1866 dmg=9734 door=127/12/3
- MT34 x2y1 fly
- MT34 x6y2 move [G 1866->1966] (auto: x1y10 swordsman, x2y11 soldier)
- MT34 x7y2 kill redKnight [HP 192->168, G 1966->2031] (+65G)
- MT34 x8y2 open yellowDoor [YK 1->0]
- MT34 x9y2 move [DEF 222->226, YK 0->3] (auto: x9y1 yellowKey, x10y2 yellowKey, x10y1 yellowKey, x11y1 blueGem)
- after: HP=168 ATK=150 DEF=226 YK=3 BK=1 RK=0 G=2031 dmg=9758 door=128/12/3

### MT40

- before: HP=168 ATK=150 DEF=226 YK=3 BK=1 RK=0 G=2031 dmg=9758 door=128/12/3
- MT40 x10y11 fly
- MT40 x11y11 pass downFloor
- after: HP=168 ATK=150 DEF=226 YK=3 BK=1 RK=0 G=2031 dmg=9758 door=128/12/3

### MT39

- before: HP=168 ATK=150 DEF=226 YK=3 BK=1 RK=0 G=2031 dmg=9758 door=128/12/3
- MT39 x2y8 open blueDoor [BK 1->0]
- MT39 x4y2 open yellowDoor [YK 3->2]
- MT39 x6y4 open yellowDoor [YK 2->1]
- MT39 x4y4 take centerFly3
- MT39 x11y11 pass upFloor
- after: HP=168 ATK=150 DEF=226 YK=1 BK=0 RK=0 G=2031 dmg=9758 door=130/13/3

### MT40

- before: HP=168 ATK=150 DEF=226 YK=1 BK=0 RK=0 G=2031 dmg=9758 door=130/13/3
- MT40 x2y1 中心飞行 centerFly
- MT40 x5y1 move [G 2031->2436] (auto: x4y2 swordsman, x3y2 swordsman, x5y4 ghostSkeleton, x2y2 swordsman, x4y4 ghostSkeleton, x3y4 ghostSkeleton, x7y4 soldier, x8y4 soldier, x9y4 soldier)
- MT40 x6y1 kill yellowKnight [G 2436->2536] (+100G)
- MT40 x8y2 kill redKnight [HP 168->156, G 2536->2601] (+65G)
- MT40 x9y2 kill redKnight [HP 156->144, G 2601->2666] (+65G)
- MT40 x10y2 kill redKnight [HP 144->132, G 2666->2731] (+65G)
- MT40 x6y7 pass
- MT40 x5y1 move [ATK 150->162, DEF 226->238, YK 1->4] (auto: x4y2 yellowKey, x3y2 yellowKey, x2y2 yellowKey, x8y2 redGem, x7y4 blueGem, x9y2 redGem, x8y4 blueGem, x10y2 redGem, x9y4 blueGem)
- MT40 x6y1 pass upFloor
- after: HP=132 ATK=162 DEF=238 YK=4 BK=0 RK=0 G=2731 dmg=9794 door=130/13/3

### MT41

- before: HP=132 ATK=162 DEF=238 YK=4 BK=0 RK=0 G=2731 dmg=9794 door=130/13/3
- MT41 x6y4 地图伤害 checkBlock [HP 132->66]
- MT41 x6y7 open yellowDoor [YK 4->3]
- MT41 x6y8 open yellowDoor [YK 3->2]
- MT41 x6y9 open yellowDoor [YK 2->1]
- MT41 x6y11 pass upFloor
- after: HP=66 ATK=162 DEF=238 YK=1 BK=0 RK=0 G=2731 dmg=9860 door=133/13/3

### MT42

- before: HP=66 ATK=162 DEF=238 YK=1 BK=0 RK=0 G=2731 dmg=9860 door=133/13/3
- MT42 x5y10 pass
- MT42 x5y10 event yellowKnightEscape
- after: HP=66 ATK=162 DEF=238 YK=1 BK=0 RK=0 G=2731 dmg=9860 door=133/13/3

### MT39

- before: HP=66 ATK=162 DEF=238 YK=1 BK=0 RK=0 G=2731 dmg=9860 door=133/13/3
- MT39 x11y10 fly
- MT39 x11y11 pass upFloor
- after: HP=66 ATK=162 DEF=238 YK=1 BK=0 RK=0 G=2731 dmg=9860 door=133/13/3

### MT40

- before: HP=66 ATK=162 DEF=238 YK=1 BK=0 RK=0 G=2731 dmg=9860 door=133/13/3
- MT40 x9y11 move [G 2731->2831] (auto: x9y10 soldier, x10y9 swordsman)
- MT40 x9y9 take redPotion [HP 66->266]
- after: HP=266 ATK=162 DEF=238 YK=1 BK=0 RK=0 G=2831 dmg=9860 door=133/13/3

### MT38

- before: HP=266 ATK=162 DEF=238 YK=1 BK=0 RK=0 G=2831 dmg=9860 door=133/13/3
- MT38 x10y1 fly
- MT38 x11y7 move [YK 1->4, G 2831->2961] (auto: x10y7 redKnight, x9y6 yellowKey, x9y5 yellowKey, x10y10 redKnight, x9y4 yellowKey)
- after: HP=266 ATK=162 DEF=238 YK=4 BK=0 RK=0 G=2961 dmg=9860 door=133/13/3

### MT32

- before: HP=266 ATK=162 DEF=238 YK=4 BK=0 RK=0 G=2961 dmg=9860 door=133/13/3
- MT32 x10y1 fly
- MT32 x6y3 move [G 2961->3006] (auto: x1y4 soldier)
- MT32 x7y3 open yellowDoor [YK 4->3]
- MT32 x8y3 move [G 3006->3106] (auto: x8y4 ghostSkeleton, x8y7 redKnight)
- MT32 x9y5 open yellowDoor [YK 3->2]
- MT32 x8y8 move [YK 2->4] (auto: x10y4 yellowKey, x11y5 yellowKey)
- MT32 x9y8 open yellowDoor [YK 4->3]
- MT32 x9y8 move [YK 3->5, BK 0->1] (auto: x10y7 yellowKey, x11y8 yellowKey, x11y7 blueKey)
- after: HP=266 ATK=162 DEF=238 YK=5 BK=1 RK=0 G=3106 dmg=9860 door=136/13/3

### MT34

- before: HP=266 ATK=162 DEF=238 YK=5 BK=1 RK=0 G=3106 dmg=9860 door=136/13/3
- MT34 x2y1 fly
- after: HP=266 ATK=162 DEF=238 YK=5 BK=1 RK=0 G=3106 dmg=9860 door=136/13/3

### MT15

- before: HP=266 ATK=162 DEF=238 YK=5 BK=1 RK=0 G=3106 dmg=9860 door=136/13/3
- MT15 x6y2 fly
- MT15 x6y6 kill octopus [G 3106->3206] (+100G)
- MT15 x6y5 take pickaxe
- after: HP=266 ATK=162 DEF=238 YK=5 BK=1 RK=0 G=3206 dmg=9860 door=136/13/3

### MT36

- before: HP=266 ATK=162 DEF=238 YK=5 BK=1 RK=0 G=3206 dmg=9860 door=136/13/3
- MT36 x11y2 fly
- MT36 x10y11 move [YK 5->6, G 3206->3651] (auto: x9y11 swordsman, x7y11 zombieKnight, x5y11 yellowKey, x11y5 swordsman, x3y11 soldier, x1y9 swordsman, x6y7 redKnight, x1y5 redKnight, x1y3 slimeMan, x3y1 soldier)
- MT36 x11y11 pass upFloor
- after: HP=266 ATK=162 DEF=238 YK=6 BK=1 RK=0 G=3651 dmg=9860 door=136/13/3

### MT37

- before: HP=266 ATK=162 DEF=238 YK=6 BK=1 RK=0 G=3651 dmg=9860 door=136/13/3
- MT37 x1y2 move [G 3651->3881] (auto: x11y9 redKnight, x11y6 swordsman, x11y3 redKnight, x9y1 soldier)
- MT37 x1y1 pass upFloor
- after: HP=266 ATK=162 DEF=238 YK=6 BK=1 RK=0 G=3881 dmg=9860 door=136/13/3

### MT38

- before: HP=266 ATK=162 DEF=238 YK=6 BK=1 RK=0 G=3881 dmg=9860 door=136/13/3
- MT38 x11y1 pass upFloor
- after: HP=266 ATK=162 DEF=238 YK=6 BK=1 RK=0 G=3881 dmg=9860 door=136/13/3

### MT39

- before: HP=266 ATK=162 DEF=238 YK=6 BK=1 RK=0 G=3881 dmg=9860 door=136/13/3
- MT39 x10y11 move [G 3881->3946] (auto: x7y9 redKnight)
- MT39 x11y11 pass upFloor
- after: HP=266 ATK=162 DEF=238 YK=6 BK=1 RK=0 G=3946 dmg=9860 door=136/13/3

### MT40

- before: HP=266 ATK=162 DEF=238 YK=6 BK=1 RK=0 G=3946 dmg=9860 door=136/13/3
- MT40 x8y11 open yellowDoor [YK 6->5]
- MT40 x8y11 move [G 3946->4006] (auto: x7y9 slimeMan, x5y9 slimeMan)
- after: HP=266 ATK=162 DEF=238 YK=5 BK=1 RK=0 G=4006 dmg=9860 door=137/13/3

### MT42

- before: HP=266 ATK=162 DEF=238 YK=5 BK=1 RK=0 G=4006 dmg=9860 door=137/13/3
- MT42 x5y11 fly
- MT42 x8y5 open yellowDoor [YK 5->4]
- MT42 x9y5 地图伤害 checkBlock [HP 266->166]
- MT42 x10y6 地图伤害 checkBlock [HP 166->66]
- MT42 x10y8 地图伤害 checkBlock [HP 66->33]
- MT42 x10y9 move [YK 4->9, BK 1->2] (auto: x10y10 yellowKey, x9y10 yellowKey, x10y11 blueKey, x11y10 yellowKey, x9y11 yellowKey, x11y11 yellowKey)
- MT42 x2y2 中心飞行 centerFly
- MT42 x1y1 pass upFloor
- after: HP=33 ATK=162 DEF=238 YK=9 BK=2 RK=0 G=4006 dmg=10093 door=138/13/3

### MT43

- before: HP=33 ATK=162 DEF=238 YK=9 BK=2 RK=0 G=4006 dmg=10093 door=138/13/3
- MT43 x1y4 open blueDoor [BK 2->1]
- MT43 x1y8 open yellowDoor [YK 9->8]
- MT43 x1y11 pass upFloor
- after: HP=33 ATK=162 DEF=238 YK=8 BK=1 RK=0 G=4006 dmg=10093 door=139/14/3

### MT45

- before: HP=33 ATK=162 DEF=238 YK=8 BK=1 RK=0 G=4006 dmg=10093 door=139/14/3
- MT45 x11y1 pass upFloor
- after: HP=33 ATK=162 DEF=238 YK=8 BK=1 RK=0 G=4006 dmg=10093 door=139/14/3

### MT46

- before: HP=33 ATK=162 DEF=238 YK=8 BK=1 RK=0 G=4006 dmg=10093 door=139/14/3
- MT46 x11y2 设置自动：battle=true, item=true, wall=true
- after: HP=33 ATK=162 DEF=238 YK=8 BK=1 RK=0 G=4006 dmg=10093 door=139/14/3

### MT40

- before: HP=33 ATK=162 DEF=238 YK=8 BK=1 RK=0 G=4006 dmg=10093 door=139/14/3
- MT40 x6y2 fly
- MT40 x5y3 move [HP 33->2433] (auto: x5y4 bluePotion, x4y4 bluePotion, x3y4 bluePotion)
- MT40 x6y1 pass upFloor
- after: HP=2433 ATK=162 DEF=238 YK=8 BK=1 RK=0 G=4006 dmg=10093 door=139/14/3

### MT46

- before: HP=2433 ATK=162 DEF=238 YK=8 BK=1 RK=0 G=4006 dmg=10093 door=139/14/3
- MT46 x11y2 fly
- MT46 x11y3 open yellowDoor [YK 8->7]
- MT46 x11y5 open yellowDoor [YK 7->6]
- MT46 x11y8 open yellowDoor [YK 6->5]
- MT46 x11y9 地图伤害 checkBlock [HP 2433->2333]
- MT46 x11y11 pass upFloor
- after: HP=2333 ATK=162 DEF=238 YK=5 BK=1 RK=0 G=4006 dmg=10193 door=142/14/3

### MT47

- before: HP=2333 ATK=162 DEF=238 YK=5 BK=1 RK=0 G=4006 dmg=10193 door=142/14/3
- MT47 x1y2 中心飞行 centerFly
- MT47 x3y1 open blueDoor [BK 1->0]
- MT47 x5y2 trader earthquake [G 4006->6]
- MT47 x1y1 pass upFloor
- after: HP=2333 ATK=162 DEF=238 YK=5 BK=0 RK=0 G=6 dmg=10193 door=142/15/3

### MT37

- before: HP=2333 ATK=162 DEF=238 YK=5 BK=0 RK=0 G=6 dmg=10193 door=142/15/3
- MT37 x2y1 fly
- MT37 x2y1 地震卷轴 earthquake
- MT37 x2y2 move [HP 2333->6533, ATK 162->178, DEF 238->254, YK 5->14, BK 0->2, RK 0->1] (auto: x3y4 redPotion, x4y3 redPotion, x3y5 yellowKey, x4y4 redPotion, x5y3 redPotion, x4y5 yellowKey, x5y4 yellowKey, x3y7 blueGem, x5y5 bomb, x7y3 redPotion, x3y8 yellowKey, x4y7 redGem, x7y4 redPotion, x8y3 redPotion, x4y8 yellowKey, x5y7 bluePotion, x7y5 redKey, x8y4 redPotion, x4y9 blueKey, x5y8 yellowKey, x8y5 yellowKey, x9y4 redPotion, x5y9 blueKey, x7y7 redGem, x9y5 yellowKey, x11y1 bluePotion, x7y8 blueGem, x8y7 redGem, x7y9 bluePotion, x8y8 blueGem, x9y7 redGem, x8y9 yellowKey, x9y8 blueGem)
- after: HP=6533 ATK=178 DEF=254 YK=14 BK=2 RK=1 G=6 dmg=10193 door=142/15/3

### MT40

- before: HP=6533 ATK=178 DEF=254 YK=14 BK=2 RK=1 G=6 dmg=10193 door=142/15/3
- MT40 x10y11 fly
- MT40 x4y11 open blueDoor [BK 2->1]
- MT40 x4y11 move [HP 6533->7333, ATK 178->182, DEF 254->258, YK 14->15, G 6->71] (auto: x3y11 redKnight, x1y11 redGem, x2y9 yellowKey, x1y10 bluePotion, x1y9 blueGem)
- MT40 x11y11 pass downFloor
- after: HP=7333 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3

### MT39

- before: HP=7333 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3
- MT39 x10y1 move [HP 7333->7533] (auto: x9y11 redPotion)
- MT39 x11y1 pass downFloor
- after: HP=7533 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3

### MT38

- before: HP=7533 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3
- MT38 x1y2 move [HP 7533->8333] (auto: x11y11 bluePotion)
- MT38 x1y1 pass downFloor
- after: HP=8333 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3

### MT37

- before: HP=8333 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3
- MT37 x11y11 pass downFloor
- after: HP=8333 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3

### MT36

- before: HP=8333 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3
- MT36 x10y1 move [HP 8333->9133] (auto: x1y11 bluePotion)
- MT36 x11y1 pass downFloor
- after: HP=9133 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3

### MT35

- before: HP=9133 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3
- MT35 x6y11 pass downFloor
- after: HP=9133 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3

### MT34

- before: HP=9133 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3
- MT34 x1y2 move [HP 9133->10133] (auto: x11y2 redPotion, x1y11 bluePotion)
- MT34 x1y1 pass downFloor
- after: HP=10133 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3

### MT33

- before: HP=10133 ATK=182 DEF=258 YK=15 BK=1 RK=1 G=71 dmg=10193 door=142/16/3
- MT33 x5y3 move [HP 10133->10933] (auto: x11y3 bluePotion)
- MT33 x5y4 open yellowDoor [YK 15->14]
- MT33 x4y5 move [G 71->191] (auto: x4y6 swordsman, x6y5 zombieKnight, x6y7 ghostSkeleton)
- MT33 x3y7 open yellowDoor [YK 14->13]
- MT33 x3y7 move [HP 10933->11133, G 191->251] (auto: x2y7 slimeMan, x2y4 redPotion, x1y5 slimeMan)
- MT33 x1y8 open yellowDoor [YK 13->12]
- MT33 x10y1 move [YK 12->13, G 251->381] (auto: x1y10 swordsman, x1y11 yellowKey, x3y9 zombieKnight, x2y11 soldier)
- MT33 x11y1 pass downFloor
- after: HP=11133 ATK=182 DEF=258 YK=13 BK=1 RK=1 G=381 dmg=10193 door=145/16/3

### MT32

- before: HP=11133 ATK=182 DEF=258 YK=13 BK=1 RK=1 G=381 dmg=10193 door=145/16/3
- MT32 x4y11 move [HP 11133->11933] (auto: x11y4 bluePotion)
- MT32 x5y11 pass downFloor
- after: HP=11933 ATK=182 DEF=258 YK=13 BK=1 RK=1 G=381 dmg=10193 door=145/16/3

### MT31

- before: HP=11933 ATK=182 DEF=258 YK=13 BK=1 RK=1 G=381 dmg=10193 door=145/16/3
- MT31 x11y2 move [HP 11933->12333] (auto: x10y1 redPotion, x2y11 redPotion)
- after: HP=12333 ATK=182 DEF=258 YK=13 BK=1 RK=1 G=381 dmg=10193 door=145/16/3

### MT45

- before: HP=12333 ATK=182 DEF=258 YK=13 BK=1 RK=1 G=381 dmg=10193 door=145/16/3
- MT45 x2y1 fly
- MT45 x6y2 open yellowDoor [YK 13->12]
- MT45 x6y3 地图伤害 checkBlock [HP 12333->12033]
- MT45 x6y5 地图伤害 checkBlock [HP 12033->11733]
- MT45 x6y6 open yellowDoor [YK 12->11]
- MT45 x4y7 open yellowDoor [YK 11->10]
- MT45 x2y8 open redDoor [RK 1->0]
- MT45 x6y5 地图伤害 checkBlock [HP 11733->11433]
- MT45 x6y3 地图伤害 checkBlock [HP 11433->11133]
- MT45 x1y1 pass downFloor
- after: HP=11133 ATK=182 DEF=258 YK=10 BK=1 RK=0 G=381 dmg=11393 door=148/16/4

### MT44

- before: HP=11133 ATK=182 DEF=258 YK=10 BK=1 RK=0 G=381 dmg=11393 door=148/16/4
- MT44 x1y10 上楼器 upFly
- MT44 x6y9 炸弹 bomb [G 381->781] (auto: +400G)
- MT44 x6y8 move [HP 11133->12133, DEF 258->358] (auto: x6y7 redPotion, x6y6 shield5, x6y5 redPotion, x5y6 redPotion, x7y6 redPotion)
- after: HP=12133 ATK=182 DEF=358 YK=10 BK=1 RK=0 G=781 dmg=11393 door=148/16/4

### MT48

- before: HP=12133 ATK=182 DEF=358 YK=10 BK=1 RK=0 G=781 dmg=11393 door=148/16/4
- MT48 x11y10 fly
- after: HP=12133 ATK=182 DEF=358 YK=10 BK=1 RK=0 G=781 dmg=11393 door=148/16/4

### MT47

- before: HP=12133 ATK=182 DEF=358 YK=10 BK=1 RK=0 G=781 dmg=11393 door=148/16/4
- MT47 x2y1 fly
- MT47 x7y1 open yellowDoor [YK 10->9]
- MT47 x8y1 move [DEF 358->363, YK 9->11, G 781->821] (auto: x11y1 yellowKey, x11y2 blueGem, x11y3 yellowKey, x9y3 slimelord)
- after: HP=12133 ATK=182 DEF=363 YK=11 BK=1 RK=0 G=821 dmg=11393 door=149/16/4

### MT46

- before: HP=12133 ATK=182 DEF=363 YK=11 BK=1 RK=0 G=821 dmg=11393 door=149/16/4
- MT46 x11y10 fly
- MT46 x11y11 pass upFloor
- after: HP=12133 ATK=182 DEF=363 YK=11 BK=1 RK=0 G=821 dmg=11393 door=149/16/4

### MT47

- before: HP=12133 ATK=182 DEF=363 YK=11 BK=1 RK=0 G=821 dmg=11393 door=149/16/4
- MT47 x8y11 move [G 821->861] (auto: x8y9 slimelord)
- MT47 x7y11 open yellowDoor [YK 11->10]
- MT47 x6y11 move [HP 12133->12383, ATK 182->187] (auto: x6y10 redGem, x4y10 redPotion)
- after: HP=12383 ATK=187 DEF=363 YK=10 BK=1 RK=0 G=861 dmg=11393 door=150/16/4

### MT41

- before: HP=12383 ATK=187 DEF=363 YK=10 BK=1 RK=0 G=861 dmg=11393 door=150/16/4
- MT41 x6y10 fly
- after: HP=12383 ATK=187 DEF=363 YK=10 BK=1 RK=0 G=861 dmg=11393 door=150/16/4

### MT48

- before: HP=12383 ATK=187 DEF=363 YK=10 BK=1 RK=0 G=861 dmg=11393 door=150/16/4
- MT48 x11y10 fly
- MT48 x11y7 move [G 861->901] (auto: x3y5 slimelord)
- MT48 x10y7 kill brownWizard [HP 12383->12369, G 901->981] (+80G)
- MT48 x6y7 使用镐 pickaxe
- MT48 x5y7 move [HP 12369->12619, ATK 187->242] (auto: x5y8 redPotion, x3y8 redGem, x8y10 sword4)
- after: HP=12619 ATK=242 DEF=363 YK=10 BK=1 RK=0 G=981 dmg=11407 door=150/16/4

### MT43

- before: HP=12619 ATK=242 DEF=363 YK=10 BK=1 RK=0 G=981 dmg=11407 door=150/16/4
- MT43 x1y10 fly
- after: HP=12619 ATK=242 DEF=363 YK=10 BK=1 RK=0 G=981 dmg=11407 door=150/16/4

### MT42

- before: HP=12619 ATK=242 DEF=363 YK=10 BK=1 RK=0 G=981 dmg=11407 door=150/16/4
- MT42 x1y2 fly
- after: HP=12619 ATK=242 DEF=363 YK=10 BK=1 RK=0 G=981 dmg=11407 door=150/16/4

### MT43

- before: HP=12619 ATK=242 DEF=363 YK=10 BK=1 RK=0 G=981 dmg=11407 door=150/16/4
- MT43 x1y2 fly
- MT43 x1y5 move [G 981->1021] (auto: x2y5 slimelord)
- MT43 x3y6 open yellowDoor [YK 10->9]
- MT43 x4y7 move [HP 12619->13619, G 1021->1061] (auto: x5y7 slimelord, x6y6 bluePotion)
- MT43 x8y6 open yellowDoor [YK 9->8]
- MT43 x11y6 move [HP 13619->13869, YK 8->9] (auto: x11y7 redPotion, x10y8 yellowKey)
- MT43 x11y5 open yellowDoor [YK 9->8]
- MT43 x9y1 kill whiteKing [HP 13869->13782, G 1061->1161] (+100G)
- MT43 x8y4 move [DEF 363->413, G 1161->1381] (auto: x9y4 shield4, x9y7 brownWizard, x4y4 redWizard, x2y9 redBat)
- MT43 x11y9 open yellowDoor [YK 8->7]
- MT43 x11y10 move [BK 1->2, G 1381->1431] (auto: x10y10 redBat, x11y11 blueKey)
- after: HP=13782 ATK=242 DEF=413 YK=7 BK=2 RK=0 G=1431 dmg=11494 door=154/16/4

### MT42

- before: HP=13782 ATK=242 DEF=413 YK=7 BK=2 RK=0 G=1431 dmg=11494 door=154/16/4
- MT42 x1y2 fly
- MT42 x2y2 move [G 1431->1471] (auto: x3y2 slimelord)
- MT42 x3y3 open yellowDoor [YK 7->6]
- MT42 x2y5 move [G 1471->1511] (auto: x3y5 slimelord)
- MT42 x1y6 open yellowDoor [YK 6->5]
- MT42 x3y7 move [HP 13782->14782, DEF 413->418, YK 5->9, G 1511->1611] (auto: x3y8 redBat, x3y9 yellowKey, x2y9 yellowKey, x1y9 bluePotion, x1y10 redBat, x1y11 yellowKey, x2y11 yellowKey, x3y11 blueGem)
- after: HP=14782 ATK=242 DEF=418 YK=9 BK=2 RK=0 G=1611 dmg=11494 door=156/16/4

### MT46

- before: HP=14782 ATK=242 DEF=418 YK=9 BK=2 RK=0 G=1611 dmg=11494 door=156/16/4
- MT46 x11y2 fly
- MT46 x10y11 move [G 1611->1781] (auto: x10y9 brownWizard, x10y6 slimelord, x9y4 redBat)
- MT46 x9y11 open yellowDoor [YK 9->8]
- MT46 x6y11 open blueDoor [BK 2->1]
- MT46 x7y9 move [G 1781->2104] (auto: x4y11 redSlime, x2y11 skeleton, x1y10 bigBat, x1y8 zombie, x1y6 soldier, x3y6 swordsman, x5y6 redKnight, x5y8 slimelord, x4y9 brownWizard, x3y8 bigKey)
- MT46 x7y8 open yellowDoor [YK 8->7]
- MT46 x4y4 move [HP 14782->15032, G 2104->2194] (auto: x7y6 redPotion, x8y7 redWizard)
- MT46 x3y4 open yellowDoor [YK 7->6]
- MT46 x10y1 move [HP 15032->15282, ATK 242->247, G 2194->2364] (auto: x2y4 brownWizard, x1y3 redGem, x2y1 redWizard, x1y2 redPotion)
- MT46 x11y1 pass downFloor
- after: HP=15282 ATK=247 DEF=418 YK=6 BK=1 RK=0 G=2364 dmg=11494 door=159/17/4

### MT41

- before: HP=15282 ATK=247 DEF=418 YK=6 BK=1 RK=0 G=2364 dmg=11494 door=159/17/4
- MT41 x6y10 fly
- MT41 x5y6 open blueDoor [BK 1->0]
- MT41 x6y6 魔法钥匙 bigKey
- MT41 x1y2 move [HP 15282->16782, ATK 247->252, YK 6->9, BK 0->1, G 2364->2584] (auto: x1y1 redPotion, x1y6 redBat, x3y5 brownWizard, x2y7 redBat, x4y7 slimelord, x1y11 bluePotion, x4y1 blueKey, x3y9 redPotion, x4y10 yellowKey, x3y10 yellowKey, x4y11 redGem, x3y11 yellowKey)
- MT41 x2y2 kill redWizard [G 2584->2674] (+90G)
- MT41 x7y6 open blueDoor [BK 1->0]
- MT41 x11y2 move [HP 16782->18282, DEF 418->423, YK 9->12, BK 0->1, G 2674->2894] (auto: x11y1 redPotion, x11y6 redBat, x9y5 brownWizard, x10y7 redBat, x8y7 slimelord, x11y11 bluePotion, x8y1 blueKey, x8y10 yellowKey, x9y9 redPotion, x8y11 blueGem, x9y10 yellowKey, x9y11 yellowKey)
- MT41 x10y2 event redWizard
- MT41 x10y2 kill redWizard [G 2894->2984] (+90G)
- after: HP=18282 ATK=252 DEF=423 YK=12 BK=1 RK=0 G=2984 dmg=11494 door=159/19/4

### MT47

- before: HP=18282 ATK=252 DEF=423 YK=12 BK=1 RK=0 G=2984 dmg=11494 door=159/19/4
- MT47 x11y10 fly
- MT47 x11y8 move [G 2984->3064] (auto: x5y11 brownWizard)
- MT47 x11y7 open yellowDoor [YK 12->11]
- MT47 x11y7 move [YK 11->12, G 3064->3194] (auto: x11y6 redBat, x9y5 brownWizard, x8y6 yellowKey)
- after: HP=18282 ATK=252 DEF=423 YK=12 BK=1 RK=0 G=3194 dmg=11494 door=160/19/4

### MT48

- before: HP=18282 ATK=252 DEF=423 YK=12 BK=1 RK=0 G=3194 dmg=11494 door=160/19/4
- MT48 x11y10 fly
- MT48 x11y11 pass downFloor
- after: HP=18282 ATK=252 DEF=423 YK=12 BK=1 RK=0 G=3194 dmg=11494 door=160/19/4

### MT47

- before: HP=18282 ATK=252 DEF=423 YK=12 BK=1 RK=0 G=3194 dmg=11494 door=160/19/4
- MT47 x1y6 move [G 3194->3284] (auto: x8y3 redWizard)
- MT47 x2y6 open yellowDoor [YK 12->11]
- MT47 x3y6 move [G 3284->3334] (auto: x3y5 redBat)
- MT47 x4y4 open yellowDoor [YK 11->10]
- MT47 x1y7 move [ATK 252->257, DEF 423->428, YK 10->11, BK 1->2, G 3334->3504] (auto: x5y4 redWizard, x6y5 brownWizard, x5y7 blueKey, x5y8 redGem, x6y7 yellowKey, x6y8 blueGem)
- MT47 x1y10 move [G 3504->3594] (auto: x1y11 redWizard)
- after: HP=18282 ATK=257 DEF=428 YK=11 BK=2 RK=0 G=3594 dmg=11494 door=162/19/4

### MT48

- before: HP=18282 ATK=257 DEF=428 YK=11 BK=2 RK=0 G=3594 dmg=11494 door=162/19/4
- MT48 x11y10 fly
- MT48 x1y6 move [G 3594->3804] (auto: x1y7 redBat, x1y9 brownWizard, x4y7 brownWizard)
- MT48 x1y11 pass upFloor
- after: HP=18282 ATK=257 DEF=428 YK=11 BK=2 RK=0 G=3804 dmg=11494 door=162/19/4

### MT49

- before: HP=18282 ATK=257 DEF=428 YK=11 BK=2 RK=0 G=3804 dmg=11494 door=162/19/4
- MT49 x1y11 pass downFloor
- after: HP=18282 ATK=257 DEF=428 YK=11 BK=2 RK=0 G=3804 dmg=11494 door=162/19/4

### MT46

- before: HP=18282 ATK=257 DEF=428 YK=11 BK=2 RK=0 G=3804 dmg=11494 door=162/19/4
- MT46 x11y10 fly
- MT46 x9y1 open blueDoor [BK 2->1]
- MT46 x6y1 shop def [DEF 428->448, G 3804->2684]
- MT46 x6y1 shop def [DEF 448->468, G 2684->1344]
- after: HP=18282 ATK=257 DEF=468 YK=11 BK=1 RK=0 G=1344 dmg=11494 door=162/20/4

### MT48

- before: HP=18282 ATK=257 DEF=468 YK=11 BK=1 RK=0 G=1344 dmg=11494 door=162/20/4
- MT48 x11y10 fly
- MT48 x4y8 move [G 1344->1744] (auto: x7y5 whiteKing, x7y3 whiteKing, x9y3 whiteKing, x9y5 whiteKing)
- MT48 x4y9 open yellowDoor [YK 11->10]
- MT48 x4y9 move [HP 18282->19282, DEF 468->473, G 1744->1864] (auto: x4y10 darkKnight, x3y11 blueGem, x5y11 bluePotion)
- after: HP=19282 ATK=257 DEF=473 YK=10 BK=1 RK=0 G=1864 dmg=11494 door=163/20/4

### MT45

- before: HP=19282 ATK=257 DEF=473 YK=10 BK=1 RK=0 G=1864 dmg=11494 door=163/20/4
- MT45 x10y1 fly
- MT45 x6y2 move [ATK 257->267, DEF 473->483, YK 10->11, G 1864->2584] (auto: x5y3 brownWizard, x7y3 redWizard, x5y5 redWizard, x7y5 brownWizard, x7y7 redBat, x3y6 darkKnight, x10y8 redWizard, x11y7 yellowKey, x3y4 darkKnight, x2y5 blueGem, x1y5 blueGem, x2y3 redGem, x1y3 redGem)
- MT45 x11y9 open yellowDoor [YK 11->10]
- MT45 x10y10 move [HP 19282->20282] (auto: x11y11 bluePotion)
- MT45 x9y10 open yellowDoor [YK 10->9]
- MT45 x8y9 kill whiteKing [G 2584->2684] (+100G)
- MT45 x8y11 kill whiteKing [G 2684->2784] (+100G)
- MT45 x5y9 kill darkKnight [G 2784->2904] (+120G)
- MT45 x5y11 kill darkKnight [G 2904->3024] (+120G)
- MT45 x11y5 open yellowDoor [YK 9->8]
- MT45 x11y5 move [G 3024->3064] (auto: x11y4 slimelord)
- after: HP=20282 ATK=267 DEF=483 YK=8 BK=1 RK=0 G=3064 dmg=11494 door=166/20/4

### MT43

- before: HP=20282 ATK=267 DEF=483 YK=8 BK=1 RK=0 G=3064 dmg=11494 door=166/20/4
- MT43 x1y10 fly
- MT43 x9y10 move [G 3064->3344] (auto: x7y4 darkKnight, x6y3 darkKnight, x5y1 slimelord)
- MT43 x8y10 open yellowDoor [YK 8->7]
- MT43 x7y9 move [HP 20282->23282, G 3344->3464] (auto: x6y9 darkKnight, x4y9 bluePotion, x4y10 bluePotion, x4y11 bluePotion)
- after: HP=23282 ATK=267 DEF=483 YK=7 BK=1 RK=0 G=3464 dmg=11494 door=167/20/4

### MT42

- before: HP=23282 ATK=267 DEF=483 YK=7 BK=1 RK=0 G=3464 dmg=11494 door=167/20/4
- MT42 x1y2 fly
- after: HP=23282 ATK=267 DEF=483 YK=7 BK=1 RK=0 G=3464 dmg=11494 door=167/20/4

### MT41

- before: HP=23282 ATK=267 DEF=483 YK=7 BK=1 RK=0 G=3464 dmg=11494 door=167/20/4
- MT41 x6y10 fly
- MT41 x6y11 pass upFloor
- after: HP=23282 ATK=267 DEF=483 YK=7 BK=1 RK=0 G=3464 dmg=11494 door=167/20/4

### MT42

- before: HP=23282 ATK=267 DEF=483 YK=7 BK=1 RK=0 G=3464 dmg=11494 door=167/20/4
- MT42 x6y5 move [YK 7->12, BK 1->2, RK 0->1, G 3464->4034] (auto: x6y4 darkKnight, x9y4 brownWizard, x7y1 redKey, x11y4 redWizard, x11y6 brownWizard, x10y2 yellowKey, x10y1 blueKey, x9y2 yellowKey, x11y2 yellowKey, x9y8 whiteKing, x11y8 whiteKing, x9y1 yellowKey, x11y1 yellowKey)
- after: HP=23282 ATK=267 DEF=483 YK=12 BK=2 RK=1 G=4034 dmg=11494 door=167/20/4

### MT41

- before: HP=23282 ATK=267 DEF=483 YK=12 BK=2 RK=1 G=4034 dmg=11494 door=167/20/4
- MT41 x6y10 fly
- after: HP=23282 ATK=267 DEF=483 YK=12 BK=2 RK=1 G=4034 dmg=11494 door=167/20/4

### MT40

- before: HP=23282 ATK=267 DEF=483 YK=12 BK=2 RK=1 G=4034 dmg=11494 door=167/20/4
- MT40 x6y2 fly
- MT40 x6y1 pass upFloor
- after: HP=23282 ATK=267 DEF=483 YK=12 BK=2 RK=1 G=4034 dmg=11494 door=167/20/4

### MT41

- before: HP=23282 ATK=267 DEF=483 YK=12 BK=2 RK=1 G=4034 dmg=11494 door=167/20/4
- MT41 x6y4 move [G 4034->4234] (auto: x5y4 whiteKing, x6y5 downFly, x7y4 whiteKing)
- after: HP=23282 ATK=267 DEF=483 YK=12 BK=2 RK=1 G=4234 dmg=11494 door=167/20/4

### MT46

- before: HP=23282 ATK=267 DEF=483 YK=12 BK=2 RK=1 G=4234 dmg=11494 door=167/20/4
- MT46 x11y2 fly
- MT46 x6y1 shop def [DEF 483->503, G 4234->2654]
- MT46 x6y1 shop def [DEF 503->523, G 2654->814]
- after: HP=23282 ATK=267 DEF=523 YK=12 BK=2 RK=1 G=814 dmg=11494 door=167/20/4

### MT33

- before: HP=23282 ATK=267 DEF=523 YK=12 BK=2 RK=1 G=814 dmg=11494 door=167/20/4
- MT33 x2y1 fly
- MT33 x4y11 open blueDoor [BK 2->1]
- MT33 x5y11 move [YK 12->13, G 814->889] (auto: x5y10 yellowKey, x6y9 soldier, x7y10 slimeMan, x8y10 flower)
- after: HP=23282 ATK=267 DEF=523 YK=13 BK=1 RK=1 G=889 dmg=11494 door=167/21/4

### MT28

- before: HP=23282 ATK=267 DEF=523 YK=13 BK=1 RK=1 G=889 dmg=11494 door=167/21/4
- MT28 x2y11 fly
- MT28 x8y4 trader specialTrader [YK 13->12, G 889->989] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 12->11, G 989->1089] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 11->10, G 1089->1189] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 10->9, G 1189->1289] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 9->8, G 1289->1389] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 8->7, G 1389->1489] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 7->6, G 1489->1589] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 6->5, G 1589->1689] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 5->4, G 1689->1789] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 4->3, G 1789->1889] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 3->2, G 1889->1989] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 2->1, G 1989->2089] (auto: +100G)
- after: HP=23282 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT16

- before: HP=23282 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT16 x6y10 fly
- after: HP=23282 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT18

- before: HP=23282 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT18 x6y2 fly
- MT18 x1y2 move [HP 23282->23382] (auto: x11y11 redPotion)
- MT18 x1y1 pass upFloor
- after: HP=23382 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT19

- before: HP=23382 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT19 x5y11 move [HP 23382->23482] (auto: x4y1 redPotion)
- MT19 x6y11 pass upFloor
- after: HP=23482 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT20

- before: HP=23482 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT20 x5y1 move [HP 23482->23582] (auto: x11y11 redPotion)
- MT20 x6y1 pass upFloor
- after: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT23

- before: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT23 x1y2 fly
- after: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT27

- before: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT27 x2y11 fly
- after: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT33

- before: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT33 x10y1 fly
- after: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT36

- before: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT36 x11y2 fly
- MT36 x11y11 pass upFloor
- after: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT37

- before: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT37 x1y1 pass upFloor
- after: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT38

- before: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT38 x11y1 pass upFloor
- after: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT42

- before: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT42 x5y11 fly
- after: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT43

- before: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT43 x1y2 fly
- MT43 x1y1 pass downFloor
- after: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4

### MT48

- before: HP=23582 ATK=267 DEF=523 YK=1 BK=1 RK=1 G=2089 dmg=11494 door=167/21/4
- MT48 x11y10 fly
- MT48 x2y4 open blueDoor [BK 1->0]
- MT48 x2y4 move [HP 23582->24582, G 2089->2179] (auto: x2y3 redWizard, x2y1 bluePotion)
- after: HP=24582 ATK=267 DEF=523 YK=1 BK=0 RK=1 G=2179 dmg=11494 door=167/22/4

### MT46

- before: HP=24582 ATK=267 DEF=523 YK=1 BK=0 RK=1 G=2179 dmg=11494 door=167/22/4
- MT46 x11y10 fly
- after: HP=24582 ATK=267 DEF=523 YK=1 BK=0 RK=1 G=2179 dmg=11494 door=167/22/4

### MT28

- before: HP=24582 ATK=267 DEF=523 YK=1 BK=0 RK=1 G=2179 dmg=11494 door=167/22/4
- MT28 x2y11 fly
- after: HP=24582 ATK=267 DEF=523 YK=1 BK=0 RK=1 G=2179 dmg=11494 door=167/22/4

### MT46

- before: HP=24582 ATK=267 DEF=523 YK=1 BK=0 RK=1 G=2179 dmg=11494 door=167/22/4
- MT46 x11y2 fly
- MT46 x6y1 shop def [DEF 523->543, G 2179->59]
- after: HP=24582 ATK=267 DEF=543 YK=1 BK=0 RK=1 G=59 dmg=11494 door=167/22/4

### MT2

- before: HP=24582 ATK=267 DEF=543 YK=1 BK=0 RK=1 G=59 dmg=11494 door=167/22/4
- MT2 x1y10 fly
- MT2 x10y7 move [HP 24582->24982] (auto: x3y11 bluePotion, x3y10 bluePotion)
- MT2 x11y7 event specialTrader [ATK 267->275, DEF 543->559]
- after: HP=24982 ATK=275 DEF=559 YK=1 BK=0 RK=1 G=59 dmg=11494 door=167/22/4

### MT35

- before: HP=24982 ATK=275 DEF=559 YK=1 BK=0 RK=1 G=59 dmg=11494 door=167/22/4
- MT35 x6y10 fly
- MT35 x6y7 kill magicDragon [HP 24982->22563, G 59->859] (+800G)
- MT35 x6y6 take snow [HP 22563->24963] (auto: x6y5 bluePotion, x5y5 bluePotion, x7y5 bluePotion)
- after: HP=24963 ATK=275 DEF=559 YK=1 BK=0 RK=1 G=859 dmg=13913 door=167/22/4

### MT13

- before: HP=24963 ATK=275 DEF=559 YK=1 BK=0 RK=1 G=859 dmg=13913 door=167/22/4
- MT13 x10y11 fly
- MT13 x6y10 open yellowDoor [YK 1->0]
- MT13 x6y10 move [ATK 275->375] (auto: x6y9 lava, x6y8 lava, x5y9 lava, x7y9 lava, x6y7 lava, x5y8 lava, x7y8 lava, x4y9 lava, x8y9 lava, x6y6 lava, x4y8 lava, x8y8 lava, x3y9 lava, x9y9 lava, x6y5 sword5, x4y7 lava, x3y8 lava, x8y7 lava, x9y8 lava, x2y9 lava, x10y9 lava, x3y7 lava, x2y8 lava, x9y7 lava, x10y8 lava, x1y9 lava, x11y9 lava, x3y6 lava, x2y7 lava, x1y8 lava, x9y6 lava, x10y7 lava, x11y8 lava, x3y5 lava, x2y6 lava, x1y7 lava, x9y5 lava, x10y6 lava, x11y7 lava, x3y4 lava, x2y5 lava, x1y6 lava, x9y4 lava, x10y5 lava, x11y6 lava, x3y3 lava, x2y4 lava, x1y5 lava, x9y3 lava, x10y4 lava, x11y5 lava, x3y2 lava, x2y3 lava, x4y3 lava, x1y4 lava, x9y2 lava, x8y3 lava, x10y3 lava, x11y4 lava, x3y1 lava, x2y2 lava, x4y2 lava, x1y3 lava, x9y1 lava, x8y2 lava, x10y2 lava, x11y3 lava, x2y1 lava, x4y1 lava, x1y2 lava, x5y2 lava, x8y1 lava, x10y1 lava, x7y2 lava, x11y2 lava, x1y1 lava, x5y1 lava, x6y2 lava, x7y1 lava, x11y1 lava, x6y1 lava)
- after: HP=24963 ATK=375 DEF=559 YK=0 BK=0 RK=1 G=859 dmg=13913 door=168/22/4

### MT25

- before: HP=24963 ATK=375 DEF=559 YK=0 BK=0 RK=1 G=859 dmg=13913 door=168/22/4
- MT25 x2y11 fly
- MT25 x6y10 open redDoor [RK 1->0]
- MT25 x6y9 pass
- MT25 x6y6 kill blackMagician [HP 24963->24894, G 859->1859] (+1000G)
- MT25 x1y11 pass upFloor [RK 0->4]
- after: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=4 G=1859 dmg=13982 door=168/22/5

### MT26

- before: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=4 G=1859 dmg=13982 door=168/22/5
- MT26 x6y10 open redDoor [RK 4->3]
- MT26 x6y9 open redDoor [RK 3->2]
- MT26 x6y8 open redDoor [RK 2->1]
- MT26 x6y6 event princess
- MT26 x2y10 pass upFloor
- after: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=1 G=1859 dmg=13982 door=168/22/8

### MT27

- before: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=1 G=1859 dmg=13982 door=168/22/8
- MT27 x2y10 pass downFloor
- after: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=1 G=1859 dmg=13982 door=168/22/8

### MT26

- before: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=1 G=1859 dmg=13982 door=168/22/8
- MT26 x1y11 pass downFloor
- after: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=1 G=1859 dmg=13982 door=168/22/8

### MT25

- before: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=1 G=1859 dmg=13982 door=168/22/8
- MT25 x2y10 pass downFloor
- after: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=1 G=1859 dmg=13982 door=168/22/8

### MT24

- before: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=1 G=1859 dmg=13982 door=168/22/8
- MT24 x6y8 open redDoor [RK 1->0]
- MT24 x6y2 pass
- after: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=0 G=1859 dmg=13982 door=168/22/9

### MT50

- before: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=0 G=1859 dmg=13982 door=168/22/9
- MT50 x6y5 event redKing
- MT50 x6y5 event thief
- after: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=0 G=1859 dmg=13982 door=168/22/9

### MT49

- before: HP=24894 ATK=375 DEF=559 YK=0 BK=0 RK=0 G=1859 dmg=13982 door=168/22/9
- MT49 x5y5 下楼器 downFly
- MT49 x6y6 pass
- MT49 x6y6 event redKing
- MT49 x6y4 kill whiteKing [G 1859->1959] (+100G)
- MT49 x7y3 kill whiteKing [G 1959->2059] (+100G)
- MT49 x6y2 kill whiteKing [G 2059->2159] (+100G)
- MT49 x5y3 kill whiteKing [G 2159->2259] (+100G)
- MT49 x5y2 kill whiteKing [G 2259->2359] (+100G)
- MT49 x7y2 kill whiteKing [G 2359->2459] (+100G)
- MT49 x7y4 kill whiteKing [G 2459->2559] (+100G)
- MT49 x5y4 kill whiteKing [G 2559->2659] (+100G)
- MT49 x6y3 kill redKing [G 2659->3159] (+500G)
- MT49 x5y8 kill darkKnight [HP 24894->27894, ATK 375->390, DEF 559->574, RK 0->1, G 3159->3279] (+120G)
- MT49 x7y8 kill darkKnight [G 3279->3399] (+120G)
- MT49 x7y10 kill redWizard [G 3399->3489] (+90G)
- MT49 x5y10 kill redWizard [G 3489->3579] (+90G)
- MT49 x3y11 open redDoor [RK 1->0]
- MT49 x1y11 pass downFloor
- after: HP=27894 ATK=390 DEF=574 YK=0 BK=0 RK=0 G=3579 dmg=13982 door=168/22/10

### MT46

- before: HP=27894 ATK=390 DEF=574 YK=0 BK=0 RK=0 G=3579 dmg=13982 door=168/22/10
- MT46 x11y10 fly
- MT46 x6y1 shop hp [HP 27894->29494, G 3579->1159]
- after: HP=29494 ATK=390 DEF=574 YK=0 BK=0 RK=0 G=1159 dmg=13982 door=168/22/10

### MT45

- before: HP=29494 ATK=390 DEF=574 YK=0 BK=0 RK=0 G=1159 dmg=13982 door=168/22/10
- MT45 x10y1 fly
- MT45 x9y3 trader hp2000 [HP 29494->31494, G 1159->159]
- MT45 x9y4 使用 superPotion [HP 31494->38624]
- after: HP=38624 ATK=390 DEF=574 YK=0 BK=0 RK=0 G=159 dmg=13982 door=168/22/10
