# 4区终战前剩余资源审计

- 目标：`2026复刻版 / 纯净版-TE / 生命`
- 终战前基线：`{'floor': 'MT24', 'x': 6, 'y': 2, 'hp': 18277, 'atk': 439, 'def': 425, 'yk': 3, 'bk': 1, 'rk': 0, 'gold': 1846, 'dmg': 17418, 'yd': 49, 'bd': 10, 'rd': 7, 'times1': 15}`
- 下一次 46F 生命商店成本：`2420G`
- 有效资金（金币 + 可售黄钥匙）：`2146G`
- 真魔王战后 500G 不计作可消费资源。

## 剩余资源计数

- `enemy:bigBat`：6
- `enemy:blackSlime`：4
- `enemy:greenSlime`：2
- `enemy:redPriest`：1
- `enemy:redSlime`：1
- `enemy:skeletonSoldier`：2
- `enemy:slimeMan`：1
- `enemy:soldier`：2
- `enemy:swordsman`：1
- `enemy:zombie`：1
- `enemy:zombieKnight`：1
- `item:blueGem`：2
- `item:redGem`：2
- `item:yellowKey`：6

## 可达目标探针（按单次点击链的实际变化排序）

| 位置 | 类型 | HP | 攻 | 防 | 黄/蓝/红钥匙 | 金币 | 开门 |
|---|---|---:|---:|---:|---:|---:|---:|
| MT33 x1y10 | enemy:swordsman | +0 | +0 | +0 | +0/+0/+0 | +130 | +1/+0/+0 |
| MT33 x1y11 | item:yellowKey | +0 | +0 | +0 | +0/+0/+0 | +130 | +1/+0/+0 |
| MT33 x2y11 | enemy:soldier | +0 | +0 | +0 | +0/+0/+0 | +130 | +1/+0/+0 |
| MT33 x3y9 | enemy:zombieKnight | +0 | +0 | +0 | +0/+0/+0 | +130 | +1/+0/+0 |
| MT18 x4y9 | enemy:bigBat | +0 | +0 | +0 | +0/+0/+0 | +48 | +1/+0/+0 |
| MT18 x4y10 | enemy:bigBat | +0 | +0 | +0 | +0/+0/+0 | +48 | +1/+0/+0 |
| MT18 x5y9 | enemy:bigBat | +0 | +0 | +0 | +0/+0/+0 | +48 | +1/+0/+0 |
| MT18 x5y10 | enemy:bigBat | +0 | +0 | +0 | +0/+0/+0 | +48 | +1/+0/+0 |
| MT18 x5y11 | item:yellowKey | +0 | +0 | +0 | +0/+0/+0 | +48 | +1/+0/+0 |
| MT12 x3y2 | enemy:bigBat | +0 | +0 | +0 | -2/+0/+0 | +34 | +2/+0/+0 |
| MT18 x7y9 | enemy:blackSlime | +0 | +0 | +0 | +0/+0/+0 | +32 | +1/+0/+0 |
| MT18 x7y10 | enemy:blackSlime | +0 | +0 | +0 | +0/+0/+0 | +32 | +1/+0/+0 |
| MT18 x7y11 | item:yellowKey | +0 | +0 | +0 | +0/+0/+0 | +32 | +1/+0/+0 |
| MT18 x8y9 | enemy:blackSlime | +0 | +0 | +0 | +0/+0/+0 | +32 | +1/+0/+0 |
| MT18 x8y10 | enemy:blackSlime | +0 | +0 | +0 | +0/+0/+0 | +32 | +1/+0/+0 |
| MT11 x5y5 | enemy:zombie | +0 | +0 | +0 | -1/+0/+0 | +30 | +1/+0/+0 |
| MT11 x6y4 | enemy:bigBat | +0 | +0 | +0 | -1/+0/+0 | +30 | +1/+0/+0 |
| MT12 x2y5 | enemy:redPriest | +0 | +0 | +0 | -1/+0/+0 | +22 | +1/+0/+0 |
| MT9 x1y7 | item:yellowKey | +0 | +0 | +0 | +0/+0/+0 | +8 | +1/+0/+0 |
| MT9 x1y8 | enemy:skeletonSoldier | +0 | +0 | +0 | +0/+0/+0 | +8 | +1/+0/+0 |
| MT9 x4y7 | enemy:skeletonSoldier | +0 | +0 | +0 | +0/+0/+0 | +8 | +1/+0/+0 |
| MT9 x5y7 | item:yellowKey | +0 | +0 | +0 | +0/+0/+0 | +8 | +1/+0/+0 |
| MT7 x11y1 | enemy:greenSlime | +0 | +0 | +0 | -1/+0/+0 | +4 | +1/+0/+0 |
| MT7 x11y2 | enemy:redSlime | +0 | +0 | +0 | -1/+0/+0 | +4 | +1/+0/+0 |
| MT7 x11y3 | enemy:greenSlime | +0 | +0 | +0 | -1/+0/+0 | +4 | +1/+0/+0 |
| MT32 x1y1 | item:blueGem | +0 | +4 | +4 | -1/+0/+0 | +0 | +1/+0/+0 |
| MT32 x2y2 | item:redGem | +0 | +4 | +4 | -1/+0/+0 | +0 | +1/+0/+0 |
| MT31 x4y8 | item:blueGem | +0 | +0 | +4 | -1/+0/+0 | +0 | +1/+0/+0 |
| MT31 x8y4 | item:redGem | +0 | +4 | +0 | -1/+0/+0 | +0 | +1/+0/+0 |

## 清场策略对比

| 策略 | 可执行 | HP变化 | 金币变化 | 钥匙变化 | 新增步骤 |
|---|---:|---:|---:|---:|---:|
| zero_damage | True | +0 | +0 | +0/+0/+0 | 0 |
| resources | True | +0 | +0 | -3/+0/+0 | 8 |
| hp_first | True | +0 | +0 | +0/+0/+0 | 0 |
| fixed_point | True | +0 | +0 | +0/+0/+0 | 0 |

## 终战闭环断言

- `fixed_point_hp_delta_zero`：通过
- `fixed_point_shop_count_unchanged`：通过
- `no_reachable_positive_hp_target`：通过
- `effective_funding_below_next_hp_shop`：通过
- `mt49_event_rewards_cleared`：通过
