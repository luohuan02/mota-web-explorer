# recording_seed_to_game converter 经验（录像 statlog -> Game walk）

来源 = `scripts/search/recording_seed_to_game.py`。和 `recording_to_game.py`（逐格
captured path 精确复现，见 `recording_converter_experience.md`）不同：本 converter 从
录像的 **statlog（每动作 pre-state）+ route token** 提取**语义动作**（target/fly/
arrow/shop/trader/tool/event），每个语义动作由通用 `Game` 类重新规划（`go_to_decomposed`
+ `auto_sweep` + `trigger_tile_event`），不逐格复现录像路径。statlog 只作诊断，绝不回写
英雄数值。

适用：录像 statlog 可靠（native replay hook `core.control._doReplayAction` 抓 pre/post）
且 Game 已建模该区域事件时。**给录像 + seed_save + capture 即可产出可验证 walk**。

## 三类 NPC 的通用转换（不会再漏商人/老头）

converter 对 noPass NPC 走三条通用路径（都在 `recording_seed_to_game.py`，非 walk 补丁）：

| NPC（eid） | 检测 | Game 动作 |
|---|---|---|
| 商店 shop/blueShop | `_is_shop_npc` + `_shop_purchase_from_delta`（statlog g 降/atk·def·hp 升） | `_execute_shop`（buy_shop） |
| 商人 trader | `_is_trader_npc` + `_trader_purchase_from_delta`（statlog g 降/yk·bk·rk 升，查 `TRADER_TABLE`） | `talk_trader` |
| 老头/小偷/其它 oldman/thief | `_safe_execute` NPC fallback（任何 kind=npc）-> `_reach_event_trigger` | `trigger_tile_event`（Game 逐个 NPC 建模） |

**关键**：录像的 shop/trader 交易 `choices`（确认购买）**不是 hooked `_doReplayAction`
token**，所以 -cost/+gain delta 落在**朝向 NPC 的那个 arrow/target 动作的 statlog 条目**
上（其 `after` = 下个 hooked 动作的 pre = post-choices）。delta 检测靠这个。

- 商人：`_trader_purchase_from_delta` 查 `g.TRADER_TABLE[floor_no(当前楼层)]`，要求
  `post.g - pre.g == -cost` 且每个 stat-trackable gain（yk/bk/rk/hp）精确匹配；
  earthquake（MT47，不在 statlog）只靠 gold cost 验。任何在 TRADER_TABLE 的 trader
  （楼层 2/6/7/12/15/31/38/39/45/47）自动识别，**不用逐个加分支**。
- MT2 (11,4) 老头 +1000G：block eid 是 "oldman" 不是 "trader"，走 `trigger_tile_event`
  路径（Game 2108 行建模），不走 talk_trader。虽 TRADER_TABLE 有 entry 2 = (-1000G)。
- **潜在缺口**：将来某区出现 Game 没建模的 NPC（既非 trader/shop、trigger_tile_event
  也无分支），converter 静默当 noop 跳过（`_reach_event_trigger` 返回 False，记
  `noop_routeerror` 进 diagnostics）。新区域跑完要扫 diagnostics：有 noop_routeerror
  就是要补建模的信号。

## 激进 coalesce：空地到达/通过全删（reachability matrix 直达目标）

`_coalesce_redundant_arrivals`：Game 类是可达矩阵，每步直达一个**有意义目标**（门/怪/
道具/事件/楼梯/飞行）。录像的空地 `move:x:y`/arrow 只走空地，不是可达矩阵状态 ->
到达/通过步是冗余噪声，全删。

**为什么安全**：replayer 点**目标**不是点中间空地。远点点击 hero automaticRoute
寻路到目标，且 `maybeRetryAdjacentTarget` 自动重试（hero 相邻但动作没触发 -> 再点一次）：
- `canRetryAdjacentTarget`：KILL（hero 相邻且怪还在 ev.cls==="enemys"）、OPEN_DOOR
  （门还关 trigger==="openDoor"）、PASS/TALK/ARRIVE 都重试。PICKUP 道具可踩上去一次到位。
- far-KILL 分支（`execute_action` arrow KILL Manhattan>1）也加 `maybeRetryAdjacentTarget`
  （否则 automaticRoute 停相邻不攻击就漏杀，如 MT33 (9,5) ghostSkeleton）。

