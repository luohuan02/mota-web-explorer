# recording_to_game converter 合并经验（.h5route 录像 -> Game walk）

来源 = `scripts/search/recording_to_game.py`。converter 把 .h5route 录像解码成
通用 `Game` 类 walk（每步 before/after），目标 = 给任意录像就能得到可验证 Game walk
（用户目标："通用转换逻辑修复，后面给录像就能得到 game 类结果"）。

**两条 pipeline 对照**（都从录像生成可验证 walk，机制不同）：
- `zone12_recording_autoon.py`：auto ON + skip-if-cleared，内容驱动逐目标 `go_to`。
  旧录像路径恰好 Game 兼容时能用；用户手玩调整路径常不兼容（见
  `zone12_kill_line_experience.md`「Game 类无法 action-by-action 复现」）。
- `recording_to_game.py`（本文件）：解码 route events -> 通用 `Game` 类 walk。**两条
  模式**：
  - **`--paths`（逐格 captured path）**：喂 web automaticRoute 抓的逐格路径精确复现
    录像（PRE-state statlog 0 mismatch），再 coalesce 成节点级直达目标步，最后剪枝/
    折返提升。路径分歧不再是问题（逐格走录像 exact 路径），coalesce + 剪枝是核心坑。
    KILL（2攻0def）线即此模式：358 步 web 0 mismatch。
  - **无 `--paths`（Game 自寻路，2026-08-09 突破）**：V1 买 rk 线 0 mismatch 跑通，
    推翻旧"Game 寻路必发散、须喂 captured path"结论。根因是 4 个可修通用模型 bug
    （见下「无需 captured path 的 4 个模型修复」），不是 go_to 寻路根本缺陷。**新录
    像优先试无 `--paths`**（最简），发散才退回 `--paths`；发散点几乎都是某个可修模型
    bug，先修模型再重试，不要写浏览器侧 path 捕获绕过根因（见 CLAUDE.md「根因优先约束」）。

## 无需 captured path 的 4 个模型修复（2026-08-09，V1 买 rk 线 0 mismatch）

V1（`best/2区2攻800买红钥匙V1.h5route`，买 rk 线）从 save1(MT4 slot1) 起，
`recording_to_game.py` **无 `--paths`**，0 mismatch 到 MT31
`HP=1232 ATK=76 DEF=64 YK=6 BK=0 RK=0 G=349`，web 复验
（`live_zone3_mouse_replayer_cdp.js --load-slot 1 --target-click-only
--set-auto battle=true,item=true,wall=true`）MT1-31 全过 0 mismatch/warning，
final-score=1815.5（stock 1706.5 + residual 109）。

4 个修复（`src/solver/game_route.py` + `scripts/search/recording_to_game.py`），都是
"Game 静态规划/合并逻辑没建模某种 web 实机行为"的可修 bug：

1. **事件 handler 要真开它开的墙/门**（`game_route.py` trigger_tile_event MT15 (9,1)
   分支加 `set_ground((8,1))`）：thief 事件 `openDoor(8,1)` 把 (8,1)=330
   `unbreakableWall` 开成空地，Game 必须 `set_ground` 移除墙 block。旧注释说
   "(8,1)=330 不创建 block(已 None)"是**错的**--330 在 `WALL_IDS` 内，classify 返回
   "wall"，是有 block 的墙。不 set_ground 则到 (5,1) 的唯一干净路径被封 ->
   `move:5:1 unreachable`。**教训**：事件里 `openDoor` 的目标若在 `WALL_IDS` 内，handler
   必须显式 `set_ground` 移除 block，不能信旧注释，用 `block_at` 核实。

2. **`go_to_decomposed` 被事件门挡住时踩触发格再重规划**（`game_route.py`
   `_reachable_event_triggers` + go_to_decomposed loose path=None 分支）：静态 BFS 规划
   时看不到"踩 (9,1) thief 中途开 (8,1)"这种**事件门**（hero 移动中踩触发格才开路）。
   loose `path_to` 返回 None 时，枚举可达 passable event-trigger 格，clone-test 只
   commit 能开路到 target 的触发格，再重规划。**教训**：静态可达性算不出事件开路时，
   不要断言 unreachable，要 clone-test 踩触发格后能否开路。

3. **arrow no-op 检查排除 fakeWall/fakeWall2**（`recording_to_game.py` arrow 分支加
   `not _tgt_breakable`）：`break_wall_stay`（破 fakeWall2 hero 停邻格）不改 pos 也不改
   stat，被"pos+stat 全不变=转身 no-op"误判跳过 -> 漏破墙 + 漏 spawn 道具。**典型**：
   MT19 (6,3) cross -- si652 `up` 破 fakeWall2 + spawn cross 被跳过 -> si653 踩上 cross
   的 spawn 时机错 -> cross 没拿到 -> MT20 vampire 无 cross atk×2 爆伤 14809。**教训**：
   no-op 判据（pos+stat 不变）要排除 trigger 型格（fakeWall/fakeWall2 破墙 spawn 道具），
   它们的副作用在 spawn 而非 pos/stat。

