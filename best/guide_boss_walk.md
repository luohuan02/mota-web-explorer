# 攻略基线 Boss Walk

手写攻略来源：
https://www.taptap.cn/moment/15225056477054087

分数模型：

- `1YK = 50HP`、`1BK = 4YK = 200HP`、`100G = 1YK = 50HP`。
- 本文件记录当前全图 final-score 模型下的固定攻略基线。

攻略基线：

```text
HP=25 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=304 dmg=2601 door=40/2/1 final-score=1327.5
```

固定攻略基线作为干净评分回放状态存于此。原始逐步手写路线见上面 TapTap 攻略链接。

# 用户验证的 9F 后路线 Walk

> 前缀: fixed 4-9 拿盾并取 9F 红蓝宝石
> 前缀状态: HP=148 ATK=23 DEF=21 YK=2 BK=1 RK=0 dmg=928 door=23/0/0
> 最终状态: HP=25 ATK=27 DEF=27 YK=0 BK=0 RK=0 dmg=2601 door=40/2/1

## 修正说明

- 6F 段补入 `x8y11` 红血瓶，原手写 `x9y10` 是空地。
- 9F 上 10F 段补入 `x2y10` 红血瓶。
- 1F `x1y3` 红血瓶未被 1-3 固定路线吃掉，可以在 Boss 前补血。

## 6F blue gem

- MT6 x9y9 击杀redSlime
- MT6 x8y11 拾取redPotion HP=148->198
- MT6 x9y11 拾取redPotion HP=198->248
- MT6 x9y10 路过
- MT6 x5y11 击杀skeleton HP=248->206
- MT6 x2y11 击杀greenSlime
- MT6 x1y10 开yellowDoor YK=2->1
- MT6 x2y9 击杀bat HP=206->189
- MT6 x4y9 拾取blueGem DEF=21->22
=> HP=189 ATK=23 DEF=22 YK=1 BK=1 RK=0 本段dmg=59 累计dmg=987 door=24/0/0

## 3F blue gem

- MT3 x3y5 击杀bat HP=189->173
- MT3 x1y4 开yellowDoor YK=1->0
- MT3 x1y3 击杀bluePriest HP=173->143
- MT3 x1y1 拾取yellowKey YK=0->1
- MT3 x2y2 拾取redPotion HP=143->193
- MT3 x2y1 拾取blueGem DEF=22->23
=> HP=193 ATK=23 DEF=23 YK=1 BK=1 RK=0 本段dmg=46 累计dmg=1033 door=25/0/0

## 8F red+blue gems

- MT8 x7y5 击杀bluePriest HP=193->166
- MT8 x7y7 击杀bat HP=166->151
- MT8 x6y8 击杀skeleton HP=151->113
- MT8 x4y8 击杀bat HP=113->98
- MT8 x1y9 开yellowDoor YK=1->0
- MT8 x1y10 击杀greenSlime
- MT8 x2y11 击杀bat HP=98->83
- MT8 x3y11 开blueDoor BK=1->0
- MT8 x4y11 拾取yellowKey YK=0->1
- MT8 x4y10 拾取redGem ATK=23->24
- MT8 x5y10 拾取yellowKey YK=1->2
- MT8 x5y11 拾取blueGem DEF=23->24
=> HP=83 ATK=24 DEF=24 YK=2 BK=0 RK=0 本段dmg=110 累计dmg=1143 door=26/1/0

## 1F red+blue gems

- MT1 x6y6 开yellowDoor YK=2->1
- MT1 x7y6 击杀bat HP=83->69
- MT1 x8y6 击杀bluePriest HP=69->45
- MT1 x9y6 击杀bat HP=45->31
- MT1 x9y5 开yellowDoor YK=1->0
- MT1 x8y4 拾取redPotion HP=31->81
- MT1 x8y3 拾取yellowKey YK=0->1
- MT1 x7y3 拾取redGem ATK=24->25
- MT1 x7y4 拾取blueGem DEF=24->25
=> HP=81 ATK=25 DEF=25 YK=1 BK=0 RK=0 本段dmg=52 累计dmg=1195 door=28/1/0

## 3F red gem

- MT3 x1y6 开yellowDoor YK=1->0
- MT3 x1y7 击杀skeleton HP=81->47
- MT3 x1y9 拾取redPotion HP=47->97
- MT3 x2y8 拾取yellowKey YK=0->1
- MT3 x2y9 拾取redGem ATK=25->26
=> HP=97 ATK=26 DEF=25 YK=1 BK=0 RK=0 本段dmg=34 累计dmg=1229 door=29/1/0

## 5F blue gem

- MT5 x2y7 击杀skeletonSoldier HP=97->16
- MT5 x2y9 拾取yellowKey YK=1->2
- MT5 x3y9 拾取redPotion HP=16->66
- MT5 x1y9 拾取blueGem DEF=25->26
=> HP=66 ATK=26 DEF=26 YK=2 BK=0 RK=0 本段dmg=81 累计dmg=1310 door=29/1/0

## 4F blue key

- MT4 x2y5 击杀bluePriest HP=66->48
- MT4 x2y4 开yellowDoor YK=2->1
- MT4 x1y2 拾取redPotion HP=48->98
- MT4 x3y2 拾取yellowKey YK=1->2
- MT4 x2y1 拾取blueKey BK=0->1
=> HP=98 ATK=26 DEF=26 YK=2 BK=1 RK=0 本段dmg=18 累计dmg=1328 door=30/1/0

