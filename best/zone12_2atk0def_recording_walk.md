# 当前最优 Walk (zone12, auto ON)

## 说明

- 本 walk 由用户手玩录像 (2攻0防 KILL 线, 杀 zKnight 不买 800 红钥匙) 经 scripts/search/recording_to_game.py 转换为 Game 类格式：逐格 captured path + PRE-state statlog 校验 0 mismatch + 走门格移除/零效果 move 剪枝/U 型折返提升。358 步, auto ON 全开, strict_live_model, times1=2。当前 zone1-2 最优 (converter 主产物)。
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone12_2atk0def_recording_walk.json --load-slot 1 --target-click-only --set-auto battle=true,item=true,wall=true`
- 源 JSON：`outputs/results/zone12_2atk0def_recording_walk.json`

## 摘要

- final: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=7111 door=91/10/2 MT20 x6y5

## Walk

### MT4

- before: HP=926 ATK=10 DEF=10 YK=4 BK=1 RK=0 G=7 dmg=0 door=0/0/0
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
- MT5 x9y11 pass [ATK 10->20] (auto: x9y11 fakeWall, x11y11 sword1)
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
- MT8 x5y4 pass [YK 0->3] (auto: x5y4 yellowKey, x4y4 yellowKey, x3y4 yellowKey)
- MT8 x6y1 pass upFloor
- after: HP=124 ATK=22 DEF=10 YK=3 BK=1 RK=0 G=64 dmg=902 door=19/0/0

### MT9

- before: HP=124 ATK=22 DEF=10 YK=3 BK=1 RK=0 G=64 dmg=902 door=19/0/0
- MT9 x8y1 open yellowDoor [YK 3->2]
- MT9 x9y1 kill greenSlime [HP 124->166, DEF 10->20, G 64->65] (auto: x11y1 redPotion, x10y5 fakeWall, x9y7 shield1) (+1G)
- MT9 x9y4 open yellowDoor [YK 2->1, G 65->66] (auto: x10y2 greenSlime)
- MT9 x8y4 open yellowDoor [YK 1->0]
- MT9 x8y4 pass [ATK 22->23, YK 0->2, G 66->68] (auto: x7y4 yellowKey, x5y4 yellowKey, x6y5 redGem, x7y6 redSlime)
- MT9 x4y5 open yellowDoor [YK 2->1]
- MT9 x3y5 kill bat [HP 166->148, DEF 20->21, YK 1->2, G 68->71] (auto: x2y4 yellowKey, x1y5 blueGem) (+3G)
- after: HP=148 ATK=23 DEF=21 YK=2 BK=1 RK=0 G=71 dmg=928 door=23/0/0

### MT6

- before: HP=148 ATK=23 DEF=21 YK=2 BK=1 RK=0 G=71 dmg=928 door=23/0/0
- MT6 x11y10 fly
- MT6 x5y11 kill skeleton [HP 148->206, G 71->80] (auto: x2y11 greenSlime, x9y9 redSlime, x9y11 redPotion, x8y11 redPotion) (+9G)
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
- MT8 x7y5 kill bluePriest [HP 193->166, G 91->97] (auto: x7y2 greenSlime) (+6G)
- MT8 x7y7 kill bat [HP 166->151, G 97->100] (+3G)
- MT8 x6y8 kill skeleton [HP 151->113, G 100->106] (+6G)
- MT8 x4y8 kill bat [HP 113->98, G 106->109] (+3G)
- MT8 x1y9 open yellowDoor [YK 1->0]
- MT8 x1y10 pass [G 109->110] (auto: x1y10 greenSlime)
- MT8 x2y11 kill bat [HP 98->83, G 110->113] (+3G)
- MT8 x3y11 open blueDoor [BK 1->0]
- MT8 x4y11 pass [ATK 23->24, DEF 23->24, YK 0->2] (auto: x4y11 yellowKey, x4y10 redGem, x5y11 blueGem, x5y10 yellowKey)
- after: HP=83 ATK=24 DEF=24 YK=2 BK=0 RK=0 G=113 dmg=1143 door=26/1/0

### MT1

- before: HP=83 ATK=24 DEF=24 YK=2 BK=0 RK=0 G=113 dmg=1143 door=26/1/0
- MT1 x2y1 fly
- MT1 x6y6 open yellowDoor [YK 2->1]
- MT1 x7y6 kill bat [HP 83->69, G 113->116] (+3G)
- MT1 x8y6 kill bluePriest [HP 69->45, G 116->121] (+5G)
- MT1 x9y6 kill bat [HP 45->31, G 121->124] (+3G)
- MT1 x9y5 open yellowDoor [YK 1->0]
- MT1 x8y4 pass [HP 31->81, ATK 24->25, DEF 24->25, YK 0->1] (auto: x8y4 redPotion, x8y3 yellowKey, x7y4 blueGem, x7y3 redGem)
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
- MT5 x2y7 kill skeletonSoldier [HP 97->66, DEF 25->26, YK 1->2, G 130->139] (auto: x2y9 yellowKey, x1y9 blueGem, x3y9 redPotion, x4y9 wand, x9y2 greenSlime) (+9G)
- MT5 x1y11 pass downFloor
- after: HP=66 ATK=26 DEF=26 YK=2 BK=0 RK=0 G=139 dmg=1310 door=29/1/0

### MT4

- before: HP=66 ATK=26 DEF=26 YK=2 BK=0 RK=0 G=139 dmg=1310 door=29/1/0
- MT4 x2y5 kill bluePriest [HP 66->48, G 139->146] (auto: x4y11 greenSlime, x8y11 greenSlime) (+7G)
- MT4 x2y4 open yellowDoor [YK 2->1]
- MT4 x2y1 pass [HP 48->98, YK 1->2, BK 0->1] (auto: x2y1 blueKey, x1y2 redPotion, x3y2 yellowKey)
- after: HP=98 ATK=26 DEF=26 YK=2 BK=1 RK=0 G=146 dmg=1328 door=30/1/0

### MT9

- before: HP=98 ATK=26 DEF=26 YK=2 BK=1 RK=0 G=146 dmg=1328 door=30/1/0
- MT9 x6y2 fly
- MT9 x7y10 kill bat [HP 98->86, G 146->149] (+3G)
- MT9 x6y11 open yellowDoor [YK 2->1]
- MT9 x3y11 open blueDoor [BK 1->0]
- MT9 x2y10 pass [HP 86->136] (auto: x2y10 redPotion)
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
- MT10 x11y9 pass [HP 178->378] (auto: x11y11 bluePotion)
- after: HP=378 ATK=27 DEF=27 YK=2 BK=0 RK=0 G=188 dmg=1548 door=36/2/0

### MT7

- before: HP=378 ATK=27 DEF=27 YK=2 BK=0 RK=0 G=188 dmg=1548 door=36/2/0
- MT7 x1y2 fly
- MT7 x7y7 open yellowDoor [YK 2->1]
- MT7 x7y9 pass [G 188->190] (auto: x7y9 redSlime)
- MT7 x7y10 kill bluePriest [HP 378->563, G 190->195] (auto: x7y11 bluePotion) (+5G)
- MT7 x1y1 pass upFloor
- after: HP=563 ATK=27 DEF=27 YK=1 BK=0 RK=0 G=195 dmg=1563 door=37/2/0

### MT8

- before: HP=563 ATK=27 DEF=27 YK=1 BK=0 RK=0 G=195 dmg=1563 door=37/2/0
- MT8 x8y8 kill bluePriest [HP 563->548, G 195->200] (+5G)
- MT8 x10y7 open yellowDoor [YK 1->0]
- MT8 x9y5 kill yellowGuard [HP 548->359, G 200->212] (+12G)
- MT8 x11y5 kill yellowGuard [HP 359->170, G 212->224] (+12G)
- MT8 x10y2 pass [HP 170->420, YK 0->2, RK 0->1] (auto: x10y2 redKey, x9y3 bluePotion, x11y3 redPotion, x9y1 yellowKey, x11y1 yellowKey)
- after: HP=420 ATK=27 DEF=27 YK=2 BK=0 RK=1 G=224 dmg=1956 door=38/2/0

### MT1

- before: HP=420 ATK=27 DEF=27 YK=2 BK=0 RK=1 G=224 dmg=1956 door=38/2/0
- MT1 x2y1 fly
- MT1 x10y9 open yellowDoor [YK 2->1]
- MT1 x10y10 kill bat [HP 420->609, G 224->229] (auto: x10y11 bluePotion, x9y11 greenSlime, x11y11 greenSlime) (+5G)
- MT1 x4y3 open yellowDoor [YK 1->0]
- MT1 x1y3 pass [HP 609->659] (auto: x1y3 redPotion)
- after: HP=659 ATK=27 DEF=27 YK=0 BK=0 RK=1 G=229 dmg=1967 door=40/2/0

### MT10

- before: HP=659 ATK=27 DEF=27 YK=0 BK=0 RK=1 G=229 dmg=1967 door=40/2/0
- MT10 x1y10 fly
- MT10 x6y9 open redDoor [RK 1->0]
- MT10 x6y5 pass (触发: 10F boss spawn)
- MT10 x6y4 kill skeletonSoldier [HP 659->584, G 229->237] (+8G)
- MT10 x5y4 kill skeleton [HP 584->554, G 237->243] (+6G)
- MT10 x4y4 open specialDoor
- MT10 x5y5 kill skeleton [HP 554->524, G 243->249] (+6G)
- MT10 x5y6 kill skeleton [HP 524->494, G 249->255] (+6G)
- MT10 x6y6 kill skeletonSoldier [HP 494->419, G 255->263] (+8G)
- MT10 x7y6 kill skeleton [HP 419->389, G 263->269] (+6G)
- MT10 x7y5 kill skeleton [HP 389->359, G 269->275] (+6G)
- MT10 x7y4 kill skeleton [HP 359->329, G 275->281] (+6G)
- MT10 x6y2 pass (触发: 队长剧情对话)
- MT10 x6y1 kill skeletonCaptain [HP 329->25, G 281->311] (+30G)
- MT10 x6y9 pass [HP 25->625, ATK 27->30, DEF 27->30, YK 0->3] (auto: x3y4 bluePotion, x9y4 yellowKey, x3y3 redGem, x2y4 bluePotion, x9y3 blueGem, x10y4 yellowKey, x2y3 redGem, x1y4 bluePotion, x10y3 blueGem, x11y4 yellowKey, x1y3 redGem, x11y3 blueGem)
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
- MT12 x4y11 pass [G 257->260] (auto: x4y11 bat)
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
- MT14 x6y9 pass [HP 719->819] (auto: x6y9 fakeWall, x5y10 redPotion)
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
- MT15 x9y11 pass [G 228->234] (auto: x9y11 bat, x10y10 bat)
- MT15 x11y11 trader blueKey1_15 [BK 0->1, G 234->34]
- MT15 x9y9 open yellowDoor [YK 4->3]
- MT15 x9y6 open yellowDoor [YK 3->2]
- MT15 x9y4 kill bigBat [HP 775->705, G 34->46] (+12G)
- MT15 x11y3 open yellowDoor [YK 2->1]
- MT15 x11y2 kill blackSlime [HP 705->615, G 46->54] (+8G)
- MT15 x9y1 pass thief (触发: 小偷对话开门)
- MT15 x6y1 pass upFloor
- after: HP=615 ATK=38 DEF=30 YK=1 BK=1 RK=0 G=54 dmg=2911 door=47/2/1

### MT16

- before: HP=615 ATK=38 DEF=30 YK=1 BK=1 RK=0 G=54 dmg=2911 door=47/2/1
- MT16 x7y3 pass [YK 1->2] (auto: x7y3 yellowKey)
- MT16 x6y4 open blueDoor [BK 1->0]
- MT16 x5y5 pass [HP 615->715, YK 2->3] (auto: x5y5 redPotion, x7y7 yellowKey)
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
- MT17 x2y2 pass [ATK 40->60] (auto: x2y2 sword2)
- after: HP=629 ATK=60 DEF=32 YK=2 BK=0 RK=0 G=122 dmg=3197 door=50/3/1

### MT6

- before: HP=629 ATK=60 DEF=32 YK=2 BK=0 RK=0 G=122 dmg=3197 door=50/3/1
- MT6 x11y10 fly
- MT6 x7y1 pass [YK 2->3, G 122->139] (auto: x8y6 skeleton, x7y1 bluePriest, x9y1 yellowKey, x10y1 greenSlime, x1y8 bluePriest)
- MT6 x11y2 open yellowDoor [YK 3->2]
- MT6 x11y4 pass [HP 629->679, G 139->148] (auto: x10y3 skeleton, x11y4 bat, x8y3 redPotion)
- MT6 x8y4 trader blueKey1 [BK 0->1, G 148->98]
- after: HP=679 ATK=60 DEF=32 YK=2 BK=1 RK=0 G=98 dmg=3197 door=51/3/1

### MT11

- before: HP=679 ATK=60 DEF=32 YK=2 BK=1 RK=0 G=98 dmg=3197 door=51/3/1
- MT11 x6y10 fly
- MT11 x5y9 open yellowDoor [YK 2->1]
- MT11 x4y9 kill blackSlime [HP 679->623, YK 1->6, G 98->106] (auto: x4y11 yellowKey, x3y11 yellowKey, x1y10 yellowKey, x2y11 yellowKey, x1y11 yellowKey) (+8G)
- MT11 x2y9 kill bigBat [HP 623->555, G 106->118] (+12G)
- MT11 x2y8 open blueDoor [BK 1->0]
- MT11 x1y5 kill redPriest [HP 555->766, G 118->140] (auto: x1y7 bluePotion) (+22G)
- MT11 x3y5 kill redPriest [HP 766->577, G 140->162] (+22G)
- MT11 x2y2 pass [DEF 32->52] (auto: x2y2 shield2)
- after: HP=577 ATK=60 DEF=52 YK=6 BK=0 RK=0 G=162 dmg=3699 door=52/4/1

### MT8

- before: HP=577 ATK=60 DEF=52 YK=6 BK=0 RK=0 G=162 dmg=3699 door=52/4/1
- MT8 x6y2 fly
- MT8 x11y9 open yellowDoor [YK 6->5]
- MT8 x11y10 pass [G 162->176] (auto: x11y10 skeleton, x10y11 skeletonSoldier)
- MT8 x9y11 open yellowDoor [YK 5->4]
- MT8 x8y10 pass [HP 577->627, YK 4->5, BK 0->1] (auto: x8y10 redPotion, x7y11 yellowKey, x7y10 blueKey)
- after: HP=627 ATK=60 DEF=52 YK=5 BK=1 RK=0 G=176 dmg=3699 door=54/4/1

### MT4

- before: HP=627 ATK=60 DEF=52 YK=5 BK=1 RK=0 G=176 dmg=3699 door=54/4/1
- MT4 x1y10 fly
- MT4 x4y5 open yellowDoor [YK 5->4]
- MT4 x6y5 pass [G 176->184] (auto: x6y5 redSlime, x9y5 skeleton)
- MT4 x10y4 open yellowDoor [YK 4->3]
- MT4 x10y3 pass [HP 627->827, YK 3->4, G 184->192] (auto: x10y3 skeletonSoldier, x9y2 yellowKey, x11y2 bluePotion)
- MT4 x11y11 pass downFloor
- after: HP=827 ATK=60 DEF=52 YK=4 BK=1 RK=0 G=192 dmg=3699 door=56/4/1

### MT3

- before: HP=827 ATK=60 DEF=52 YK=4 BK=1 RK=0 G=192 dmg=3699 door=56/4/1
- MT3 x9y8 open yellowDoor [YK 4->3]
- MT3 x10y8 pass [HP 827->877, YK 3->4, G 192->197] (auto: x10y8 bluePriest, x11y8 yellowKey, x11y7 redPotion)
- after: HP=877 ATK=60 DEF=52 YK=4 BK=1 RK=0 G=197 dmg=3699 door=57/4/1

### MT1

- before: HP=877 ATK=60 DEF=52 YK=4 BK=1 RK=0 G=197 dmg=3699 door=57/4/1
- MT1 x2y1 fly
- MT1 x2y4 pass [G 197->203] (auto: x2y4 skeleton)
- MT1 x2y5 open yellowDoor [YK 4->3]
- MT1 x2y7 pass [YK 3->4, G 203->211] (auto: x1y6 yellowKey, x2y7 skeletonSoldier)
- MT1 x2y8 open yellowDoor [YK 4->3]
- MT1 x2y11 pass [HP 877->977, YK 3->5] (auto: x1y10 redPotion, x2y11 fly, x3y10 yellowKey, x1y11 redPotion, x3y11 yellowKey)
- after: HP=977 ATK=60 DEF=52 YK=5 BK=1 RK=0 G=211 dmg=3699 door=59/4/1

### MT9

- before: HP=977 ATK=60 DEF=52 YK=5 BK=1 RK=0 G=211 dmg=3699 door=59/4/1
- MT9 x6y2 fly
- MT9 x8y11 open yellowDoor [G 211->239] (auto: x11y6 skeletonSoldier, x1y3 skeletonSoldier, x5y10 skeleton, x2y2 yellowKey, x3y1 skeleton)
- MT9 x9y11 pass [HP 977->1027, YK 5->6, G 239->255] (auto: x9y11 bluePriest, x9y9 yellowKey, x10y10 skeleton, x11y11 redPotion, x11y9 bluePriest)
- MT9 x1y9 open yellowDoor [YK 6->5]
- MT9 x1y8 pass [YK 5->6, G 255->263] (auto: x1y8 skeletonSoldier, x1y7 yellowKey)
- MT9 x3y7 open yellowDoor [YK 6->5]
- MT9 x4y7 pass [YK 5->6, G 263->271] (auto: x4y7 skeletonSoldier, x5y7 yellowKey)
- after: HP=1027 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=271 dmg=3699 door=62/4/1

### MT15

- before: HP=1027 ATK=60 DEF=52 YK=6 BK=1 RK=0 G=271 dmg=3699 door=62/4/1
- MT15 x6y10 fly
- MT15 x4y1 open yellowDoor [YK 6->5]
- MT15 x1y2 kill zombie [HP 1027->895, DEF 52->54, G 271->289] (auto: x1y1 blueGem) (+18G)
- after: HP=895 ATK=60 DEF=54 YK=5 BK=1 RK=0 G=289 dmg=3831 door=63/4/1

### MT12

- before: HP=895 ATK=60 DEF=54 YK=5 BK=1 RK=0 G=289 dmg=3831 door=63/4/1
- MT12 x2y11 fly
- MT12 x11y9 kill zombie [HP 895->771, G 289->307] (+18G)
- MT12 x11y8 open yellowDoor [YK 5->4]
- MT12 x11y7 kill blackSlime [HP 771->859, DEF 54->56, YK 4->5, G 307->315] (auto: x10y6 blueGem, x9y7 yellowKey, x9y5 redPotion) (+8G)
- MT12 x8y6 open yellowDoor [YK 5->4]
- MT12 x7y6 kill redPriest [HP 859->1142, G 315->337] (auto: x6y7 bluePotion) (+22G)
- MT12 x6y5 kill zombie [HP 1142->1026, G 337->355] (+18G)
- MT12 x6y4 open yellowDoor [YK 4->3]
- MT12 x7y3 kill redPriest [HP 1026->909, ATK 60->62, YK 3->5, G 355->377] (auto: x7y1 yellowKey, x6y1 redGem, x5y1 yellowKey) (+22G)
- MT12 x11y11 pass downFloor
- after: HP=909 ATK=62 DEF=56 YK=5 BK=1 RK=0 G=377 dmg=4317 door=66/4/1

### MT11

- before: HP=909 ATK=62 DEF=56 YK=5 BK=1 RK=0 G=377 dmg=4317 door=66/4/1
- MT11 x11y8 kill bigBat [HP 909->865, G 377->389] (+12G)
- MT11 x11y4 kill blackSlime [HP 865->957, YK 5->6, G 389->397] (auto: x11y1 yellowKey, x10y1 redPotion) (+8G)
- MT11 x9y3 open yellowDoor [YK 6->5]
- MT11 x8y2 kill zombie [HP 957->841, G 397->415] (+18G)
- MT11 x7y1 open yellowDoor [YK 5->4]
- MT11 x5y1 pass [ATK 62->64, G 415->418] (auto: x5y1 redGem, x6y2 bat)
- after: HP=841 ATK=64 DEF=56 YK=4 BK=1 RK=0 G=418 dmg=4485 door=68/4/1

### MT15

- before: HP=841 ATK=64 DEF=56 YK=4 BK=1 RK=0 G=418 dmg=4485 door=68/4/1
- MT15 x6y10 fly
- MT15 x1y4 open yellowDoor [YK 4->3]
- MT15 x1y7 kill blackSlime [HP 841->833, G 418->426] (+8G)
- MT15 x2y9 open yellowDoor [YK 3->2]
- MT15 x3y7 pass [YK 2->4, BK 1->2] (auto: x3y7 yellowKey, x3y6 blueKey, x3y5 yellowKey)
- after: HP=833 ATK=64 DEF=56 YK=4 BK=2 RK=0 G=426 dmg=4493 door=70/4/1

### MT17

- before: HP=833 ATK=64 DEF=56 YK=4 BK=2 RK=0 G=426 dmg=4493 door=70/4/1
- MT17 x5y11 fly
- MT17 x6y9 kill redPriest [HP 833->755, G 426->448] (+22G)
- MT17 x7y7 kill blackSlime [HP 755->747, G 448->456] (+8G)
- MT17 x7y5 open blueDoor [BK 2->1]
- MT17 x7y3 kill bigBat [HP 747->703, G 456->468] (+12G)
- MT17 x6y1 pass upFloor
- after: HP=703 ATK=64 DEF=56 YK=4 BK=1 RK=0 G=468 dmg=4623 door=70/5/1

### MT18

- before: HP=703 ATK=64 DEF=56 YK=4 BK=1 RK=0 G=468 dmg=4623 door=70/5/1
- MT18 x8y1 open yellowDoor [YK 4->3] (auto: x6y3 fakeWall)
- MT18 x9y1 kill redPriest [HP 703->625, YK 3->7, BK 1->2, G 468->490] (auto: x11y1 yellowKey, x11y2 yellowKey, x11y3 blueKey, x11y4 yellowKey, x11y5 yellowKey) (+22G)
- MT18 x4y1 open blueDoor [BK 2->1]
- MT18 x1y1 pass upFloor
- after: HP=625 ATK=64 DEF=56 YK=7 BK=1 RK=0 G=490 dmg=4701 door=71/6/1

### MT19

- before: HP=625 ATK=64 DEF=56 YK=7 BK=1 RK=0 G=490 dmg=4701 door=71/6/1
- MT19 x1y3 open yellowDoor [YK 7->6]
- MT19 x1y4 pass [G 490->493] (auto: x1y4 bat)
- MT19 x1y6 open yellowDoor [YK 6->5]
- MT19 x1y7 kill bigBat [HP 625->581, G 493->505] (+12G)
- MT19 x1y9 open yellowDoor [YK 5->4]
- MT19 x1y11 kill blackSlime [HP 581->573, G 505->513] (+8G)
- MT19 x3y11 kill bigBat [HP 573->529, G 513->525] (+12G)
- MT19 x4y10 open yellowDoor [YK 4->3]
- MT19 x5y10 pass [YK 3->5] (auto: x5y10 yellowKey, x7y10 yellowKey)
- MT19 x6y11 pass upFloor
- after: HP=529 ATK=64 DEF=56 YK=5 BK=1 RK=0 G=525 dmg=4797 door=75/6/1

### MT20

- before: HP=529 ATK=64 DEF=56 YK=5 BK=1 RK=0 G=525 dmg=4797 door=75/6/1
- MT20 x4y11 kill redPriest [HP 529->551, G 525->547] (auto: x1y11 redPotion) (+22G)
- MT20 x1y9 open yellowDoor [YK 5->4]
- MT20 x1y7 pass [G 547->553] (auto: x1y7 bat, x2y8 bat)
- MT20 x2y6 open blueDoor [BK 1->0]
- MT20 x1y5 pass [ATK 64->66, DEF 56->58, YK 4->5] (auto: x2y4 blueGem, x1y5 yellowKey, x1y4 redGem)
- after: HP=551 ATK=66 DEF=58 YK=5 BK=0 RK=0 G=553 dmg=4875 door=76/7/1

### MT12

- before: HP=551 ATK=66 DEF=58 YK=5 BK=0 RK=0 G=553 dmg=4875 door=76/7/1
- MT12 x2y11 fly
- MT12 x3y10 open yellowDoor [YK 5->4]
- MT12 x3y9 kill zombie [HP 551->443, YK 4->7, BK 0->1, G 553->571] (auto: x2y8 blueKey, x2y7 yellowKey, x1y8 yellowKey, x1y7 yellowKey) (+18G)
- after: HP=443 ATK=66 DEF=58 YK=7 BK=1 RK=0 G=571 dmg=4983 door=77/7/1

### MT18

- before: HP=443 ATK=66 DEF=58 YK=7 BK=1 RK=0 G=571 dmg=4983 door=77/7/1
- MT18 x6y2 fly
- MT18 x6y6 open blueDoor [BK 1->0]
- MT18 x2y7 kill zombie [HP 443->335, G 571->589] (+18G)
- MT18 x1y8 open yellowDoor [YK 7->6]
- MT18 x1y9 kill redPriest [HP 335->361, ATK 66->68, YK 6->7, G 589->623] (auto: x1y11 redPotion, x2y10 yellowKey, x2y11 redGem, x10y5 bigBat) (+34G)
- MT18 x1y1 pass upFloor
- after: HP=361 ATK=68 DEF=58 YK=7 BK=0 RK=0 G=623 dmg=5165 door=78/8/1

### MT19

- before: HP=361 ATK=68 DEF=58 YK=7 BK=0 RK=0 G=623 dmg=5165 door=78/8/1
- MT19 x8y11 open yellowDoor [YK 7->6]
- MT19 x10y11 pass [HP 361->461, YK 6->7, G 623->638] (auto: x10y11 bat, x11y10 bigBat, x10y9 yellowKey, x9y9 redPotion)
- MT19 x11y8 kill zombie [HP 461->353, G 638->656] (+18G)
- MT19 x11y7 open yellowDoor [YK 7->6]
- MT19 x10y5 kill blackSlime [HP 353->351, G 656->664] (+8G)
- MT19 x10y3 open yellowDoor [YK 6->5]
- MT19 x10y2 pass [ATK 68->70, YK 5->6, G 664->676] (auto: x10y2 bigBat, x10y1 yellowKey, x11y1 redGem)
- after: HP=351 ATK=70 DEF=58 YK=6 BK=0 RK=0 G=676 dmg=5275 door=81/8/1

### MT16

- before: HP=351 ATK=70 DEF=58 YK=6 BK=0 RK=0 G=676 dmg=5275 door=81/8/1
- MT16 x6y10 fly
- MT16 x4y2 open yellowDoor [YK 6->5, G 676->700] (auto: x5y9 bigBat, x7y9 bigBat)
- MT16 x2y1 pass [YK 5->8, G 700->724] (auto: x2y1 bigBat, x2y3 bigBat, x1y1 yellowKey, x1y3 yellowKey, x1y2 yellowKey)
- MT16 x8y2 open yellowDoor [YK 8->7]
- MT16 x9y2 kill blackSlime [HP 351->449, G 724->744] (auto: x11y1 bigBat, x11y3 redPotion) (+20G)
- MT16 x10y4 open yellowDoor [YK 7->6]
- MT16 x10y5 kill zombie [HP 449->368, BK 0->1, G 744->774] (auto: x9y7 bigBat, x11y7 blueKey) (+30G)
- after: HP=368 ATK=70 DEF=58 YK=6 BK=1 RK=0 G=774 dmg=5358 door=84/8/1

### MT11

- before: HP=368 ATK=70 DEF=58 YK=6 BK=1 RK=0 G=774 dmg=5358 door=84/8/1
- MT11 x11y10 fly
- MT11 x9y10 open yellowDoor [YK 6->5, G 774->786] (auto: x4y7 bigBat)
- MT11 x9y11 pass [HP 368->768, G 786->798] (auto: x9y11 bigBat, x8y11 bluePotion)
- after: HP=768 ATK=70 DEF=58 YK=5 BK=1 RK=0 G=798 dmg=5358 door=85/8/1

### MT19

- before: HP=768 ATK=70 DEF=58 YK=5 BK=1 RK=0 G=798 dmg=5358 door=85/8/1
- MT19 x1y2 fly
- MT19 x3y8 kill blackSlime [HP 768->766, G 798->806] (+8G)
- MT19 x6y7 open blueDoor [BK 1->0]
- MT19 x5y6 kill rock [HP 766->388, YK 5->7, G 806->834] (auto: x4y5 yellowKey, x6y4 fakeWall, x8y5 yellowKey) (+28G)
- MT19 x6y3 pass fakeWall2
- MT19 x6y3 take cross
- after: HP=388 ATK=70 DEF=58 YK=7 BK=0 RK=0 G=834 dmg=5738 door=85/9/1

### MT14

- before: HP=388 ATK=70 DEF=58 YK=7 BK=0 RK=0 G=834 dmg=5738 door=85/9/1
- MT14 x6y10 fly
- MT14 x10y8 kill blackSlime [HP 388->386, G 834->842] (+8G)
- MT14 x11y7 open yellowDoor [YK 7->6]
- MT14 x11y6 kill zombie [HP 386->459, G 842->872] (auto: x9y6 redPotion, x8y5 bigBat) (+30G)
- MT14 x7y4 open yellowDoor [YK 6->5]
- MT14 x7y2 kill zombieKnight [HP 459->435, DEF 58->60, YK 5->6, G 872->910] (auto: x7y1 redPotion, x6y1 yellowKey, x5y1 blueGem, x5y2 blackSlime) (+38G)
- MT14 x4y8 kill zombie [HP 435->410, G 910->928] (+18G)
- MT14 x3y7 open yellowDoor [YK 6->5]
- MT14 x2y6 pass [HP 410->510, G 928->948] (auto: x2y6 blackSlime, x4y5 bigBat, x1y5 redPotion)
- MT14 x1y7 open yellowDoor [YK 5->4]
- MT14 x1y9 kill redPriest [HP 510->440, BK 0->1, G 948->970] (auto: x1y11 blueKey) (+22G)
- MT14 x2y4 open blueDoor [BK 1->0]
- MT14 x2y2 kill zombieKnight [HP 440->320, G 970->1000] (+30G)
- MT14 x1y1 kill zombieKnight [HP 320->200, G 1000->1030] (+30G)
- MT14 x3y1 kill zombieKnight [HP 200->80, G 1030->1060] (+30G)
- MT14 x1y3 pass [RK 0->1] (auto: x1y3 redKey)
- after: HP=80 ATK=70 DEF=60 YK=4 BK=0 RK=1 G=1060 dmg=6346 door=89/10/1

### MT15

- before: HP=80 ATK=70 DEF=60 YK=4 BK=0 RK=1 G=1060 dmg=6346 door=89/10/1
- MT15 x6y10 fly
- MT15 x11y6 kill redPriest [HP 80->410, G 1060->1126] (auto: x11y8 bluePotion, x10y5 bigBat, x3y3 blackSlime, x1y10 bigBat, x3y10 bigBat) (+66G)
- after: HP=410 ATK=70 DEF=60 YK=4 BK=0 RK=1 G=1126 dmg=6416 door=89/10/1

### MT17

- before: HP=410 ATK=70 DEF=60 YK=4 BK=0 RK=1 G=1126 dmg=6416 door=89/10/1
- MT17 x5y11 fly
- MT17 x8y11 pass [HP 410->510, G 1126->1138] (auto: x8y11 bigBat, x11y11 redPotion)
- after: HP=510 ATK=70 DEF=60 YK=4 BK=0 RK=1 G=1138 dmg=6416 door=89/10/1

### MT18

- before: HP=510 ATK=70 DEF=60 YK=4 BK=0 RK=1 G=1138 dmg=6416 door=89/10/1
- MT18 x6y2 fly
- MT18 x1y3 open yellowDoor [YK 4->3, G 1138->1146] (auto: x10y2 blackSlime)
- MT18 x2y4 pass [HP 510->610] (auto: x2y4 redPotion)
- after: HP=610 ATK=70 DEF=60 YK=3 BK=0 RK=1 G=1146 dmg=6416 door=90/10/1

### MT11

- before: HP=610 ATK=70 DEF=60 YK=3 BK=0 RK=1 G=1146 dmg=6416 door=90/10/1
- MT11 x11y10 fly
- MT11 x7y7 open yellowDoor [YK 3->2]
- MT11 x8y7 pass [HP 610->710, G 1146->1154] (auto: x8y7 blackSlime, x9y6 redPotion)
- after: HP=710 ATK=70 DEF=60 YK=2 BK=0 RK=1 G=1154 dmg=6416 door=91/10/1

### MT20

- before: HP=710 ATK=70 DEF=60 YK=2 BK=0 RK=1 G=1154 dmg=6416 door=91/10/1
- MT20 x6y10 fly
- MT20 x6y9 open redDoor [RK 1->0]
- MT20 x6y8 pass (触发: 吸血鬼入场)
- MT20 x6y6 kill vampire [HP 710->15, G 1154->1298] (+144G)
- MT20 x6y5 pass [HP 15->1215, ATK 70->76, DEF 60->66, YK 2->5] (auto: x6y4 yellowKey, x5y4 yellowKey, x7y4 yellowKey, x4y5 redGem, x8y5 blueGem, x4y6 redGem, x6y8 bluePotion, x8y6 blueGem, x4y7 redGem, x5y8 bluePotion, x7y8 bluePotion, x8y7 blueGem)
- after: HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=7111 door=91/10/2
