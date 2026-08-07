# zone2 经验（2攻线，MT10 Boss 后 -> MT20 吸血鬼）

来源 = **2 攻线通用经验**（2攻+防延后 4 区 + 宝石序 + cross + vampire 机制，两 redKey 变体共享）。当前 zone1-2 最优 = **KILL 线** `best/zone12_2atk0def_recording_walk.md`（358 步 MT4-20，2攻0def 杀 zKnight，auto ON，web 0 mismatch；源 JSON `outputs/results/zone12_2atk0def_recording_walk.json`，生成器 `scripts/search/recording_to_game.py`），zone2 末（MT20 vampire 后）**HP=1215 ATK=76 DEF=66 YK=5**。旧买红钥匙 2 攻线（autoon 复刻 `best/zone12_2atk_recording_walk.md`，HP=1249 DEF=64 MT31）walk 已删，数值保留作下文 D8 redKey 买/杀对比。另参考官方纯净版-TE 41477（2攻+800红钥匙+4区爆防）。

经验记**策略思路 + 关键抉择 + 事件机制**，详细坐标/数据看 walk。宝石顺序的数值依据来自 Game 类实测 + 已验证 walk 的 before/after。

## 核心策略：2攻 + 防延后到 4 区

zone2 中心抉择 = **MT12 商店只买 2 攻**（ATK 30->38），不买第 3 攻、不买防。省下的 80G 延后到 4 区买防（ratio 5，+20 DEF）。这与 2ATK1DEF 分支（2攻+1防）和 canonical 3ATK 都不同。原因全是资源花费对比（用户原则：同样目的少花资源）。

## 复刻方法论：auto ON + skip-if-cleared（录像驱动，旧 fallback）

> 当前主流程 = `recording_to_game.py` converter（逐格 captured path，见 `recording_converter_experience.md`）。autoon 仅在录像路径恰好 Game 兼容时作 fallback；用户手玩调整路径常不兼容，用 converter。

2攻线 ground truth 是录像（auto OFF 显式步），离线用 **auto ON** 复刻（1/2区全开 per CLAUDE.md）。机制（`zone12_recording_autoon.py`）：

- 按录像 statlog 的 hero 位置顺序走。
- 下一目标格若已被 auto 清空（`block_at is None` -- 道具已拾/怪已杀/门已开/fakeWall 已破），**跳过**该步（auto 已做），走下一个真实目标。
- 否则 `go_to(target)` auto ON；auto_sweep 顺带清路上的零伤怪/道具/暗墙。这就是「杀 (8,2) 史莱姆 -> auto 拾 (8,3)(8,4)(9,3)(9,4)」「走到 (10,11) -> auto 拾 (11,11) 剑（随后 (11,11) 步跳过）」的来源。
- 楼层切换：相邻层走楼梯，跨层 fly。
- 商店/商人购买：同层同位 + gold 变化判定，走 `buy_shop`/`talk_trader`（录像是 auto OFF 显式买）。
- **金币口径**：auto ON 比 auto OFF 录像多杀零伤小怪，gold 比录像高约 +190（录像 176 vs walk 367），**HP/ATK/DEF/YK/BK/RK/位置 全精确匹配**，gold 差已接受。web 验证比的是 walk JSON vs 实机（0 mismatch），不是 walk vs 录像 gold。

事件触发（录像 auto OFF 用 choices 触发，看不见位置变化）：见下文「事件机制」。

## 分段依据

按**装备/属性里程碑**切分（与 zone1 / `milestone_strategy` 一致）。zone2 地板访问高度交错（MT12×N、MT11×N、MT17、MT19、MT20…），非逐层清。