4. **coalesce `_fold_move_waypoint` 不折叠 shop/NPC 目标**（`recording_to_game.py` 加
   `_is_shop_npc_target`，排除 action `商店`/`商人` 或 `事件`+`blueShop`/`trader`/
   `shop`/`oldman`）："到达(6,10)" + adjacent"事件 blueShop(6,9)" 被折叠成一步，用"到达"
   的 before(post-move 6,10) 当合并 before，丢 (8,11)->(6,10) 位移。replayer 从 (8,11) 远点
   click (6,9) -> `repeatTargetClick` 误买 HP（blueShop 选项标准序
   `[HP+500(0), ATK+4(1), DEF+8(2), 离开(3)]`，`choose("atk")=1` 本应买 atk，但远点寻路 +
   repeat 命中 index 0 买 HP）。**教训**：shop/trader 需 hero 相邻 face-on 才交易，不能 fold
   进 move-waypoint；保留"到达"独立步即可。同源 bug 见
   `mt32_multitile_shop_approach`、`buy_shop_position_agnostic_needs_approach`。

**诊断方法论**（新录像转 walk 发散时）：先 `recording_to_game.py` 无 `--paths` 跑，看首个
mismatch 的录像 step。发散点几乎都指向上面 4 类之一：(a) 事件门/墙没开 ->
查 `trigger_tile_event` 该格有没有 case + `set_ground`/`set_block`；(b) 静态到不了但
实机能到 -> go_to_decomposed 要踩触发格；(c) arrow 步被误跳 -> 查 no-op 判据是否漏了
spawn 型 trigger；(d) 数值对但远点寻路买错 -> 查 coalesce 是否把 shop/NPC fold 了。
**不要**写浏览器侧 `setHeroLoc` hook 抓 automaticRoute paths 绕过--那是治标，根因是模型 bug
（本次曾走过此弯路，被用户纠正"game 类的通用转换逻辑为什么不适配"，转向修模型才 0 mismatch）。

**适用边界**：4 修复是通用 Game 模型 + converter 逻辑修复，理论上对所有录像都适用。但本次
只对 V1（买 rk 线，auto ON，MT1-31）web 验证了无 `--paths` 0 mismatch；KILL（2攻0def）线仍用
`--paths`（358 步产物未重测无 paths）。新录像先试无 `--paths`，发散再退 `--paths`。

## converter 输出的 step 分类（coalesce 合并的依据）

coalesce（`coalesce_node_level`）把逐格 pass 合并成"直达目标"1 步，贴合 Game `go_to`
+ replayer 点目标游戏 automaticRoute 一次到位。合并与否取决于 step 类型：

| 类型 | 识别 | 合并? | 原因 |
|---|---|---|---|
| `move_merge`（move:x:y）| note 以 `"move "` 开头 | **可 fold 进紧接 adjacent 目标** | 多格 automaticRoute 到 waypoint（停靠点），非目标格 |
| 有 `auto_sweep` 的 pass | note 含 auto marker | 不可合并（独立节点）| auto 触发点，合并丢 auto 时序 |
| `trigger-event` pass | note 含 trigger-event | 不可合并 | hero 踩格触发 spawn，web 寻路中途踩会中断 |
| 换层 / 拾取 / 击杀 / 破墙 | action 换层 / _is_target | 目标步（合并终点）| 节点直达终点 |

> 走门格（walkonto-door）已移除，见下节。点相邻门 = door_stay 开门（hero 停邻格消费
> 钥匙），不再产生"走门格"独立步；门开后该格成为 former-door，后续寻路可经它，move
> 进它直接 fold 进目标。

## fold move-waypoint 的安全性（核心可复用论证）

**问题**：walk 里大量 `move:x:y` 移到非物品/事件空格（waypoint）= 冗余费步。用户
反馈"移动位置不是任何物品、事件的动作"。

**fold 规则**：`move:W` + 紧接 **adjacent**（Manhattan=1）目标 T -> 折成 T 一步。
replayer 点 T，hero auto-route 经 W 到 T。

**为什么安全**（不是肉眼判断，是机制论证）：
- `auto_sweep` at T ⊇ `auto_sweep` at W。W 是 T 的相邻格，T 的 auto BFS 从 T 出发
  必扫到 W 的邻域，故 W 处会触发的 auto 副作用在 T 处都会触发。
- converter 已分别算了 W 和 T 的 auto items，`_merge_waypoint_into_target` 把两者
  合并成一个 `auto_sweep:` 段，累计 = T 的 BFS，不丢。
