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