**必须保留的例外**（空地到达步是 load-bearing，删了 web 失败）：
1. **stat 变步**（击杀/拾取/开门/事件/商店/商人）-- 本来就不是 noop 定位。
2. **auto_sweep 步**：stat 不变但破了墙/开了路，map 副作用对后续可达性 load-bearing。
3. **楼梯点击**（eid upFloor/downFloor）+ 紧接换层：replayer 配对 通过-stair + 换层。
4. **event-trigger 格的到达**（如 MT40 (6,7) boss 事件）：before==after（spawn 奖励/
   开门本步不改 stat）但踩了才触发事件 spawn 奖励，删了事件不触发。
5. **centerFly·upFly·downFly 前一个定位步**：飞目的地 = hero 源位置函数（见下节）。
6. **工具计数变化的拾取步**（2026-08-12 章鱼镐修复）：`stat_same` 原只查
   `value_fields=("hp","atk","def","yk","bk","rk","gold")`，工具拾取（pickaxe/centerFly/
   upFly/downFly/bomb/earthquake/bigKey/superPotion/snow）只改工具计数不改 value_fields
   -> 拾取步被误判 stat_same 折叠进下一飞步 before（如 MT15 章鱼杀后镐在 x6y5，recording
   `up` 拾取，但 walk 折叠进 `fly:MT18` 的 before -> web 镐留原地 -> 后续
   `core.useItem("pickaxe")`（MT48）失败）。fix：`stat_same` 追加 `tool_fields` 检查
   （同上列表），工具计数变化恒为 load-bearing 拾取，保留该步总正确。
7. **MT50 redKing 键盘触发前的定位 到达**（2026-08-16 根因修复，39944）：redKing 揭示是
   **键盘触发 EVENT**，verifier 检查 `|dx|+|dy|==1`（hero 须在 (5,5)/(6,6)/(6,4)/(7,5) 相邻
   (6,5)），**它不会把 hero 路由到事件格**。换层落点（MT50 x6y7）≠ 相邻要求；recording 的
   定位 `move:5:5`（(6,7)->(5,5)）是空地走位，coalesce 之前会误删 -> hero 停 (6,7) 非相邻，
   reveal 抛 "must be adjacent"（38624/39003/39529/39944 四线同一模式，早期靠手动重插
   `到达 (6,7)->(5,5)`）。**fix**：`_coalesce_redundant_arrivals` 加 `before_redking_reveal`
   检测（下一步 action=事件 eid=redKing floor=MT50），保留其前定位 到达 步。修复后 39944
   walk 原生产出该步（step idx 1006 `到达 MT50(5,5)`），web 0 值 mismatch（含金币）。注意
   redKing 的**击杀**是 replayer 直接路由的有意义动作，不需要定位步；**49F 封印后 redKing
   击杀奖励拾取步**（MT49 (6,4) +3000hp/+15atk/+15def/+1rk）仍须显式保留（见「折叠的 boss
   后置奖励」节）。
8. **击杀前一个曼哈顿相邻的定位 到达**（`is_kill_approach`，2026-08-22 2攻录像修复）：
   recording 常先 `move:x:y`（到 kill 目标相邻格）再 arrow 朝向击杀，coalesce 会把这
   `到达` 当 stat_same 冗余删掉 -> replayer 直接远点点击 kill 目标，自动寻路走**自己选**的
   路径（Game `go_to` item-epsilon 不同），可能开错黄门/yk 掉/卡死（2攻录像 MT5 (3,3) bat
   web 卡 (1,3)）。**fix**：coalesce 新增 `is_kill_approach` 例外——下一步 action=击杀、
   同楼层、pos != 下一 pos 且曼哈顿相邻的到达步**保留**（二攻录像 507 步含 `step43 到达
   (3,2)` -> `step44 击杀 bat (3,3)`，web 0 mismatch）。注意触码顺序：`pos` 必须在
   `is_kill_approach` 之前定义（曾因名字顺序 NameError `is_kill_approach` 引用了未定义
   `pos`）。**只在击杀前相邻定位步保留；普通空地到达仍删**。