- replayer `assertAutoSweepSideEffects` 只查首个 `auto_sweep:` 段，故必须合并（否则
  W 的 auto 在第二段被漏检）；`gen_zone_walk_md.py extract_clear_note` 遍历所有 marker
  也能正确显示。

**非 adjacent（Manhattan>1）不能 fold** = 必要中断停顿。hero 寻路到 W 停下是因为路被
墙/障碍挡或踩了事件格，不能直达 T；fold 会让 replayer 点 T 时 hero 走直线被挡 -> 卡死。

**链式 fold**（move->move->target）：`move:W1 + move:W2 + target`，若 W1-W2 相邻且
W2-target 相邻，链式折成 target。`auto_sweep` at target ⊇ 链上所有 waypoint（BFS
覆盖相邻链）。实现 = in-place 折叠后 **重处理 folded step**（`continue` 不 `i++`），
使 folded target 可能继续折进 next-next。adjacent 链断处停（必要中断）。

## 走门格移除（旧"door-pass 不可合并"已作废）

**旧结论已撤回**：曾认为"开门+走门格"必须 replayer 独立两步点击（点门开门 + retry 走
门格），否则合并进后续目标会让门未开寻路被挡。**这是错的**。

**正确机制**（用户 3 点纠正）：
1. 走门格（hero 走到门格上）**不是游戏机制**。h5mota 点相邻门 = door_stay：开门 +
   hero 停在邻格（消费钥匙），不走进门格。
2. 录像里看似"走门格"的动作，通常是开门后**走到门后资源/暗墙位**触发 auto，不是
   为了踩门格。
3. 门一旦 door_stay 开了就是开（former-door），后续寻路可自由经过该格，不会被挡。

**fix**：`_merge_door_walkonto`（Pass 1）改为 **no-op**（`return list(steps)`）。开门
（arrow door_stay）独立成 step（hero 邻格）；"走到 former-door 格"的 move 交给 Pass 2
`_fold_move_waypoint` 折进紧接目标。replayer 点开门（门开 hero 邻格）+ 点目标，hero
寻路经 former-door auto 拿门后资源到达目标。录像 statlog 证明 hero 一次性可达目标
（web auto 不中断），故折进目标安全。

## coalesce 顺序（为什么是这个序）

`coalesce_node_level` 主体：`steps = _fold_move_waypoint(steps)` 后跑 Pass 2 主合并；
输出再经 `_hoist_stair_uturn`（Pass 3，后处理 U 型折返）。

- **Pass 0 `_merge_door_walkonto`**（先，现 no-op）：保留函数骨架为占位，走门格已移除。
- **Pass 1 `_fold_move_waypoint`**（中）：fold move waypoint + adjacent target。消除
  waypoint 冗余。
- **Pass 2 主 coalesce**（后）：合并连续无 auto、非 move_merge、非 trigger 的 pass +
  紧接目标 -> "直达 X,Y (合并 N pass + action)" 1 步。
- **Pass 3 `_hoist_stair_uturn`**（最后，后处理）：剪楼梯 U 型折返（见下节）。

## 零效果 move 剪枝（转换期，在 move handler 内）

**问题**：录像里有些 `move:x:y` 前后 7 项 stat（hp/atk/def/yk/bk/rk/g）全不变、也无
auto/trigger = 纯零效果移动，是冗余动作（用户反馈"多余动作"）。

**剪枝规则**（满足任一则剪）：
- **a. 后接 fly**：fly 楼层传送器位置无关（任意格 -> 固定楼层入口），前导 move 纯冗余。
  例：MT6 `move:3:8 @ (2,9)` 后接 `fly:MT3` -> 剪。
- **b. 后接 move 且其 captured path 含本 move 的 pre-move pos**：hero 在下一 move 的
  寻路路径中间格，从该格的后缀继续即可。例：MT4 `move:9:1 @ (10,3)` 后接
  `move:11,10`，(10,3) 在后者 captured path index 2 -> 剪，replayer 点 (11,11) hero
  走 22 格后缀。

**关键坑 -- no-op 箭头**：move 与 fly/下一 move 之间，录像常夹着**无效箭头**（玩家
转身/面墙误触，如 `move:9:1 -> right -> move:11,10`）。这些 arrow 的 statlog 前后
pos+stat 全同（`_statlog_noop` 判定），是 no-op。剪枝时**必须一并跳过**这些 arrow
（`ri = j2 - 1` 让尾随 `ri += 1` 落在 j2），否则从剪枝位置重放 arrow 会错误位移 hero
（例：从 (10,3) 重放 `right` 会把 hero 推到 (11,3)）。

**drift_check 处理**：剪枝后，被剪区段的 statlog pos 期望不可达，加入 `skip_pos_si`
集合 -> drift_check 对该区段**跳过 pos 校验，stat 仍逐条校验**（保持 0 mismatch）。
hero 在下一真实 action 处重新对齐。

