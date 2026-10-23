# 当前最优 Walk (zone3, auto ON)

## 说明

- 本 walk 由 Game 类 (`scripts/search/zone3_game_route.py`, auto_sweep, strict_live_model) 离线推导生成。
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone3_game_route.json --load-slot <100+> --target-click-only`（统一点击 verifier，1-4 区通用；3 区起按需 `--set-auto battle=true,item=nopotion,wall=true`）
- 源 JSON：`outputs/results/2atk6def_39003_s1.json`

## 摘要

- final: HP=156 ATK=162 DEF=238 YK=4 BK=0 RK=0 G=2719 dmg=9920 door=129/13/3 MT41 x6y2

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
- MT16 x8y2 open yellowDoor [YK 3->2]
- MT16 x9y2 kill blackSlime [HP 529->627, G 804->824] (auto: x11y1 bigBat, x11y3 redPotion) (+20G)
- MT16 x10y4 open yellowDoor [YK 2->1]
- MT16 x10y5 kill zombie [HP 627->546, BK 0->1, G 824->854] (auto: x9y7 bigBat, x11y7 blueKey) (+30G)
- after: HP=546 ATK=70 DEF=58 YK=1 BK=1 RK=0 G=854 dmg=5630 door=85/7/1

### MT19

- before: HP=546 ATK=70 DEF=58 YK=1 BK=1 RK=0 G=854 dmg=5630 door=85/7/1
- MT19 x1y2 fly
- MT19 x3y8 kill blackSlime [HP 546->544, G 854->862] (+8G)
- MT19 x6y7 open blueDoor [BK 1->0]
- MT19 x7y6 kill rock [HP 544->166, YK 1->3, G 862->890] (auto: x8y5 yellowKey, x6y4 fakeWall, x4y5 yellowKey) (+28G)
- MT19 x6y3 pass fakeWall2
- after: HP=166 ATK=70 DEF=58 YK=3 BK=0 RK=0 G=890 dmg=6010 door=85/8/1

### MT17

- before: HP=166 ATK=70 DEF=58 YK=3 BK=0 RK=0 G=890 dmg=6010 door=85/8/1
- MT17 x6y2 fly
- MT17 x7y11 move [HP 166->266, G 890->902] (auto: x8y11 bigBat, x11y11 redPotion)
- after: HP=266 ATK=70 DEF=58 YK=3 BK=0 RK=0 G=902 dmg=6010 door=85/8/1

### MT15

- before: HP=266 ATK=70 DEF=58 YK=3 BK=0 RK=0 G=902 dmg=6010 door=85/8/1
- MT15 x6y2 fly
- MT15 x11y6 kill redPriest [HP 266->592, G 902->924] (auto: x11y8 bluePotion) (+22G)
- after: HP=592 ATK=70 DEF=58 YK=3 BK=0 RK=0 G=924 dmg=6084 door=85/8/1

### MT11

- before: HP=592 ATK=70 DEF=58 YK=3 BK=0 RK=0 G=924 dmg=6084 door=85/8/1
- MT11 x11y10 fly
- MT11 x7y7 open yellowDoor [YK 3->2]
- MT11 x8y7 kill blackSlime [HP 592->690, G 924->932] (auto: x9y6 redPotion) (+8G)
- after: HP=690 ATK=70 DEF=58 YK=2 BK=0 RK=0 G=932 dmg=6086 door=86/8/1

### MT14

- before: HP=690 ATK=70 DEF=58 YK=2 BK=0 RK=0 G=932 dmg=6086 door=86/8/1
- MT14 x11y10 fly
- after: HP=690 ATK=70 DEF=58 YK=2 BK=0 RK=0 G=932 dmg=6086 door=86/8/1

### MT12

- before: HP=690 ATK=70 DEF=58 YK=2 BK=0 RK=0 G=932 dmg=6086 door=86/8/1
- MT12 x2y11 fly
- MT12 x5y5 move [G 932->944] (auto: x11y5 bigBat)
- MT12 x3y10 open yellowDoor [YK 2->1]
- MT12 x3y9 kill zombie [HP 690->663, YK 1->4, BK 0->1, G 944->962] (auto: x2y8 blueKey, x2y7 yellowKey, x1y8 yellowKey, x1y7 yellowKey) (+18G)
- MT12 x4y5 open yellowDoor [YK 4->3]
- MT12 x2y5 kill redPriest [HP 663->589, G 962->984] (+22G)
- MT12 x1y4 open yellowDoor [YK 3->2]
- MT12 x2y3 move [G 984->996] (auto: x3y2 bigBat, x2y1 fakeWall)
- MT12 x1y1 trader redKey1 [RK 0->1, G 996->196]
- after: HP=589 ATK=70 DEF=58 YK=2 BK=1 RK=1 G=196 dmg=6187 door=89/8/1

### MT14

- before: HP=589 ATK=70 DEF=58 YK=2 BK=1 RK=1 G=196 dmg=6187 door=89/8/1
- MT14 x11y10 fly
- MT14 x10y8 kill blackSlime [HP 589->587, G 196->204] (+8G)
- MT14 x11y7 open yellowDoor [YK 2->1]
- MT14 x11y6 kill zombie [HP 587->660, G 204->234] (auto: x9y6 redPotion, x8y5 bigBat) (+30G)
- MT14 x4y8 kill zombie [HP 660->633, G 234->252] (+18G)
- MT14 x3y7 open yellowDoor [YK 1->0]
- MT14 x2y5 move [HP 633->733, G 252->264] (auto: x1y5 redPotion, x4y5 bigBat)
- MT14 x2y6 kill blackSlime [HP 733->731, G 264->272] (+8G)
- after: HP=731 ATK=70 DEF=58 YK=0 BK=1 RK=1 G=272 dmg=6245 door=91/8/1

### MT20

- before: HP=731 ATK=70 DEF=58 YK=0 BK=1 RK=1 G=272 dmg=6245 door=91/8/1
- MT20 x6y10 fly
- MT20 x6y9 open redDoor [RK 1->0]
- MT20 x6y8 pass
- MT20 x6y6 kill vampire [HP 731->26, G 272->416] (+144G)
- MT20 x6y5 move [HP 26->1226, ATK 70->76, DEF 58->64, YK 0->3] (auto: x6y4 yellowKey, x5y4 yellowKey, x7y4 yellowKey, x4y5 redGem, x8y5 blueGem, x4y6 redGem, x6y8 bluePotion, x8y6 blueGem, x4y7 redGem, x5y8 bluePotion, x7y8 bluePotion, x8y7 blueGem)
- MT20 x6y1 pass upFloor
- after: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2

### MT21

- before: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2
- MT21 x6y11 pass upFloor
- after: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2

### MT22

- before: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2
- MT22 x6y6 pass upFloor
- after: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2

### MT23

- before: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2
- MT23 x11y1 pass upFloor
- after: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2

### MT24

- before: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2
- MT24 x2y10 pass upFloor
- after: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2

### MT25

- before: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2
- MT25 x1y11 pass upFloor
- after: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2

### MT26

- before: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2
- MT26 x2y10 pass upFloor
- after: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2

### MT27

- before: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2
- MT27 x11y11 pass upFloor
- after: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2

### MT28

- before: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2
- MT28 x1y11 pass upFloor
- after: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2

### MT29

- before: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2
- MT29 x6y2 event thief
- MT29 x6y11 pass upFloor
- after: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2

### MT30

- before: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=416 dmg=6950 door=91/8/2
- MT30 x5y5 kill greenSlime [G 416->417] (+1G)
- MT30 x4y5 kill redSlime [G 417->419] (+2G)
- MT30 x3y5 kill blackSlime [G 419->427] (+8G)
- MT30 x7y5 kill greenSlime [G 427->428] (+1G)
- MT30 x8y5 kill redSlime [G 428->430] (+2G)
- MT30 x9y5 kill blackSlime [G 430->438] (+8G)
- MT30 x6y1 pass upFloor
- after: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=438 dmg=6950 door=91/8/2

### MT31

- before: HP=1226 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=438 dmg=6950 door=91/8/2
- MT31 x6y8 kill zombieKnight [HP 1226->1114, G 438->468] (+30G)
- MT31 x6y9 kill zombieKnight [HP 1114->1002, G 468->498] (+30G)
- MT31 x6y11 pass upFloor
- after: HP=1002 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=498 dmg=7174 door=91/8/2

### MT32

- before: HP=1002 ATK=76 DEF=64 YK=3 BK=1 RK=0 G=498 dmg=7174 door=91/8/2
- MT32 x6y10 pass [HP 1002->572, G 498->598] (auto: +100G)
- MT32 x8y10 设置自动：battle=true, item=nopotion, wall=true
- MT32 x8y11 kill ghostSkeleton [HP 572->108, G 598->633] (+35G)
- MT32 x10y10 shop def [DEF 64->80, G 633->553]
- MT32 x10y10 shop def [DEF 80->96, G 553->413]
- MT32 x10y10 shop def [DEF 96->112, G 413->193]
- after: HP=108 ATK=76 DEF=112 YK=3 BK=1 RK=0 G=193 dmg=8068 door=91/8/2

### MT11

- before: HP=108 ATK=76 DEF=112 YK=3 BK=1 RK=0 G=193 dmg=8068 door=91/8/2
- MT11 x11y10 fly
- MT11 x10y9 move [G 193->215] (auto: x8y5 redPriest)
- MT11 x11y11 pass upFloor
- after: HP=108 ATK=76 DEF=112 YK=3 BK=1 RK=0 G=215 dmg=8068 door=91/8/2

### MT12

- before: HP=108 ATK=76 DEF=112 YK=3 BK=1 RK=0 G=215 dmg=8068 door=91/8/2
- MT12 x2y11 move [G 215->263] (auto: x9y9 blackSlime, x10y3 zombie, x10y1 fakeWall, x5y3 redPriest)
- MT12 x1y11 pass upFloor
- after: HP=108 ATK=76 DEF=112 YK=3 BK=1 RK=0 G=263 dmg=8068 door=91/8/2

### MT13

- before: HP=108 ATK=76 DEF=112 YK=3 BK=1 RK=0 G=263 dmg=8068 door=91/8/2
- MT13 x11y11 pass upFloor
- after: HP=108 ATK=76 DEF=112 YK=3 BK=1 RK=0 G=263 dmg=8068 door=91/8/2

### MT14

- before: HP=108 ATK=76 DEF=112 YK=3 BK=1 RK=0 G=263 dmg=8068 door=91/8/2
- MT14 x1y6 move [G 263->313] (auto: x3y9 redPriest, x6y5 rock)
- MT14 x1y7 open yellowDoor [YK 3->2]
- MT14 x1y8 move [BK 1->2, G 313->335] (auto: x1y9 redPriest, x1y11 blueKey)
- MT14 x6y11 pass upFloor
- after: HP=108 ATK=76 DEF=112 YK=2 BK=2 RK=0 G=335 dmg=8068 door=92/8/2

### MT15

- before: HP=108 ATK=76 DEF=112 YK=2 BK=2 RK=0 G=335 dmg=8068 door=92/8/2
- MT15 x5y1 move [G 335->365] (auto: x3y3 blackSlime, x2y11 redPriest)
- MT15 x6y1 pass upFloor
- after: HP=108 ATK=76 DEF=112 YK=2 BK=2 RK=0 G=365 dmg=8068 door=92/8/2

### MT16

- before: HP=108 ATK=76 DEF=112 YK=2 BK=2 RK=0 G=365 dmg=8068 door=92/8/2
- MT16 x5y11 move [G 365->433] (auto: x3y6 rock, x5y3 zombie, x2y2 redPriest)
- MT16 x6y11 pass upFloor
- after: HP=108 ATK=76 DEF=112 YK=2 BK=2 RK=0 G=433 dmg=8068 door=92/8/2

### MT17

- before: HP=108 ATK=76 DEF=112 YK=2 BK=2 RK=0 G=433 dmg=8068 door=92/8/2
- MT17 x5y1 move [G 433->451] (auto: x5y7 zombie)
- MT17 x6y1 pass upFloor
- after: HP=108 ATK=76 DEF=112 YK=2 BK=2 RK=0 G=451 dmg=8068 door=92/8/2

### MT18

- before: HP=108 ATK=76 DEF=112 YK=2 BK=2 RK=0 G=451 dmg=8068 door=92/8/2
- MT18 x4y7 move [G 451->561] (auto: x10y7 rock, x3y5 rock, x1y5 rock, x10y2 blackSlime, x9y4 zombie)
- MT18 x4y8 open yellowDoor [YK 2->1]
- MT18 x4y8 move [YK 1->2, G 561->609] (auto: x4y9 bigBat, x4y10 bigBat, x5y9 bigBat, x5y10 bigBat, x5y11 yellowKey)
- MT18 x8y8 open yellowDoor [YK 2->1]
- MT18 x11y7 move [YK 1->2, G 609->641] (auto: x8y9 blackSlime, x7y9 blackSlime, x8y10 blackSlime, x7y10 blackSlime, x7y11 yellowKey)
- MT18 x11y8 open yellowDoor [YK 2->1]
- MT18 x11y8 move [DEF 112->114, YK 1->2, G 641->663] (auto: x11y9 redPriest, x10y10 yellowKey, x10y11 blueGem)
- MT18 x1y1 pass upFloor
- after: HP=108 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=663 dmg=8068 door=95/8/2

### MT19

- before: HP=108 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=663 dmg=8068 door=95/8/2
- MT19 x5y11 move [G 663->699] (auto: x11y5 blackSlime, x5y6 rock)
- MT19 x6y11 pass upFloor
- after: HP=108 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=699 dmg=8068 door=95/8/2

### MT20

- before: HP=108 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=699 dmg=8068 door=95/8/2
- MT20 x7y11 move [G 699->777] (auto: x8y11 redPriest, x10y10 rock, x2y10 rock)
- after: HP=108 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=777 dmg=8068 door=95/8/2

### MT32

- before: HP=108 ATK=76 DEF=114 YK=2 BK=2 RK=0 G=777 dmg=8068 door=95/8/2
- MT32 x6y11 fly
- MT32 x10y10 shop def [DEF 114->130, G 777->457]
- MT32 x10y10 shop def [DEF 130->146, G 457->17]
- after: HP=108 ATK=76 DEF=146 YK=2 BK=2 RK=0 G=17 dmg=8068 door=95/8/2

### MT10

- before: HP=108 ATK=76 DEF=146 YK=2 BK=2 RK=0 G=17 dmg=8068 door=95/8/2
- MT10 x6y10 fly
- MT10 x5y10 move [G 17->45] (auto: x3y6 skeleton, x2y7 skeletonSoldier, x10y7 skeletonSoldier, x11y6 skeleton)
- after: HP=108 ATK=76 DEF=146 YK=2 BK=2 RK=0 G=45 dmg=8068 door=95/8/2

### MT14

- before: HP=108 ATK=76 DEF=146 YK=2 BK=2 RK=0 G=45 dmg=8068 door=95/8/2
- MT14 x11y10 fly
- MT14 x9y4 move [G 45->75] (auto: x10y4 zombieKnight)
- MT14 x10y3 open yellowDoor [YK 2->1]
- MT14 x7y5 move [YK 1->5] (auto: x10y1 yellowKey, x11y2 yellowKey, x9y1 yellowKey, x11y1 yellowKey)
- MT14 x7y4 open yellowDoor [YK 5->4]
- MT14 x7y3 move [G 75->105] (auto: x7y2 zombieKnight)
- MT14 x7y1 take redPotion [HP 108->208, DEF 146->148, YK 4->5, G 105->113] (auto: x6y1 yellowKey, x5y1 blueGem, x5y2 blackSlime)
- after: HP=208 ATK=76 DEF=148 YK=5 BK=2 RK=0 G=113 dmg=8068 door=97/8/2

### MT15

- before: HP=208 ATK=76 DEF=148 YK=5 BK=2 RK=0 G=113 dmg=8068 door=97/8/2
- MT15 x6y10 fly
- MT15 x5y1 move [G 113->143] (auto: x2y1 zombieKnight)
- MT15 x6y1 pass upFloor
- after: HP=208 ATK=76 DEF=148 YK=5 BK=2 RK=0 G=143 dmg=8068 door=97/8/2

### MT16

- before: HP=208 ATK=76 DEF=148 YK=5 BK=2 RK=0 G=143 dmg=8068 door=97/8/2
- MT16 x5y11 move [G 143->173] (auto: x6y6 zombieKnight)
- MT16 x6y11 pass upFloor
- after: HP=208 ATK=76 DEF=148 YK=5 BK=2 RK=0 G=173 dmg=8068 door=97/8/2

### MT17

- before: HP=208 ATK=76 DEF=148 YK=5 BK=2 RK=0 G=173 dmg=8068 door=97/8/2
- MT17 x10y11 move [G 173->203] (auto: x5y3 zombieKnight)
- MT17 x10y10 open yellowDoor [YK 5->4]
- MT17 x9y8 kill zombie [G 203->221] (+18G)
- MT17 x11y8 kill zombie [G 221->239] (+18G)
- MT17 x9y5 kill zombieKnight [G 239->269] (+30G)
- MT17 x11y5 kill zombieKnight [G 269->299] (+30G)
- MT17 x10y3 move [ATK 76->78, DEF 148->150, YK 4->6] (auto: x9y3 yellowKey, x11y3 yellowKey, x9y1 redGem, x11y1 blueGem)
- MT17 x10y2 take bluePotion [HP 208->608]
- after: HP=608 ATK=78 DEF=150 YK=6 BK=2 RK=0 G=299 dmg=8068 door=98/8/2

### MT18

- before: HP=608 ATK=78 DEF=150 YK=6 BK=2 RK=0 G=299 dmg=8068 door=98/8/2
- MT18 x6y2 fly
- MT18 x1y2 move [G 299->329] (auto: x7y4 zombieKnight)
- MT18 x1y1 pass upFloor
- after: HP=608 ATK=78 DEF=150 YK=6 BK=2 RK=0 G=329 dmg=8068 door=98/8/2

### MT19

- before: HP=608 ATK=78 DEF=150 YK=6 BK=2 RK=0 G=329 dmg=8068 door=98/8/2
- MT19 x5y11 move [BK 2->3, G 329->471] (auto: x6y9 zombieKnight, x8y8 zombieKnight, x4y3 zombieKnight, x8y3 zombieKnight, x8y1 blueKey, x6y1 redPriest)
- MT19 x6y11 pass upFloor
- after: HP=608 ATK=78 DEF=150 YK=6 BK=3 RK=0 G=471 dmg=8068 door=98/8/2

### MT32

- before: HP=608 ATK=78 DEF=150 YK=6 BK=3 RK=0 G=471 dmg=8068 door=98/8/2
- MT32 x6y11 fly
- MT32 x3y1 open blueDoor [BK 3->2]
- MT32 x3y1 move [ATK 78->82, DEF 150->154] (auto: x1y1 blueGem, x2y2 redGem)
- MT32 x5y3 open yellowDoor [YK 6->5]
- MT32 x5y3 move [YK 5->6, G 471->531] (auto: x3y4 slimeMan, x4y5 slimeMan, x2y5 yellowKey)
- after: HP=608 ATK=82 DEF=154 YK=6 BK=2 RK=0 G=531 dmg=8068 door=99/9/2

### MT28

- before: HP=608 ATK=82 DEF=154 YK=6 BK=2 RK=0 G=531 dmg=8068 door=99/9/2
- MT28 x2y11 fly
- MT28 x8y4 trader specialTrader [YK 6->5, G 531->631] (auto: +100G)
- after: HP=608 ATK=82 DEF=154 YK=5 BK=2 RK=0 G=631 dmg=8068 door=99/9/2

### MT32

- before: HP=608 ATK=82 DEF=154 YK=5 BK=2 RK=0 G=631 dmg=8068 door=99/9/2
- MT32 x6y11 fly
- MT32 x10y10 shop def [DEF 154->170, G 631->51]
- MT32 x11y1 pass upFloor
- after: HP=608 ATK=82 DEF=170 YK=5 BK=2 RK=0 G=51 dmg=8068 door=99/9/2

### MT33

- before: HP=608 ATK=82 DEF=170 YK=5 BK=2 RK=0 G=51 dmg=8068 door=99/9/2
- MT33 x8y2 open yellowDoor [YK 5->4]
- MT33 x7y1 open yellowDoor [YK 4->3]
- MT33 x7y1 move [YK 3->4, G 51->111] (auto: x6y1 slimeMan, x4y1 zombieKnight, x6y3 yellowKey)
- MT33 x5y2 take redPotion [HP 608->808]
- MT33 x10y5 pass
- MT33 x9y5 kill ghostSkeleton [HP 808->768, G 111->146] (+35G)
- MT33 x11y5 kill ghostSkeleton [HP 768->728, G 146->181] (+35G)
- MT33 x11y7 kill soldier [HP 728->368, G 181->226] (+45G)
- MT33 x9y7 kill soldier [HP 368->8, G 226->271] (+45G)
- MT33 x9y10 move [ATK 82->122] (auto: x10y10 sword3)
- MT33 x3y1 open yellowDoor [YK 4->3]
- MT33 x1y1 pass upFloor
- after: HP=8 ATK=122 DEF=170 YK=3 BK=2 RK=0 G=271 dmg=8868 door=102/9/2

### MT34

- before: HP=8 ATK=122 DEF=170 YK=3 BK=2 RK=0 G=271 dmg=8868 door=102/9/2
- MT34 x3y1 take redPotion [HP 8->208, G 271->301] (auto: x2y3 slimeMan)
- MT34 x4y2 open yellowDoor [YK 3->2]
- MT34 x2y3 move [YK 2->3, G 301->331] (auto: x5y2 slimeMan, x6y1 yellowKey)
- MT34 x2y4 open yellowDoor [YK 3->2]
- MT34 x2y8 open yellowDoor [YK 2->1]
- after: HP=208 ATK=122 DEF=170 YK=1 BK=2 RK=0 G=331 dmg=8868 door=105/9/2

### MT2

- before: HP=208 ATK=122 DEF=170 YK=1 BK=2 RK=0 G=331 dmg=8868 door=105/9/2
- MT2 x1y10 fly
- MT2 x3y1 open blueDoor [BK 2->1]
- MT2 x6y2 kill blueGuard [HP 208->128, G 331->381] (+50G)
- MT2 x8y2 kill blueGuard [HP 128->48, G 381->431] (+50G)
- MT2 x10y4 move [YK 1->4] (auto: x4y4 yellowKey, x3y5 yellowKey, x3y4 yellowKey)
- MT2 x11y4 event oldman [G 431->1431] (auto: +1000G)
- MT2 x10y11 event thief
- MT2 x4y10 take bluePotion [HP 48->248]
- after: HP=248 ATK=122 DEF=170 YK=4 BK=1 RK=0 G=1431 dmg=9028 door=105/10/2

### MT34

- before: HP=248 ATK=122 DEF=170 YK=4 BK=1 RK=0 G=1431 dmg=9028 door=105/10/2
- MT34 x2y1 fly
- after: HP=248 ATK=122 DEF=170 YK=4 BK=1 RK=0 G=1431 dmg=9028 door=105/10/2

### MT32

- before: HP=248 ATK=122 DEF=170 YK=4 BK=1 RK=0 G=1431 dmg=9028 door=105/10/2
- MT32 x10y1 fly
- MT32 x10y10 shop atk [ATK 122->130, G 1431->691]
- MT32 x11y1 pass upFloor
- after: HP=248 ATK=130 DEF=170 YK=4 BK=1 RK=0 G=691 dmg=9028 door=105/10/2

### MT33

- before: HP=248 ATK=130 DEF=170 YK=4 BK=1 RK=0 G=691 dmg=9028 door=105/10/2
- MT33 x1y1 pass upFloor
- after: HP=248 ATK=130 DEF=170 YK=4 BK=1 RK=0 G=691 dmg=9028 door=105/10/2

### MT34

- before: HP=248 ATK=130 DEF=170 YK=4 BK=1 RK=0 G=691 dmg=9028 door=105/10/2
- MT34 x3y9 kill ghostSkeleton [HP 248->228, G 691->726] (+35G)
- after: HP=228 ATK=130 DEF=170 YK=4 BK=1 RK=0 G=726 dmg=9048 door=105/10/2

### MT32

- before: HP=228 ATK=130 DEF=170 YK=4 BK=1 RK=0 G=726 dmg=9048 door=105/10/2
- MT32 x10y1 fly
- after: HP=228 ATK=130 DEF=170 YK=4 BK=1 RK=0 G=726 dmg=9048 door=105/10/2

### MT28

- before: HP=228 ATK=130 DEF=170 YK=4 BK=1 RK=0 G=726 dmg=9048 door=105/10/2
- MT28 x2y11 fly
- MT28 x8y4 trader specialTrader [YK 4->3, G 726->826] (auto: +100G)
- MT28 x8y4 trader specialTrader [YK 3->2, G 826->926] (auto: +100G)
- after: HP=228 ATK=130 DEF=170 YK=2 BK=1 RK=0 G=926 dmg=9048 door=105/10/2

### MT32

- before: HP=228 ATK=130 DEF=170 YK=2 BK=1 RK=0 G=926 dmg=9048 door=105/10/2
- MT32 x6y11 fly
- MT32 x10y10 shop atk [ATK 130->138, G 926->6]
- after: HP=228 ATK=138 DEF=170 YK=2 BK=1 RK=0 G=6 dmg=9048 door=105/10/2

### MT34

- before: HP=228 ATK=138 DEF=170 YK=2 BK=1 RK=0 G=6 dmg=9048 door=105/10/2
- MT34 x2y1 fly
- MT34 x4y10 open yellowDoor [YK 2->1]
- MT34 x8y10 open yellowDoor [YK 1->0]
- MT34 x9y10 kill soldier [HP 228->168, ATK 138->142, YK 0->1, G 6->51] (auto: x10y11 yellowKey, x11y11 redGem) (+45G)
- after: HP=168 ATK=142 DEF=170 YK=1 BK=1 RK=0 G=51 dmg=9108 door=107/10/2

### MT31

- before: HP=168 ATK=142 DEF=170 YK=1 BK=1 RK=0 G=51 dmg=9108 door=107/10/2
- MT31 x6y10 fly
- MT31 x10y6 kill ghostSkeleton [HP 168->158, G 51->86] (+35G)
- MT31 x11y7 open yellowDoor [YK 1->0]
- MT31 x10y8 move [YK 0->4, G 86->146] (auto: x10y9 slimeMan, x9y10 yellowKey, x11y10 slimeMan, x8y10 yellowKey, x9y11 yellowKey, x8y11 yellowKey)
- MT31 x11y5 open yellowDoor [YK 4->3]
- MT31 x10y3 kill ghostSkeleton [HP 158->148, G 146->181] (+35G)
- MT31 x8y2 kill soldier [HP 148->88, G 181->226] (+45G)
- MT31 x8y3 open yellowDoor [YK 3->2]
- MT31 x8y3 move [ATK 142->146] (auto: x8y4 redGem)
- after: HP=88 ATK=146 DEF=170 YK=2 BK=1 RK=0 G=226 dmg=9188 door=110/10/2

### MT32

- before: HP=88 ATK=146 DEF=170 YK=2 BK=1 RK=0 G=226 dmg=9188 door=110/10/2
- MT32 x6y11 fly
- MT32 x3y10 kill blueGuard [HP 88->68, G 226->276] (+50G)
- MT32 x1y10 kill blueGuard [HP 68->48, G 276->326] (+50G)
- MT32 x3y8 move [YK 2->6, BK 1->2] (auto: x3y7 yellowKey, x4y8 blueKey, x2y7 yellowKey, x4y7 yellowKey, x1y7 yellowKey)
- after: HP=48 ATK=146 DEF=170 YK=6 BK=2 RK=0 G=326 dmg=9228 door=110/10/2

### MT14

- before: HP=48 ATK=146 DEF=170 YK=6 BK=2 RK=0 G=326 dmg=9228 door=110/10/2
- MT14 x6y10 fly
- MT14 x2y4 open blueDoor [BK 2->1]
- MT14 x2y3 move [G 326->416] (auto: x2y2 zombieKnight, x1y1 zombieKnight, x3y1 zombieKnight)
- MT14 x2y2 move [RK 0->1] (auto: x1y3 redKey)
- after: HP=48 ATK=146 DEF=170 YK=6 BK=1 RK=1 G=416 dmg=9228 door=110/11/2

### MT2

- before: HP=48 ATK=146 DEF=170 YK=6 BK=1 RK=1 G=416 dmg=9228 door=110/11/2
- MT2 x1y10 fly
- MT2 x3y10 take bluePotion [HP 48->248]
- MT2 x3y11 take bluePotion [HP 248->448]
- after: HP=448 ATK=146 DEF=170 YK=6 BK=1 RK=1 G=416 dmg=9228 door=110/11/2

### MT34

- before: HP=448 ATK=146 DEF=170 YK=6 BK=1 RK=1 G=416 dmg=9228 door=110/11/2
- MT34 x2y1 fly
- MT34 x6y11 pass upFloor
- after: HP=448 ATK=146 DEF=170 YK=6 BK=1 RK=1 G=416 dmg=9228 door=110/11/2

### MT35

- before: HP=448 ATK=146 DEF=170 YK=6 BK=1 RK=1 G=416 dmg=9228 door=110/11/2
- MT35 x11y1 pass upFloor
- after: HP=448 ATK=146 DEF=170 YK=6 BK=1 RK=1 G=416 dmg=9228 door=110/11/2

### MT36

- before: HP=448 ATK=146 DEF=170 YK=6 BK=1 RK=1 G=416 dmg=9228 door=110/11/2
- MT36 x10y1 move [G 416->446] (auto: x11y3 slimeMan)
- MT36 x9y1 kill redKnight [HP 448->268, G 446->541] (auto: x7y1 zombieKnight) (+95G)
- MT36 x6y2 open yellowDoor [YK 6->5]
- MT36 x6y5 kill ghostSkeleton [HP 268->258, G 541->636] (auto: x5y6 slimeMan, x7y6 slimeMan) (+95G)
- MT36 x10y6 open yellowDoor [YK 5->4]
- MT36 x11y7 kill redKnight [HP 258->78, G 636->701] (+65G)
- MT36 x11y11 pass upFloor
- after: HP=78 ATK=146 DEF=170 YK=4 BK=1 RK=1 G=701 dmg=9598 door=112/11/2

### MT37

- before: HP=78 ATK=146 DEF=170 YK=4 BK=1 RK=1 G=701 dmg=9598 door=112/11/2
- MT37 x9y11 kill ghostSkeleton [HP 78->68, G 701->766] (auto: x3y11 slimeMan) (+65G)
- MT37 x1y9 kill soldier [HP 68->8, G 766->811] (+45G)
- MT37 x1y6 take redPotion [HP 8->208]
- MT37 x1y3 open blueDoor [BK 1->0]
- MT37 x1y1 pass upFloor
- after: HP=208 ATK=146 DEF=170 YK=4 BK=0 RK=1 G=811 dmg=9668 door=112/12/2

### MT38

- before: HP=208 ATK=146 DEF=170 YK=4 BK=0 RK=1 G=811 dmg=9668 door=112/12/2
- MT38 x3y1 open redDoor [RK 1->0]
- MT38 x3y1 move [YK 4->5, G 811->871] (auto: x4y1 slimeMan, x6y2 yellowKey, x8y1 slimeMan)
- MT38 x5y2 trader yellowKey3 [YK 5->8, G 871->671]
- MT38 x9y1 open yellowDoor [YK 8->7]
- MT38 x11y1 pass upFloor
- after: HP=208 ATK=146 DEF=170 YK=7 BK=0 RK=0 G=671 dmg=9668 door=113/12/3

### MT39

- before: HP=208 ATK=146 DEF=170 YK=7 BK=0 RK=0 G=671 dmg=9668 door=113/12/3
- MT39 x10y3 move [YK 7->8] (auto: x11y3 yellowKey)
- MT39 x10y4 open yellowDoor [YK 8->7]
- MT39 x9y5 move [G 671->701] (auto: x9y6 slimeMan)
- MT39 x11y7 kill ghostSkeleton [HP 208->198, ATK 146->150, G 701->736] (auto: x11y6 redGem) (+35G)
- MT39 x11y1 pass downFloor
- after: HP=198 ATK=150 DEF=170 YK=7 BK=0 RK=0 G=736 dmg=9678 door=114/12/3

### MT38

- before: HP=198 ATK=150 DEF=170 YK=7 BK=0 RK=0 G=736 dmg=9678 door=114/12/3
- MT38 x7y3 open yellowDoor [YK 7->6]
- MT38 x7y6 kill ghostSkeleton [HP 198->188, G 736->826] (auto: x7y7 swordsman) (+90G)
- MT38 x6y8 take redPotion [HP 188->388, DEF 170->174] (auto: x5y8 blueGem)
- MT38 x11y3 open yellowDoor [YK 6->5]
- MT38 x11y6 kill ghostSkeleton [HP 388->382, G 826->861] (+35G)
- MT38 x11y8 open yellowDoor [YK 5->4]
- MT38 x11y9 kill ghostSkeleton [HP 382->376, YK 4->5, G 861->896] (auto: x9y9 yellowKey) (+35G)
- MT38 x9y11 kill soldier [HP 376->324, G 896->941] (+45G)
- MT38 x8y11 open yellowDoor [YK 5->4]
- MT38 x8y11 move [G 941->1014] (auto: x7y11 zombie, x5y11 swordsman)
- MT38 x4y11 open yellowDoor [YK 4->3]
- MT38 x3y10 kill blueGuard [HP 324->312, G 1014->1064] (+50G)
- MT38 x1y10 kill blueGuard [HP 312->300, G 1064->1114] (+50G)
- MT38 x1y7 move [DEF 174->214, G 1114->1239] (auto: x2y7 shield3, x1y3 ghostSkeleton, x2y5 flower, x3y4 soldier, x4y4 soldier)
- MT38 x11y1 pass upFloor
- after: HP=300 ATK=150 DEF=214 YK=3 BK=0 RK=0 G=1239 dmg=9776 door=119/12/3

### MT39

- before: HP=300 ATK=150 DEF=214 YK=3 BK=0 RK=0 G=1239 dmg=9776 door=119/12/3
- MT39 x10y7 move [G 1239->1284] (auto: x11y5 soldier)
- MT39 x10y8 open yellowDoor [YK 3->2]
- MT39 x10y9 kill redKnight [HP 300->252, G 1284->1349] (+65G)
- MT39 x8y10 open yellowDoor [YK 2->1]
- MT39 x7y11 move [DEF 214->218, G 1349->1434] (auto: x6y11 slimeMan, x5y9 swordsman, x6y9 blueGem)
- MT39 x4y10 open yellowDoor [YK 1->0]
- MT39 x3y10 move [YK 0->1, G 1434->1504] (auto: x3y9 ghostSkeleton, x2y10 ghostSkeleton, x3y11 yellowKey)
- after: HP=252 ATK=150 DEF=218 YK=1 BK=0 RK=0 G=1504 dmg=9824 door=122/12/3

### MT31

- before: HP=252 ATK=150 DEF=218 YK=1 BK=0 RK=0 G=1504 dmg=9824 door=122/12/3
- MT31 x6y10 fly
- MT31 x3y6 move [G 1504->1574] (auto: x2y6 ghostSkeleton, x11y3 ghostSkeleton)
- MT31 x1y5 open yellowDoor [YK 1->0]
- MT31 x1y3 move [YK 0->4, G 1574->1674] (auto: x1y2 swordsman, x2y3 soldier, x3y2 yellowKey, x3y1 yellowKey, x4y2 yellowKey, x4y1 yellowKey)
- MT31 x3y4 open yellowDoor [YK 4->3]
- MT31 x1y6 move [BK 0->1] (auto: x4y4 blueKey)
- MT31 x1y7 open yellowDoor [YK 3->2]
- MT31 x2y8 move [G 1674->1744] (auto: x2y9 ghostSkeleton, x1y9 ghostSkeleton)
- MT31 x4y10 kill redKnight [HP 252->216, G 1744->1809] (+65G)
- MT31 x4y9 open yellowDoor [YK 2->1]
- MT31 x6y10 move [DEF 218->222] (auto: x4y8 blueGem)
- MT31 x6y11 pass upFloor
- after: HP=216 ATK=150 DEF=222 YK=1 BK=1 RK=0 G=1809 dmg=9860 door=126/12/3

### MT32

- before: HP=216 ATK=150 DEF=222 YK=1 BK=1 RK=0 G=1809 dmg=9860 door=126/12/3
- MT32 x6y3 move [G 1809->1854] (auto: x1y4 soldier)
- after: HP=216 ATK=150 DEF=222 YK=1 BK=1 RK=0 G=1854 dmg=9860 door=126/12/3

### MT34

- before: HP=216 ATK=150 DEF=222 YK=1 BK=1 RK=0 G=1854 dmg=9860 door=126/12/3
- MT34 x2y1 fly
- MT34 x6y2 move [G 1854->1954] (auto: x1y10 swordsman, x2y11 soldier)
- MT34 x7y2 kill redKnight [HP 216->192, G 1954->2019] (+65G)
- MT34 x8y2 open yellowDoor [YK 1->0]
- MT34 x5y11 move [DEF 222->226, YK 0->3] (auto: x9y1 yellowKey, x10y2 yellowKey, x10y1 yellowKey, x11y1 blueGem)
- MT34 x6y11 pass upFloor
- after: HP=192 ATK=150 DEF=226 YK=3 BK=1 RK=0 G=2019 dmg=9884 door=127/12/3

### MT39

- before: HP=192 ATK=150 DEF=226 YK=3 BK=1 RK=0 G=2019 dmg=9884 door=127/12/3
- MT39 x11y2 fly
- MT39 x2y8 open blueDoor [BK 1->0]
- MT39 x4y2 open yellowDoor [YK 3->2]
- MT39 x6y4 open yellowDoor [YK 2->1]
- MT39 x4y4 take centerFly3
- MT39 x11y11 pass upFloor
- after: HP=192 ATK=150 DEF=226 YK=1 BK=0 RK=0 G=2019 dmg=9884 door=129/13/3

### MT40

- before: HP=192 ATK=150 DEF=226 YK=1 BK=0 RK=0 G=2019 dmg=9884 door=129/13/3
- MT40 x2y1 中心飞行 centerFly
- MT40 x5y1 move [G 2019->2424] (auto: x4y2 swordsman, x3y2 swordsman, x5y4 ghostSkeleton, x2y2 swordsman, x4y4 ghostSkeleton, x3y4 ghostSkeleton, x7y4 soldier, x8y4 soldier, x9y4 soldier)
- MT40 x6y1 kill yellowKnight [G 2424->2524] (+100G)
- MT40 x8y2 kill redKnight [HP 192->180, G 2524->2589] (+65G)
- MT40 x9y2 kill redKnight [HP 180->168, G 2589->2654] (+65G)
- MT40 x10y2 kill redKnight [HP 168->156, G 2654->2719] (+65G)
- MT40 x6y7 pass
- MT40 x5y1 move [ATK 150->162, DEF 226->238, YK 1->4] (auto: x4y2 yellowKey, x3y2 yellowKey, x2y2 yellowKey, x8y2 redGem, x7y4 blueGem, x9y2 redGem, x8y4 blueGem, x10y2 redGem, x9y4 blueGem)
- MT40 x6y1 pass upFloor
- after: HP=156 ATK=162 DEF=238 YK=4 BK=0 RK=0 G=2719 dmg=9920 door=129/13/3
