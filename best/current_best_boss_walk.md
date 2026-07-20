# 当前最优 Walk (zone1, auto ON)

## 说明

- 最新通用 Game strict replay（auto 全开）生成
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts\live\live_zone3_mouse_replayer_cdp.js --walk outputs\results\zone1_game_route.json --load-slot <100+> --target-click-only`（统一点击 verifier；旧 live_zone1_auto_replay_cdp.js 已归档）
- 源 JSON：`outputs/results/zone1_game_route.json`

## 摘要

- final: HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=313 dmg=2454 door=41/2/1 MT10 x6y1

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
- MT5 x9y11 pass fakeWall [ATK 10->20] (auto: x11y11 sword1)
- MT5 x11y2 kill redSlime [HP 754->734, G 14->16] (+2G)
- MT5 x10y1 open yellowDoor [YK 1->0]
- MT5 x8y2 kill greenSlime [HP 734->726, YK 0->4, G 16->17] (+1G)
- after: HP=726 ATK=20 DEF=10 YK=4 BK=1 RK=0 G=17 dmg=200 door=4/0/0

### MT4

- before: HP=726 ATK=20 DEF=10 YK=4 BK=1 RK=0 G=17 dmg=200 door=4/0/0
- MT4 x8y8 open yellowDoor [YK 4->3]
- MT4 x8y9 kill bluePriest [HP 726->688, ATK 20->21, G 17->22] (+5G)
- MT4 x4y8 open yellowDoor [YK 3->2]
- MT4 x4y9 kill bat [HP 688->660, YK 2->4, G 22->25] (+3G)
- MT4 x3y10 kill greenSlime [HP 660->652, YK 4->5, G 25->26] (+1G)
- after: HP=652 ATK=21 DEF=10 YK=5 BK=1 RK=0 G=26 dmg=324 door=6/0/0

### MT5

- before: HP=652 ATK=21 DEF=10 YK=5 BK=1 RK=0 G=26 dmg=324 door=6/0/0
- MT5 x6y4 kill bat [HP 652->624, YK 5->6, G 26->29] (+3G)
- MT5 x5y1 open yellowDoor [YK 6->5]
- MT5 x4y1 kill redSlime [HP 624->604, G 29->31] (+2G)
- MT5 x4y4 open yellowDoor [YK 5->4]
- MT5 x4y6 kill bat [HP 604->576, YK 4->6, G 31->34] (+3G)
- MT5 x3y3 kill bat [HP 576->548, G 34->37] (+3G)
- MT5 x2y3 open yellowDoor [YK 6->5]
- MT5 x1y1 pass upFloor
- after: HP=548 ATK=21 DEF=10 YK=5 BK=1 RK=0 G=37 dmg=428 door=9/0/0

### MT6

- before: HP=548 ATK=21 DEF=10 YK=5 BK=1 RK=0 G=37 dmg=428 door=9/0/0
- MT6 x3y6 kill redSlime [HP 548->528, G 37->39] (+2G)
- MT6 x4y6 kill bluePriest [HP 528->440, YK 5->6, G 39->44] (+5G)
- MT6 x5y4 open yellowDoor [YK 6->5]
- MT6 x4y3 kill redSlime [HP 440->420, YK 5->9, G 44->46] (+2G)
- MT6 x7y8 open yellowDoor [YK 9->8]
- MT6 x8y8 open yellowDoor [YK 8->7]
- MT6 x10y8 open yellowDoor [YK 7->6]
- MT6 x11y9 kill redSlime [HP 420->400, G 46->48] (+2G)
- MT6 x11y11 pass upFloor
- after: HP=400 ATK=21 DEF=10 YK=6 BK=1 RK=0 G=48 dmg=576 door=13/0/0

### MT7

- before: HP=400 ATK=21 DEF=10 YK=6 BK=1 RK=0 G=48 dmg=576 door=13/0/0
- MT7 x11y7 open yellowDoor [YK 6->5]
- MT7 x5y7 open yellowDoor [YK 5->4]
- MT7 x5y9 kill bat [HP 400->372, YK 4->6, G 48->51] (+3G)
- MT7 x4y6 kill bluePriest [HP 372->284, G 51->56] (+5G)
- MT7 x3y7 open yellowDoor [YK 6->5]
- MT7 x3y10 kill greenSlime [HP 284->276, G 56->57] (+1G)
- MT7 x2y11 kill redSlime [HP 276->256, G 57->59] (+2G)
- MT7 x1y10 kill greenSlime [HP 256->248, G 59->60] (+1G)
- MT7 x1y7 open yellowDoor [YK 5->4]
- MT7 x1y5 open yellowDoor [YK 4->3]
- MT7 x1y1 pass upFloor
- after: HP=248 ATK=21 DEF=10 YK=3 BK=1 RK=0 G=60 dmg=728 door=18/0/0

### MT8

- before: HP=248 ATK=21 DEF=10 YK=3 BK=1 RK=0 G=60 dmg=728 door=18/0/0
- MT8 x3y1 open yellowDoor [YK 3->2]
- MT8 x4y1 open yellowDoor [YK 2->1]
- MT8 x6y3 open yellowDoor [YK 1->0]
- MT8 x5y4 take yellowKey [YK 0->3] (auto: x4y4 yellowKey, x3y4 yellowKey)
- MT8 x6y1 pass upFloor
- after: HP=248 ATK=21 DEF=10 YK=3 BK=1 RK=0 G=60 dmg=728 door=21/0/0

### MT9

- before: HP=248 ATK=21 DEF=10 YK=3 BK=1 RK=0 G=60 dmg=728 door=21/0/0
- MT9 x8y1 open yellowDoor [YK 3->2]
- MT9 x9y1 kill greenSlime [HP 248->290, DEF 10->20, G 60->61] (+1G)
- MT9 x9y4 open yellowDoor [YK 2->1, G 61->62] (auto: +1G)
- MT9 x8y4 open yellowDoor [YK 1->0]
- MT9 x7y4 take yellowKey [ATK 21->22, YK 0->2, G 62->64] (auto: x5y4 yellowKey, x6y5 redGem, x7y6 redSlime)
- MT9 x4y5 open yellowDoor [YK 2->1]
- MT9 x3y5 kill bat [HP 290->272, DEF 20->21, YK 1->2, G 64->67] (+3G)
- after: HP=272 ATK=22 DEF=21 YK=2 BK=1 RK=0 G=67 dmg=754 door=25/0/0

### MT7

- before: HP=272 ATK=22 DEF=21 YK=2 BK=1 RK=0 G=67 dmg=754 door=25/0/0
- MT7 x3y5 open yellowDoor [YK 2->1]
- MT7 x3y3 kill bat [HP 272->305, ATK 22->23, G 67->70] (+3G)
- after: HP=305 ATK=23 DEF=21 YK=1 BK=1 RK=0 G=70 dmg=771 door=26/0/0

### MT3

- before: HP=305 ATK=23 DEF=21 YK=1 BK=1 RK=0 G=70 dmg=771 door=26/0/0
- MT3 x3y5 kill bat [HP 305->288, G 70->73] (+3G)
- MT3 x1y4 open yellowDoor [YK 1->0]
- MT3 x1y3 kill bluePriest [HP 288->305, DEF 21->22, YK 0->1, G 73->78] (+5G)
- after: HP=305 ATK=23 DEF=22 YK=1 BK=1 RK=0 G=78 dmg=821 door=27/0/0

### MT6

- before: HP=305 ATK=23 DEF=22 YK=1 BK=1 RK=0 G=78 dmg=821 door=27/0/0
- MT6 x5y11 kill skeleton [HP 305->365, G 78->87] (+9G)
- MT6 x1y10 open yellowDoor [YK 1->0]
- MT6 x2y9 kill bat [HP 365->349, DEF 22->23, G 87->90] (+3G)
- after: HP=349 ATK=23 DEF=23 YK=0 BK=1 RK=0 G=90 dmg=877 door=28/0/0

### MT7

- before: HP=349 ATK=23 DEF=23 YK=0 BK=1 RK=0 G=90 dmg=877 door=28/0/0
- MT7 x9y5 kill skeleton [HP 349->361, YK 0->2, G 90->96] (+6G)
- after: HP=361 ATK=23 DEF=23 YK=2 BK=1 RK=0 G=96 dmg=915 door=28/0/0

### MT1

- before: HP=361 ATK=23 DEF=23 YK=2 BK=1 RK=0 G=96 dmg=915 door=28/0/0
- MT1 x6y6 open yellowDoor [YK 2->1]
- MT1 x7y6 kill bat [HP 361->346, G 96->99] (+3G)
- MT1 x8y6 kill bluePriest [HP 346->319, G 99->104] (+5G)
- MT1 x9y6 kill bat [HP 319->304, G 104->107] (+3G)
- MT1 x9y5 open yellowDoor [YK 1->0]
- MT1 x8y4 take redPotion [HP 304->354, ATK 23->24, DEF 23->24, YK 0->1] (auto: x8y3 yellowKey, x7y4 blueGem, x7y3 redGem)
- after: HP=354 ATK=24 DEF=24 YK=1 BK=1 RK=0 G=107 dmg=972 door=30/0/0

### MT8

- before: HP=354 ATK=24 DEF=24 YK=1 BK=1 RK=0 G=107 dmg=972 door=30/0/0
- MT8 x7y5 kill bluePriest [HP 354->330, G 107->113] (+6G)
- MT8 x7y7 kill bat [HP 330->316, G 113->116] (+3G)
- MT8 x6y8 kill skeleton [HP 316->280, G 116->122] (+6G)
- MT8 x4y8 kill bat [HP 280->266, G 122->125] (+3G)
- MT8 x1y9 open yellowDoor [YK 1->0]
- MT8 x1y10 kill greenSlime [G 125->126] (+1G)
- MT8 x2y11 kill bat [HP 266->252, G 126->129] (+3G)
- MT8 x3y11 open blueDoor [BK 1->0]
- MT8 x4y11 take yellowKey [ATK 24->25, DEF 24->25, YK 0->2] (auto: x4y10 redGem, x5y11 blueGem, x5y10 yellowKey)
- after: HP=252 ATK=25 DEF=25 YK=2 BK=0 RK=0 G=129 dmg=1074 door=31/1/0

### MT3

- before: HP=252 ATK=25 DEF=25 YK=2 BK=0 RK=0 G=129 dmg=1074 door=31/1/0
- MT3 x1y6 open yellowDoor [YK 2->1]
- MT3 x1y7 kill skeleton [HP 252->268, ATK 25->26, YK 1->2, G 129->135] (+6G)
- after: HP=268 ATK=26 DEF=25 YK=2 BK=0 RK=0 G=135 dmg=1108 door=32/1/0

### MT5

- before: HP=268 ATK=26 DEF=25 YK=2 BK=0 RK=0 G=135 dmg=1108 door=32/1/0
- MT5 x2y7 kill skeletonSoldier [HP 268->237, DEF 25->26, YK 2->3, G 135->144] (+9G)
- after: HP=237 ATK=26 DEF=26 YK=3 BK=0 RK=0 G=144 dmg=1189 door=32/1/0

### MT4

- before: HP=237 ATK=26 DEF=26 YK=3 BK=0 RK=0 G=144 dmg=1189 door=32/1/0
- MT4 x2y5 kill bluePriest [HP 237->219, G 144->151] (+7G)
- MT4 x2y4 open yellowDoor [YK 3->2]
- MT4 x2y1 take blueKey [HP 219->269, YK 2->3, BK 0->1] (auto: x1y2 redPotion, x3y2 yellowKey)
- after: HP=269 ATK=26 DEF=26 YK=3 BK=1 RK=0 G=151 dmg=1207 door=33/1/0

### MT9

- before: HP=269 ATK=26 DEF=26 YK=3 BK=1 RK=0 G=151 dmg=1207 door=33/1/0
- MT9 x7y10 kill bat [HP 269->257, G 151->154] (+3G)
- MT9 x6y11 open yellowDoor [YK 3->2]
- MT9 x3y11 open blueDoor [BK 1->0]
- MT9 x1y11 pass upFloor [HP 257->307] (auto: x2y10 redPotion)
- after: HP=307 ATK=26 DEF=26 YK=2 BK=0 RK=0 G=154 dmg=1219 door=34/2/0

### MT10

- before: HP=307 ATK=26 DEF=26 YK=2 BK=0 RK=0 G=154 dmg=1219 door=34/2/0
- MT10 x1y9 open yellowDoor [YK 2->1]
- MT10 x1y6 kill skeleton [HP 307->275, DEF 26->27, G 154->160] (+6G)
- after: HP=275 ATK=26 DEF=27 YK=1 BK=0 RK=0 G=160 dmg=1251 door=35/2/0

### MT7

- before: HP=275 ATK=26 DEF=27 YK=1 BK=0 RK=0 G=160 dmg=1251 door=35/2/0
- MT7 x9y7 kill skeletonSoldier [HP 275->400, YK 1->3, G 160->168] (+8G)
- after: HP=400 ATK=26 DEF=27 YK=3 BK=0 RK=0 G=168 dmg=1326 door=35/2/0

### MT10

- before: HP=400 ATK=26 DEF=27 YK=3 BK=0 RK=0 G=168 dmg=1326 door=35/2/0
- MT10 x3y9 open yellowDoor [YK 3->2]
- MT10 x4y11 kill bluePriest [HP 400->385, G 168->173] (+5G)
- MT10 x8y11 kill bluePriest [HP 385->370, G 173->178] (+5G)
- MT10 x9y9 open yellowDoor [YK 2->1]
- MT10 x9y6 kill skeleton [HP 370->340, ATK 26->27, G 178->184] (+6G)
- MT10 x11y9 open yellowDoor [YK 1->0]
- MT10 x11y11 take bluePotion [HP 340->540]
- after: HP=540 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=184 dmg=1386 door=38/2/0

### MT6

- before: HP=540 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=184 dmg=1386 door=38/2/0
- MT6 x7y1 kill bluePriest [HP 540->525, YK 0->1, G 184->190] (+6G)
- after: HP=525 ATK=27 DEF=27 YK=1 BK=0 RK=0 G=190 dmg=1401 door=38/2/0

### MT8

- before: HP=525 ATK=27 DEF=27 YK=1 BK=0 RK=0 G=190 dmg=1401 door=38/2/0
- MT8 x8y8 kill bluePriest [HP 525->510, G 190->195] (+5G)
- MT8 x10y7 open yellowDoor [YK 1->0]
- MT8 x11y5 kill yellowGuard [HP 510->321, G 195->207] (+12G)
- MT8 x9y5 kill yellowGuard [HP 321->132, G 207->219] (+12G)
- MT8 x9y3 take bluePotion [HP 132->382, YK 0->2, RK 0->1] (auto: x9y1 yellowKey, x10y2 redKey, x11y3 redPotion, x11y1 yellowKey)
- after: HP=382 ATK=27 DEF=27 YK=2 BK=0 RK=1 G=219 dmg=1794 door=39/2/0

### MT1

- before: HP=382 ATK=27 DEF=27 YK=2 BK=0 RK=1 G=219 dmg=1794 door=39/2/0
- MT1 x10y9 open yellowDoor [YK 2->1]
- MT1 x10y10 kill bat [HP 382->571, G 219->224] (+5G)
- after: HP=571 ATK=27 DEF=27 YK=1 BK=0 RK=1 G=224 dmg=1805 door=40/2/0

### MT7

- before: HP=571 ATK=27 DEF=27 YK=1 BK=0 RK=1 G=224 dmg=1805 door=40/2/0
- MT7 x7y7 open yellowDoor [YK 1->0]
- MT7 x7y9 kill redSlime [G 224->226] (+2G)
- MT7 x7y10 kill bluePriest [HP 571->756, G 226->231] (+5G) (auto: x7y11 bluePotion)
- after: HP=756 ATK=27 DEF=27 YK=0 BK=0 RK=1 G=231 dmg=1820 door=41/2/0

### MT10

- before: HP=756 ATK=27 DEF=27 YK=0 BK=0 RK=1 G=231 dmg=1820 door=41/2/0
- MT10 x6y9 open redDoor [RK 1->0]
- MT10 x6y5 trigger boss event [HP 756->122, G 231->313] (boss 动态清: x5y4 skeletonSoldier, x7y4 skeletonSoldier, x6y4 skeleton, x5y5 skeleton, x7y5 skeleton, x5y6 skeleton, x6y6 skeleton, x7y6 skeleton, x6y1 skeletonCaptain)
- after: HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=313 dmg=2454 door=41/2/1