| 段 | 里程碑 | 起止属性（已验证 walk）| 核心策略 |
|---|---|---|---|
| seg1 | MT12 商店 2攻 | ATK 30->38（DEF 30）| 只买 2 攻，省 80G 延后 4 区防 |
| seg2 | sword2 + shield2 | ATK 38->60, DEF 30->52（MT16 blackSlime + MT17 剑 + MT11 盾）| 剑先盾后（atk 杠杆 > def），MT16 blackSlime 必须先于 MT17 剑（过 yellowGuard 4->3 回合阈值）|
| seg3 | ATK70 宝石路 + cross | ATK 60->70, DEF 52->58, +cross（MT19）| 凑 ATK70 过 rock(def68) 拿 cross，cross 是吸血鬼硬门槛 |
| seg4 | redKey + 吸血鬼 | ATK 70->76, DEF 58->64（vampire afterBattle +6/+6）| 红钥匙买(800G)，吸血鬼 cross 必备 + (6,8) 触发 |

## 口径

- **cross（十字架）当前模型生效**（`game_route.py:633`：atk×2 for zombie/zombieKnight/vampire）。旧记忆 [[cross-bug-no-effect]] 称 cross 是 dead code **已过时**，实测+验证 walk 吸血鬼无 cross=15510（必死）、有 cross=705。**cross 是 zone2 吸血鬼的硬门槛**，必须在 MT19 拿到。
- walk HP delta 含 auto_sweep 副作用（血瓶/拾取计入同一步），**不是纯单怪伤害**。纯伤害看 dmg 增量或 Game `enemy_damage`（同 zone1 口径）。dmg 公式 = `(turns-1)*per`，turns=ceil(怪hp/hero_hit)，hero_hit=atk-怪def，per=怪atk-hero_def（hero 先手，怪少打一回合）。

## seg1：MT12 商店 2攻

**思路**：10F boss+thief 后补给（MT10 终态 HP=625 ATK=30 DEF=30 YK=3 G=311，thief 事件 +3ATK/+3DEF/+600HP/+3YK）上 11F/12F，在 MT12 blueShop 买 2 攻（ATK 30->38，花 20+40=60G）。**不买第 3 攻、不买防**。

**抉择 D1：为什么只买 2 攻--全是资源花费对比**：

| 选项 | 花费 | 收益 | HP等价净 | 结论 |
|---|---|---|---|---|
| 第3攻 ATK38->42 | 80G(=400HP) | yellowGuard 4->3 回合，4 只省 72 伤 | -328 | **亏**（72<400），3 攻坏交易 |
| zone2 防 DEF30->38 | 80G(=400HP) | +8 DEF，zone2/3 减每回合 1 伤 | ~省 240 HP | **次优**，同 80G 4 区给 +20 DEF |
| 4 区防（延后）| 80G | +20 DEF（ratio5 vs zone2 ratio2）| 省 500+ HP（魔龙/大法师）| **最优**，省 80G 到这里 |

- **第 3 攻亏**：ATK38->42 只跨 yellowGuard（hp50 def22：hero_hit 16->20，turns 4->3）一个阈值，4 只省 72。bigBat（hp60 def8）ATK38/42 均 2 回合，无阈值不省。80G=400HP 只换 72 HP，亏 328。故 2 攻够。
- **防延后到 4 区**：`buy_shop`（`game_route.py:2120`）cost 不乘 ratio、收益乘 ratio（atk += 2×ratio，def += 4×ratio）。zone2 ratio2 防 +8/80G，4 区 ratio5 防 +20/80G，同金币多 +12 DEF。zone2/3 因 -8 DEF 多吃的血（~240，walk MT31 HP=1249 证明可活）远小于 4 区省的。
- **times1 红利**：`times1` 全局累计。2 攻（times1=0,1）后 4 区首防买 times1=2=80G；2ATK1DEF（times1=0,1,2）后 4 区首防买 times1=3=140G。**2 攻线 4 区防买还便宜 60G**。

## seg2：sword2 + shield2（剑先盾后，交错里程碑）

**思路框架**：买 2 攻后**不逐层清，交错访问里程碑**：先 MT16 blackSlime（ATK 38->40），再 MT17 拿 sword2（ATK 40->60，最大杠杆），再 MT11 拿 shield2（DEF 32->52）。剑先盾后因 zone2 **ATK 主导**（吸血鬼 def66/zombieKnight def15 高防，atk 减回合 > def 减每回合）。

