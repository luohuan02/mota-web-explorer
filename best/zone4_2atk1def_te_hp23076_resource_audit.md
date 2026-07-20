# 4区终战前剩余资源审计

- 目标：`2026复刻版 / 纯净版-TE / 生命`
- 终战前基线：`{'floor': 'MT24', 'x': 6, 'y': 2, 'hp': 23076, 'atk': 417, 'def': 475, 'yk': 5, 'bk': 1, 'rk': 0, 'gold': 406, 'dmg': 14479, 'yd': 51, 'bd': 11, 'rd': 7, 'times1': 15}`
- 下一次 46F 生命商店成本：`2420G`
- 有效资金（金币 + 可售黄钥匙）：`906G`
- 幸运金币：`False`；怪物金币倍率：`1x`
- 真魔王战后 500G 不计作可消费资源。

## 剩余资源计数

- `enemy:bigBat`：6
- `enemy:blackSlime`：4
- `enemy:darkKnight`：2
- `enemy:greenSlime`：2
- `enemy:redPriest`：1
- `enemy:redSlime`：1
- `enemy:skeletonSoldier`：2
- `enemy:slimeMan`：1
- `enemy:soldier`：2
- `enemy:swordsman`：1
- `enemy:whiteKing`：2
- `enemy:zombie`：1
- `enemy:zombieKnight`：1
- `item:yellowKey`：6

## 可达目标探针（按单次点击链的实际变化排序）

| 位置 | 类型 | HP | 攻 | 防 | 黄/蓝/红钥匙 | 金币 | 开门 |
|---|---|---:|---:|---:|---:|---:|---:|
| MT33 x1y10 | enemy:swordsman | +0 | +0 | +0 | +0/+0/+0 | +130 | +1/+0/+0 |
| MT33 x1y11 | item:yellowKey | +0 | +0 | +0 | +0/+0/+0 | +130 | +1/+0/+0 |
| MT33 x2y11 | enemy:soldier | +0 | +0 | +0 | +0/+0/+0 | +130 | +1/+0/+0 |
| MT33 x3y9 | enemy:zombieKnight | +0 | +0 | +0 | +0/+0/+0 | +130 | +1/+0/+0 |
| MT45 x8y9 | enemy:whiteKing | +0 | +0 | +0 | -1/+0/+0 | +100 | +1/+0/+0 |
| MT45 x8y11 | enemy:whiteKing | +0 | +0 | +0 | -1/+0/+0 | +100 | +1/+0/+0 |
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

## 清场策略对比

| 策略 | 可执行 | HP变化 | 金币变化 | 钥匙变化 | 新增步骤 |
|---|---:|---:|---:|---:|---:|
| zero_damage | True | +0 | +0 | +0/+0/+0 | 0 |
| resources | True | +0 | +0 | +0/+0/+0 | 0 |
| hp_first | True | +0 | +0 | +0/+0/+0 | 0 |
| fixed_point | True | +0 | +0 | +0/+0/+0 | 0 |

## 终战闭环断言

- `fixed_point_hp_delta_zero`：通过
- `fixed_point_shop_count_unchanged`：通过
- `no_reachable_positive_hp_target`：通过
- `mt49_event_rewards_cleared`：通过