9. **开门前一个曼哈顿相邻的定位 到达**（`is_door_approach`，2026-08-30 41200 录像修复）：
   与 `is_kill_approach` 同族——下一步 action=开门、同楼层、pos 与门格曼哈顿相邻的
   到达步保留。删除它会让 replayer 从更远处点门格，live automaticRoute 穿过刚开的门
   并触发 auto sweep，提前收走 walk 排在几十步后的门后口袋资源（41200 MT47 (8,4)）。
   配合 Game `_apply_door_live` 的门步 sweep（见下「开门后以门格为起点的 auto sweep」）
   与 verifier 的确定性走门格一起使用。

## 开门后以门格为起点的 auto sweep（`_apply_door_live`，2026-08-31 定稿）

**旧约定「到门前开门，不触发自动BFS」已被 41200 录像实测推翻**。真实机制链（从
live 页面源码取证 + plugins.js bfs 源码 + door-trace 40ms 轮询实证）：

1. `control.prototype.moveOneStep` 被游戏补丁：hero 每移动一格后，若
   `core.status.event.data` 为真则**插入** `core.auto()`（事件链结束后执行），否则
   `update()` = updateCheckBlock + updateDamage + **立即 `core.auto()`**。
2. 开门点击后，游戏的 route-resume（continueAutomaticRoute）让 hero **踏上刚开的
   门格**——那一拍 `core.auto()` 触发，auto BFS **从门格起跑**。
3. bfs 源码（plugins.js `function bfs`）：**不检查 fgmap 火本身**——阻挡来自
   `judge()` 第一行 `if (core.getFgNumber(tx,ty)===103) return {canGoThrough:false}`，
   读的是**运行时火格**（初始数据 + setBgFgBlock 撤退变异 + hero 踩火清除；
   模型 fgmap 逐一镜像）。模型曾错误地以为 auto BFS 无视火，实测 (7,1) 门步
   live 被 (8,1) 运行时火挡住——阻挡语义保留。
4. `hasBlockDamage(loc)` 用 checkBlock 的 damage/ambush/repulse/chase 四图——
   **special 15 法术场不在其中**（MT47 实测两只红巫师在场 damage=[]）→ BFS 的
   扩展/拾取**不被法术场阻挡**，hero 站法术场格 deep 也**不会**被压成 0。
   法术场的地图伤害由 apply_check_damage 在 hero 实际踩格时结算，与 auto BFS
   是两个系统。模型已删 BFS 内的 check_damage_at 阻挡与 deep 压制。
5. 门格若带火（撤退三步传播），hero 踏上门格那一刻火被清除——模型在
   `_apply_door_live` 开门后调 `_check_fire_retreat(fid, pos)` 镜像。
6. **hero 位置保持录像语义（停邻格）**：Game 的 hero 位置链必须与录像的 arrow 序列
   落点一致（arrow 开门 hero 不动），否则后续 arrow 动作整体错位（41200 MT8 (6,3) 门
   步 hero 落门格曾导致 MT8→MT9 弹跳楼梯换层错位、转换断链）。位置差异交给
   verifier 的 ±1 容忍。
7. **live 的 route-resume 时机不确定**（0.3s 内或随下一次移动才发生，依赖事件壳残留），
   所以 verifier 对每个开门步确定性补一次「走进门格」点击（见
   mota-live-verify SKILL「开门步确定性走门格」），把 sweep 归属固定在门步。

旧的 23076 等验证线之所以在旧模型下 0 mismatch，是竞态恰好把这次 sweep 计入下一步
（其下一步的目的地 sweep 覆盖同一资源集）。新模型下旧 walk 不能直接重验，需用现管线
重新生成。

**读火格的探针陷阱**：`core.getFgNumber(x,y,floorId)` 三参调用返回错值（曾误报
(8,2) 有火）——必须用双参 `core.getFgNumber(x,y)` 或直接读 `core.floors[fid].fgmap`
数组；且运行时火（getFgNumber）与 `core.status.fgmaps`（显示层）是两个东西。

## 地图数据重导出必须带 fgmap（2026-09-05 41218 根因）

重导出 `core.floors.MTn` 时**漏掉 `fgmap`（前景火层）会让模型丢失全部初始火**：
live 楼层数据自带静态火（MT47: (8,1),(4,3),(8,3),(1,8),(1,10)），模型没有 →
火格时间线全错 → 门格 sweep 可达性与 live 分歧（41218 MT47 (7,1) 门格 sweep
被 (8,1) 火挡住收不到 x11 资源，模型却穿过去收了）。决定性实验：在失败态手动
`core.auto()`（bail 全不满足）收集仍为空 → `getFgNumber(8,1)=103` → 火阻挡实锤。
修复：export 脚本补 `fgmap` 字段。**教训：导出楼层数据必须逐字段对照旧文件**。