## 9F up to 10F

- MT9 x7y6 击杀redSlime
- MT9 x7y10 击杀bat HP=98->86
- MT9 x6y11 开yellowDoor YK=2->1
- MT9 x3y11 开blueDoor BK=1->0
- MT9 x2y10 拾取redPotion HP=86->136
- MT9 x1y11 通过upFloor
=> HP=136 ATK=26 DEF=26 YK=1 BK=0 RK=0 本段dmg=12 累计dmg=1340 door=31/2/0

## 10F blue gem

- MT10 x1y9 开yellowDoor YK=1->0
- MT10 x1y6 击杀skeleton HP=136->104
- MT10 x2y6 拾取blueGem DEF=26->27
=> HP=104 ATK=26 DEF=27 YK=0 BK=0 RK=0 本段dmg=32 累计dmg=1372 door=32/2/0

## 7F six yellow keys and HP

- MT7 x9y5 击杀skeleton HP=104->74
- MT7 x9y3 拾取redPotion HP=74->124
- MT7 x9y2 拾取yellowKey YK=0->1
- MT7 x9y1 拾取yellowKey YK=1->2
- MT7 x9y7 击杀skeletonSoldier HP=124->49
- MT7 x9y9 拾取bluePotion HP=49->249
- MT7 x9y10 拾取yellowKey YK=2->3
- MT7 x9y11 拾取yellowKey YK=3->4
- MT7 x5y7 开yellowDoor YK=4->3
- MT7 x5y9 击杀bat HP=249->238
- MT7 x5y10 拾取yellowKey YK=3->4
- MT7 x5y11 拾取yellowKey YK=4->5
=> HP=238 ATK=26 DEF=27 YK=5 BK=0 RK=0 本段dmg=116 累计dmg=1488 door=33/2/0

## 10F red gem

- MT10 x3y9 开yellowDoor YK=5->4
- MT10 x4y11 击杀bluePriest HP=238->223
- MT10 x8y11 击杀bluePriest HP=223->208
- MT10 x9y9 开yellowDoor YK=4->3
- MT10 x9y6 击杀skeleton HP=208->178
- MT10 x10y6 拾取redGem ATK=26->27
=> HP=178 ATK=27 DEF=27 YK=3 BK=0 RK=0 本段dmg=60 累计dmg=1548 door=35/2/0

## 10F blue potion

- MT10 x11y9 开yellowDoor YK=3->2
- MT10 x11y11 拾取bluePotion HP=178->378
=> HP=378 ATK=27 DEF=27 YK=2 BK=0 RK=0 本段dmg=0 累计dmg=1548 door=36/2/0

## 7F blue potion

- MT7 x7y7 开yellowDoor YK=2->1
- MT7 x7y9 击杀redSlime
- MT7 x7y10 击杀bluePriest HP=378->363
- MT7 x7y11 拾取bluePotion HP=363->563
=> HP=563 ATK=27 DEF=27 YK=1 BK=0 RK=0 本段dmg=15 累计dmg=1563 door=37/2/0

## 8F red key

- MT8 x8y8 击杀bluePriest HP=563->548
- MT8 x10y7 开yellowDoor YK=1->0
- MT8 x9y5 击杀yellowGuard HP=548->359
- MT8 x11y5 击杀yellowGuard HP=359->170
- MT8 x10y4 路过
- MT8 x9y3 拾取bluePotion HP=170->370
- MT8 x9y1 拾取yellowKey YK=0->1
- MT8 x11y3 拾取redPotion HP=370->420
- MT8 x11y1 拾取yellowKey YK=1->2
- MT8 x10y2 拾取redKey RK=0->1
=> HP=420 ATK=27 DEF=27 YK=2 BK=0 RK=1 本段dmg=393 累计dmg=1956 door=38/2/0

## 1F final HP refill

- MT1 x10y9 开yellowDoor YK=2->1
- MT1 x10y10 击杀bat HP=420->409
- MT1 x10y11 拾取bluePotion HP=409->609
- MT1 x4y3 开yellowDoor YK=1->0
- MT1 x1y3 拾取redPotion HP=609->659
=> HP=659 ATK=27 DEF=27 YK=0 BK=0 RK=1 本段dmg=11 累计dmg=1967 door=40/2/0

## 10F boss

- MT10 x6y9 开redDoor RK=1->0
- MT10 x6y5 触发Boss事件
- MT10 x5y4 击杀skeletonSoldier HP=659->584
- MT10 x7y4 击杀skeletonSoldier HP=584->509
- MT10 x6y4 击杀skeleton HP=509->479
- MT10 x5y5 击杀skeleton HP=479->449
- MT10 x7y5 击杀skeleton HP=449->419
- MT10 x5y6 击杀skeleton HP=419->389
- MT10 x6y6 击杀skeleton HP=389->359
- MT10 x7y6 击杀skeleton HP=359->329
- MT10 x6y1 击杀skeletonCaptain HP=329->25
=> HP=25 ATK=27 DEF=27 YK=0 BK=0 RK=0 本段dmg=634 累计dmg=2601 door=40/2/1

## Final

**HP=25 ATK=27 DEF=27 YK=0 BK=0 RK=0 dmg=2601 door=40/2/1**