**抉择 D2：剑先于盾 = atk 杠杆 > def**：
- sword2（MT17，ATK 40->60）：+20 ATK 是 zone2 最大杠杆，跨多怪回合阈值（yellowGuard t3->2、zombie t8->5、blackSlime t4->3、redPriest t10->4 等，见 `data/heuristics_table.json`），全 zone2 受益。
- shield2（MT11，DEF 32->52）：+20 DEF 减每回合，不跨回合。zone2 高防怪 atk 减回合收益更大。
- 故先剑后盾。楼层依赖也匹配：sword2 在 MT17（4 yellowGuard 机关门），shield2 在 MT11（2 redPriest + 蓝门），路径独立可交错。

**抉择 D3：MT16 blackSlime 必须先于 MT17 sword2（过 yellowGuard 阈值，非仅 +2 ATK）**：
- MT17 sword2 由 4 yellowGuard（hp50 atk48 def22）守。**ATK38**（无 blackSlime）：hero_hit=16，turns=ceil(50/16)=4（16×3=48<50），per=18（DEF30），dmg=(4-1)×18=**54/只**。**ATK40**（有 blackSlime）：hero_hit=18，turns=ceil(50/18)=3（18×3=54≥50），per=16（DEF32），dmg=(3-1)×16=**32/只**。
- **MT16 blackSlime（+2 ATK, 38->40）跨 yellowGuard 4->3 回合阈值**，4 只省 (54-32)×4=88 伤。这是 gem 序硬约束：blackSlime 必须先于 MT17 sword2 的卫兵。walk 实测 MT17 4 卫兵均 32 dmg（725->693->661->629，各 -32），印证 ATK40/3 回合。
- 旧推断「2攻线比 3ATK 多花 72 伤打 sword2 卫兵」**基于 ATK38 前提，已过时**：2攻线实际到卫兵时 ATK40（blackSlime 先做），与 3ATK(ATK42) 同为 3 回合，**不多花代价**。3 攻的 80G 在 sword2 卫兵上无收益。

**抉择 D4：MT11 shield2 的 2 redPriest + 蓝门 + 200G BK**：
- shield2 由 2 redPriest（hp100 atk95 def30）+ 蓝门守。zone2 BK 紧（MT6 商人 50G/BK、MT15 商人 200G/BK、MT11 蓝门是盾房唯一入口）。walk 在 MT15 花 200G 买 BK 开 MT11 蓝门（`trader blueKey1_15`，G 234->34）。
- redPriest @ATK60 DEF52 = (turns-1)×per 伤，2 只。shield2 后 DEF 32->52。

## seg3：ATK70 宝石路 + cross（MT19）-- cross 是吸血鬼硬门槛

**思路框架**：sword2（ATK60）后扫宝石到 ATK70。**ATK70 是 rock 的硬地板**（rock def68，ATK<69 则 hero_hit≤0 杀不掉，`dmg=inf`）。rock 守 MT19 cross。cross 让吸血鬼 atk×2（15510->705），**不拿 cross 必死**。故宝石序必须保证 **ATK70 在 MT19 rock 之前**。

### 已验证 ATK 宝石序（walk 实测）

| # | 来源 | ATK | 备注 |
|---|---|---|---|
| 0 | zone1 末（MT10 thief）| 30 | 起点 |
| 1 | MT12 blueShop 买 2 攻 | 38 | seg1 |
| 2 | MT16 blackSlime（x2y9，auto 拾 redGem x1y6 + blueGem x1y7）| 40 | +2，**先于 MT17 剑过 yellowGuard 阈值**（D3）|
| 3 | MT17 sword2（x2y2）| 60 | +20，最大杠杆 |
| 4 | MT12 redPriest（x7y3，auto 拾 redGem x6y1）| 62 | +2 |
| 5 | MT11 redGem（x5y1，ARRIVE auto 拾）| 64 | +2 |
| 6 | MT20 redGem（x1y4）+ blueGem（x2y4）| 66 | +2 ATK +2 DEF（->58），同 visit auto 拾 |
| 7 | MT18 redPriest（x1y9，auto 拾 redGem x2y11）| 68 | +2 |
| 8 | MT19 redGem（x11y1，杀 bigBat x10y2 时 auto 拾，第 2 次 visit）| 70 | +2，**ATK70 到手**|
| 9 | MT19 rock（x5y6，第 3 次 visit）+ cross（x6y3）| 70 | 杀 rock 拿 cross，见下 |
| 10 | MT20 vampire afterBattle（auto 拾 3 redGem x4y5/4y6/4y7）| 76 | +6 |