## 「下载源码逐字对齐」优先于探针猜语义（2026-09-05）

探针（读 `core.status.checkBlock.damage` 现值、逐格 block）只能给出现象；
**curl 游戏源文件提取函数本体是决定性证据**：`https://h5mota.com/games/51/`
的 `project/project.min.js`（游戏插件：bfs / hasBlockDamage / canBattle /
canGetItem / `_performGetItem` / potionIds）与 `project/functions.js`
（楼层定制：updateCheckBlock 领域/阻击/激光/捕捉/夹击的 damage 图计算）、
`libs/control.js`（moveOneStep 补丁）都是明文 JS。本轮 40145 的
damage-格语义（visit 不扩展 / canGetItem / deep=0）全部从源码逐字核实后
再改模型，避免了又一次「单层现象推全塔结论」。判读时注意 build 产物是
混淆过的（`_core$status$hero$loc4` 之类解构变量名），按关键字
（`function bfs`、`updateCheckBlock`、`potionIds`）定位即可读。

## 40145 复验两大根因（2026-09-05 定稿，「楼梯 run 原子化」假设作废）

**根因一：walk JSON 是 stale 的 + 转换命令缺 `--start-stat`。**
40145 录像从 1F（hp=1000）开始的完整录像，seed 是 MT4(11,9) hp=926 快照——
statlog 284 起才匹配 seed 状态，缺 `--start-stat 284` 会在 action #4（target MT1）
直接报 "requires current floor MT4"。旧 walk（00:46）比 converter 最后修改（00:58）
旧，丢了 MT8↔MT9 真实两连按弹跳（press A #739 MT8→MT9 + press B #744 MT9→MT8
回弹）。**教训：复验前必须用当前 converter 重新生成 walk，不能信旧文件；
`--start-stat` 要随命令记录（provenance 不含它）**。派生侧同方向连按 run 按
CHG 相位各 emit 一支箭头（#739/#744 都保留）、`_cancel_stair_bounce_arrows`
对首访 load-bearing 弹跳不误删——当前管线本来就正确，无需 run 原子化。

**根因二：auto_sweep BFS 未镜像 web 的 hasBlockDamage 语义（推翻 2026-08-30
「四图不含法术场」结论）。**
- `updateCheckBlock`（project/functions.js）：special 15 领域/16 夹击**会**写入
  `checkBlock.damage`，仅受 `!core.hasFlag("魔法免疫")` 限制。MT47 damage=[]
  是因为该线已拿神圣盾（magicImmune），**不是法术场不入图**；MT42（未拿盾）
  实测 damage 11 格。
- web bfs（project.min.js）：每个 tile visit 后 `if (hasBlockDamage(loc)) return`
  ——damage 格可访问（战斗/拾取/破墙结算）但**绝不扩展**；
  `canGetItem = !hasBlockDamage(loc)`——damage 格上道具不能远程拾取；
  hero 站 damage 格 → `deep=0` → sweep 完全不跑。
- 40145 现场：MT42 (8,5) 门步 BFS 被 (9,5) 法术场格挡住收不到顶部钥匙房；
  +5yk+1bk 是 (10,9) 收的下方钥匙房（经 (10,10) 无 damage 格）；顶部房全程没收。
- 修复（game_route.py auto_sweep 通用三处）：① `deep = 0 if check_damage_at(start)>0
  else 1e9`；② 每 tile visit 后 `check_damage_at(nxt)>0 → 不扩展`；③ item 分支
  `check_damage_at(nxt)>0 → 不拾`。`check_damage_at` 与 updateCheckBlock 同源
  （special 15/16 + magicImmune + 怪死场消）。special 18（阻击：骷髅法师/铁守卫/
  高级巫师（阻击））本塔无楼层使用，暂未建模。
- **教训：改 sweep/阻挡语义前先读 live 的 checkBlock.damage 现值+看 updateCheckBlock
  源码，不要从单层（MT47）现象推全塔结论**；strict 测试迷你图要镜像真实线的
  flag 状态（41200 在 MT48 已魔免）。

## capture statlog 与 walk 漂移的容忍口径

