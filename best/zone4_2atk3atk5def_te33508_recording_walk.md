# 当前最优 Walk (zone4, auto ON)

## 说明

- 本 walk 由 Game 类 (`scripts/search/zone4_game_route.py`, auto_sweep, strict_live_model) 离线推导生成。
- auto 配置：battle/item/wall 全开。金币/属性标注为 **auto_sweep 后**的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。
- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。
- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。
- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone4_game_route.json --load-slot <100+> --target-click-only`（统一点击 verifier，1-4 区通用；3 区起按需 `--set-auto battle=true,item=nopotion,wall=true`）
- 源 JSON：`D:/claude/mota-web-explorer/best/zone4_2atk3atk5def_te33508_recording_walk.json`

## 摘要

- final: HP=33508 ATK=390 DEF=542 YK=4 BK=0 RK=1 G=1907 dmg=8105 door=55/10/7 MT50 x7y5

## Walk

### MT41

- before: HP=13 ATK=166 DEF=214 YK=6 BK=1 RK=0 G=2954 dmg=0 door=0/0/0
- MT41 x6y2 设置自动：battle=true, item=nopotion, wall=true
- MT41 x6y4 地图伤害 checkBlock [HP 13->7]
- MT41 x6y7 open yellowDoor [YK 6->5]
- MT41 x6y8 open yellowDoor [YK 5->4]
- MT41 x6y9 open yellowDoor [YK 4->3]
- MT41 x6y11 pass upFloor
- after: HP=7 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=6 door=3/0/0

### MT42

- before: HP=7 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=6 door=3/0/0
- MT42 x5y10 pass
- MT42 x5y10 event yellowKnightEscape
- after: HP=7 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=6 door=3/0/0

### MT40

- before: HP=7 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=6 door=3/0/0
- MT40 x6y2 fly
- after: HP=7 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=6 door=3/0/0

### MT41

- before: HP=7 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=6 door=3/0/0
- MT41 x6y2 fly
- MT41 x6y1 pass downFloor
- after: HP=7 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=6 door=3/0/0

### MT39

- before: HP=7 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=6 door=3/0/0
- MT39 x11y10 fly
- MT39 x9y11 take redPotion [HP 7->207]
- after: HP=207 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=6 door=3/0/0

### MT42

- before: HP=207 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=6 door=3/0/0
- MT42 x5y11 fly
- MT42 x8y5 open yellowDoor [YK 3->2]
- MT42 x9y5 地图伤害 checkBlock [HP 207->107]
- MT42 x10y6 地图伤害 checkBlock [HP 107->7]
- MT42 x10y8 地图伤害 checkBlock [HP 7->4]
- MT42 x10y8 设置自动：battle=true, item=true, wall=true
- MT42 x10y9 move [YK 2->7, BK 1->2] (auto: x10y10 yellowKey, x9y10 yellowKey, x10y11 blueKey, x11y10 yellowKey, x9y11 yellowKey, x11y11 yellowKey)
- MT42 x2y2 中心飞行 centerFly
- MT42 x1y1 pass upFloor
- after: HP=4 ATK=166 DEF=214 YK=7 BK=2 RK=0 G=2954 dmg=209 door=4/0/0

### MT43

- before: HP=4 ATK=166 DEF=214 YK=7 BK=2 RK=0 G=2954 dmg=209 door=4/0/0
- MT43 x1y4 open blueDoor [BK 2->1]
- MT43 x1y8 open yellowDoor [YK 7->6]
- MT43 x1y11 pass upFloor
- after: HP=4 ATK=166 DEF=214 YK=6 BK=1 RK=0 G=2954 dmg=209 door=5/1/0

### MT45

- before: HP=4 ATK=166 DEF=214 YK=6 BK=1 RK=0 G=2954 dmg=209 door=5/1/0
- MT45 x11y1 pass upFloor
- after: HP=4 ATK=166 DEF=214 YK=6 BK=1 RK=0 G=2954 dmg=209 door=5/1/0

### MT40

- before: HP=4 ATK=166 DEF=214 YK=6 BK=1 RK=0 G=2954 dmg=209 door=5/1/0
- MT40 x6y2 fly
- MT40 x5y3 move [HP 4->2404] (auto: x5y4 bluePotion, x4y4 bluePotion, x3y4 bluePotion)
- after: HP=2404 ATK=166 DEF=214 YK=6 BK=1 RK=0 G=2954 dmg=209 door=5/1/0

### MT46

- before: HP=2404 ATK=166 DEF=214 YK=6 BK=1 RK=0 G=2954 dmg=209 door=5/1/0
- MT46 x11y2 fly
- MT46 x11y3 open yellowDoor [YK 6->5]
- MT46 x11y5 open yellowDoor [YK 5->4]
- MT46 x11y8 open yellowDoor [YK 4->3]
- MT46 x11y9 地图伤害 checkBlock [HP 2404->2304]
- MT46 x11y11 pass upFloor
- after: HP=2304 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=309 door=8/1/0

### MT47

- before: HP=2304 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=309 door=8/1/0
- MT47 x1y2 中心飞行 centerFly
- MT47 x1y1 pass upFloor
- after: HP=2304 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=309 door=8/1/0

### MT15

- before: HP=2304 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=2954 dmg=309 door=8/1/0
- MT15 x6y2 fly
- MT15 x6y6 kill octopus [G 2954->3054] (+100G)
- MT15 x6y5 take pickaxe
- after: HP=2304 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=3054 dmg=309 door=8/1/0

### MT46

- before: HP=2304 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=3054 dmg=309 door=8/1/0
- MT46 x11y2 fly
- after: HP=2304 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=3054 dmg=309 door=8/1/0

### MT48

- before: HP=2304 ATK=166 DEF=214 YK=3 BK=1 RK=0 G=3054 dmg=309 door=8/1/0
- MT48 x11y10 fly
- MT48 x10y10 使用镐 pickaxe
- MT48 x7y10 move [ATK 166->216] (auto: x8y10 sword4)
- after: HP=2304 ATK=216 DEF=214 YK=3 BK=1 RK=0 G=3054 dmg=309 door=8/1/0

### MT47

- before: HP=2304 ATK=216 DEF=214 YK=3 BK=1 RK=0 G=3054 dmg=309 door=8/1/0
- MT47 x2y1 fly
- after: HP=2304 ATK=216 DEF=214 YK=3 BK=1 RK=0 G=3054 dmg=309 door=8/1/0

### MT16

- before: HP=2304 ATK=216 DEF=214 YK=3 BK=1 RK=0 G=3054 dmg=309 door=8/1/0
- MT16 x6y10 fly
- MT16 x8y10 open yellowDoor [YK 3->2]
- MT16 x9y10 move [G 3054->3106] (auto: x9y11 slimeMan, x10y9 redPriest, x10y11 fakeWall)
- MT16 x11y11 pass fakeWall2
- MT16 x11y11 event superPotion
- after: HP=2304 ATK=216 DEF=214 YK=2 BK=1 RK=0 G=3106 dmg=309 door=9/1/0

### MT31

- before: HP=2304 ATK=216 DEF=214 YK=2 BK=1 RK=0 G=3106 dmg=309 door=9/1/0
- MT31 x6y2 fly
- MT31 x9y6 move [G 3106->3186] (auto: x10y6 ghostSkeleton, x2y3 soldier)
- MT31 x11y7 open yellowDoor [YK 2->1]
- MT31 x10y8 move [YK 1->5, G 3186->3246] (auto: x10y9 slimeMan, x11y10 slimeMan, x9y10 yellowKey, x8y10 yellowKey, x9y11 yellowKey, x8y11 yellowKey)
- MT31 x11y5 open yellowDoor [YK 5->4]
- MT31 x10y4 move [HP 2304->2504, G 3246->3361] (auto: x11y3 ghostSkeleton, x10y3 ghostSkeleton, x10y1 redPotion, x8y2 soldier)
- MT31 x8y3 open yellowDoor [YK 4->3]
- MT31 x8y3 move [ATK 216->220] (auto: x8y4 redGem)
- after: HP=2504 ATK=220 DEF=214 YK=3 BK=1 RK=0 G=3361 dmg=309 door=12/1/0

### MT34

- before: HP=2504 ATK=220 DEF=214 YK=3 BK=1 RK=0 G=3361 dmg=309 door=12/1/0
- MT34 x2y1 fly
- MT34 x3y2 move [G 3361->3406] (auto: x2y11 soldier)
- MT34 x4y2 open yellowDoor [YK 3->2]
- MT34 x4y2 move [YK 2->3, G 3406->3436] (auto: x5y2 slimeMan, x6y1 yellowKey)
- MT34 x6y11 pass upFloor
- after: HP=2504 ATK=220 DEF=214 YK=3 BK=1 RK=0 G=3436 dmg=309 door=13/1/0

### MT35

- before: HP=2504 ATK=220 DEF=214 YK=3 BK=1 RK=0 G=3436 dmg=309 door=13/1/0
- MT35 x11y1 pass upFloor
- after: HP=2504 ATK=220 DEF=214 YK=3 BK=1 RK=0 G=3436 dmg=309 door=13/1/0

### MT36

- before: HP=2504 ATK=220 DEF=214 YK=3 BK=1 RK=0 G=3436 dmg=309 door=13/1/0
- MT36 x4y11 move [HP 2504->3304, G 3436->3536] (auto: x3y11 soldier, x1y11 bluePotion, x1y9 swordsman)
- MT36 x2y6 open yellowDoor [YK 3->2]
- MT36 x2y6 move [G 3536->3631] (auto: x5y6 slimeMan, x6y5 ghostSkeleton, x7y6 slimeMan)
- after: HP=3304 ATK=220 DEF=214 YK=2 BK=1 RK=0 G=3631 dmg=309 door=14/1/0

### MT37

- before: HP=3304 ATK=220 DEF=214 YK=2 BK=1 RK=0 G=3631 dmg=309 door=14/1/0
- MT37 x11y10 fly
- MT37 x10y11 move [HP 3304->4304, G 3631->3741] (auto: x9y11 ghostSkeleton, x3y11 slimeMan, x11y1 bluePotion, x1y9 soldier, x1y6 redPotion)
- after: HP=4304 ATK=220 DEF=214 YK=2 BK=1 RK=0 G=3741 dmg=309 door=14/1/0

### MT38

- before: HP=4304 ATK=220 DEF=214 YK=2 BK=1 RK=0 G=3741 dmg=309 door=14/1/0
- MT38 x2y1 fly
- MT38 x4y2 move [HP 4304->5104, G 3741->3831] (auto: x2y5 flower, x3y4 soldier, x4y4 soldier, x11y11 bluePotion)
- MT38 x11y1 pass upFloor
- after: HP=5104 ATK=220 DEF=214 YK=2 BK=1 RK=0 G=3831 dmg=309 door=14/1/0

### MT39

- before: HP=5104 ATK=220 DEF=214 YK=2 BK=1 RK=0 G=3831 dmg=309 door=14/1/0
- MT39 x11y11 pass upFloor
- after: HP=5104 ATK=220 DEF=214 YK=2 BK=1 RK=0 G=3831 dmg=309 door=14/1/0

### MT40

- before: HP=5104 ATK=220 DEF=214 YK=2 BK=1 RK=0 G=3831 dmg=309 door=14/1/0
- MT40 x8y11 open yellowDoor [YK 2->1]
- MT40 x8y11 move [G 3831->3891] (auto: x7y9 slimeMan, x5y9 slimeMan)
- after: HP=5104 ATK=220 DEF=214 YK=1 BK=1 RK=0 G=3891 dmg=309 door=15/1/0

### MT32

- before: HP=5104 ATK=220 DEF=214 YK=1 BK=1 RK=0 G=3891 dmg=309 door=15/1/0
- MT32 x10y1 fly
- after: HP=5104 ATK=220 DEF=214 YK=1 BK=1 RK=0 G=3891 dmg=309 door=15/1/0

### MT34

- before: HP=5104 ATK=220 DEF=214 YK=1 BK=1 RK=0 G=3891 dmg=309 door=15/1/0
- MT34 x2y1 fly
- after: HP=5104 ATK=220 DEF=214 YK=1 BK=1 RK=0 G=3891 dmg=309 door=15/1/0

### MT33

- before: HP=5104 ATK=220 DEF=214 YK=1 BK=1 RK=0 G=3891 dmg=309 door=15/1/0
- MT33 x2y1 fly
- MT33 x5y4 open yellowDoor [YK 1->0]
- MT33 x5y4 move [G 3891->4011] (auto: x6y5 zombieKnight, x4y6 swordsman, x6y7 ghostSkeleton)
- after: HP=5104 ATK=220 DEF=214 YK=0 BK=1 RK=0 G=4011 dmg=309 door=16/1/0

### MT47

- before: HP=5104 ATK=220 DEF=214 YK=0 BK=1 RK=0 G=4011 dmg=309 door=16/1/0
- MT47 x11y10 fly
- after: HP=5104 ATK=220 DEF=214 YK=0 BK=1 RK=0 G=4011 dmg=309 door=16/1/0

### MT48

- before: HP=5104 ATK=220 DEF=214 YK=0 BK=1 RK=0 G=4011 dmg=309 door=16/1/0
- MT48 x11y10 fly
- MT48 x11y11 pass downFloor
- after: HP=5104 ATK=220 DEF=214 YK=0 BK=1 RK=0 G=4011 dmg=309 door=16/1/0

### MT47

- before: HP=5104 ATK=220 DEF=214 YK=0 BK=1 RK=0 G=4011 dmg=309 door=16/1/0
- MT47 x3y1 open blueDoor [BK 1->0]
- MT47 x5y2 trader earthquake [G 4011->11]
- after: HP=5104 ATK=220 DEF=214 YK=0 BK=0 RK=0 G=11 dmg=309 door=16/2/0

### MT37

- before: HP=5104 ATK=220 DEF=214 YK=0 BK=0 RK=0 G=11 dmg=309 door=16/2/0
- MT37 x2y1 fly
- MT37 x2y1 地震卷轴 earthquake
- MT37 x6y3 move [HP 5104->8504, ATK 220->236, DEF 214->230, YK 0->9, BK 0->2, RK 0->1] (auto: x3y4 redPotion, x4y3 redPotion, x3y5 yellowKey, x4y4 redPotion, x5y3 redPotion, x4y5 yellowKey, x5y4 yellowKey, x3y7 blueGem, x5y5 bomb, x7y3 redPotion, x3y8 yellowKey, x4y7 redGem, x7y4 redPotion, x8y3 redPotion, x4y8 yellowKey, x5y7 bluePotion, x7y5 redKey, x8y4 redPotion, x4y9 blueKey, x5y8 yellowKey, x8y5 yellowKey, x9y4 redPotion, x5y9 blueKey, x7y7 redGem, x9y5 yellowKey, x7y8 blueGem, x8y7 redGem, x7y9 bluePotion, x8y8 blueGem, x9y7 redGem, x8y9 yellowKey, x9y8 blueGem)
- after: HP=8504 ATK=236 DEF=230 YK=9 BK=2 RK=1 G=11 dmg=309 door=16/2/0

### MT45

- before: HP=8504 ATK=236 DEF=230 YK=9 BK=2 RK=1 G=11 dmg=309 door=16/2/0
- MT45 x2y1 fly
- after: HP=8504 ATK=236 DEF=230 YK=9 BK=2 RK=1 G=11 dmg=309 door=16/2/0

### MT40

- before: HP=8504 ATK=236 DEF=230 YK=9 BK=2 RK=1 G=11 dmg=309 door=16/2/0
- MT40 x6y2 fly
- after: HP=8504 ATK=236 DEF=230 YK=9 BK=2 RK=1 G=11 dmg=309 door=16/2/0

### MT31

- before: HP=8504 ATK=236 DEF=230 YK=9 BK=2 RK=1 G=11 dmg=309 door=16/2/0
- MT31 x6y10 fly
- MT31 x1y7 open yellowDoor [YK 9->8]
- MT31 x2y8 move [HP 8504->8704, G 11->146] (auto: x1y9 ghostSkeleton, x2y9 ghostSkeleton, x2y11 redPotion, x4y10 redKnight)
- MT31 x4y9 open yellowDoor [YK 8->7]
- MT31 x4y9 move [DEF 230->234] (auto: x4y8 blueGem)
- MT31 x6y11 pass upFloor
- after: HP=8704 ATK=236 DEF=234 YK=7 BK=2 RK=1 G=146 dmg=309 door=18/2/0

### MT32

- before: HP=8704 ATK=236 DEF=234 YK=7 BK=2 RK=1 G=146 dmg=309 door=18/2/0
- MT32 x7y3 open yellowDoor [YK 7->6]
- MT32 x8y3 move [G 146->246] (auto: x8y4 ghostSkeleton, x8y7 redKnight)
- MT32 x9y5 open yellowDoor [YK 6->5]
- MT32 x8y8 move [HP 8704->9504, YK 5->7] (auto: x10y4 yellowKey, x11y5 yellowKey, x11y4 bluePotion)
- MT32 x9y8 open yellowDoor [YK 7->6]
- MT32 x9y8 move [YK 6->8, BK 2->3] (auto: x10y7 yellowKey, x11y8 yellowKey, x11y7 blueKey)
- MT32 x11y1 pass upFloor
- after: HP=9504 ATK=236 DEF=234 YK=8 BK=3 RK=1 G=246 dmg=309 door=21/2/0

### MT33

- before: HP=9504 ATK=236 DEF=234 YK=8 BK=3 RK=1 G=246 dmg=309 door=21/2/0
- MT33 x3y7 open yellowDoor [YK 8->7]
- MT33 x3y7 move [HP 9504->9704, G 246->306] (auto: x2y7 slimeMan, x2y4 redPotion, x1y5 slimeMan)
- MT33 x1y8 open yellowDoor [YK 7->6]
- MT33 x2y9 move [YK 6->7, G 306->436] (auto: x1y10 swordsman, x1y11 yellowKey, x3y9 zombieKnight, x2y11 soldier)
- MT33 x1y1 pass upFloor
- after: HP=9704 ATK=236 DEF=234 YK=7 BK=3 RK=1 G=436 dmg=309 door=23/2/0

### MT34

- before: HP=9704 ATK=236 DEF=234 YK=7 BK=3 RK=1 G=436 dmg=309 door=23/2/0
- MT34 x6y2 move [G 436->501] (auto: x7y2 redKnight)
- MT34 x8y2 open yellowDoor [YK 7->6]
- MT34 x8y2 move [HP 9704->9904, DEF 234->238, YK 6->9] (auto: x9y1 yellowKey, x10y2 yellowKey, x10y1 yellowKey, x11y2 redPotion, x11y1 blueGem)
- MT34 x6y11 pass upFloor
- after: HP=9904 ATK=236 DEF=238 YK=9 BK=3 RK=1 G=501 dmg=309 door=24/2/0

### MT35

- before: HP=9904 ATK=236 DEF=238 YK=9 BK=3 RK=1 G=501 dmg=309 door=24/2/0
- MT35 x11y1 pass upFloor
- after: HP=9904 ATK=236 DEF=238 YK=9 BK=3 RK=1 G=501 dmg=309 door=24/2/0

### MT36

- before: HP=9904 ATK=236 DEF=238 YK=9 BK=3 RK=1 G=501 dmg=309 door=24/2/0
- MT36 x10y11 move [G 501->801] (auto: x9y1 redKnight, x7y1 zombieKnight, x3y1 soldier, x1y3 slimeMan, x1y5 redKnight, x6y7 redKnight)
- MT36 x11y11 pass upFloor
- after: HP=9904 ATK=236 DEF=238 YK=9 BK=3 RK=1 G=801 dmg=309 door=24/2/0

### MT37

- before: HP=9904 ATK=236 DEF=238 YK=9 BK=3 RK=1 G=801 dmg=309 door=24/2/0
- MT37 x1y1 pass upFloor
- after: HP=9904 ATK=236 DEF=238 YK=9 BK=3 RK=1 G=801 dmg=309 door=24/2/0

### MT38

- before: HP=9904 ATK=236 DEF=238 YK=9 BK=3 RK=1 G=801 dmg=309 door=24/2/0
- MT38 x10y1 move [YK 9->12, G 801->931] (auto: x10y7 redKnight, x9y6 yellowKey, x9y5 yellowKey, x10y10 redKnight, x9y4 yellowKey)
- MT38 x11y1 pass upFloor
- after: HP=9904 ATK=236 DEF=238 YK=12 BK=3 RK=1 G=931 dmg=309 door=24/2/0

### MT39

- before: HP=9904 ATK=236 DEF=238 YK=12 BK=3 RK=1 G=931 dmg=309 door=24/2/0
- MT39 x10y11 move [G 931->996] (auto: x7y9 redKnight)
- MT39 x11y11 pass upFloor
- after: HP=9904 ATK=236 DEF=238 YK=12 BK=3 RK=1 G=996 dmg=309 door=24/2/0

### MT40

- before: HP=9904 ATK=236 DEF=238 YK=12 BK=3 RK=1 G=996 dmg=309 door=24/2/0
- MT40 x4y11 open blueDoor [BK 3->2]
- MT40 x4y11 move [HP 9904->10704, ATK 236->240, DEF 238->242, YK 12->13, G 996->1061] (auto: x3y11 redKnight, x1y11 redGem, x2y9 yellowKey, x1y10 bluePotion, x1y9 blueGem)
- after: HP=10704 ATK=240 DEF=242 YK=13 BK=2 RK=1 G=1061 dmg=309 door=24/3/0

### MT45

- before: HP=10704 ATK=240 DEF=242 YK=13 BK=2 RK=1 G=1061 dmg=309 door=24/3/0
- MT45 x2y1 fly
- after: HP=10704 ATK=240 DEF=242 YK=13 BK=2 RK=1 G=1061 dmg=309 door=24/3/0

### MT32

- before: HP=10704 ATK=240 DEF=242 YK=13 BK=2 RK=1 G=1061 dmg=309 door=24/3/0
- MT32 x10y1 fly
- after: HP=10704 ATK=240 DEF=242 YK=13 BK=2 RK=1 G=1061 dmg=309 door=24/3/0

### MT45

- before: HP=10704 ATK=240 DEF=242 YK=13 BK=2 RK=1 G=1061 dmg=309 door=24/3/0
- MT45 x2y1 fly
- MT45 x6y2 open yellowDoor [YK 13->12]
- MT45 x6y3 地图伤害 checkBlock [HP 10704->10404]
- MT45 x7y3 kill redWizard [HP 10404->10266, G 1061->1151] (+90G)
- MT45 x7y4 地图伤害 checkBlock [HP 10266->10166]
- MT45 x7y5 kill brownWizard [HP 10166->10038, G 1151->1231] (+80G)
- MT45 x6y5 地图伤害 checkBlock [HP 10038->9838]
- MT45 x5y5 kill redWizard [HP 9838->9700, G 1231->1321] (+90G)
- MT45 x6y6 open yellowDoor [YK 12->11]
- MT45 x4y7 open yellowDoor [YK 11->10]
- MT45 x2y8 open redDoor [RK 1->0]
- MT45 x6y3 地图伤害 checkBlock [HP 9700->9600]
- MT45 x1y1 pass downFloor
- after: HP=9600 ATK=240 DEF=242 YK=10 BK=2 RK=0 G=1321 dmg=1413 door=27/3/1

### MT44

- before: HP=9600 ATK=240 DEF=242 YK=10 BK=2 RK=0 G=1321 dmg=1413 door=27/3/1
- MT44 x1y10 上楼器 upFly
- MT44 x6y9 炸弹 bomb [G 1321->1721] (auto: +400G)
- MT44 x6y8 move [HP 9600->10600, DEF 242->342] (auto: x6y7 redPotion, x6y6 shield5, x6y5 redPotion, x5y6 redPotion, x7y6 redPotion)
- after: HP=10600 ATK=240 DEF=342 YK=10 BK=2 RK=0 G=1721 dmg=1413 door=27/3/1

### MT2

- before: HP=10600 ATK=240 DEF=342 YK=10 BK=2 RK=0 G=1721 dmg=1413 door=27/3/1
- MT2 x1y10 fly
- MT2 x1y9 pass
- MT2 x1y8 move [HP 10600->11200] (auto: x4y10 bluePotion, x3y11 bluePotion, x3y10 bluePotion)
- MT2 x1y11 pass upFloor
- after: HP=11200 ATK=240 DEF=342 YK=10 BK=2 RK=0 G=1721 dmg=1413 door=27/3/1

### MT3

- before: HP=11200 ATK=240 DEF=342 YK=10 BK=2 RK=0 G=1721 dmg=1413 door=27/3/1
- MT3 x11y11 pass upFloor
- after: HP=11200 ATK=240 DEF=342 YK=10 BK=2 RK=0 G=1721 dmg=1413 door=27/3/1

### MT4

- before: HP=11200 ATK=240 DEF=342 YK=10 BK=2 RK=0 G=1721 dmg=1413 door=27/3/1
- MT4 x1y11 pass upFloor
- after: HP=11200 ATK=240 DEF=342 YK=10 BK=2 RK=0 G=1721 dmg=1413 door=27/3/1

### MT5

- before: HP=11200 ATK=240 DEF=342 YK=10 BK=2 RK=0 G=1721 dmg=1413 door=27/3/1
- MT5 x1y1 pass upFloor
- after: HP=11200 ATK=240 DEF=342 YK=10 BK=2 RK=0 G=1721 dmg=1413 door=27/3/1

### MT6

- before: HP=11200 ATK=240 DEF=342 YK=10 BK=2 RK=0 G=1721 dmg=1413 door=27/3/1
- MT6 x11y11 pass upFloor
- after: HP=11200 ATK=240 DEF=342 YK=10 BK=2 RK=0 G=1721 dmg=1413 door=27/3/1

### MT43

- before: HP=11200 ATK=240 DEF=342 YK=10 BK=2 RK=0 G=1721 dmg=1413 door=27/3/1
- MT43 x1y2 fly
- MT43 x1y5 move [G 1721->1761] (auto: x2y5 slimelord)
- MT43 x3y6 open yellowDoor [YK 10->9]
- MT43 x4y7 move [HP 11200->12200, G 1761->1801] (auto: x5y7 slimelord, x6y6 bluePotion)
- MT43 x8y6 open yellowDoor [YK 9->8]
- MT43 x11y6 move [HP 12200->12450, YK 8->9] (auto: x10y8 yellowKey, x11y7 redPotion)
- MT43 x11y5 open yellowDoor [YK 9->8]
- MT43 x9y1 kill whiteKing [HP 12450->12342, G 1801->1901] (+100G)
- MT43 x8y4 move [DEF 342->392, G 1901->2121] (auto: x9y4 shield4, x9y7 brownWizard, x4y4 redWizard, x2y9 redBat)
- after: HP=12342 ATK=240 DEF=392 YK=8 BK=2 RK=0 G=2121 dmg=1521 door=30/3/1

### MT46

- before: HP=12342 ATK=240 DEF=392 YK=8 BK=2 RK=0 G=2121 dmg=1521 door=30/3/1
- MT46 x11y2 fly
- MT46 x10y4 move [G 2121->2291] (auto: x9y4 redBat, x10y6 slimelord, x10y9 brownWizard)
- MT46 x3y4 open yellowDoor [YK 8->7]
- MT46 x3y4 move [HP 12342->12592, ATK 240->245, G 2291->2461] (auto: x2y4 brownWizard, x1y3 redGem, x2y1 redWizard, x1y2 redPotion)
- MT46 x3y1 open yellowDoor [YK 7->6]
- after: HP=12592 ATK=245 DEF=392 YK=6 BK=2 RK=0 G=2461 dmg=1521 door=32/3/1

### MT45

- before: HP=12592 ATK=245 DEF=392 YK=6 BK=2 RK=0 G=2461 dmg=1521 door=32/3/1
- MT45 x10y1 fly
- after: HP=12592 ATK=245 DEF=392 YK=6 BK=2 RK=0 G=2461 dmg=1521 door=32/3/1

### MT46

- before: HP=12592 ATK=245 DEF=392 YK=6 BK=2 RK=0 G=2461 dmg=1521 door=32/3/1
- MT46 x11y2 fly
- MT46 x6y1 shop def [DEF 392->412, G 2461->1341]
- MT46 x6y1 shop def [DEF 412->432, G 1341->1]
- after: HP=12592 ATK=245 DEF=432 YK=6 BK=2 RK=0 G=1 dmg=1521 door=32/3/1

### MT41

- before: HP=12592 ATK=245 DEF=432 YK=6 BK=2 RK=0 G=1 dmg=1521 door=32/3/1
- MT41 x6y10 fly
- after: HP=12592 ATK=245 DEF=432 YK=6 BK=2 RK=0 G=1 dmg=1521 door=32/3/1

### MT42

- before: HP=12592 ATK=245 DEF=432 YK=6 BK=2 RK=0 G=1 dmg=1521 door=32/3/1
- MT42 x5y11 fly
- MT42 x6y5 move [YK 6->11, BK 2->3, RK 0->1, G 1->371] (auto: x6y4 darkKnight, x9y4 brownWizard, x7y1 redKey, x11y4 redWizard, x11y6 brownWizard, x10y2 yellowKey, x10y1 blueKey, x9y2 yellowKey, x11y2 yellowKey, x9y1 yellowKey, x11y1 yellowKey)
- MT42 x4y5 open yellowDoor [YK 11->10]
- MT42 x4y5 move [G 371->411] (auto: x3y5 slimelord)
- MT42 x1y6 open yellowDoor [YK 10->9]
- MT42 x3y7 move [HP 12592->13592, DEF 432->437, YK 9->13, G 411->511] (auto: x3y8 redBat, x3y9 yellowKey, x2y9 yellowKey, x1y9 bluePotion, x1y10 redBat, x1y11 yellowKey, x2y11 yellowKey, x3y11 blueGem)
- after: HP=13592 ATK=245 DEF=437 YK=13 BK=3 RK=1 G=511 dmg=1521 door=34/3/1

### MT43

- before: HP=13592 ATK=245 DEF=437 YK=13 BK=3 RK=1 G=511 dmg=1521 door=34/3/1
- MT43 x1y2 fly
- MT43 x11y8 move [G 511->791] (auto: x7y4 darkKnight, x6y3 darkKnight, x5y1 slimelord)
- MT43 x11y9 open yellowDoor [YK 13->12]
- MT43 x11y10 move [BK 3->4, G 791->841] (auto: x10y10 redBat, x11y11 blueKey)
- MT43 x8y10 open yellowDoor [YK 12->11]
- MT43 x7y9 move [HP 13592->16592, G 841->961] (auto: x6y9 darkKnight, x4y9 bluePotion, x4y10 bluePotion, x4y11 bluePotion)
- MT43 x1y11 pass upFloor
- after: HP=16592 ATK=245 DEF=437 YK=11 BK=4 RK=1 G=961 dmg=1521 door=36/3/1

### MT45

- before: HP=16592 ATK=245 DEF=437 YK=11 BK=4 RK=1 G=961 dmg=1521 door=36/3/1
- MT45 x6y7 move [ATK 245->255, DEF 437->447, YK 11->12, G 961->1421] (auto: x5y3 brownWizard, x7y7 redBat, x3y6 darkKnight, x10y8 redWizard, x11y7 yellowKey, x3y4 darkKnight, x2y5 blueGem, x1y5 blueGem, x2y3 redGem, x1y3 redGem)
- MT45 x11y1 pass upFloor
- after: HP=16592 ATK=255 DEF=447 YK=12 BK=4 RK=1 G=1421 dmg=1521 door=36/3/1

### MT46

- before: HP=16592 ATK=255 DEF=447 YK=12 BK=4 RK=1 G=1421 dmg=1521 door=36/3/1
- MT46 x9y11 open yellowDoor [YK 12->11]
- MT46 x6y11 open blueDoor [BK 4->3]
- MT46 x6y11 move [G 1421->1744] (auto: x4y11 redSlime, x2y11 skeleton, x1y10 bigBat, x1y8 zombie, x1y6 soldier, x3y6 swordsman, x5y6 redKnight, x5y8 slimelord, x4y9 brownWizard, x3y8 bigKey)
- MT46 x7y8 open yellowDoor [YK 11->10]
- MT46 x7y8 move [HP 16592->16842, G 1744->1834] (auto: x7y6 redPotion, x8y7 redWizard)
- MT46 x11y1 pass downFloor
- after: HP=16842 ATK=255 DEF=447 YK=10 BK=3 RK=1 G=1834 dmg=1521 door=38/4/1

### MT45

- before: HP=16842 ATK=255 DEF=447 YK=10 BK=3 RK=1 G=1834 dmg=1521 door=38/4/1
- MT45 x11y1 pass upFloor
- after: HP=16842 ATK=255 DEF=447 YK=10 BK=3 RK=1 G=1834 dmg=1521 door=38/4/1

### MT46

- before: HP=16842 ATK=255 DEF=447 YK=10 BK=3 RK=1 G=1834 dmg=1521 door=38/4/1
- MT46 x6y1 shop def [DEF 447->467, G 1834->254]
- after: HP=16842 ATK=255 DEF=467 YK=10 BK=3 RK=1 G=254 dmg=1521 door=38/4/1

### MT41

- before: HP=16842 ATK=255 DEF=467 YK=10 BK=3 RK=1 G=254 dmg=1521 door=38/4/1
- MT41 x6y10 fly
- MT41 x6y10 魔法钥匙 bigKey
- MT41 x6y6 move [G 254->454] (auto: x5y4 whiteKing, x7y4 whiteKing)
- MT41 x7y6 open blueDoor [BK 3->2]
- MT41 x5y6 open blueDoor [BK 2->1]
- MT41 x1y2 move [HP 16842->19842, ATK 255->260, DEF 467->472, YK 10->16, BK 1->3, G 454->894] (auto: x4y7 slimelord, x3y5 brownWizard, x1y6 redBat, x2y7 redBat, x8y7 slimelord, x3y9 redPotion, x4y10 yellowKey, x9y5 brownWizard, x3y10 yellowKey, x4y11 redGem, x10y7 redBat, x11y6 redBat, x3y11 yellowKey, x8y10 yellowKey, x9y9 redPotion, x4y1 blueKey, x8y11 blueGem, x9y10 yellowKey, x1y1 redPotion, x1y11 bluePotion, x9y11 yellowKey, x8y1 blueKey, x11y11 bluePotion, x11y1 redPotion)
- MT41 x2y2 kill redWizard [G 894->984] (+90G)
- MT41 x10y2 event redWizard
- MT41 x10y2 kill redWizard [G 984->1074] (+90G)
- after: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1074 dmg=1521 door=38/6/1

### MT40

- before: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1074 dmg=1521 door=38/6/1
- MT40 x6y2 fly
- MT40 x6y1 pass upFloor
- after: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1074 dmg=1521 door=38/6/1

### MT41

- before: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1074 dmg=1521 door=38/6/1
- MT41 x6y1 pass downFloor
- after: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1074 dmg=1521 door=38/6/1

### MT40

- before: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1074 dmg=1521 door=38/6/1
- MT40 x6y1 pass upFloor
- after: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1074 dmg=1521 door=38/6/1

### MT42

- before: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1074 dmg=1521 door=38/6/1
- MT42 x5y11 fly
- MT42 x6y10 pass
- MT42 x10y8 move [G 1074->1274] (auto: x9y8 whiteKing, x11y8 whiteKing)
- after: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1274 dmg=1521 door=38/6/1

### MT43

- before: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1274 dmg=1521 door=38/6/1
- MT43 x1y2 fly
- MT43 x1y1 pass downFloor
- after: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1274 dmg=1521 door=38/6/1

### MT42

- before: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1274 dmg=1521 door=38/6/1
- MT42 x2y2 move [G 1274->1314] (auto: x3y2 slimelord)
- MT42 x1y1 pass upFloor
- after: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1314 dmg=1521 door=38/6/1

### MT43

- before: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1314 dmg=1521 door=38/6/1
- MT43 x1y11 pass upFloor
- after: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1314 dmg=1521 door=38/6/1

### MT45

- before: HP=19842 ATK=260 DEF=472 YK=16 BK=3 RK=1 G=1314 dmg=1521 door=38/6/1
- MT45 x11y9 open yellowDoor [YK 16->15]
- MT45 x10y10 move [HP 19842->20842] (auto: x11y11 bluePotion)
- MT45 x9y10 open yellowDoor [YK 15->14]
- MT45 x8y9 kill whiteKing [G 1314->1414] (+100G)
- MT45 x8y11 kill whiteKing [G 1414->1514] (+100G)
- MT45 x5y9 kill darkKnight [G 1514->1634] (+120G)
- MT45 x5y11 kill darkKnight [G 1634->1754] (+120G)
- MT45 x11y5 open yellowDoor [YK 14->13]
- MT45 x11y5 move [G 1754->1794] (auto: x11y4 slimelord)
- MT45 x11y1 pass upFloor
- after: HP=20842 ATK=260 DEF=472 YK=13 BK=3 RK=1 G=1794 dmg=1521 door=41/6/1

### MT46

- before: HP=20842 ATK=260 DEF=472 YK=13 BK=3 RK=1 G=1794 dmg=1521 door=41/6/1
- MT46 x11y11 pass upFloor
- after: HP=20842 ATK=260 DEF=472 YK=13 BK=3 RK=1 G=1794 dmg=1521 door=41/6/1

### MT47

- before: HP=20842 ATK=260 DEF=472 YK=13 BK=3 RK=1 G=1794 dmg=1521 door=41/6/1
- MT47 x8y11 move [G 1794->1834] (auto: x8y9 slimelord)
- MT47 x7y11 open yellowDoor [YK 13->12]
- MT47 x7y11 move [HP 20842->21092, ATK 260->265, G 1834->1914] (auto: x6y10 redGem, x5y11 brownWizard, x4y10 redPotion)
- MT47 x11y7 open yellowDoor [YK 12->11]
- MT47 x11y7 move [YK 11->12, G 1914->2044] (auto: x11y6 redBat, x9y5 brownWizard, x8y6 yellowKey)
- MT47 x8y4 open yellowDoor [YK 12->11]
- MT47 x8y3 move [DEF 472->477, YK 11->13, G 2044->2174] (auto: x9y3 slimelord, x11y3 yellowKey, x11y2 blueGem, x11y1 yellowKey, x8y1 redWizard)
- after: HP=21092 ATK=265 DEF=477 YK=13 BK=3 RK=1 G=2174 dmg=1521 door=44/6/1

### MT48

- before: HP=21092 ATK=265 DEF=477 YK=13 BK=3 RK=1 G=2174 dmg=1521 door=44/6/1
- MT48 x11y10 fly
- MT48 x11y11 pass downFloor
- after: HP=21092 ATK=265 DEF=477 YK=13 BK=3 RK=1 G=2174 dmg=1521 door=44/6/1

### MT47

- before: HP=21092 ATK=265 DEF=477 YK=13 BK=3 RK=1 G=2174 dmg=1521 door=44/6/1
- MT47 x2y6 open yellowDoor [YK 13->12]
- MT47 x3y6 move [G 2174->2224] (auto: x3y5 redBat)
- MT47 x1y10 move [G 2224->2314] (auto: x1y11 redWizard)
- MT47 x4y4 open yellowDoor [YK 12->11]
- MT47 x4y4 move [ATK 265->270, DEF 477->482, YK 11->12, BK 3->4, G 2314->2484] (auto: x5y4 redWizard, x6y5 brownWizard, x5y7 blueKey, x5y8 redGem, x6y7 yellowKey, x6y8 blueGem)
- MT47 x1y1 pass upFloor
- after: HP=21092 ATK=270 DEF=482 YK=12 BK=4 RK=1 G=2484 dmg=1521 door=46/6/1

### MT48

- before: HP=21092 ATK=270 DEF=482 YK=12 BK=4 RK=1 G=2484 dmg=1521 door=46/6/1
- MT48 x4y5 move [G 2484->3134] (auto: x10y7 brownWizard, x9y3 whiteKing, x9y5 whiteKing, x7y3 whiteKing, x7y5 whiteKing, x3y5 slimelord, x1y7 redBat, x1y9 brownWizard)
- MT48 x4y6 open yellowDoor [YK 12->11]
- MT48 x4y6 move [HP 21092->21342, ATK 270->275, G 3134->3214] (auto: x4y7 brownWizard, x3y8 redGem, x5y8 redPotion)
- MT48 x4y9 open yellowDoor [YK 11->10]
- MT48 x4y9 move [HP 21342->22342, DEF 482->487, G 3214->3334] (auto: x4y10 darkKnight, x3y11 blueGem, x5y11 bluePotion)
- MT48 x2y4 open blueDoor [BK 4->3]
- MT48 x2y4 move [HP 22342->23342, G 3334->3424] (auto: x2y3 redWizard, x2y1 bluePotion)
- MT48 x1y11 pass upFloor
- after: HP=23342 ATK=275 DEF=487 YK=10 BK=3 RK=1 G=3424 dmg=1521 door=48/7/1

### MT49

- before: HP=23342 ATK=275 DEF=487 YK=10 BK=3 RK=1 G=3424 dmg=1521 door=48/7/1
- MT49 x3y11 open redDoor [RK 1->0]
- MT49 x5y10 kill redWizard [G 3424->3514] (+90G)
- MT49 x7y10 kill redWizard [G 3514->3604] (+90G)
- MT49 x5y8 kill darkKnight [G 3604->3724] (+120G)
- MT49 x7y8 kill darkKnight [G 3724->3844] (+120G)
- after: HP=23342 ATK=275 DEF=487 YK=10 BK=3 RK=0 G=3844 dmg=1521 door=48/7/2

### MT46

- before: HP=23342 ATK=275 DEF=487 YK=10 BK=3 RK=0 G=3844 dmg=1521 door=48/7/2
- MT46 x11y10 fly
- after: HP=23342 ATK=275 DEF=487 YK=10 BK=3 RK=0 G=3844 dmg=1521 door=48/7/2

### MT35

- before: HP=23342 ATK=275 DEF=487 YK=10 BK=3 RK=0 G=3844 dmg=1521 door=48/7/2
- MT35 x10y1 fly
- after: HP=23342 ATK=275 DEF=487 YK=10 BK=3 RK=0 G=3844 dmg=1521 door=48/7/2

### MT46

- before: HP=23342 ATK=275 DEF=487 YK=10 BK=3 RK=0 G=3844 dmg=1521 door=48/7/2
- MT46 x11y2 fly
- MT46 x6y1 shop def [DEF 487->507, G 3844->2004]
- after: HP=23342 ATK=275 DEF=507 YK=10 BK=3 RK=0 G=2004 dmg=1521 door=48/7/2

### MT18

- before: HP=23342 ATK=275 DEF=507 YK=10 BK=3 RK=0 G=2004 dmg=1521 door=48/7/2
- MT18 x1y2 fly
- MT18 x10y11 move [HP 23342->23442] (auto: x11y11 redPotion)
- after: HP=23442 ATK=275 DEF=507 YK=10 BK=3 RK=0 G=2004 dmg=1521 door=48/7/2

### MT19

- before: HP=23442 ATK=275 DEF=507 YK=10 BK=3 RK=0 G=2004 dmg=1521 door=48/7/2
- MT19 x1y2 fly
- MT19 x4y2 move [HP 23442->23542] (auto: x4y1 redPotion)
- after: HP=23542 ATK=275 DEF=507 YK=10 BK=3 RK=0 G=2004 dmg=1521 door=48/7/2

### MT20

- before: HP=23542 ATK=275 DEF=507 YK=10 BK=3 RK=0 G=2004 dmg=1521 door=48/7/2
- MT20 x6y10 fly
- MT20 x11y10 move [HP 23542->23642] (auto: x11y11 redPotion)
- MT20 x11y9 open yellowDoor [YK 10->9]
- MT20 x11y8 move [G 2004->2010] (auto: x11y7 bat, x10y8 bat)
- MT20 x10y6 open blueDoor [BK 3->2]
- MT20 x10y5 move [HP 23642->24142, YK 9->10] (auto: x10y4 redPotion, x11y5 yellowKey, x11y4 bluePotion)
- after: HP=24142 ATK=275 DEF=507 YK=10 BK=2 RK=0 G=2010 dmg=1521 door=49/8/2

### MT31

- before: HP=24142 ATK=275 DEF=507 YK=10 BK=2 RK=0 G=2010 dmg=1521 door=49/8/2
- MT31 x6y2 fly
- MT31 x9y8 open yellowDoor [YK 10->9]
- MT31 x9y8 move [HP 24142->24942] (auto: x8y8 bluePotion)
- MT31 x6y11 pass upFloor
- after: HP=24942 ATK=275 DEF=507 YK=9 BK=2 RK=0 G=2010 dmg=1521 door=50/8/2

### MT32

- before: HP=24942 ATK=275 DEF=507 YK=9 BK=2 RK=0 G=2010 dmg=1521 door=50/8/2
- MT32 x11y1 pass upFloor
- after: HP=24942 ATK=275 DEF=507 YK=9 BK=2 RK=0 G=2010 dmg=1521 door=50/8/2

### MT33

- before: HP=24942 ATK=275 DEF=507 YK=9 BK=2 RK=0 G=2010 dmg=1521 door=50/8/2
- MT33 x4y11 open blueDoor [BK 2->1]
- MT33 x4y11 move [YK 9->10, G 2010->2085] (auto: x5y10 yellowKey, x6y9 soldier, x7y10 slimeMan, x8y10 flower)
- after: HP=24942 ATK=275 DEF=507 YK=10 BK=1 RK=0 G=2085 dmg=1521 door=50/9/2

### MT46

- before: HP=24942 ATK=275 DEF=507 YK=10 BK=1 RK=0 G=2085 dmg=1521 door=50/9/2
- MT46 x11y2 fly
- after: HP=24942 ATK=275 DEF=507 YK=10 BK=1 RK=0 G=2085 dmg=1521 door=50/9/2

### MT38

- before: HP=24942 ATK=275 DEF=507 YK=10 BK=1 RK=0 G=2085 dmg=1521 door=50/9/2
- MT38 x10y1 fly
- after: HP=24942 ATK=275 DEF=507 YK=10 BK=1 RK=0 G=2085 dmg=1521 door=50/9/2

### MT28

- before: HP=24942 ATK=275 DEF=507 YK=10 BK=1 RK=0 G=2085 dmg=1521 door=50/9/2
- MT28 x2y11 fly
- MT28 x8y4 trader specialTrader [YK 10->9, G 2085->2185] (auto: +100G)
- after: HP=24942 ATK=275 DEF=507 YK=9 BK=1 RK=0 G=2185 dmg=1521 door=50/9/2

### MT48

- before: HP=24942 ATK=275 DEF=507 YK=9 BK=1 RK=0 G=2185 dmg=1521 door=50/9/2
- MT48 x11y10 fly
- MT48 x5y2 open blueDoor [BK 1->0]
- MT48 x5y2 move [HP 24942->25692] (auto: x7y1 redPotion, x8y1 redPotion, x9y1 redPotion)
- after: HP=25692 ATK=275 DEF=507 YK=9 BK=0 RK=0 G=2185 dmg=1521 door=50/10/2

### MT46

- before: HP=25692 ATK=275 DEF=507 YK=9 BK=0 RK=0 G=2185 dmg=1521 door=50/10/2
- MT46 x11y10 fly
- MT46 x6y1 shop def [DEF 507->527, G 2185->65]
- after: HP=25692 ATK=275 DEF=527 YK=9 BK=0 RK=0 G=65 dmg=1521 door=50/10/2

### MT35

- before: HP=25692 ATK=275 DEF=527 YK=9 BK=0 RK=0 G=65 dmg=1521 door=50/10/2
- MT35 x10y1 fly
- MT35 x6y7 kill magicDragon [HP 25692->21385, G 65->865] (+800G)
- MT35 x6y6 take snow [HP 21385->23785] (auto: x6y5 bluePotion, x5y5 bluePotion, x7y5 bluePotion)
- after: HP=23785 ATK=275 DEF=527 YK=9 BK=0 RK=0 G=865 dmg=5828 door=50/10/2

### MT13

- before: HP=23785 ATK=275 DEF=527 YK=9 BK=0 RK=0 G=865 dmg=5828 door=50/10/2
- MT13 x10y11 fly
- MT13 x6y10 open yellowDoor [YK 9->8]
- MT13 x6y10 move [ATK 275->375] (auto: x6y9 lava, x6y8 lava, x5y9 lava, x7y9 lava, x6y7 lava, x5y8 lava, x7y8 lava, x4y9 lava, x8y9 lava, x6y6 lava, x4y8 lava, x8y8 lava, x3y9 lava, x9y9 lava, x6y5 sword5, x4y7 lava, x3y8 lava, x8y7 lava, x9y8 lava, x2y9 lava, x10y9 lava, x3y7 lava, x2y8 lava, x9y7 lava, x10y8 lava, x1y9 lava, x11y9 lava, x3y6 lava, x2y7 lava, x1y8 lava, x9y6 lava, x10y7 lava, x11y8 lava, x3y5 lava, x2y6 lava, x1y7 lava, x9y5 lava, x10y6 lava, x11y7 lava, x3y4 lava, x2y5 lava, x1y6 lava, x9y4 lava, x10y5 lava, x11y6 lava, x3y3 lava, x2y4 lava, x1y5 lava, x9y3 lava, x10y4 lava, x11y5 lava, x3y2 lava, x2y3 lava, x4y3 lava, x1y4 lava, x9y2 lava, x8y3 lava, x10y3 lava, x11y4 lava, x3y1 lava, x2y2 lava, x4y2 lava, x1y3 lava, x9y1 lava, x8y2 lava, x10y2 lava, x11y3 lava, x2y1 lava, x4y1 lava, x1y2 lava, x5y2 lava, x8y1 lava, x10y1 lava, x7y2 lava, x11y2 lava, x1y1 lava, x5y1 lava, x6y2 lava, x7y1 lava, x11y1 lava, x6y1 lava)
- after: HP=23785 ATK=375 DEF=527 YK=8 BK=0 RK=0 G=865 dmg=5828 door=51/10/2

### MT12

- before: HP=23785 ATK=375 DEF=527 YK=8 BK=0 RK=0 G=865 dmg=5828 door=51/10/2
- MT12 x2y11 fly
- MT12 x4y5 open yellowDoor [YK 8->7]
- MT12 x3y5 move [G 865->887] (auto: x2y5 redPriest)
- MT12 x1y4 open yellowDoor [YK 7->6]
- MT12 x3y3 move [G 887->899] (auto: x3y2 bigBat, x2y1 fakeWall)
- MT12 x1y1 trader redKey1 [RK 0->1, G 899->99]
- after: HP=23785 ATK=375 DEF=527 YK=6 BK=0 RK=1 G=99 dmg=5828 door=53/10/2

### MT24

- before: HP=23785 ATK=375 DEF=527 YK=6 BK=0 RK=1 G=99 dmg=5828 door=53/10/2
- MT24 x2y11 fly
- MT24 x2y10 pass upFloor
- after: HP=23785 ATK=375 DEF=527 YK=6 BK=0 RK=1 G=99 dmg=5828 door=53/10/2

### MT25

- before: HP=23785 ATK=375 DEF=527 YK=6 BK=0 RK=1 G=99 dmg=5828 door=53/10/2
- MT25 x6y10 open redDoor [RK 1->0]
- MT25 x6y9 pass
- MT25 x6y6 kill blackMagician [HP 23785->21508, G 99->1099] (+1000G)
- MT25 x6y8 move [RK 0->4] (auto: x5y8 redKey, x7y8 redKey, x4y8 redKey, x8y8 redKey)
- MT25 x1y11 pass upFloor
- after: HP=21508 ATK=375 DEF=527 YK=6 BK=0 RK=4 G=1099 dmg=8105 door=53/10/3

### MT26

- before: HP=21508 ATK=375 DEF=527 YK=6 BK=0 RK=4 G=1099 dmg=8105 door=53/10/3
- MT26 x6y10 open redDoor [RK 4->3]
- MT26 x6y9 open redDoor [RK 3->2]
- MT26 x6y8 open redDoor [RK 2->1]
- MT26 x6y6 event princess
- MT26 x1y11 pass downFloor
- after: HP=21508 ATK=375 DEF=527 YK=6 BK=0 RK=1 G=1099 dmg=8105 door=53/10/6

### MT25

- before: HP=21508 ATK=375 DEF=527 YK=6 BK=0 RK=1 G=1099 dmg=8105 door=53/10/6
- MT25 x2y10 pass downFloor
- after: HP=21508 ATK=375 DEF=527 YK=6 BK=0 RK=1 G=1099 dmg=8105 door=53/10/6

### MT24

- before: HP=21508 ATK=375 DEF=527 YK=6 BK=0 RK=1 G=1099 dmg=8105 door=53/10/6
- MT24 x6y8 open redDoor [RK 1->0]
- MT24 x6y2 pass
- after: HP=21508 ATK=375 DEF=527 YK=6 BK=0 RK=0 G=1099 dmg=8105 door=53/10/7

### MT50

- before: HP=21508 ATK=375 DEF=527 YK=6 BK=0 RK=0 G=1099 dmg=8105 door=53/10/7
- MT50 x6y5 pass thief
- MT50 x6y5 event redKing
- after: HP=21508 ATK=375 DEF=527 YK=6 BK=0 RK=0 G=1099 dmg=8105 door=53/10/7

### MT49

- before: HP=21508 ATK=375 DEF=527 YK=6 BK=0 RK=0 G=1099 dmg=8105 door=53/10/7
- MT49 x6y7 下楼器 downFly
- MT49 x6y6 pass
- MT49 x6y6 event redKing
- MT49 x6y4 kill whiteKing [G 1099->1199] (+100G)
- MT49 x7y3 kill whiteKing [G 1199->1299] (+100G)
- MT49 x6y2 kill whiteKing [G 1299->1399] (+100G)
- MT49 x5y3 kill whiteKing [G 1399->1499] (+100G)
- MT49 x5y2 kill whiteKing [G 1499->1599] (+100G)
- MT49 x7y2 kill whiteKing [G 1599->1699] (+100G)
- MT49 x7y4 kill whiteKing [G 1699->1799] (+100G)
- MT49 x5y4 kill whiteKing [G 1799->1899] (+100G)
- MT49 x6y3 kill redKing [G 1899->2399] (+500G)
- MT49 x6y4 move [HP 21508->24508, ATK 375->390, DEF 527->542, RK 0->1] (auto: x6y5 bluePotion, x4y4 redGem, x5y5 bluePotion, x7y5 bluePotion, x8y4 blueGem, x5y2 redKey, x7y2 knife, x3y4 redGem, x9y4 blueGem, x2y4 redGem, x10y4 blueGem)
- after: HP=24508 ATK=390 DEF=542 YK=6 BK=0 RK=1 G=2399 dmg=8105 door=53/10/7

### MT45

- before: HP=24508 ATK=390 DEF=542 YK=6 BK=0 RK=1 G=2399 dmg=8105 door=53/10/7
- MT45 x10y1 fly
- MT45 x9y3 trader hp2000 [HP 24508->26508, G 2399->1399]
- after: HP=26508 ATK=390 DEF=542 YK=6 BK=0 RK=1 G=1399 dmg=8105 door=53/10/7

### MT3

- before: HP=26508 ATK=390 DEF=542 YK=6 BK=0 RK=1 G=1399 dmg=8105 door=53/10/7
- MT3 x10y11 fly
- after: HP=26508 ATK=390 DEF=542 YK=6 BK=0 RK=1 G=1399 dmg=8105 door=53/10/7

### MT46

- before: HP=26508 ATK=390 DEF=542 YK=6 BK=0 RK=1 G=1399 dmg=8105 door=53/10/7
- MT46 x11y2 fly
- after: HP=26508 ATK=390 DEF=542 YK=6 BK=0 RK=1 G=1399 dmg=8105 door=53/10/7

### MT3

- before: HP=26508 ATK=390 DEF=542 YK=6 BK=0 RK=1 G=1399 dmg=8105 door=53/10/7
- MT3 x10y11 fly
- MT3 x9y2 open yellowDoor [YK 6->5]
- MT3 x9y2 move [HP 26508->26558, G 1399->1402] (auto: x10y2 bat, x11y1 redPotion)
- MT3 x11y11 pass upFloor
- after: HP=26558 ATK=390 DEF=542 YK=5 BK=0 RK=1 G=1402 dmg=8105 door=54/10/7

### MT4

- before: HP=26558 ATK=390 DEF=542 YK=5 BK=0 RK=1 G=1402 dmg=8105 door=54/10/7
- MT4 x1y11 pass upFloor
- after: HP=26558 ATK=390 DEF=542 YK=5 BK=0 RK=1 G=1402 dmg=8105 door=54/10/7

### MT8

- before: HP=26558 ATK=390 DEF=542 YK=5 BK=0 RK=1 G=1402 dmg=8105 door=54/10/7
- MT8 x1y2 fly
- MT8 x1y3 open yellowDoor [YK 5->4]
- MT8 x1y3 move [HP 26558->26608, G 1402->1407] (auto: x1y5 redPotion, x2y6 redSlime, x3y6 greenSlime, x4y6 redSlime)
- after: HP=26608 ATK=390 DEF=542 YK=4 BK=0 RK=1 G=1407 dmg=8105 door=55/10/7

### MT49

- before: HP=26608 ATK=390 DEF=542 YK=4 BK=0 RK=1 G=1407 dmg=8105 door=55/10/7
- MT49 x2y11 fly
- MT49 x2y11 使用 superPotion [HP 26608->33508]
- after: HP=33508 ATK=390 DEF=542 YK=4 BK=0 RK=1 G=1407 dmg=8105 door=55/10/7

### MT24

- before: HP=33508 ATK=390 DEF=542 YK=4 BK=0 RK=1 G=1407 dmg=8105 door=55/10/7
- MT24 x2y11 fly
- MT24 x6y2 pass
- after: HP=33508 ATK=390 DEF=542 YK=4 BK=0 RK=1 G=1407 dmg=8105 door=55/10/7

### MT50

- before: HP=33508 ATK=390 DEF=542 YK=4 BK=0 RK=1 G=1407 dmg=8105 door=55/10/7
- MT50 x6y5 kill redKing [G 1407->1907] (+500G)
- after: HP=33508 ATK=390 DEF=542 YK=4 BK=0 RK=1 G=1907 dmg=8105 door=55/10/7