**抉择 D5：ATK70 硬地板锁宝石序（修正）**：
- rock hp20 atk100 def68。ATK68：hero_hit=0 杀不掉（inf）。ATK70：hero_hit=2，turns=10，@DEF58 dmg=(10-1)×(100-58)=378。**ATK≥69 才能杀 rock**。
- **ATK70 来自 MT19 redGem（x11y1，杀 bigBat x10y2 时 auto 拾，第 2 次 visit），不是 MT18 redPriest**。旧推断「MT18 redPriest ATK68->70 必须先于 MT19 rock」**宝石归因错了**：walk 实测 MT18 redPriest 是 66->68，MT19 redGem 是 68->70。约束是 **MT19 redGem（ATK70）必须先于 MT19 rock**，二者同层 MT19、不同 visit（redGem 第 2 次、rock 第 3 次）。
- MT19 redGem（x11y1）由 bigBat（x10y2）守，第 2 次 visit 顺路拿；rock（x5y6）在第 3 次 visit 杀。redGem 在 rock 前是 visit 顺序锁，不可换。

### 事件机制：MT19 cross（fakeWall2 + setBlock 事件锁）

cross 在 MT19 (6,3)，是 **fakeWall2（id 3，afterOpenDoor setBlock）**：破墙触发 openDoor 事件锁 spawn cross。

- **离线 Game**（`game_route.py:1771`）：`trigger_tile_event` 在 ARRIVE (6,3) 且 block.eid in {fakeWall2, cross} 时，`set_block((6,3), "item", "cross")`（破 fakeWall2 -> spawn cross）。walk step 360 杀 rock (5,6) 时 auto_sweep 顺带破 (6,4) fakeWall + (6,3) fakeWall2；step 361 ARRIVE (6,3) 拾 cross（note `auto_sweep: x6y3 cross`）。
- **实机边界**（replayer）：破 fakeWall2 (6,3) 触发 setBlock 事件锁，hero 停相邻 (6,4)，lock=setBlock，cross 已 spawn 但 **auto 不拾**（事件锁打断 auto_sweep）。replayer ARRIVE else 分支需 **setBlock retry 循环**：pressKey Space 推进事件锁 -> retry mouseClickTile (6,3) 拾 cross。不加此循环则 cross 未拾，后续 vampire 战 atk 不翻倍 -> HP 大发散。见 [[replayer-arrive-setblock-retry]]。
- **不是补丁**：fakeWall2+setBlock 是通用地图事件机制，修复在通用 `trigger_tile_event` + replayer ARRIVE 通用分支，非 MT19 单坐标跳过。

**抉择 D6：cross 必备，非可选**：
- 吸血鬼 hp444 atk199 def66。无 cross：ATK70 hero_hit=4，turns=111，dmg=15510（必死）。有 cross（atk×2=140）：hero_hit=74，turns=6，dmg=705。**cross 把吸血鬼从必死变可打**。
- cross 在 MT19，前置 rock（ATK70 地板）+ 蓝门。rock @ATK70 DEF58 = (10-1)×(100-58)=378 伤（walk 766->388 印证）。这也修正 [[cross-bug-no-effect]]：cross 当前生效，canonical zone2 模型可行。