converter 语义动作由 Game 重规划，walk 与录像 statlog 在 sweep 时序上允许漂移
（如门步 sweep 比录像提前收资源）；终态字段（hp/atk/def/yk/bk/rk/gold）必须逐项一致
（41200 终态 HP=41200 gold=165 与 native capture 末帧完全一致）。web 复验才是
walk-vs-live 的仲裁，statlog 漂移只进 diagnostics。

**工具拾取步必须用 `拾取`(PICKUP) 而非 `到达`(ARRIVE)**：即便补进 tool_fields 保留了步，
若它是 `到达` 且紧接 `飞行`，verifier 的 pre-fly-arrive 跳过（note 无 "auto_sweep" 且
valuesMatch 就 `-> skipped pre-fly arrive`）会吞掉它（pickaxe 不在 verifier valuesMatch，
恒真）。用 `拾取`(PICKUP) 分支直接点击，或保证下一步非飞行。

**折叠的 boss 后置奖励也要显式 step**（同「折叠 sweep 不可回放」族）：某些击杀奖励不在
击杀步 after、而折叠进下一飞步 before（如 MT49 (6,3) redKing 死后 +3000hp/+15atk/+15def/
+1rk 在 (6,4) 走位步 apply，recording `down` (6,3)->(6,4)，对齐已验证 TE33508 #381）。
web 只在 hero 走到那格时 apply -> 需显式 `到达` 步携带该奖励（before=击杀 after 状态、
after=+奖励），否则下一飞步 before 与实际不符。

## centerFly 目的地依赖源位置（key 例外，必保留前定位步）

`Game.center_fly`：destination = `(width-1-x, height-1-y)` = hero 当前位置的**中心对称
点**。`up_fly`/`down_fly`：destination = 同 (x,y) 上/下楼。**飞目的地是源位置的函数**。

Game 在 hero 处于某位置（前一个到达步之后）时算出飞步 pos。coalesce 删了前定位步 ->
hero 源位置变 -> 飞目的地错（飞步 pos 没重算，仍指向旧目的地）。

**典型**：MT40 centerFly，hero 须在 (10,11) 才对称到 (2,1)（空地，飞成功）。若删了
到达 (10,11)，hero 在 (9,9)（前一步 redPotion 拾取处），对称到 (3,3) 被挡 -> 飞失败
hero 停 (9,9)，replayer timeout。

**fix**：coalesce 保留 `中心飞行/上楼器/下楼器` 前一个到达/通过步（`before_position_fly`）。
飞行（fly:floor）目的地是固定楼层入口，源位置无关，前定位步可删。

## 验证方法（coalesce/NPC 改动后必跑）

1. converter 自身 `ok=true`（Game 内部一致，无 errors）。
2. web replayer 0 mismatch：`node scripts/live/live_zone3_mouse_replayer_cdp.js
   --walk <walk.json> --load-slot <seed_slot> --target-click-only
   --set-auto battle=true,item=nopotion,wall=true --out-json <verify.json>`。
   **--load-slot 状态须 = walk 起点**（seed_save 对应槽；3 区起用 save33 MT31 替代
   save153，因 100+ 槽无法录像）。看 final state == 期望 + 全程无 MISMATCH/timeout。
3. **注意**：verify 0 mismatch 是 walk 自洽（Game 预测 vs live 回放同一条 walk），
   不是 walk vs 录像。要确认对齐录像真终态须另比对 save（如 zone3 2atk3atk5def
   walk final vs save33 录像真终态 = MT41 yk=6 gold=2954）。
4. **双线互证**（39003）：整链 save1→MT50 和「从区起点 save（MT41 checkpoint）→MT50」
   各验证一遍，两线 final 全等即互证（区起点 save 也顺带验证了分链 checkpoint 一致）。
   区起点 save 可用上一段验证的末态重建（非旧的不一致 checkpoint）。

## SET_AUTO（游戏说明 help+choices）快照：statlog-help-run ↔ route-help 精确对应

