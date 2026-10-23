# 当前最优 Walk (zone12, auto ON)

## 说明

- 本 walk 由 Game 类 (`scripts/search/zone12_game_route.py`, auto_sweep, strict_live_model) 离线推导生成。
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone12_game_route.json --load-slot <100+> --target-click-only`（统一点击 verifier，1-4 区通用；3 区起按需 `--set-auto battle=true,item=nopotion,wall=true`）
- 源 JSON：`outputs/results/2atk6def_v1_save1_to_mt40_walk.json`

## 摘要

- final: HP=138 ATK=162 DEF=238 YK=8 BK=0 RK=0 G=3069 dmg=9988 door=133/14/3 MT41 x6y2

## Walk

### MT4

- before: HP=926 ATK=10 DEF=10 YK=4 BK=1 RK=0 G=7 dmg=0 door=0/0/0
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
- MT6 x6y1 move [YK 2->3, G 122->139] (auto: x8y6 skeleton, x7y1 bluePriest, x9y1 yellowKey, x10y1 greenSlime, x1y8 bluePriest)
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
- MT11 x6y11 pass downFloor
- after: HP=577 ATK=60 DEF=52 YK=6 BK=0 RK=0 G=162 dmg=3699 door=52/4/1

### MT10

- before: HP=577 ATK=60 DEF=52 YK=6 BK=0 RK=0 G=162 dmg=3699 door=52/4/1
- MT10 x1y10 move [G 162->190] (auto: x3y6 skeleton, x2y7 skeletonSoldier, x10y7 skeletonSoldier, x11y6 skeleton)
- MT10 x1y11 pass downFloor
- after: HP=577 ATK=60 DEF=52 YK=6 BK=0 RK=0 G=190 dmg=3699 door=52/4/1

### MT9

- before: HP=577 ATK=60 DEF=52 YK=6 BK=0 RK=0 G=190 dmg=3699 door=52/4/1
- MT9 x1y9 open yellowDoor [YK 6->5]
- MT9 x1y9 move [YK 5->7, G 190->226] (auto: x1y8 skeletonSoldier, x1y7 yellowKey, x5y10 skeleton, x11y6 skeletonSoldier, x1y3 skeletonSoldier, x2y2 yellowKey, x3y1 skeleton)
- MT9 x3y7 open yellowDoor [YK 7->6]
- MT9 x3y7 move [YK 6->7, G 226->234] (auto: x4y7 skeletonSoldier, x5y7 yellowKey)
- MT9 x8y11 open yellowDoor [YK 7->6]
- MT9 x8y11 move [HP 577->627, YK 6->7, G 234->250] (auto: x9y11 bluePriest, x9y9 yellowKey, x10y10 skeleton, x11y11 redPotion, x11y9 bluePriest)
- MT9 x6y1 pass downFloor
- after: HP=627 ATK=60 DEF=52 YK=7 BK=0 RK=0 G=250 dmg=3699 door=55/4/1

### MT8

- before: HP=627 ATK=60 DEF=52 YK=7 BK=0 RK=0 G=250 dmg=3699 door=55/4/1
- MT8 x11y9 open yellowDoor [YK 7->6]
- MT8 x11y9 move [G 250->264] (auto: x11y10 skeleton, x10y11 skeletonSoldier)
- MT8 x9y11 open yellowDoor [YK 6->5]
- MT8 x8y11 move [HP 627->677, YK 5->6, BK 0->1] (auto: x8y10 redPotion, x7y11 yellowKey, x7y10 blueKey)
- MT8 x1y1 pass downFloor
- after: HP=677 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=264 dmg=3699 door=57/4/1

### MT7

- before: HP=677 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=264 dmg=3699 door=57/4/1
- MT7 x11y11 pass downFloor
- after: HP=677 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=264 dmg=3699 door=57/4/1

### MT6

- before: HP=677 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=264 dmg=3699 door=57/4/1
- MT6 x1y2 move [G 264->272] (auto: x9y6 skeletonSoldier)
- MT6 x1y1 pass downFloor
- after: HP=677 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=272 dmg=3699 door=57/4/1

### MT5

- before: HP=677 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=272 dmg=3699 door=57/4/1
- MT5 x2y11 move [G 272->277] (auto: x3y5 bluePriest)
- MT5 x1y11 pass downFloor
- after: HP=677 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=277 dmg=3699 door=57/4/1

### MT4

- before: HP=677 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=277 dmg=3699 door=57/4/1
- MT4 x4y5 open yellowDoor [YK 6->5]
- MT4 x5y5 move [G 277->285] (auto: x6y5 redSlime, x9y5 skeleton)
- MT4 x10y4 open yellowDoor [YK 5->4]
- MT4 x10y4 move [HP 677->877, YK 4->5, G 285->293] (auto: x10y3 skeletonSoldier, x9y2 yellowKey, x11y2 bluePotion)
- MT4 x11y11 pass downFloor
- after: HP=877 ATK=60 DEF=52 YK=5 BK=1 RK=0 G=293 dmg=3699 door=59/4/1

### MT3

- before: HP=877 ATK=60 DEF=52 YK=5 BK=1 RK=0 G=293 dmg=3699 door=59/4/1
- MT3 x9y8 open yellowDoor [YK 5->4]
- MT3 x9y8 move [HP 877->927, YK 4->5, G 293->298] (auto: x10y8 bluePriest, x11y8 yellowKey, x11y7 redPotion)
- MT3 x1y11 pass downFloor
- after: HP=927 ATK=60 DEF=52 YK=5 BK=1 RK=0 G=298 dmg=3699 door=60/4/1

### MT2

- before: HP=927 ATK=60 DEF=52 YK=5 BK=1 RK=0 G=298 dmg=3699 door=60/4/1
- MT2 x1y1 pass downFloor
- after: HP=927 ATK=60 DEF=52 YK=5 BK=1 RK=0 G=298 dmg=3699 door=60/4/1

### MT1

- before: HP=927 ATK=60 DEF=52 YK=5 BK=1 RK=0 G=298 dmg=3699 door=60/4/1
- MT1 x1y4 move [G 298->304] (auto: x2y4 skeleton)
- MT1 x2y5 open yellowDoor [YK 5->4]
- MT1 x2y6 move [YK 4->5, G 304->312] (auto: x1y6 yellowKey, x2y7 skeletonSoldier)
- MT1 x2y8 open yellowDoor [YK 5->4]
- MT1 x2y10 move [HP 927->1027, YK 4->6] (auto: x1y10 redPotion, x2y11 fly, x3y10 yellowKey, x1y11 redPotion, x3y11 yellowKey)
- after: HP=1027 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=312 dmg=3699 door=62/4/1

### MT15

- before: HP=1027 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=312 dmg=3699 door=62/4/1
- MT15 x6y10 fly
- MT15 x4y1 open yellowDoor [YK 6->5]
- MT15 x1y2 kill zombie [HP 1027->895, DEF 52->54, G 312->330] (auto: x1y1 blueGem) (+18G)
- after: HP=895 ATK=60 DEF=54 YK=5 BK=1 RK=0 G=330 dmg=3831 door=63/4/1

### MT17

- before: HP=895 ATK=60 DEF=54 YK=5 BK=1 RK=0 G=330 dmg=3831 door=63/4/1
- MT17 x5y11 fly
- MT17 x6y9 kill redPriest [HP 895->772, G 330->352] (+22G)
- MT17 x7y7 kill blackSlime [HP 772->760, G 352->360] (+8G)
- MT17 x7y5 open blueDoor [BK 1->0]
- MT17 x7y3 kill bigBat [HP 760->714, G 360->372] (+12G)
- MT17 x6y1 pass upFloor
- after: HP=714 ATK=60 DEF=54 YK=5 BK=0 RK=0 G=372 dmg=4012 door=63/5/1

### MT12

- before: HP=714 ATK=60 DEF=54 YK=5 BK=0 RK=0 G=372 dmg=4012 door=63/5/1
- MT12 x2y11 fly
- MT12 x11y9 kill zombie [HP 714->590, G 372->390] (+18G)
- MT12 x11y8 open yellowDoor [YK 5->4]
- MT12 x11y7 kill blackSlime [HP 590->678, DEF 54->56, YK 4->5, G 390->398] (auto: x10y6 blueGem, x9y7 yellowKey, x9y5 redPotion) (+8G)
- MT12 x8y6 open yellowDoor [YK 5->4]
- MT12 x7y6 kill redPriest [HP 678->961, G 398->420] (auto: x6y7 bluePotion) (+22G)
- MT12 x6y5 kill zombie [HP 961->845, G 420->438] (+18G)
- MT12 x6y4 open yellowDoor [YK 4->3]
- MT12 x7y3 kill redPriest [HP 845->728, ATK 60->62, YK 3->5, G 438->460] (auto: x7y1 yellowKey, x6y1 redGem, x5y1 yellowKey) (+22G)
- after: HP=728 ATK=62 DEF=56 YK=5 BK=0 RK=0 G=460 dmg=4498 door=66/5/1

### MT11

- before: HP=728 ATK=62 DEF=56 YK=5 BK=0 RK=0 G=460 dmg=4498 door=66/5/1
- MT11 x11y10 fly
- MT11 x11y8 kill bigBat [HP 728->684, G 460->472] (+12G)
- MT11 x11y4 kill blackSlime [HP 684->776, YK 5->6, G 472->480] (auto: x11y1 yellowKey, x10y1 redPotion) (+8G)
- MT11 x9y3 open yellowDoor [YK 6->5]
- MT11 x8y2 kill zombie [HP 776->660, G 480->498] (+18G)
- MT11 x7y1 open yellowDoor [YK 5->4]
- MT11 x6y1 move [ATK 62->64, G 498->501] (auto: x5y1 redGem, x6y2 bat)
- after: HP=660 ATK=64 DEF=56 YK=4 BK=0 RK=0 G=501 dmg=4666 door=68/5/1

### MT18

- before: HP=660 ATK=64 DEF=56 YK=4 BK=0 RK=0 G=501 dmg=4666 door=68/5/1
- MT18 x6y2 fly
- MT18 x8y1 open yellowDoor [YK 4->3]
- MT18 x9y1 kill redPriest [HP 660->582, YK 3->7, BK 0->1, G 501->523] (auto: x11y1 yellowKey, x11y2 yellowKey, x11y3 blueKey, x11y4 yellowKey, x11y5 yellowKey) (+22G)
- MT18 x4y1 open blueDoor [BK 1->0]
- MT18 x1y1 pass upFloor
- after: HP=582 ATK=64 DEF=56 YK=7 BK=0 RK=0 G=523 dmg=4744 door=69/6/1

### MT15

- before: HP=582 ATK=64 DEF=56 YK=7 BK=0 RK=0 G=523 dmg=4744 door=69/6/1
- MT15 x6y2 fly
- MT15 x1y4 open yellowDoor [YK 7->6]
- MT15 x1y7 kill blackSlime [HP 582->574, G 523->531] (+8G)
- MT15 x2y9 open yellowDoor [YK 6->5]
- MT15 x3y8 move [YK 5->7, BK 0->1] (auto: x3y7 yellowKey, x3y6 blueKey, x3y5 yellowKey)
- after: HP=574 ATK=64 DEF=56 YK=7 BK=1 RK=0 G=531 dmg=4752 door=71/6/1

### MT19

- before: HP=574 ATK=64 DEF=56 YK=7 BK=1 RK=0 G=531 dmg=4752 door=71/6/1
- MT19 x1y2 fly
- MT19 x1y3 open yellowDoor [YK 7->6]
- MT19 x1y3 move [G 531->534] (auto: x1y4 bat)
- MT19 x1y6 open yellowDoor [YK 6->5]
- MT19 x1y7 kill bigBat [HP 574->530, G 534->546] (+12G)
- MT19 x1y9 open yellowDoor [YK 5->4]
- MT19 x1y11 kill blackSlime [HP 530->522, G 546->554] (+8G)
- MT19 x3y11 kill bigBat [HP 522->478, G 554->566] (+12G)
- MT19 x4y10 open yellowDoor [YK 4->3]
- MT19 x4y10 move [YK 3->5] (auto: x5y10 yellowKey, x7y10 yellowKey)
- MT19 x6y11 pass upFloor
- after: HP=478 ATK=64 DEF=56 YK=5 BK=1 RK=0 G=566 dmg=4848 door=75/6/1

### MT20

- before: HP=478 ATK=64 DEF=56 YK=5 BK=1 RK=0 G=566 dmg=4848 door=75/6/1
- MT20 x4y11 kill redPriest [HP 478->500, G 566->588] (auto: x1y11 redPotion) (+22G)
- MT20 x1y9 open yellowDoor [YK 5->4]
- MT20 x1y8 move [G 588->594] (auto: x1y7 bat, x2y8 bat)
- MT20 x2y6 open blueDoor [BK 1->0]
- MT20 x5y11 move [ATK 64->66, DEF 56->58, YK 4->5] (auto: x2y4 blueGem, x1y5 yellowKey, x1y4 redGem)
- MT20 x6y11 pass downFloor
- after: HP=500 ATK=66 DEF=58 YK=5 BK=0 RK=0 G=594 dmg=4926 door=76/7/1

### MT19

- before: HP=500 ATK=66 DEF=58 YK=5 BK=0 RK=0 G=594 dmg=4926 door=76/7/1
- MT19 x8y11 open yellowDoor [YK 5->4]
- MT19 x9y11 move [G 594->597] (auto: x10y11 bat)
- MT19 x11y10 kill bigBat [HP 500->558, YK 4->5, G 597->609] (auto: x10y9 yellowKey, x9y9 redPotion) (+12G)
- MT19 x11y8 kill zombie [HP 558->450, G 609->627] (+18G)
- MT19 x11y7 open yellowDoor [YK 5->4]
- MT19 x10y5 kill blackSlime [HP 450->446, G 627->635] (+8G)
- MT19 x10y3 open yellowDoor [YK 4->3]
- MT19 x10y2 kill bigBat [HP 446->404, ATK 66->68, YK 3->4, G 635->647] (auto: x10y1 yellowKey, x11y1 redGem) (+12G)
- MT19 x1y1 pass downFloor
- after: HP=404 ATK=68 DEF=58 YK=4 BK=0 RK=0 G=647 dmg=5122 door=79/7/1

### MT18

- before: HP=404 ATK=68 DEF=58 YK=4 BK=0 RK=0 G=647 dmg=5122 door=79/7/1
- MT18 x6y5 move [G 647->659] (auto: x10y5 bigBat)
- after: HP=404 ATK=68 DEF=58 YK=4 BK=0 RK=0 G=659 dmg=5122 door=79/7/1

### MT12

- before: HP=404 ATK=68 DEF=58 YK=4 BK=0 RK=0 G=659 dmg=5122 door=79/7/1
- MT12 x2y11 fly
- MT12 x3y11 move [G 659->671] (auto: x11y5 bigBat)
- after: HP=404 ATK=68 DEF=58 YK=4 BK=0 RK=0 G=671 dmg=5122 door=79/7/1

### MT16

- before: HP=404 ATK=68 DEF=58 YK=4 BK=0 RK=0 G=671 dmg=5122 door=79/7/1
- MT16 x6y2 fly
- MT16 x7y10 move [G 671->695] (auto: x5y9 bigBat, x7y9 bigBat)
- MT16 x8y10 open yellowDoor [YK 4->3]
- MT16 x10y9 kill redPriest [HP 404->330, G 695->717] (+22G)
- MT16 x10y8 open yellowDoor [YK 3->2]
- MT16 x10y7 move [BK 0->1, G 717->729] (auto: x9y7 bigBat, x11y7 blueKey)
- MT16 x4y2 open yellowDoor [YK 2->1]
- MT16 x3y1 move [YK 1->4, G 729->753] (auto: x2y1 bigBat, x2y3 bigBat, x1y1 yellowKey, x1y3 yellowKey, x1y2 yellowKey)
- after: HP=330 ATK=68 DEF=58 YK=4 BK=1 RK=0 G=753 dmg=5196 door=82/7/1

### MT18

- before: HP=330 ATK=68 DEF=58 YK=4 BK=1 RK=0 G=753 dmg=5196 door=82/7/1
- MT18 x6y2 fly
- MT18 x6y6 open blueDoor [BK 1->0]
- MT18 x2y7 kill zombie [HP 330->222, G 753->771] (+18G)
- MT18 x1y8 open yellowDoor [YK 4->3]
- MT18 x1y9 kill redPriest [HP 222->248, ATK 68->70, YK 3->4, G 771->793] (auto: x1y11 redPotion, x2y10 yellowKey, x2y11 redGem) (+22G)
- after: HP=248 ATK=70 DEF=58 YK=4 BK=0 RK=0 G=793 dmg=5378 door=83/8/1

### MT19

- before: HP=248 ATK=70 DEF=58 YK=4 BK=0 RK=0 G=793 dmg=5378 door=83/8/1
- MT19 x1y2 fly
- after: HP=248 ATK=70 DEF=58 YK=4 BK=0 RK=0 G=793 dmg=5378 door=83/8/1

### MT12

- before: HP=248 ATK=70 DEF=58 YK=4 BK=0 RK=0 G=793 dmg=5378 door=83/8/1
- MT12 x2y11 fly
- MT12 x3y10 open yellowDoor [YK 4->3]
- MT12 x3y9 kill zombie [HP 248->167, YK 3->6, BK 0->1, G 793->811] (auto: x2y8 blueKey, x2y7 yellowKey, x1y8 yellowKey, x1y7 yellowKey) (+18G)
- after: HP=167 ATK=70 DEF=58 YK=6 BK=1 RK=0 G=811 dmg=5459 door=84/8/1

### MT19

- before: HP=167 ATK=70 DEF=58 YK=6 BK=1 RK=0 G=811 dmg=5459 door=84/8/1
- MT19 x1y2 fly
- MT19 x3y8 kill blackSlime [HP 167->165, G 811->819] (+8G)
- MT19 x6y7 open blueDoor [BK 1->0]
- after: HP=165 ATK=70 DEF=58 YK=6 BK=0 RK=0 G=819 dmg=5461 door=84/9/1

### MT17

- before: HP=165 ATK=70 DEF=58 YK=6 BK=0 RK=0 G=819 dmg=5461 door=84/9/1
- MT17 x6y2 fly
- MT17 x7y11 move [HP 165->265, G 819->831] (auto: x8y11 bigBat, x11y11 redPotion)
- after: HP=265 ATK=70 DEF=58 YK=6 BK=0 RK=0 G=831 dmg=5461 door=84/9/1

### MT11

- before: HP=265 ATK=70 DEF=58 YK=6 BK=0 RK=0 G=831 dmg=5461 door=84/9/1
- MT11 x11y10 fly
- MT11 x9y9 move [G 831->843] (auto: x4y7 bigBat)
- MT11 x9y10 open yellowDoor [YK 6->5]
- MT11 x9y10 move [HP 265->665, G 843->855] (auto: x9y11 bigBat, x8y11 bluePotion)
- after: HP=665 ATK=70 DEF=58 YK=5 BK=0 RK=0 G=855 dmg=5461 door=85/9/1

### MT19

- before: HP=665 ATK=70 DEF=58 YK=5 BK=0 RK=0 G=855 dmg=5461 door=85/9/1
- MT19 x1y2 fly
- MT19 x7y6 kill rock [HP 665->287, YK 5->7, G 855->883] (auto: x8y5 yellowKey, x6y4 fakeWall, x4y5 yellowKey) (+28G)
- MT19 x6y3 pass fakeWall2
- after: HP=287 ATK=70 DEF=58 YK=7 BK=0 RK=0 G=883 dmg=5839 door=85/9/1

### MT20

- before: HP=287 ATK=70 DEF=58 YK=7 BK=0 RK=0 G=883 dmg=5839 door=85/9/1
- MT20 x6y10 fly
- after: HP=287 ATK=70 DEF=58 YK=7 BK=0 RK=0 G=883 dmg=5839 door=85/9/1

### MT12

- before: HP=287 ATK=70 DEF=58 YK=7 BK=0 RK=0 G=883 dmg=5839 door=85/9/1
- MT12 x2y11 fly
- MT12 x4y5 open yellowDoor [YK 7->6]
- MT12 x2y5 kill redPriest [HP 287->213, G 883->905] (+22G)
- MT12 x1y4 open yellowDoor [YK 6->5]
- MT12 x3y3 move [G 905->917] (auto: x3y2 bigBat, x2y1 fakeWall)
- MT12 x1y1 trader redKey1 [RK 0->1, G 917->117]
- after: HP=213 ATK=70 DEF=58 YK=5 BK=0 RK=1 G=117 dmg=5913 door=87/9/1

### MT20

- before: HP=213 ATK=70 DEF=58 YK=5 BK=0 RK=1 G=117 dmg=5913 door=87/9/1
- MT20 x6y10 fly
- after: HP=213 ATK=70 DEF=58 YK=5 BK=0 RK=1 G=117 dmg=5913 door=87/9/1

### MT15

- before: HP=213 ATK=70 DEF=58 YK=5 BK=0 RK=1 G=117 dmg=5913 door=87/9/1
- MT15 x6y2 fly
- MT15 x11y5 move [G 117->153] (auto: x10y5 bigBat, x1y10 bigBat, x3y10 bigBat)
- MT15 x11y6 kill redPriest [HP 213->539, G 153->175] (auto: x11y8 bluePotion) (+22G)
- after: HP=539 ATK=70 DEF=58 YK=5 BK=0 RK=1 G=175 dmg=5987 door=87/9/1

### MT11

- before: HP=539 ATK=70 DEF=58 YK=5 BK=0 RK=1 G=175 dmg=5987 door=87/9/1
- MT11 x11y10 fly
- MT11 x7y7 open yellowDoor [YK 5->4]
- MT11 x8y7 kill blackSlime [HP 539->637, G 175->183] (auto: x9y6 redPotion) (+8G)
- after: HP=637 ATK=70 DEF=58 YK=4 BK=0 RK=1 G=183 dmg=5989 door=88/9/1

### MT18

- before: HP=637 ATK=70 DEF=58 YK=4 BK=0 RK=1 G=183 dmg=5989 door=88/9/1
- MT18 x6y2 fly
- MT18 x1y3 open yellowDoor [YK 4->3]
- MT18 x1y4 move [HP 637->737] (auto: x2y4 redPotion)
- after: HP=737 ATK=70 DEF=58 YK=3 BK=0 RK=1 G=183 dmg=5989 door=89/9/1

### MT20

- before: HP=737 ATK=70 DEF=58 YK=3 BK=0 RK=1 G=183 dmg=5989 door=89/9/1
- MT20 x6y10 fly
- MT20 x6y9 open redDoor [RK 1->0]
- MT20 x6y8 pass
- MT20 x6y6 kill vampire [HP 737->32, G 183->327] (+144G)
- MT20 x6y5 move [HP 32->1232, ATK 70->76, DEF 58->64, YK 3->6] (auto: x6y4 yellowKey, x5y4 yellowKey, x7y4 yellowKey, x4y5 redGem, x8y5 blueGem, x4y6 redGem, x6y8 bluePotion, x8y6 blueGem, x4y7 redGem, x5y8 bluePotion, x7y8 bluePotion, x8y7 blueGem)
- MT20 x6y1 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2

### MT21

- before: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2
- MT21 x6y11 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2

### MT22

- before: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2
- MT22 x6y6 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2

### MT23

- before: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2
- MT23 x11y1 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2

### MT24

- before: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2
- MT24 x2y10 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2

### MT25

- before: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2
- MT25 x1y11 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2

### MT26

- before: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2
- MT26 x2y10 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2

### MT27

- before: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2
- MT27 x11y11 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2

### MT28

- before: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2
- MT28 x1y11 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2

### MT29

- before: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2
- MT29 x6y2 event thief
- MT29 x6y11 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2

### MT30

- before: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=327 dmg=6694 door=89/9/2
- MT30 x5y5 kill greenSlime [G 327->328] (+1G)
- MT30 x4y5 kill redSlime [G 328->330] (+2G)
- MT30 x3y5 kill blackSlime [G 330->338] (+8G)
- MT30 x7y5 kill greenSlime [G 338->339] (+1G)
- MT30 x8y5 kill redSlime [G 339->341] (+2G)
- MT30 x9y5 kill blackSlime [G 341->349] (+8G)
- MT30 x6y1 pass upFloor
- after: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=349 dmg=6694 door=89/9/2

### MT31

- before: HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=349 dmg=6694 door=89/9/2
- MT31 x6y2 设置自动：battle=true, item=nopotion, wall=true
- MT31 x6y8 kill zombieKnight [HP 1232->1120, G 349->379] (+30G)
- MT31 x6y9 kill zombieKnight [HP 1120->1008, G 379->409] (+30G)
- MT31 x6y11 pass upFloor
- after: HP=1008 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=409 dmg=6918 door=89/9/2

### MT32

- before: HP=1008 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=409 dmg=6918 door=89/9/2
- MT32 x6y10 pass [HP 1008->578, G 409->509] (auto: +100G)
- MT32 x8y11 kill ghostSkeleton [HP 578->114, G 509->544] (+35G)
- MT32 x10y10 shop def [DEF 64->80, G 544->464]
- MT32 x10y10 shop def [DEF 80->96, G 464->324]
- MT32 x10y10 shop def [DEF 96->112, G 324->104]
- after: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=104 dmg=7812 door=89/9/2

### MT11

- before: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=104 dmg=7812 door=89/9/2
- MT11 x11y10 fly
- MT11 x10y9 move [G 104->126] (auto: x8y5 redPriest)
- MT11 x11y11 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=126 dmg=7812 door=89/9/2

### MT12

- before: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=126 dmg=7812 door=89/9/2
- MT12 x2y11 move [G 126->174] (auto: x9y9 blackSlime, x10y3 zombie, x10y1 fakeWall, x5y3 redPriest)
- MT12 x1y11 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=174 dmg=7812 door=89/9/2

### MT13

- before: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=174 dmg=7812 door=89/9/2
- MT13 x11y11 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=174 dmg=7812 door=89/9/2

### MT14

- before: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=174 dmg=7812 door=89/9/2
- MT14 x5y11 move [G 174->222] (auto: x10y8 blackSlime, x4y8 zombie, x3y9 redPriest)
- MT14 x6y11 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=222 dmg=7812 door=89/9/2

### MT15

- before: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=222 dmg=7812 door=89/9/2
- MT15 x5y1 move [G 222->252] (auto: x3y3 blackSlime, x2y11 redPriest)
- MT15 x6y1 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=252 dmg=7812 door=89/9/2

### MT16

- before: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=252 dmg=7812 door=89/9/2
- MT16 x5y11 move [G 252->338] (auto: x5y3 zombie, x2y2 redPriest, x3y6 rock, x10y5 zombie)
- MT16 x6y11 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=338 dmg=7812 door=89/9/2

### MT17

- before: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=338 dmg=7812 door=89/9/2
- MT17 x5y1 move [G 338->356] (auto: x5y7 zombie)
- MT17 x6y1 pass upFloor
- after: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=356 dmg=7812 door=89/9/2

### MT18

- before: HP=114 ATK=76 DEF=112 YK=6 BK=0 RK=0 G=356 dmg=7812 door=89/9/2
- MT18 x4y7 move [G 356->466] (auto: x10y2 blackSlime, x9y4 zombie, x10y7 rock, x1y5 rock, x3y5 rock)
- MT18 x4y8 open yellowDoor [YK 6->5]
- MT18 x4y8 move [YK 5->6, G 466->514] (auto: x4y9 bigBat, x4y10 bigBat, x5y9 bigBat, x5y10 bigBat, x5y11 yellowKey)
- MT18 x8y8 open yellowDoor [YK 6->5]
- MT18 x11y7 move [YK 5->6, G 514->546] (auto: x8y9 blackSlime, x7y9 blackSlime, x8y10 blackSlime, x7y10 blackSlime, x7y11 yellowKey)
- MT18 x11y8 open yellowDoor [YK 6->5]
- MT18 x11y8 move [DEF 112->114, YK 5->6, G 546->568] (auto: x11y9 redPriest, x10y10 yellowKey, x10y11 blueGem)
- MT18 x1y1 pass upFloor
- after: HP=114 ATK=76 DEF=114 YK=6 BK=0 RK=0 G=568 dmg=7812 door=92/9/2

### MT19

- before: HP=114 ATK=76 DEF=114 YK=6 BK=0 RK=0 G=568 dmg=7812 door=92/9/2
- MT19 x5y11 move [G 568->604] (auto: x5y6 rock, x11y5 blackSlime)
- MT19 x6y11 pass upFloor
- after: HP=114 ATK=76 DEF=114 YK=6 BK=0 RK=0 G=604 dmg=7812 door=92/9/2

### MT20

- before: HP=114 ATK=76 DEF=114 YK=6 BK=0 RK=0 G=604 dmg=7812 door=92/9/2
- MT20 x7y11 move [G 604->682] (auto: x8y11 redPriest, x10y10 rock, x2y10 rock)
- after: HP=114 ATK=76 DEF=114 YK=6 BK=0 RK=0 G=682 dmg=7812 door=92/9/2

### MT32

- before: HP=114 ATK=76 DEF=114 YK=6 BK=0 RK=0 G=682 dmg=7812 door=92/9/2
- MT32 x6y11 fly
- MT32 x10y10 shop def [DEF 114->130, G 682->362]
- after: HP=114 ATK=76 DEF=130 YK=6 BK=0 RK=0 G=362 dmg=7812 door=92/9/2

### MT19

- before: HP=114 ATK=76 DEF=130 YK=6 BK=0 RK=0 G=362 dmg=7812 door=92/9/2
- MT19 x6y10 fly
- MT19 x1y2 move [BK 0->1, G 362->504] (auto: x6y9 zombieKnight, x8y8 zombieKnight, x4y3 zombieKnight, x8y3 zombieKnight, x8y1 blueKey, x6y1 redPriest)
- MT19 x1y1 pass downFloor
- after: HP=114 ATK=76 DEF=130 YK=6 BK=1 RK=0 G=504 dmg=7812 door=92/9/2

### MT18

- before: HP=114 ATK=76 DEF=130 YK=6 BK=1 RK=0 G=504 dmg=7812 door=92/9/2
- MT18 x5y1 move [G 504->564] (auto: x5y4 zombieKnight, x7y4 zombieKnight)
- MT18 x6y1 pass downFloor
- after: HP=114 ATK=76 DEF=130 YK=6 BK=1 RK=0 G=564 dmg=7812 door=92/9/2

### MT17

- before: HP=114 ATK=76 DEF=130 YK=6 BK=1 RK=0 G=564 dmg=7812 door=92/9/2
- MT17 x10y11 move [G 564->594] (auto: x5y3 zombieKnight)
- MT17 x10y10 open yellowDoor [YK 6->5]
- MT17 x9y8 kill zombie [G 594->612] (+18G)
- MT17 x11y8 kill zombie [G 612->630] (+18G)
- MT17 x9y5 kill zombieKnight [G 630->660] (+30G)
- MT17 x11y5 kill zombieKnight [G 660->690] (+30G)
- MT17 x10y3 move [ATK 76->78, DEF 130->132, YK 5->7] (auto: x9y3 yellowKey, x11y3 yellowKey, x9y1 redGem, x11y1 blueGem)
- MT17 x10y2 take bluePotion [HP 114->514]
- after: HP=514 ATK=78 DEF=132 YK=7 BK=1 RK=0 G=690 dmg=7812 door=93/9/2

### MT16

- before: HP=514 ATK=78 DEF=132 YK=7 BK=1 RK=0 G=690 dmg=7812 door=93/9/2
- MT16 x6y10 fly
- MT16 x7y2 move [G 690->720] (auto: x6y6 zombieKnight)
- MT16 x8y2 open yellowDoor [YK 7->6]
- MT16 x5y1 move [G 720->740] (auto: x9y2 blackSlime, x11y1 bigBat)
- MT16 x6y1 pass downFloor
- after: HP=514 ATK=78 DEF=132 YK=6 BK=1 RK=0 G=740 dmg=7812 door=94/9/2

### MT15

- before: HP=514 ATK=78 DEF=132 YK=6 BK=1 RK=0 G=740 dmg=7812 door=94/9/2
- MT15 x5y11 move [G 740->770] (auto: x2y1 zombieKnight)
- MT15 x6y11 pass downFloor
- after: HP=514 ATK=78 DEF=132 YK=6 BK=1 RK=0 G=770 dmg=7812 door=94/9/2

### MT14

- before: HP=514 ATK=78 DEF=132 YK=6 BK=1 RK=0 G=770 dmg=7812 door=94/9/2
- MT14 x11y7 open yellowDoor [YK 6->5]
- MT14 x11y7 move [G 770->878] (auto: x11y6 zombie, x10y4 zombieKnight, x8y5 bigBat, x6y5 rock, x4y5 bigBat, x2y6 blackSlime)
- MT14 x10y3 open yellowDoor [YK 5->4]
- MT14 x7y5 move [YK 4->8] (auto: x10y1 yellowKey, x11y2 yellowKey, x9y1 yellowKey, x11y1 yellowKey)
- MT14 x7y4 open yellowDoor [YK 8->7]
- MT14 x1y6 move [G 878->908] (auto: x7y2 zombieKnight)
- MT14 x1y7 open yellowDoor [YK 7->6]
- MT14 x7y2 move [BK 1->2, G 908->930] (auto: x1y9 redPriest, x1y11 blueKey)
- MT14 x7y1 take redPotion [HP 514->614, DEF 132->134, YK 6->7, G 930->938] (auto: x6y1 yellowKey, x5y1 blueGem, x5y2 blackSlime)
- MT14 x11y11 pass downFloor
- after: HP=614 ATK=78 DEF=134 YK=7 BK=2 RK=0 G=938 dmg=7812 door=98/9/2

### MT13

- before: HP=614 ATK=78 DEF=134 YK=7 BK=2 RK=0 G=938 dmg=7812 door=98/9/2
- MT13 x1y11 pass downFloor
- after: HP=614 ATK=78 DEF=134 YK=7 BK=2 RK=0 G=938 dmg=7812 door=98/9/2

### MT12

- before: HP=614 ATK=78 DEF=134 YK=7 BK=2 RK=0 G=938 dmg=7812 door=98/9/2
- MT12 x11y11 pass downFloor
- after: HP=614 ATK=78 DEF=134 YK=7 BK=2 RK=0 G=938 dmg=7812 door=98/9/2

### MT32

- before: HP=614 ATK=78 DEF=134 YK=7 BK=2 RK=0 G=938 dmg=7812 door=98/9/2
- MT32 x6y11 fly
- MT32 x10y10 shop def [DEF 134->150, G 938->498]
- after: HP=614 ATK=78 DEF=150 YK=7 BK=2 RK=0 G=498 dmg=7812 door=98/9/2

### MT28

- before: HP=614 ATK=78 DEF=150 YK=7 BK=2 RK=0 G=498 dmg=7812 door=98/9/2
- MT28 x2y11 fly
- MT28 x8y4 trader specialTrader [YK 7->6, G 498->598] (auto: +100G)
- after: HP=614 ATK=78 DEF=150 YK=6 BK=2 RK=0 G=598 dmg=7812 door=98/9/2

### MT32

- before: HP=614 ATK=78 DEF=150 YK=6 BK=2 RK=0 G=598 dmg=7812 door=98/9/2
- MT32 x6y11 fly
- MT32 x10y10 shop atk [ATK 78->86, G 598->18]
- MT32 x3y1 open blueDoor [BK 2->1]
- MT32 x3y1 move [ATK 86->90, DEF 150->154] (auto: x1y1 blueGem, x2y2 redGem)
- MT32 x11y1 pass upFloor
- after: HP=614 ATK=90 DEF=154 YK=6 BK=1 RK=0 G=18 dmg=7812 door=98/10/2

### MT33

- before: HP=614 ATK=90 DEF=154 YK=6 BK=1 RK=0 G=18 dmg=7812 door=98/10/2
- MT33 x8y2 open yellowDoor [YK 6->5]
- MT33 x11y3 take bluePotion [HP 614->1414]
- MT33 x10y5 pass
- MT33 x9y5 kill ghostSkeleton [HP 1414->1336, G 18->53] (+35G)
- MT33 x11y5 kill ghostSkeleton [HP 1336->1258, G 53->88] (+35G)
- MT33 x11y7 kill soldier [HP 1258->890, G 88->133] (+45G)
- MT33 x9y7 kill soldier [HP 890->522, G 133->178] (+45G)
- MT33 x9y10 move [ATK 90->130] (auto: x10y10 sword3)
- after: HP=522 ATK=130 DEF=154 YK=5 BK=1 RK=0 G=178 dmg=8704 door=99/10/2

### MT2

- before: HP=522 ATK=130 DEF=154 YK=5 BK=1 RK=0 G=178 dmg=8704 door=99/10/2
- MT2 x1y10 fly
- MT2 x3y1 open blueDoor [BK 1->0]
- MT2 x6y2 kill blueGuard [HP 522->418, G 178->228] (+50G)
- MT2 x8y2 kill blueGuard [HP 418->314, G 228->278] (+50G)
- MT2 x10y4 move [YK 5->8] (auto: x4y4 yellowKey, x3y5 yellowKey, x3y4 yellowKey)
- MT2 x11y4 event oldman [G 278->1278] (auto: +1000G)
- MT2 x10y11 event thief
- after: HP=314 ATK=130 DEF=154 YK=8 BK=0 RK=0 G=1278 dmg=8912 door=99/11/2

### MT32

- before: HP=314 ATK=130 DEF=154 YK=8 BK=0 RK=0 G=1278 dmg=8912 door=99/11/2
- MT32 x6y11 fly
- MT32 x10y10 shop atk [ATK 130->138, G 1278->538]
- MT32 x11y1 pass upFloor
- after: HP=314 ATK=138 DEF=154 YK=8 BK=0 RK=0 G=538 dmg=8912 door=99/11/2

### MT33

- before: HP=314 ATK=138 DEF=154 YK=8 BK=0 RK=0 G=538 dmg=8912 door=99/11/2
- MT33 x7y1 open yellowDoor [YK 8->7]
- MT33 x7y1 move [YK 7->8, G 538->598] (auto: x6y1 slimeMan, x4y1 zombieKnight, x6y3 yellowKey)
- MT33 x3y1 open yellowDoor [YK 8->7]
- MT33 x1y1 pass upFloor
- after: HP=314 ATK=138 DEF=154 YK=7 BK=0 RK=0 G=598 dmg=8912 door=101/11/2

### MT34

- before: HP=314 ATK=138 DEF=154 YK=7 BK=0 RK=0 G=598 dmg=8912 door=101/11/2
- MT34 x3y2 move [G 598->628] (auto: x2y3 slimeMan)
- MT34 x4y2 open yellowDoor [YK 7->6]
- MT34 x2y3 move [YK 6->7, G 628->658] (auto: x5y2 slimeMan, x6y1 yellowKey)
- MT34 x2y4 open yellowDoor [YK 7->6]
- MT34 x2y8 open yellowDoor [YK 6->5]
- MT34 x3y9 kill ghostSkeleton [HP 314->262, G 658->693] (+35G)
- MT34 x4y10 open yellowDoor [YK 5->4]
- MT34 x6y11 pass upFloor
- after: HP=262 ATK=138 DEF=154 YK=4 BK=0 RK=0 G=693 dmg=8964 door=105/11/2

### MT35

- before: HP=262 ATK=138 DEF=154 YK=4 BK=0 RK=0 G=693 dmg=8964 door=105/11/2
- MT35 x11y1 pass upFloor
- after: HP=262 ATK=138 DEF=154 YK=4 BK=0 RK=0 G=693 dmg=8964 door=105/11/2

### MT36

- before: HP=262 ATK=138 DEF=154 YK=4 BK=0 RK=0 G=693 dmg=8964 door=105/11/2
- MT36 x11y3 kill slimeMan [G 693->723] (+30G)
- MT36 x11y1 pass downFloor
- after: HP=262 ATK=138 DEF=154 YK=4 BK=0 RK=0 G=723 dmg=8964 door=105/11/2

### MT35

- before: HP=262 ATK=138 DEF=154 YK=4 BK=0 RK=0 G=723 dmg=8964 door=105/11/2
- MT35 x11y1 pass upFloor
- after: HP=262 ATK=138 DEF=154 YK=4 BK=0 RK=0 G=723 dmg=8964 door=105/11/2

### MT32

- before: HP=262 ATK=138 DEF=154 YK=4 BK=0 RK=0 G=723 dmg=8964 door=105/11/2
- MT32 x10y1 fly
- MT32 x5y3 open yellowDoor [YK 4->3]
- MT32 x4y4 move [YK 3->4, G 723->783] (auto: x3y4 slimeMan, x4y5 slimeMan, x2y5 yellowKey)
- after: HP=262 ATK=138 DEF=154 YK=4 BK=0 RK=0 G=783 dmg=8964 door=106/11/2

### MT31

- before: HP=262 ATK=138 DEF=154 YK=4 BK=0 RK=0 G=783 dmg=8964 door=106/11/2
- MT31 x6y10 fly
- MT31 x10y6 kill ghostSkeleton [HP 262->210, G 783->818] (+35G)
- MT31 x11y7 open yellowDoor [YK 4->3]
- MT31 x11y5 open yellowDoor [YK 3->2]
- MT31 x10y4 move [YK 2->6, G 818->878] (auto: x10y9 slimeMan, x11y10 slimeMan, x9y10 yellowKey, x8y10 yellowKey, x9y11 yellowKey, x8y11 yellowKey)
- MT31 x10y3 kill ghostSkeleton [HP 210->158, G 878->913] (+35G)
- after: HP=158 ATK=138 DEF=154 YK=6 BK=0 RK=0 G=913 dmg=9068 door=108/11/2

### MT30

- before: HP=158 ATK=138 DEF=154 YK=6 BK=0 RK=0 G=913 dmg=9068 door=108/11/2
- MT30 x6y2 fly
- after: HP=158 ATK=138 DEF=154 YK=6 BK=0 RK=0 G=913 dmg=9068 door=108/11/2

### MT32

- before: HP=158 ATK=138 DEF=154 YK=6 BK=0 RK=0 G=913 dmg=9068 door=108/11/2
- MT32 x6y11 fly
- after: HP=158 ATK=138 DEF=154 YK=6 BK=0 RK=0 G=913 dmg=9068 door=108/11/2

### MT34

- before: HP=158 ATK=138 DEF=154 YK=6 BK=0 RK=0 G=913 dmg=9068 door=108/11/2
- MT34 x2y1 fly
- MT34 x9y5 open yellowDoor [YK 6->5]
- MT34 x9y5 move [G 913->921] (auto: x9y4 blackSlime)
- after: HP=158 ATK=138 DEF=154 YK=5 BK=0 RK=0 G=921 dmg=9068 door=109/11/2

### MT32

- before: HP=158 ATK=138 DEF=154 YK=5 BK=0 RK=0 G=921 dmg=9068 door=109/11/2
- MT32 x10y1 fly
- MT32 x10y10 shop def [DEF 154->170, G 921->1]
- after: HP=158 ATK=138 DEF=170 YK=5 BK=0 RK=0 G=1 dmg=9068 door=109/11/2

### MT31

- before: HP=158 ATK=138 DEF=170 YK=5 BK=0 RK=0 G=1 dmg=9068 door=109/11/2
- MT31 x6y10 fly
- MT31 x8y2 kill soldier [HP 158->98, G 1->46] (+45G)
- MT31 x8y3 open yellowDoor [YK 5->4]
- MT31 x8y3 move [ATK 138->142] (auto: x8y4 redGem)
- after: HP=98 ATK=142 DEF=170 YK=4 BK=0 RK=0 G=46 dmg=9128 door=110/11/2

### MT34

- before: HP=98 ATK=142 DEF=170 YK=4 BK=0 RK=0 G=46 dmg=9128 door=110/11/2
- MT34 x2y1 fly
- MT34 x8y10 open yellowDoor [YK 4->3]
- MT34 x9y10 kill soldier [HP 98->38, ATK 142->146, YK 3->4, G 46->91] (auto: x10y11 yellowKey, x11y11 redGem) (+45G)
- MT34 x3y1 take redPotion [HP 38->238]
- MT34 x11y10 take redPotion [HP 238->438]
- MT34 x6y11 pass upFloor
- after: HP=438 ATK=146 DEF=170 YK=4 BK=0 RK=0 G=91 dmg=9188 door=111/11/2

### MT35

- before: HP=438 ATK=146 DEF=170 YK=4 BK=0 RK=0 G=91 dmg=9188 door=111/11/2
- MT35 x11y1 pass upFloor
- after: HP=438 ATK=146 DEF=170 YK=4 BK=0 RK=0 G=91 dmg=9188 door=111/11/2

### MT36

- before: HP=438 ATK=146 DEF=170 YK=4 BK=0 RK=0 G=91 dmg=9188 door=111/11/2
- MT36 x9y1 kill redKnight [HP 438->258, G 91->186] (auto: x7y1 zombieKnight) (+95G)
- MT36 x6y2 open yellowDoor [YK 4->3]
- MT36 x6y5 kill ghostSkeleton [HP 258->248, G 186->281] (auto: x5y6 slimeMan, x7y6 slimeMan) (+95G)
- MT36 x10y6 open yellowDoor [YK 3->2]
- MT36 x11y7 kill redKnight [HP 248->68, G 281->346] (+65G)
- MT36 x11y11 pass upFloor
- after: HP=68 ATK=146 DEF=170 YK=2 BK=0 RK=0 G=346 dmg=9558 door=113/11/2

### MT37

- before: HP=68 ATK=146 DEF=170 YK=2 BK=0 RK=0 G=346 dmg=9558 door=113/11/2
- MT37 x9y11 kill ghostSkeleton [HP 68->58, G 346->411] (auto: x3y11 slimeMan) (+65G)
- after: HP=58 ATK=146 DEF=170 YK=2 BK=0 RK=0 G=411 dmg=9568 door=113/11/2

### MT14

- before: HP=58 ATK=146 DEF=170 YK=2 BK=0 RK=0 G=411 dmg=9568 door=113/11/2
- MT14 x6y10 fly
- MT14 x9y6 take redPotion [HP 58->158]
- after: HP=158 ATK=146 DEF=170 YK=2 BK=0 RK=0 G=411 dmg=9568 door=113/11/2

### MT37

- before: HP=158 ATK=146 DEF=170 YK=2 BK=0 RK=0 G=411 dmg=9568 door=113/11/2
- MT37 x11y10 fly
- MT37 x1y9 kill soldier [HP 158->98, G 411->456] (+45G)
- MT37 x1y6 take redPotion [HP 98->298]
- after: HP=298 ATK=146 DEF=170 YK=2 BK=0 RK=0 G=456 dmg=9628 door=113/11/2

### MT32

- before: HP=298 ATK=146 DEF=170 YK=2 BK=0 RK=0 G=456 dmg=9628 door=113/11/2
- MT32 x10y1 fly
- MT32 x3y10 kill blueGuard [HP 298->278, G 456->506] (+50G)
- MT32 x1y10 kill blueGuard [HP 278->258, G 506->556] (+50G)
- MT32 x3y8 move [YK 2->6, BK 0->1] (auto: x2y7 yellowKey, x1y7 yellowKey, x3y7 yellowKey, x4y8 blueKey, x4y7 yellowKey)
- after: HP=258 ATK=146 DEF=170 YK=6 BK=1 RK=0 G=556 dmg=9668 door=113/11/2

### MT37

- before: HP=258 ATK=146 DEF=170 YK=6 BK=1 RK=0 G=556 dmg=9668 door=113/11/2
- MT37 x11y10 fly
- MT37 x1y3 open blueDoor [BK 1->0]
- MT37 x1y1 pass upFloor
- after: HP=258 ATK=146 DEF=170 YK=6 BK=0 RK=0 G=556 dmg=9668 door=113/12/2

### MT31

- before: HP=258 ATK=146 DEF=170 YK=6 BK=0 RK=0 G=556 dmg=9668 door=113/12/2
- MT31 x6y10 fly
- MT31 x2y6 kill ghostSkeleton [HP 258->248, G 556->591] (+35G)
- MT31 x1y5 open yellowDoor [YK 6->5]
- MT31 x3y4 open yellowDoor [YK 5->4]
- MT31 x3y4 move [BK 0->1] (auto: x4y4 blueKey)
- after: HP=248 ATK=146 DEF=170 YK=4 BK=1 RK=0 G=591 dmg=9678 door=115/12/2

### MT14

- before: HP=248 ATK=146 DEF=170 YK=4 BK=1 RK=0 G=591 dmg=9678 door=115/12/2
- MT14 x6y10 fly
- MT14 x2y4 open blueDoor [BK 1->0]
- MT14 x2y3 move [RK 0->1, G 591->681] (auto: x2y2 zombieKnight, x1y1 zombieKnight, x3y1 zombieKnight, x1y3 redKey)
- after: HP=248 ATK=146 DEF=170 YK=4 BK=0 RK=1 G=681 dmg=9678 door=115/13/2

### MT38

- before: HP=248 ATK=146 DEF=170 YK=4 BK=0 RK=1 G=681 dmg=9678 door=115/13/2
- MT38 x2y1 fly
- MT38 x3y1 open redDoor [RK 1->0]
- MT38 x3y1 move [YK 4->5, G 681->741] (auto: x4y1 slimeMan, x6y2 yellowKey, x8y1 slimeMan)
- MT38 x5y2 trader yellowKey3 [YK 5->8, G 741->541]
- MT38 x9y1 open yellowDoor [YK 8->7]
- MT38 x11y1 pass upFloor
- after: HP=248 ATK=146 DEF=170 YK=7 BK=0 RK=0 G=541 dmg=9678 door=116/13/3

### MT39

- before: HP=248 ATK=146 DEF=170 YK=7 BK=0 RK=0 G=541 dmg=9678 door=116/13/3
- MT39 x10y3 move [YK 7->8] (auto: x11y3 yellowKey)
- MT39 x10y4 open yellowDoor [YK 8->7]
- MT39 x9y5 move [G 541->571] (auto: x9y6 slimeMan)
- MT39 x11y7 kill ghostSkeleton [HP 248->238, ATK 146->150, G 571->606] (auto: x11y6 redGem) (+35G)
- MT39 x11y1 pass downFloor
- after: HP=238 ATK=150 DEF=170 YK=7 BK=0 RK=0 G=606 dmg=9688 door=117/13/3

### MT38

- before: HP=238 ATK=150 DEF=170 YK=7 BK=0 RK=0 G=606 dmg=9688 door=117/13/3
- MT38 x11y3 open yellowDoor [YK 7->6]
- MT38 x11y6 kill ghostSkeleton [HP 238->228, G 606->641] (+35G)
- MT38 x11y8 open yellowDoor [YK 6->5]
- MT38 x11y9 kill ghostSkeleton [HP 228->218, YK 5->6, G 641->676] (auto: x9y9 yellowKey) (+35G)
- MT38 x9y11 kill soldier [HP 218->158, G 676->721] (+45G)
- MT38 x8y11 open yellowDoor [YK 6->5]
- MT38 x8y11 move [G 721->794] (auto: x7y11 zombie, x5y11 swordsman)
- MT38 x4y11 open yellowDoor [YK 5->4]
- MT38 x3y10 kill blueGuard [HP 158->138, G 794->844] (+50G)
- MT38 x1y10 kill blueGuard [HP 138->118, G 844->894] (+50G)
- MT38 x3y7 move [DEF 170->210, G 894->1019] (auto: x2y7 shield3, x1y3 ghostSkeleton, x2y5 flower, x3y4 soldier, x4y4 soldier)
- MT38 x11y1 pass upFloor
- MT38 x10y1 fly
- MT38 x7y3 open yellowDoor [YK 4->3]
- MT38 x7y5 move [G 1019->1109] (auto: x7y6 ghostSkeleton, x7y7 swordsman)
- MT38 x6y8 take redPotion [HP 118->318, DEF 210->214] (auto: x5y8 blueGem)
- after: HP=318 ATK=150 DEF=214 YK=3 BK=0 RK=0 G=1109 dmg=9808 door=122/13/3

### MT31

- before: HP=318 ATK=150 DEF=214 YK=3 BK=0 RK=0 G=1109 dmg=9808 door=122/13/3
- MT31 x6y10 fly
- MT31 x1y6 move [YK 3->7, G 1109->1244] (auto: x11y3 ghostSkeleton, x1y2 swordsman, x2y3 soldier, x3y2 yellowKey, x3y1 yellowKey, x4y2 yellowKey, x4y1 yellowKey)
- MT31 x1y7 open yellowDoor [YK 7->6]
- MT31 x2y8 move [G 1244->1314] (auto: x1y9 ghostSkeleton, x2y9 ghostSkeleton)
- MT31 x4y10 kill redKnight [HP 318->270, G 1314->1379] (+65G)
- MT31 x4y9 open yellowDoor [YK 6->5]
- MT31 x4y9 move [DEF 214->218] (auto: x4y8 blueGem)
- after: HP=270 ATK=150 DEF=218 YK=5 BK=0 RK=0 G=1379 dmg=9856 door=124/13/3

### MT32

- before: HP=270 ATK=150 DEF=218 YK=5 BK=0 RK=0 G=1379 dmg=9856 door=124/13/3
- MT32 x6y11 fly
- MT32 x6y3 move [G 1379->1424] (auto: x1y4 soldier)
- MT32 x7y3 open yellowDoor [YK 5->4]
- MT32 x8y3 move [G 1424->1459] (auto: x8y4 ghostSkeleton)
- MT32 x9y5 open yellowDoor [YK 4->3]
- MT32 x8y6 move [YK 3->5] (auto: x10y4 yellowKey, x11y5 yellowKey)
- MT32 x8y7 kill redKnight [HP 270->234, G 1459->1524] (+65G)
- MT32 x9y8 open yellowDoor [YK 5->4]
- MT32 x9y8 move [YK 4->6, BK 0->1] (auto: x10y7 yellowKey, x11y8 yellowKey, x11y7 blueKey)
- after: HP=234 ATK=150 DEF=218 YK=6 BK=1 RK=0 G=1524 dmg=9892 door=127/13/3

### MT34

- before: HP=234 ATK=150 DEF=218 YK=6 BK=1 RK=0 G=1524 dmg=9892 door=127/13/3
- MT34 x2y1 fly
- MT34 x6y2 move [G 1524->1624] (auto: x1y10 swordsman, x2y11 soldier)
- MT34 x7y2 kill redKnight [HP 234->198, G 1624->1689] (+65G)
- MT34 x8y2 open yellowDoor [YK 6->5]
- MT34 x9y2 move [DEF 218->222, YK 5->8] (auto: x9y1 yellowKey, x10y2 yellowKey, x10y1 yellowKey, x11y1 blueGem)
- MT34 x6y11 pass upFloor
- after: HP=198 ATK=150 DEF=222 YK=8 BK=1 RK=0 G=1689 dmg=9928 door=128/13/3

### MT35

- before: HP=198 ATK=150 DEF=222 YK=8 BK=1 RK=0 G=1689 dmg=9928 door=128/13/3
- MT35 x11y1 pass upFloor
- after: HP=198 ATK=150 DEF=222 YK=8 BK=1 RK=0 G=1689 dmg=9928 door=128/13/3

### MT36

- before: HP=198 ATK=150 DEF=222 YK=8 BK=1 RK=0 G=1689 dmg=9928 door=128/13/3
- MT36 x10y11 move [YK 8->9, G 1689->2004] (auto: x11y5 swordsman, x3y1 soldier, x1y3 slimeMan, x9y11 swordsman, x7y11 zombieKnight, x5y11 yellowKey, x3y11 soldier, x1y9 swordsman)
- MT36 x11y11 pass upFloor
- after: HP=198 ATK=150 DEF=222 YK=9 BK=1 RK=0 G=2004 dmg=9928 door=128/13/3

### MT37

- before: HP=198 ATK=150 DEF=222 YK=9 BK=1 RK=0 G=2004 dmg=9928 door=128/13/3
- MT37 x1y1 pass upFloor
- after: HP=198 ATK=150 DEF=222 YK=9 BK=1 RK=0 G=2004 dmg=9928 door=128/13/3

### MT38

- before: HP=198 ATK=150 DEF=222 YK=9 BK=1 RK=0 G=2004 dmg=9928 door=128/13/3
- MT38 x11y1 pass upFloor
- after: HP=198 ATK=150 DEF=222 YK=9 BK=1 RK=0 G=2004 dmg=9928 door=128/13/3

### MT39

- before: HP=198 ATK=150 DEF=222 YK=9 BK=1 RK=0 G=2004 dmg=9928 door=128/13/3
- MT39 x10y7 move [G 2004->2049] (auto: x11y5 soldier)
- MT39 x10y8 open yellowDoor [YK 9->8]
- MT39 x10y9 kill redKnight [HP 198->174, G 2049->2114] (+65G)
- MT39 x8y10 open yellowDoor [YK 8->7]
- MT39 x7y11 move [DEF 222->226, G 2114->2199] (auto: x6y11 slimeMan, x5y9 swordsman, x6y9 blueGem)
- MT39 x4y10 open yellowDoor [YK 7->6]
- MT39 x3y10 move [YK 6->7, G 2199->2269] (auto: x3y9 ghostSkeleton, x2y10 ghostSkeleton, x3y11 yellowKey)
- MT39 x2y8 open blueDoor [BK 1->0]
- MT39 x4y2 open yellowDoor [YK 7->6]
- MT39 x6y4 open yellowDoor [YK 6->5]
- MT39 x11y11 pass upFloor
- after: HP=174 ATK=150 DEF=226 YK=5 BK=0 RK=0 G=2269 dmg=9952 door=133/14/3

### MT40

- before: HP=174 ATK=150 DEF=226 YK=5 BK=0 RK=0 G=2269 dmg=9952 door=133/14/3
- MT40 x9y11 move [G 2269->2369] (auto: x9y10 soldier, x10y9 swordsman)
- MT40 x2y1 中心飞行 centerFly
- MT40 x2y2 kill swordsman [G 2369->2774] (auto: x3y2 swordsman, x4y2 swordsman, x3y4 ghostSkeleton, x4y4 ghostSkeleton, x5y4 ghostSkeleton, x7y4 soldier, x8y4 soldier, x9y4 soldier) (+405G)
- MT40 x8y2 kill redKnight [HP 174->162, G 2774->2839] (+65G)
- MT40 x9y2 kill redKnight [HP 162->150, G 2839->2904] (+65G)
- MT40 x10y2 kill redKnight [HP 150->138, G 2904->2969] (+65G)
- MT40 x6y1 kill yellowKnight [G 2969->3069] (+100G)
- MT40 x5y7 move [ATK 150->162, DEF 226->238, YK 5->8] (auto: x7y4 blueGem, x8y4 blueGem, x9y4 blueGem, x2y2 yellowKey, x4y2 yellowKey, x8y2 redGem, x3y2 yellowKey, x9y2 redGem, x10y2 redGem)
- MT40 x6y7 pass
- MT40 x6y1 pass upFloor
- after: HP=138 ATK=162 DEF=238 YK=8 BK=0 RK=0 G=3069 dmg=9988 door=133/14/3