## 楼梯 U 型折返提升（`_hoist_stair_uturn`，Pass 3 后处理）

**问题**：录像里 hero 踩楼梯上楼、立刻原楼梯下楼、做完本层动作、再踩同楼梯上楼 =
4 步浪费的折返弹跳。用户反馈"第一次 8 楼上 9 楼没拿钥匙，又回 8 楼拿"。

**模式**：`[踩楼梯 F->G][换层][踩楼梯 G->F][换层][F 层动作序列][同楼梯同向踩]`。
hero 落回出发格（断言 `(折返后 pos) == (折返前 pos)`），中间动作全在 F 层。

**变换**：把 F 层动作序列 + 末尾同楼梯踩 提到折返之前，丢弃 4 步弹跳。
`out.extend(mid); out.append(同楼梯踩); out.append(换层)`，跳过 4 步 bounce。

**安全论证**（结构性，非肉眼）：弹跳 4 步全程零效果（statlog 证明）+ hero 落回出发
格（断言）；中间动作的入参状态/起点与提升后完全相同（mid[0].before pos == 折返前
pos，断言）；mid 全在 F 层、无换层/飞行（断言）；扫描有界（40 步）。全 walk 命中 1 处
（MT8 钥匙 U 型折返），无误伤。

## 验证方法（合并/剪枝改动后必跑）

任何 coalesce/剪枝改动后双验证：
1. **converter PRE-state statlog 0 mismatch**：每步 before/after 对照录像 statlog
   ground truth（fold/剪枝不改终态，只改步数）。
2. **web replayer 0 mismatch**：`node scripts/live/live_zone3_mouse_replayer_cdp.js
   --walk <live.json> --load-slot 1 --target-click-only`，看全程无 MISMATCH/ERROR/
   timeout + final state == 期望。

本次（走门格移除 + U 型折返提升 + 零效果 move 剪枝）后：walk step 364->358（U 型折返
-4，剪 move:3:8 / move:9:1 各 -1），walk.md 655->641 行，0 mismatch 保持，final
HP=1215 == exp。剩余 move_merge 仅 1 个（MT15 thief trigger，必要）。

## 通用教训

- 录像转 walk 的 coalesce **不是无脑合并连续 pass**：须区分 waypoint（可 fold）、
  trigger/walkonto（独立步）、有 auto 的 pass（独立节点）。
- fold 安全性靠 **auto_sweep BFS 路径无关性**论证（T 的 BFS ⊇ adjacent W 的 BFS），
  不是肉眼"看起来挨着就能折"。adjacent 才安全，非 adjacent 是真中断。
- `move_merge` 的 note `"move ..."` 是 h5route automaticRoute 多格产物，代表绕路 /
  waypoint，**不是目标格**；coalesce 默认排除它独立成步，fold 只处理"紧接 adjacent
  目标"的子集。
- 合并 auto items 须聚成**一个** `auto_sweep:` 段：replayer 只查首段，多段会漏检。
- **走门格不是游戏机制**：door_stay 开门 hero 停邻格；门开即 former-door 可经。不要
  把"走到门格"当独立步保留，更不要为它加"门未开寻路被挡"的伪 bug 逻辑。
- **零效果 move 剪枝须处理 no-op 箭头**：move 与下一真实 action 间常夹 statlog 证明
  无效的转身/面墙 arrow，剪枝时一并跳过，否则从剪枝位置重放 arrow 会位移 hero。
- **结构性变换靠断言保安全**：U 型折返提升靠"弹跳零效果 + 落回出发格 + mid 同层无
  换层/飞行"等断言，不是肉眼判断"看起来能提"。
- **读后台任务输出用 `TaskOutput`**（得 exit_code + final 状态），不要 Read/Grep
  `tasks/*.output` 临时路径（`check_read.py` 只拦 Read 工具，Grep 漏过弹窗）。
- **录像转 walk 发散先修模型，别写浏览器 path 捕获**：`recording_to_game.py` 无
  `--paths` 能跑通多数录像（V1 买 rk 线 0 mismatch）；发散点几乎都是可修通用模型 bug
  （事件门没开/触发格没踩/no-op 误跳 spawn 型 trigger/coalesce 折了 shop 目标），见
  「无需 captured path 的 4 个模型修复」。`--paths` 是退路不是默认；浏览器侧
  `setHeroLoc` hook 抓 automaticRoute paths 是治标绕过根因，已被用户纠正并弃用。
  关联 [[game_conversion_no_paths_needed]]。

相关：[[recording_to_game_converter]]、`zone12_kill_line_experience.md`、
`zone2_experience.md`「事件机制」、[[h5route_replay_mechanics]]。