录像的 SET_AUTO 步记录为 `help` + `choices:N`（见 [[setauto_menu_root_cause_fix]]）。
converter 需要把 statlog 里的 help 步映射到 route 里的 `help` token，读其后的 `choices`
解码 auto 切换（submenu enter=4 / battle=0 / item true↔false=1 / true↔nopotion=4 / wall=2 /
exit=3 / return=6）。**坑（2026-08-22，zone4 门少开全防停41楼）**：旧实现 `_statlog_to_route_map`
是粗线性映射（~1 statlog/route token），而 capture 的分 phase 展开器每 route token 产生
~2.9 个 statlog 项 → 线性 index 比真实靠后 ~3x 漂移。旧快照
`max((i for i,t in enumerate(route[:help_ri+1]) if t=="help"))` 把每个 help 都错快照到
**最后一个** help。当录像有多个 toggle（zone4 录像 route 里 3 个 help：route 58 / 730 / 849；
route 730 是 item true->nopotion 的切血瓶）时，route-730 的 nopotion help 被错快照到
route-849 的 `choices:6` 空操作 → **nopotion 步从未写出** → 后续自动喝光省下的 ~6600HP
血瓶 → **web 复验错误地 HP=6643**（用户点破：录像 zone4 中途关了自动拿血瓶）。

**fix**：先采集 `route_help_idxs`（route 里所有 `help` 下标）+ `statlog_help_run_starts`
（statlog 里连续 help 段的起始下标），每个 statlog help 按所在 run 序号映射到对应的 route help，
再读该 route help 后的 `choices`。修复后 zone4 walk 在步 13（MT20）正确发出
SET_AUTO item=nopotion，web 复验降到 **HP=43**（守恒）。**How to apply**：
后半段录像接续（尤其从另一条的 MT31/MT41 种子继续）**必须先审计 SET_AUTO 何时下发**，
不能默认 item 一直开；多 help 录像务必核对每个 help 的 choices 归属。相关
[[zone4_alldef_stop41_web_verified]]。

## 通用教训

- **NPC 转换三类路径**（shop/trader delta 检测 + oldman trigger_tile_event），新区域
  扫 diagnostics 的 noop_routeerror 找未建模 NPC。商人/商店全自动 delta 识别，不用
  逐个加分支。
- **coalesce 删空地到达步安全**靠 replayer 远点点击+重试（maybeRetryAdjacentTarget +
  far-KILL 分支重试），不是无脑删。
- **飞步源位置依赖**是 coalesce 的硬例外：centerFly/upFly/downFly 前定位步必保留，
  否则飞目的地错。飞行（fly:floor）源无关可删。
- **--load-slot 和 --start-step 须手动对齐**：存档状态 = walk 第 N 步 before。
  save = walk 种子 -> `--start-step 1`；save = 跑完第 K 步后 -> `--start-step K+1`；
  不匹配任何步 -> 换 walk（详见 SKILL.md verifier 用法）。
- **100+ 槽无法录像**：实机录像（.h5route）从 100+ 槽起会失败，改用普通槽（如
  save33 MT31）做 converter verify 起点。converter seed_save JSON 不变，只换 --load-slot。

## stair 往返弹跳删除（`_cancel_stair_bounce_arrows`）

录像里玩家有时在 upFloor/downFloor 楼梯反复按方向键弹跳（如 MT32(10,1)<->
MT33(10,1) 连按 7 次 right；MT20<->MT21、MT36<->MT37、MT38<->MT39 同），每支 arrow
变成 walk 里的 通过+换层 对，纯噪音。

检测：arrow 的 `before.floor != after.floor`（statlog 提供，可靠）= 踩楼梯换层。
栈式消除相邻相反对（A->B 后 B->A 弹回），保留单个净换层。move/fly/item/event 等
非-arrow 语义动作断开栈（中间有真动作的往返不删，如 MT32->MT33 商店->MT32 是真购物）。

**关键：visited 跟踪**。用 seed `hero.flags.__visited__` + stage 内已访问楼层集合，
只删**已访问**楼层的往返（如 809-816 MT32<->MT33，MT33 已在 777 首次访问）；**保留
首次访问**的往返（如 777-778 MT32->MT33->MT32，MT33 新访问解锁后续 fly:MT33，删了
fly 失败 converter 报 "cannot fly to unvisited floor MT33"）。shop/trader 的 move/arrow
在单层内不换层，永不是 stair-step arrow，不会被删。

## automaticRoute 语义（Game 必须镜像：go_to 目的地才 sweep + path_cost 不折扣事件格）

录像->Game 复现的两个关键模型事实（2026-08-11，2攻6防 V1 复现后 web 0 mismatch），
都源于「Game 的 go_to/path_cost 必须复现 live `automaticRoute` 的实际行为」：