**抉择 D7：宝石序其余 = 钥匙流 + 路径成本（同 zone1 蓝宝石原则）**：
- 蓝宝石（+DEF，无阈值）按钥匙/门流排：MT16 blackSlime（DEF30->32）、MT11 shield2（32->52）、MT15 zombie（52->54）、MT12 blackSlime（54->56）、MT20 blueGem（56->58）。
- 红宝石（+ATK，有阈值）按 atk 阈值排：**MT16 blackSlime 必须先于 MT17 sword2**（D3，yellowGuard 4->3 回合）；**MT19 redGem 必须先于 MT19 rock**（D5，ATK70 地板）。

## seg4：redKey + 吸血鬼

**思路框架**：cross 拿到后凑 redKey 开 MT20 红门打吸血鬼。redKey 两源：MT12 商人 800G 买、MT14 杀 3 zombieKnight。官方 2攻线 = 买（walk `MT12 x1y1 trader redKey1`，G 1001->201）。吸血鬼 cross 必备（D6）+ (6,8) 触发（下）。

**抉择 D8：红钥匙买(800G) vs 杀(3 zombieKnight)--接近，但 end-to-end 买会饿死 4 区攻**：

| 方式 | HP 代价 | 金币代价 | HP等价净 | 备注 |
|---|---|---|---|---|
| 杀 3 zombieKnight（+cross, ATK70 DEF58）| 372 伤 | +90G（掉落）| 327 | 需 MT14 蓝门+黄门绕路 |
| 买 MT12 redKey | 0 伤 | -800G | 400 | 无绕路，但饿死 4 区攻商店 |

- **纯 zone2 HP 等价：杀略便宜**（327 < 400）。zombieKnight hp320 atk120 def15，+cross atk×2=140，hero_hit=125，turns=3，per=62（DEF58），dmg=(3-1)×62=124/只，3 只=372。
- **但官方选买，且 end-to-end 买会饿死 4 区攻**：买 redKey 花 800G，这笔金否则可买 4 区攻商店（+10 ATK/buy）。walk MT20 vampire 后 G=345（买 redKey 致 G 贫）；对比 2ATK1DEF（杀 zKnight）MT31 G=1138，差大头是 800G redKey。金币贫 -> 4 区攻商店少 -> 入 4 区 ATK=142（vs 2ATK1DEF 166）-> 魔龙战 ATK270 挨 10212（2ATK1DEF ATK312 只挨 4440）-> redkey12 线 19562 < 2ATK1DEF 23076。
- **判断**：纯 zone2 杀略优；end-to-end 买要靠 4 区爆防（官方 DEF559/590+）补偿金币贫，repo 未实现（DEF492）-> 19562。**2攻+杀zKnight（保 800G 给 4 区攻）是未探的另一条线**，可能避开饿死攻商店，值得探。

### 事件机制：MT20 吸血鬼触发（hero 踩 (6,8)，非 floor-entry）

MT20 吸血鬼是 **hero 踩 (6,8) 触发**，不是进楼 floor-entry。

- **触发**（`game_route.py:1904` `trigger_tile_event` + `zone12_recording_autoon.py:71` 注释）：hero 走到 (6,8) -> 8 bigBat 在 (6,6) 周围 spawn -> 合并成 vampire (6,6) + specialDoor 封 (6,9) 南出口。hero 停 (6,8)。
- **bigBat 合并不计金币**：8 bigBat 合并进 vampire，**不单独战斗，无金币**（只有 vampire afterBattle money）。Game trigger 清 8 spawn 格（含原 (6,5) bigBat + (5,5) whiteWall2 装饰）时**不 +gold**；若 auto_sweep 单独杀 (6,5) bigBat 会 +12G 误计（早期 bug，已修）。
- **afterBattle**（`game_route.py:1774`）：vampire 死 -> 开 (6,3)+(6,9) + spawn 3 yellowKey + 3 redGem + 3 blueGem + 3 bluePotion。auto 拾 -> +6 ATK +6 DEF + HP 回复（walk 754->1249）+ 3 YK。
- **skip-if-cleared 不能跳 (6,8)**：(6,8) 是空格（id 0）但是 event trigger 格，跳过则 vampire 不 spawn。`zone12_recording_autoon.py:251` 用 `is_event_trigger = f"{tx},{ty}" in events` 守卫，event trigger 格永不跳。见 [[zone12-event-trigger-not-floor-entry]]。
- **不是补丁**：(6,8) 触发是通用 hero-step 事件模型（`trigger_tile_event`），修正了旧 floor-entry spawn 假设；MT29 thief 同模型（zone3）。

