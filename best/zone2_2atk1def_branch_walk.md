# 当前最优 Walk (zone2, auto ON)
- Markdown expands JSON steps from step 132; earlier steps reuse `best/current_best_boss_walk.md（1区最新通用 Game 前缀）`. The exported JSON remains fully stitched for replay.

## 说明

- 最新通用 Game strict replay（2ATK1DEF，auto 全开）生成
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone2_2atk1def_game_route.json --load-slot 100 --target-click-only`（统一点击 verifier；旧 `live_zone2_runner.py` 已归档）
- 源 JSON：`outputs/results/zone2_2atk1def_game_route.json`

## 摘要

- final: HP=11 ATK=70 DEF=66 YK=1 BK=0 RK=0 G=1116 dmg=6415 door=89/9/2 MT20 x6y6

## Walk

### MT7

- before: HP=571 ATK=27 DEF=27 YK=1 BK=0 RK=1 G=224 dmg=1805 door=40/2/0
- MT7 x7y7 open yellowDoor [YK 1->0]
- MT7 x7y10 kill bluePriest [HP 571->756, G 224->231] (+7G)
- after: HP=756 ATK=27 DEF=27 YK=0 BK=0 RK=1 G=231 dmg=1820 door=41/2/0

### MT10

- before: HP=756 ATK=27 DEF=27 YK=0 BK=0 RK=1 G=231 dmg=1820 door=41/2/0
- MT10 x6y9 open redDoor [RK 1->0]
- MT10 x6y5 trigger boss event [HP 756->122, G 231->313] (boss 动态清: x5y4 skeletonSoldier, x7y4 skeletonSoldier, x6y4 skeleton, x5y5 skeleton, x7y5 skeleton, x5y6 skeleton, x6y6 skeleton, x7y6 skeleton, x6y1 skeletonCaptain)
- MT10 x6y9 event thief [HP 122->722, ATK 27->30, DEF 27->30, YK 0->3]
- MT10 x6y11 pass upFloor
- after: HP=722 ATK=30 DEF=30 YK=3 BK=0 RK=0 G=313 dmg=2454 door=41/2/1

### MT11

- before: HP=722 ATK=30 DEF=30 YK=3 BK=0 RK=0 G=313 dmg=2454 door=41/2/1
- MT11 x10y9 kill bat [HP 722->714, G 313->316] (+3G)
- MT11 x11y11 pass upFloor
- after: HP=714 ATK=30 DEF=30 YK=3 BK=0 RK=0 G=316 dmg=2462 door=41/2/1

### MT12

- before: HP=714 ATK=30 DEF=30 YK=3 BK=0 RK=0 G=316 dmg=2462 door=41/2/1
- MT12 x8y11 kill bat [HP 714->906, G 316->319] (+3G)
- MT12 x6y9 shop atk [ATK 30->34, G 319->299]
- MT12 x6y9 shop atk [ATK 34->38, G 299->259]
- MT12 x6y9 shop def [DEF 30->38, G 259->179]
- MT12 x4y11 kill bat [G 179->182] (+3G)
- MT12 x1y11 pass upFloor
- after: HP=906 ATK=38 DEF=38 YK=3 BK=0 RK=0 G=182 dmg=2470 door=41/2/1

### MT13

- before: HP=906 ATK=38 DEF=38 YK=3 BK=0 RK=0 G=182 dmg=2470 door=41/2/1
- MT13 x11y11 pass upFloor
- after: HP=906 ATK=38 DEF=38 YK=3 BK=0 RK=0 G=182 dmg=2470 door=41/2/1

### MT14

- before: HP=906 ATK=38 DEF=38 YK=3 BK=0 RK=0 G=182 dmg=2470 door=41/2/1
- MT14 x9y9 open yellowDoor [YK 3->2]
- MT14 x8y8 kill blackSlime [HP 906->840, G 182->190] (+8G)
- MT14 x6y8 open yellowDoor [YK 2->1]
- MT14 x6y9 pass fakeWall [HP 840->940] (auto: x5y10 redPotion)
- after: HP=940 ATK=38 DEF=38 YK=1 BK=0 RK=0 G=190 dmg=2536 door=43/2/1

### MT7

- before: HP=940 ATK=38 DEF=38 YK=1 BK=0 RK=0 G=190 dmg=2536 door=43/2/1
- MT7 x7y5 open yellowDoor [YK 1->0]
- MT7 x7y3 kill skeletonSoldier [HP 940->912, G 190->200] (+10G)
- MT7 x6y1 trader yellowKey5 [YK 0->5, G 200->150]
- after: HP=912 ATK=38 DEF=38 YK=5 BK=0 RK=0 G=150 dmg=2564 door=44/2/1

### MT6

- before: HP=912 ATK=38 DEF=38 YK=5 BK=0 RK=0 G=150 dmg=2564 door=44/2/1
- MT6 x11y2 open yellowDoor [YK 5->4, G 150->155] (auto: +5G)
- MT6 x11y4 kill bat [G 155->158] (+3G)
- MT6 x8y3 take redPotion [HP 912->962]
- MT6 x8y4 trader blueKey1 [BK 0->1, G 158->108]
- after: HP=962 ATK=38 DEF=38 YK=4 BK=1 RK=0 G=108 dmg=2564 door=45/2/1

### MT14

- before: HP=962 ATK=38 DEF=38 YK=4 BK=1 RK=0 G=108 dmg=2564 door=45/2/1
- MT14 x6y11 pass upFloor
- after: HP=962 ATK=38 DEF=38 YK=4 BK=1 RK=0 G=108 dmg=2564 door=45/2/1

### MT15

- before: HP=962 ATK=38 DEF=38 YK=4 BK=1 RK=0 G=108 dmg=2564 door=45/2/1
- MT15 x8y11 open yellowDoor [YK 4->3]
- MT15 x9y11 kill bat [G 108->111] (+3G)
- MT15 x10y10 kill bat [G 111->114] (+3G)
- MT15 x9y9 open yellowDoor [YK 3->2]
- MT15 x9y6 open yellowDoor [YK 2->1]
- MT15 x10y5 kill bigBat [HP 962->900, G 114->126] (+12G)
- MT15 x11y3 open yellowDoor [YK 1->0]
- MT15 x11y2 kill blackSlime [HP 900->834, G 126->134] (+8G)
- MT15 x9y1 event thief
- MT15 x6y1 pass upFloor
- after: HP=834 ATK=38 DEF=38 YK=0 BK=1 RK=0 G=134 dmg=2692 door=49/2/1

### MT16

- before: HP=834 ATK=38 DEF=38 YK=0 BK=1 RK=0 G=134 dmg=2692 door=49/2/1
- MT16 x7y3 take yellowKey [YK 0->1]
- MT16 x6y4 open blueDoor [BK 1->0]
- MT16 x5y5 take redPotion [HP 834->934, YK 1->2] (auto: x7y7 yellowKey)
- MT16 x6y8 open yellowDoor [YK 2->1]
- MT16 x6y11 pass upFloor
- after: HP=934 ATK=38 DEF=38 YK=1 BK=0 RK=0 G=134 dmg=2692 door=50/3/1

### MT17

- before: HP=934 ATK=38 DEF=38 YK=1 BK=0 RK=0 G=134 dmg=2692 door=50/3/1
- MT17 x4y11 kill bigBat [HP 934->972, G 134->146] (+12G)
- MT17 x2y10 open yellowDoor [YK 1->0]
- MT17 x1y8 kill yellowGuard [HP 972->942, G 146->158] (+12G)
- MT17 x3y8 kill yellowGuard [HP 942->912, G 158->170] (+12G)
- MT17 x1y5 kill yellowGuard [HP 912->882, G 170->182] (+12G)
- MT17 x3y5 kill yellowGuard [HP 882->852, G 182->194] (+12G)
- MT17 x2y2 take sword2 [ATK 38->58]
- after: HP=852 ATK=58 DEF=38 YK=0 BK=0 RK=0 G=194 dmg=2874 door=51/3/1

### MT9

- before: HP=852 ATK=58 DEF=38 YK=0 BK=0 RK=0 G=194 dmg=2874 door=51/3/1
- MT9 x1y3 kill skeletonSoldier [HP 852->838, YK 0->1, G 194->214] (+20G)
- after: HP=838 ATK=58 DEF=38 YK=1 BK=0 RK=0 G=214 dmg=2888 door=51/3/1

### MT16

- before: HP=838 ATK=58 DEF=38 YK=1 BK=0 RK=0 G=214 dmg=2888 door=51/3/1
- MT16 x4y10 open yellowDoor [YK 1->0]
- MT16 x2y9 kill blackSlime [HP 838->894, ATK 58->60, DEF 38->40, YK 0->2, G 214->222] (+8G)
- after: HP=894 ATK=60 DEF=40 YK=2 BK=0 RK=0 G=222 dmg=2932 door=52/3/1

### MT15

- before: HP=894 ATK=60 DEF=40 YK=2 BK=0 RK=0 G=222 dmg=2932 door=52/3/1
- MT15 x11y11 trader blueKey1 [BK 0->1, G 222->22]
- after: HP=894 ATK=60 DEF=40 YK=2 BK=1 RK=0 G=22 dmg=2932 door=52/3/1

### MT11

- before: HP=894 ATK=60 DEF=40 YK=2 BK=1 RK=0 G=22 dmg=2932 door=52/3/1
- MT11 x5y9 open yellowDoor [YK 2->1]
- MT11 x4y9 kill blackSlime [HP 894->854, YK 1->6, G 22->30] (+8G)
- MT11 x2y9 kill bigBat [HP 854->794, G 30->42] (+12G)
- MT11 x2y8 open blueDoor [BK 1->0]
- MT11 x1y7 take bluePotion [HP 794->1194]
- MT11 x1y5 kill redPriest [HP 1194->1029, G 42->64] (+22G)
- MT11 x3y5 kill redPriest [HP 1029->864, G 64->86] (+22G)
- MT11 x2y2 take shield2 [DEF 40->60]
- after: HP=864 ATK=60 DEF=60 YK=6 BK=0 RK=0 G=86 dmg=3362 door=53/4/1

### MT1

- before: HP=864 ATK=60 DEF=60 YK=6 BK=0 RK=0 G=86 dmg=3362 door=53/4/1
- MT1 x4y3 open yellowDoor [YK 6->5]
- MT1 x1y3 take redPotion [HP 864->914, G 86->92] (auto: x2y4 skeleton)
- MT1 x2y5 open yellowDoor [YK 5->4]
- MT1 x1y6 take yellowKey [YK 4->5, G 92->100] (auto: x2y7 skeletonSoldier)
- MT1 x2y8 open yellowDoor [YK 5->4]
- MT1 x3y10 take yellowKey [HP 914->1014, YK 4->6] (auto: x3y11 yellowKey, x1y10 redPotion, x2y11 fly, x1y11 redPotion)
- after: HP=1014 ATK=60 DEF=60 YK=6 BK=0 RK=0 G=100 dmg=3362 door=56/4/1

### MT8

- before: HP=1014 ATK=60 DEF=60 YK=6 BK=0 RK=0 G=100 dmg=3362 door=56/4/1
- MT8 x11y9 open yellowDoor [YK 6->5]
- MT8 x11y10 kill skeleton [G 100->106] (+6G)
- MT8 x10y11 kill skeletonSoldier [G 106->114] (+8G)
- MT8 x9y11 open yellowDoor [YK 5->4]
- MT8 x8y10 take redPotion [HP 1014->1064, YK 4->5, BK 0->1] (auto: x7y10 blueKey, x7y11 yellowKey)
- after: HP=1064 ATK=60 DEF=60 YK=5 BK=1 RK=0 G=114 dmg=3362 door=58/4/1

### MT12

- before: HP=1064 ATK=60 DEF=60 YK=5 BK=1 RK=0 G=114 dmg=3362 door=58/4/1
- MT12 x11y9 kill zombie [HP 1064->964, G 114->140] (+26G)
- MT12 x11y8 open yellowDoor [YK 5->4]
- MT12 x11y7 kill blackSlime [G 140->148] (+8G)
- MT12 x10y6 take blueGem [HP 964->1064, DEF 60->62, YK 4->5] (auto: x9y5 redPotion, x9y7 yellowKey)
- MT12 x8y6 open yellowDoor [YK 5->4]
- MT12 x7y6 kill redPriest [HP 1064->1365, G 148->170] (+22G)
- MT12 x6y5 kill zombie [HP 1365->1273, G 170->188] (+18G)
- MT12 x6y4 open yellowDoor [YK 4->3]
- MT12 x7y3 kill redPriest [HP 1273->1174, ATK 60->62, YK 3->5, G 188->210] (+22G)
- after: HP=1174 ATK=62 DEF=62 YK=5 BK=1 RK=0 G=210 dmg=3752 door=61/4/1

### MT11

- before: HP=1174 ATK=62 DEF=62 YK=5 BK=1 RK=0 G=210 dmg=3752 door=61/4/1
- MT11 x11y8 kill bigBat [HP 1174->1236, YK 5->6, G 210->230] (+20G)
- MT11 x9y3 open yellowDoor [YK 6->5]
- MT11 x8y2 kill zombie [HP 1236->1144, G 230->248] (+18G)
- MT11 x7y1 open yellowDoor [YK 5->4]
- MT11 x6y2 kill bat [G 248->251] (+3G)
- MT11 x5y1 take redGem [ATK 62->64]
- after: HP=1144 ATK=64 DEF=62 YK=4 BK=1 RK=0 G=251 dmg=3882 door=63/4/1

### MT16

- before: HP=1144 ATK=64 DEF=62 YK=4 BK=1 RK=0 G=251 dmg=3882 door=63/4/1
- MT16 x4y2 open yellowDoor [YK 4->3]
- MT16 x2y1 kill bigBat [HP 1144->1106, YK 3->6, G 251->263] (+12G)
- after: HP=1106 ATK=64 DEF=62 YK=6 BK=1 RK=0 G=263 dmg=3920 door=64/4/1

### MT17

- before: HP=1106 ATK=64 DEF=62 YK=6 BK=1 RK=0 G=263 dmg=3920 door=64/4/1
- MT17 x8y11 kill bigBat [HP 1106->1168, G 263->275] (+12G)
- MT17 x6y9 kill redPriest [HP 1168->1102, G 275->305] (+30G)
- MT17 x7y5 open blueDoor [BK 1->0]
- MT17 x7y3 kill bigBat [HP 1102->1064, G 305->317] (+12G)
- MT17 x6y1 pass upFloor
- after: HP=1064 ATK=64 DEF=62 YK=6 BK=0 RK=0 G=317 dmg=4062 door=64/5/1

### MT18

- before: HP=1064 ATK=64 DEF=62 YK=6 BK=0 RK=0 G=317 dmg=4062 door=64/5/1
- MT18 x6y3 pass fakeWall
- MT18 x8y1 open yellowDoor [YK 6->5]
- MT18 x9y1 kill redPriest [HP 1064->998, YK 5->9, BK 0->1, G 317->347] (+30G)
- MT18 x5y4 kill zombieKnight [HP 998->650, G 347->377] (+30G)
- MT18 x4y4 open yellowDoor [YK 9->8]
- MT18 x2y4 take redPotion [HP 650->750]
- MT18 x1y3 open yellowDoor [YK 8->7]
- MT18 x1y1 pass upFloor (auto: after previous map change -> MT18 x2y2)
- after: HP=750 ATK=64 DEF=62 YK=7 BK=1 RK=0 G=377 dmg=4476 door=67/5/1

### MT19

- before: HP=750 ATK=64 DEF=62 YK=7 BK=1 RK=0 G=377 dmg=4476 door=67/5/1
- MT19 x1y3 open yellowDoor [YK 7->6]
- MT19 x1y4 kill bat [G 377->380] (+3G)
- MT19 x1y6 open yellowDoor [YK 6->5]
- MT19 x1y7 kill bigBat [HP 750->712, G 380->400] (+20G)
- MT19 x1y9 open yellowDoor [YK 5->4]
- MT19 x1y11 kill blackSlime [G 400->408] (+8G)
- MT19 x3y11 kill bigBat [HP 712->674, G 408->420] (+12G)
- MT19 x4y10 open yellowDoor [YK 4->3]
- MT19 x5y10 take yellowKey [YK 3->5] (auto: x7y10 yellowKey)
- MT19 x6y11 pass upFloor
- after: HP=674 ATK=64 DEF=62 YK=5 BK=1 RK=0 G=420 dmg=4552 door=71/5/1

### MT20

- before: HP=674 ATK=64 DEF=62 YK=5 BK=1 RK=0 G=420 dmg=4552 door=71/5/1
- MT20 x4y11 kill redPriest [HP 674->708, G 420->442] (+22G)
- MT20 x1y9 open yellowDoor [YK 5->4]
- MT20 x1y7 kill bat [G 442->445] (+3G)
- MT20 x2y6 open blueDoor [BK 1->0, G 445->448] (auto: +3G)
- MT20 x2y4 take blueGem [ATK 64->66, DEF 62->64, YK 4->5] (auto: x1y4 redGem, x1y5 yellowKey)
- MT20 x6y11 pass downFloor
- after: HP=708 ATK=66 DEF=64 YK=5 BK=0 RK=0 G=448 dmg=4618 door=72/6/1

### MT19

- before: HP=708 ATK=66 DEF=64 YK=5 BK=0 RK=0 G=448 dmg=4618 door=72/6/1
- MT19 x8y11 open yellowDoor [YK 5->4]
- MT19 x10y11 kill bat [G 448->451] (+3G)
- MT19 x11y10 kill bigBat [HP 708->772, YK 4->5, G 451->463] (+12G)
- MT19 x11y8 kill zombie [HP 772->688, G 463->481] (+18G)
- MT19 x11y7 open yellowDoor [YK 5->4]
- MT19 x11y5 kill blackSlime [G 481->489] (+8G)
- MT19 x10y3 open yellowDoor [YK 4->3, G 489->497] (auto: +8G)
- MT19 x10y2 kill bigBat [HP 688->652, ATK 66->68, YK 3->4, G 497->509] (+12G)
- after: HP=652 ATK=68 DEF=64 YK=4 BK=0 RK=0 G=509 dmg=4774 door=75/6/1

### MT15

- before: HP=652 ATK=68 DEF=64 YK=4 BK=0 RK=0 G=509 dmg=4774 door=75/6/1
- MT15 x4y1 open yellowDoor [YK 4->3, G 509->521] (auto: +12G)
- MT15 x1y4 open yellowDoor [YK 3->2, G 521->529] (auto: +8G)
- MT15 x1y7 kill blackSlime [G 529->537] (+8G)
- MT15 x2y9 open yellowDoor [YK 2->1, G 537->549] (auto: +12G)
- MT15 x3y7 take yellowKey [YK 1->3, BK 0->1, G 549->561] (auto: x3y10 bigBat, x3y6 blueKey, x3y5 yellowKey)
- after: HP=652 ATK=68 DEF=64 YK=3 BK=1 RK=0 G=561 dmg=4774 door=78/6/1

### MT12

- before: HP=652 ATK=68 DEF=64 YK=3 BK=1 RK=0 G=561 dmg=4774 door=78/6/1
- MT12 x3y10 open yellowDoor [YK 3->2, G 561->573] (auto: +12G)
- MT12 x3y9 kill zombie [HP 652->568, YK 2->5, BK 1->2, G 573->591] (+18G)
- after: HP=568 ATK=68 DEF=64 YK=5 BK=2 RK=0 G=591 dmg=4858 door=79/6/1

### MT18

- before: HP=568 ATK=68 DEF=64 YK=5 BK=2 RK=0 G=591 dmg=4858 door=79/6/1
- MT18 x6y6 open blueDoor [BK 2->1, G 591->603] (auto: +12G)
- MT18 x2y7 kill zombie [HP 568->484, G 603->621] (+18G)
- MT18 x1y8 open yellowDoor [YK 5->4]
- MT18 x1y9 kill redPriest [HP 484->522, ATK 68->70, YK 4->5, G 621->643] (+22G)
- after: HP=522 ATK=70 DEF=64 YK=5 BK=1 RK=0 G=643 dmg=5004 door=80/7/1

### MT11

- before: HP=522 ATK=70 DEF=64 YK=5 BK=1 RK=0 G=643 dmg=5004 door=80/7/1
- MT11 x9y10 open yellowDoor [YK 5->4, G 643->655] (auto: +12G)
- MT11 x9y11 kill bigBat [G 655->667] (+12G)
- MT11 x8y11 take bluePotion [HP 522->922]
- after: HP=922 ATK=70 DEF=64 YK=4 BK=1 RK=0 G=667 dmg=5004 door=81/7/1

### MT19

- before: HP=922 ATK=70 DEF=64 YK=4 BK=1 RK=0 G=667 dmg=5004 door=81/7/1
- MT19 x6y7 open blueDoor [BK 1->0]
- MT19 x7y6 kill rock [HP 922->598, YK 4->5, G 667->695] (+28G)
- MT19 x6y4 pass fakeWall [YK 5->6] (auto: x6y3 fakeWall2, x4y5 yellowKey)
- MT19 x6y3 take cross
- after: HP=598 ATK=70 DEF=64 YK=6 BK=0 RK=0 G=695 dmg=5328 door=81/8/1

### MT15

- before: HP=598 ATK=70 DEF=64 YK=6 BK=0 RK=0 G=695 dmg=5328 door=81/8/1
- MT15 x1y2 kill zombie [HP 598->577, DEF 64->66, G 695->713] (+18G)
- after: HP=577 ATK=70 DEF=66 YK=6 BK=0 RK=0 G=713 dmg=5349 door=81/8/1

### MT3

- before: HP=577 ATK=70 DEF=66 YK=6 BK=0 RK=0 G=713 dmg=5349 door=81/8/1
- MT3 x9y8 open yellowDoor [YK 6->5]
- MT3 x10y8 kill bluePriest [G 713->718] (+5G)
- MT3 x11y8 take yellowKey [HP 577->627, YK 5->6] (auto: x11y7 redPotion)
- after: HP=627 ATK=70 DEF=66 YK=6 BK=0 RK=0 G=718 dmg=5349 door=82/8/1

### MT9

- before: HP=627 ATK=70 DEF=66 YK=6 BK=0 RK=0 G=718 dmg=5349 door=82/8/1
- MT9 x8y11 open yellowDoor [YK 6->5, G 718->726] (auto: +8G)
- MT9 x9y11 kill bluePriest [G 726->731] (+5G)
- MT9 x9y9 take yellowKey [HP 627->677, YK 5->6, G 731->742] (auto: x10y10 skeleton, x11y9 bluePriest, x11y11 redPotion)
- after: HP=677 ATK=70 DEF=66 YK=6 BK=0 RK=0 G=742 dmg=5349 door=83/8/1

### MT16

- before: HP=677 ATK=70 DEF=66 YK=6 BK=0 RK=0 G=742 dmg=5349 door=83/8/1
- MT16 x8y10 open yellowDoor [YK 6->5, G 742->778] (auto: +36G)
- MT16 x10y9 kill redPriest [HP 677->619, G 778->800] (+22G)
- MT16 x10y8 open yellowDoor [YK 5->4]
- MT16 x11y7 take blueKey [BK 0->1, G 800->812] (auto: x9y7 bigBat)
- after: HP=619 ATK=70 DEF=66 YK=4 BK=1 RK=0 G=812 dmg=5407 door=85/8/1

### MT14

- before: HP=619 ATK=70 DEF=66 YK=4 BK=1 RK=0 G=812 dmg=5407 door=85/8/1
- MT14 x4y8 kill zombie [HP 619->600, G 812->838] (+26G)
- MT14 x3y7 open yellowDoor [YK 4->3]
- MT14 x1y5 take redPotion [HP 600->700, G 838->858] (auto: x2y6 blackSlime, x4y5 bigBat)
- MT14 x2y4 open blueDoor [BK 1->0]
- MT14 x2y2 kill zombieKnight [HP 700->592, G 858->888] (+30G)
- MT14 x1y1 kill zombieKnight [HP 592->484, G 888->918] (+30G)
- MT14 x3y1 kill zombieKnight [HP 484->376, G 918->948] (+30G)
- MT14 x1y3 take redKey [RK 0->1]
- after: HP=376 ATK=70 DEF=66 YK=3 BK=0 RK=1 G=948 dmg=5750 door=86/9/1

### MT4

- before: HP=376 ATK=70 DEF=66 YK=3 BK=0 RK=1 G=948 dmg=5750 door=86/9/1
- MT4 x4y5 open yellowDoor [YK 3->2]
- MT4 x6y5 kill redSlime [G 948->950] (+2G)
- MT4 x9y5 kill skeleton [G 950->956] (+6G)
- MT4 x10y4 open yellowDoor [YK 2->1]
- MT4 x10y3 kill skeletonSoldier [G 956->964] (+8G)
- MT4 x9y2 take yellowKey [HP 376->576, YK 1->2] (auto: x11y2 bluePotion)
- after: HP=576 ATK=70 DEF=66 YK=2 BK=0 RK=1 G=964 dmg=5750 door=88/9/1

### MT11

- before: HP=576 ATK=70 DEF=66 YK=2 BK=0 RK=1 G=964 dmg=5750 door=88/9/1
- MT11 x7y7 open yellowDoor [YK 2->1]
- MT11 x8y7 kill blackSlime [G 964->972] (+8G)
- MT11 x9y6 take redPotion [HP 576->676]
- after: HP=676 ATK=70 DEF=66 YK=1 BK=0 RK=1 G=972 dmg=5750 door=89/9/1

### MT20

- before: HP=676 ATK=70 DEF=66 YK=1 BK=0 RK=1 G=972 dmg=5750 door=89/9/1
- MT20 x6y9 open redDoor [RK 1->0]
- MT20 x6y8 event vampire
- MT20 x6y6 kill vampire [HP 676->11, G 972->1116] (+144G)
- after: HP=11 ATK=70 DEF=66 YK=1 BK=0 RK=0 G=1116 dmg=6415 door=89/9/2