1. **go_to 只在目的地跑 auto_sweep**（`_go_to_body` 移除中途 auto_sweep）：live 的
   `automaticRoute(move:x:y)` 只在**目的地**跑一次 auto_sweep（`autoNextStep` 需 hero
   idle），**中途 path 格不跑**。Game 若在中途格跑 auto_sweep，会提前杀怪/spawn 道具——
   例：go_to(2,3) 曾在 (2,4) 杀 3 zombieKnight + spawn (1,3) redKey 并提前拾（rk 0->1
   时序错）。修后 redKey 在下一步显式 up 到 (2,2) 才拾（rec#997 rk 0->1），匹配录像。

2. **path_cost 不折扣事件格，破坏性事件中断 automaticRoute**：live 的 automaticRoute
   **不折扣事件格**，且**破坏性事件格**（如 MT40 (6,7) 40F boss）会**中断 automaticRoute**
   ——hero 不可能一步穿过它。原 `strict_live_model` 曾给事件格 cost 0.9 偏好 path_to 穿过
   事件触发格（为 MT26 (6,6) 公主），导致 go_to(MT40,5,7) from (6,1) 绕经 (6,7) 提前触发
   boss、奖励拾取错位（#1120(5,7)，实际 #1122 move:6,2）。修后 go_to(5,7) 走 column5 避开
   (6,7)；boss 在 go_to(6,7)（rec#1121）触发、奖励在 go_to(6,2)（rec#1122）拾取
   （atk150->162 def226->238 yk5->8），完全匹配录像。

**How to apply**：可穿 step-on NPC（公主/thief，PASSABLE_NPC_EIDS）本身是通行地 cost 1.0，
`trigger_tile_event` / `move_adjacent` 处理其事件，**不需要事件格折扣**。若将来某线需要在
等长路径里"穿过某事件格"，那是 path_to 方向序 tiebreak 与 live 的差异，应单独对齐，不要
恢复通用事件折扣。关联 [[path_cost_event_discount_removed]] [[zone12_2atk6def_v1_reproduction]]

## event_positions 必在 action 循环前快照（coalesce 例外依赖它）

coalesce 的 `is_event_tile` 例外（保留 floor-event trigger 步）依赖 `event_positions`
集合（`g.floors[fid].events` 键）。**不能在 action 循环后构建**：`trigger_tile_event`
触发后 `hide` 会从 `floor.events` 删掉该格（如 MT33 (10,5) 骑士剑机关关门事件触发后
events["10,5"] 被清），导致已触发的 trigger 不在集合 -> coalesce 误删其 到达 步 ->
replayer 没显式 click (10,5) -> hero 寻路到 (9,5) 时穿过 (10,5) 触发事件中途停住
（事件打断 automaticRoute，hero 停 (10,5) 不动）。**fix**：在循环前快照
event_positions，保留所有初始 trigger 步。

## replayer waitAsync 滞留 workaround（`clearStuckWaitAsync`）

某些 afterBattle 的 async openDoor 在 `core.animateFrame.asyncId` 留下 function 回调
永不调用（如 MT2 (8,2) blueGuard afterBattle 开 6 个 steelDoor，steelDoor 的 async
openDoor 完成后回调没清），waitAsync 永不清空 -> 复验卡死 timeout。

replayer `clearStuckWaitAsync(cdp, force)`：waitAsync 滞留 >6s 后删 asyncId 的 falsy
键（首遍）和滞留 function 回调键（force）。**关键：不 dismiss 事件**（不 set
event=null / unlockControl），让游戏自己的 waitAsync 轮询检测 asyncId 空 -> 自清 ->
afterBattle 队列继续 -> 触发开门后 auto-sweep 拾取新可达道具（MT2 开 6 steelDoor 后
auto-sweep 拾 (3,4)/(4,4)/(3,5) 三个 yellowKey，yk 4->7）。若 dismiss 事件则 bypass
开门完成 -> auto-sweep 不重跑 -> yk 少 3 发散。

相关：`recording_converter_experience.md`（recording_to_game.py，逐格复现路线）、
`zone2_experience.md`「事件机制」、[[recording_seed_trader_delta]]、
[[recording_seed_coalesce_arrivals]]、[[h5route_replay_mechanics]]。
39003 全链（save1→MT50）与 zone4（MT41→MT50）双线 web 0 mismatch 的 4 处折叠修复见
[[39003_te_web_verified]]。