**抉择 D9：吸血鬼触发 = cross + redKey + 踩 (6,8) 后**：
- MT20 红门（redKey）-> 踩 (6,8) spawn vampire -> 杀 vampire (6,6)（705 伤 @ATK70 DEF58 +cross）-> afterBattle +6/+6 + HP + 开门。zone2 终态：买红钥匙线 ATK76 DEF64 HP1249（autoon，已删）；**KILL 线（当前最优）ATK76 DEF66 HP1215**（杀 zKnight 拿 blueGem DEF+2，保 800G 给 4 区攻）。

## 替代线路对比

| 线 | MT12 商店 | zone2 末（vampire 后）ATK/DEF | 红钥匙 | MT31 G | 4 区潜力 | 实测终态 |
|---|---|---|---|---|---|---|
| **2攻线买红钥匙（autoon，walk 已删）** | 2攻（60G）| 76/64（HP1249）| 买 800G | ~345（walk gold 367 含 auto 多杀）| 防+20(80G)，理论 41477 | redkey12 实现 **19562**（gap）|
| 2ATK1DEF（当前 best）| 2攻+1防（140G）| 76/64（同 vampire +6/+6）| 杀 zKnight | 1138 | 防+8 zone2 浪费 | **23076**（web 验证）|
| canonical 3ATK | 3攻（140G）| 76/64 | 杀 zKnight | - | 80G 花第 3 攻 | 未实机验证 |

- **2攻线 vs 2ATK1DEF**：二者 zone2 末 ATK/DEF 相同（76/64，vampire afterBattle 抹平差异）。差异在金币：2攻线买 redKey 致 G 贫（~345 vs 1138），4 区攻商店饿死，魔龙战多挨 6180 -> 19562 < 23076。**2攻线理论更优（官方 41477 需 DEF559/590+），repo 实现未达**。
- **3ATK**：zone2 dmg 最低，但 80G 花第 3 攻（sword2 卫兵上无收益，见 D3）不延后防，4 区防少 +20，end-to-end 不优。

## 探索状态 / 搜索瓶颈

- **zone1-2 当前最优 walk**：`best/zone12_2atk0def_recording_walk.md`（KILL 线，358 步 MT4-20，web 0 mismatch）。旧买红钥匙线 autoon walk（HP=1249）已删。KILL 线保 800G 给 4 区攻，理论应超 2ATK1DEF 23076（待 zone3/4 跑通）。
- **redkey12 线 end-to-end gap**：实测 19562 < 2ATK1DEF 23076。根因 4 区防堆叠不足（DEF492 vs 官方 559/590）+ 买 redKey 饿死 4 区攻（入 4 区 ATK142 vs 166）。[[redkey-12-line-findings]] [[dragon-defer-lever]]。
- **2攻+杀zKnight（KILL 线）已探 = 当前 zone1-2 最优**：converter 版 `best/zone12_2atk0def_recording_walk.md`（HP=1215，保 800G 给 4 区攻）。下一步接 zone3/4 验证能否超 2ATK1DEF 23076。
- **搜索退化**（[[two-attack-line-search-lessons]]）：zone2 搜索用 guide-scaffold + 选项枚举，非资源组顺序搜索，2 攻线（不同顺序/策略）在搜索空间外。需把 zone1 资源组顺序搜索搬回 zone2。
- **cross 生效修正**：旧 [[cross-bug-no-effect]] 已过时，当前模型 cross 生效，canonical zone2 模型可行。

## 对比工具

`scripts/audit/compare_segment_walks.py`（待建，同 zone1）：2 攻线（已验证 walk）/ 2ATK1DEF / 3ATK 三线对照，找分叉点 + HP/dmg 归因。
