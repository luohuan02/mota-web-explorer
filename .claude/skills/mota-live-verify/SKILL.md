---
name: mota-live-verify
description: 用于在实机浏览器执行生成的魔塔/h5mota walk、对照真实游戏行为验证路线、给存档槽做检查点、从槽位恢复、或对比实机状态与本地 walk。
---

# 魔塔网页实机验证 Skill

这个 skill 用于把本地生成的 walk 真实跑进网页游戏，并在每步后校验状态。只读取网页状态时用 `mota-live-browser`；只做本地审计时用 `mota-route-audit`。

## 前置检查

0. 如果要复现跨区路线，先读取 `best/route_chains.md` 或 `best/route_chains.json`，确认当前分支是 `guide_chain_to_22264`、`non_guide_current_best_branch`，还是某个独立存档尾段。不要把 save37 的 22264 尾段直接接到 slot26 状态上。

1. 确认本地 route JSON 已生成：

```powershell
python scripts\baseline\replay_zone2_guide_route.py
python scripts\search\search_zone2_macro_routes.py
```

2. 确认 chrome 已由 `scripts/live/launch_h5mota_chrome.ps1` 在真实端口 9222 外部启动（带 browser-profile），并 `agent-browser connect 9222`。**不要用 `--cdp 9222` flag**（会启动 agent-browser 自管 chrome、用 TEMP profile，丢 browser-profile 存档），**不要用 `--auto-connect`**（粘错 tab）。

3. 读取当前网页状态，确认是否与 route checkpoint 匹配（楼层感知，避免 cmd.exe 破坏 JS）：

```powershell
node scripts\live\live_read_state.js
```

## 生成式 walk 的 web 复验（Game 生成路线专用，2026-09-12 实战沉淀）

Game 类直接生成的全新拓扑 walk（非录像转换）复验时有独有坑，全踩过：

1. **换层步 pos 必须写"出发楼梯格"**：生成器常误写落层侧格子（换层后的位置）。
   批量修法：对每个 act=换层 步，从 before 层的 changeFloor 表里找指向 after 层的
   楼梯格替换 pos（跳过 MT44 隐藏层）。
2. **跨层跳（|层数差|>1）必须写 act=飞行**：写 act=换层 会引导 replayer 点击落层
   格，hero 在出发层点击无效。fly 步的 pos 写**落点层的落点格**（pos=None 会让
   replayer 崩溃 "object null is not iterable"）。
3. **楼梯换层优先用 fly**：楼梯相邻格的 click 触发不可靠——①对角相邻的楼梯
   moveDirectly 折断（hero 停在 (2,2) 上不去 (1,1)）②正交相邻也可能不上楼。
   **CDP 真键盘**（agent-browser press ArrowUp 等）是相邻格移动/楼梯踩踏的可靠
   方式；eval 合成 KeyboardEvent 不可靠。
4. **boss/剧情复合步必须拆成显式步**：生成器把"事件触发+9 战+供给"压成一步
   （after=终态）时，live 单击只触发事件（状态不变），verifier 期望链对不上。
   必须镜像已验证录像的逐步点击序（如 MT10 boss：触发步→8 骨架清场→(6,2)
   剧情步（**不可跳，无 after 差异最易漏**）→captain→供给事件）。
5. **sweep 微差平移迭代**：生成 walk 的期望链与 live 的 auto_sweep 范围存在
   ±16~39G/±1yk 级周期性微差——strict 模式逐卡点把后续步的 before/after 平移
   （gold/yk += 偏移）后可继续推进几百步；或非 strict 跑完读终态对比。
6. **正确存档 API**：`core.control.saveData(null)` + `core.utils.setLocalForage(
   'saveN', data, cb)`（Promise 包装等回调）——`core.saveGame` 不是函数。
   **每个关键节点立即存槽**（页面刷新/重启丢现场且无 autoSave）。
7. **--start-step 续跑必须配套对应步的存档槽**：--load-slot 1 + --start-step N
   = 重载起点后从第 N 步点起，状态对齐即刻失败。live 现场续跑 = 不带 --load-slot。


## 执行路线（统一点击 verifier，1-4 区 / 4-50 层通用）

**禁止**使用旧 `live_zone2_runner.py` / `live_zone3_guide_runner.py`
（方向键逐步走 + `core.doAction`；已于 2026-08-08 pre-cleanup 删除，git tag `pre-cleanup-2026-08-08` 可恢复）。
1-4 区全部用统一 CDP 点击 verifier `scripts/live/live_zone3_mouse_replayer_cdp.js`
+ 通用 `Game` 类生成的 walk JSON。它用游戏地图点击 handler（`_sys_ondown` /
`_sys_onup`）由游戏自身寻路一次到位，不逐步走、不强制移动英雄。

从指定存档位加载后，从头（或从某步）验证整条 walk：

```powershell
node scripts\live\live_zone3_mouse_replayer_cdp.js `
  --walk outputs\results\zone2_2atk1def_game_route.json `
  --load-slot 100 `
  --set-auto battle=true,item=true,wall=true `
  --target-click-only `
  --out-json outputs\results\zone2_live_verify_latest.json
```

只跑到某一步用于试探（`--start-step` / `--stop-step` 均为 1-based）：

```powershell
node scripts\live\live_zone3_mouse_replayer_cdp.js `
  --walk outputs\results\zone2_2atk1def_game_route.json `
  --load-slot 100 --start-step 141 --stop-step 160 `
  --set-auto battle=true,item=true,wall=true --target-click-only
```

要点：

- walk JSON 必须是通用 `Game` 类输出（`before/after` 直接对照实机），不是旧
  Replay 的楼梯合并格式。
- replayer **只按 pos 点击，不解析 walk JSON 的 `action` 字段**（2026-07-16
  grep 实证）。action 中文名/.md 英文动词（`game_route.ACTION_VERB_EN`）只服务
  人读 .md；JSON 里出现 `破墙` 等中文 action 不影响复现，gen 旧版
  `破墙->通过` 归一化已删除。
- 3 区起按需 `--set-auto battle=true,item=nopotion,wall=true`（4 区半血陷阱控血）。
- verifier 每步对照 `steps[startStep-1].before` 与实机状态；传送/换层/开门允许
  忽略最终坐标但不忽略数值。出错停下报告，不要继续猜。
- 存档/checkpoint 用 `scripts/live/export_save_slot_cdp.js` 导出到
  `best/checkpoints/`，只写 100+ 槽。

## 合法移动约束

- 不要在实机路线里直接调用 `core.changeFloor(...)`。
- 到过的楼层使用飞行器行为，脚本封装为 `core.flyTo(...)`。
- 未到过的楼层必须通过楼梯或剧情触发进入，例如首次进 15F 要从 14F 真实走到楼梯触发点。
- 20F 吸血鬼事件触发后，周围大蝙蝠会合并为吸血鬼，不能再按旧资源单独击杀。
- 纯净版-TE 验证中禁止使用特性版的对话破墙、破门、破怪，也不要使用 2026 复刻版已取消的旧 TE 下楼器/稿/地震直杀真魔王技巧。
- 使用楼层传送前，如果实机会检查“是否能到达任意楼梯边”，必须以 live 状态为准。若出现“无法到达任何一个楼梯边”，立即停止并回到 replay 审计，不要脚本侧强制飞楼。

## 自动操作策略

实机 replay / verifier 可以动态控制游戏内“特殊设置 -> 自动操作”来减少点击，但必须把这些自动 side effect 纳入状态校验：

- 自动清零伤怪：`core.status.hero.flags.__auto__.battle = true`。TE 真结局流程或拿到双倍金币后可开启；后续金币/怪物数量仍要按实机结果核对。
- 自动拾取非血瓶物品：`core.status.hero.flags.__auto__.item = "nopotion"`。这是“自动拾取物品 on / 拾取血瓶 off”的真实状态，可在需要保留血瓶时使用。
- 自动拾取含血瓶：`core.status.hero.flags.__auto__.item = true`。1区/2区缺血复现可开启；3区以后若为了保留血瓶已切到 `"nopotion"`，则只在拿到圣盾后，或确认后续不会再经过半血/固定扣血检查时再切回 `true`。
- 纯净版-TE 的 44F 神圣盾路线在 `magicImmune=true` 后应立即执行机器 walk 中的 `设置自动` step，把 `item` 切为 `true`，并回读 `__auto__` 校验。不要把它简化成整条路线启动时就开 true，也不要继续全程 `nopotion`。
- 自动开暗墙岩浆：`core.status.hero.flags.__auto__.wall = true`。原则上可全程开启；岩浆仍应遵守拿到雪花后的真实清理规则。
- 当前 1区/2区缺血复现优先组合：`{ battle: true, item: true, wall: true }`，让血瓶也自动拾取；进入 3区或需要保留血瓶时再切到 `{ battle: true, item: "nopotion", wall: true }`。
- 若目标是给 4区半血陷阱控血，不要先在实机里边跑边猜该删哪瓶血。正确顺序是：先在离线 strict walk 上做“固定动作序列下的最低存活 HP 压缩”，得到 minhp 版 walk；再拿这个新 walk 做一次正式 replay。`record-only` 只适合重录/适配 live，不适合作为最低血版是否成立的最终证明。
- 开门 sweep 归属（2026-08-31 定稿，推翻旧「开门不立即结算」表述）：hero 点击开门经 walk-through 踏上刚开的门格，auto sweep 从门格起跑并归入**门步**（`Game._apply_door_live`）；verifier 对每个开门步确定性补一次「走进门格」点击（见下「开门步确定性走门格」）使 live 归属与 walk 一致。例外：事件开门/Boss 掉落等非 hero 移动的开门不触发 auto，等下一次 hero 移动再结算。
- 生成实机 walk 时不要照本地逐资源顺序远点一个组内最后目标。应点击真实的自动资源组入口，并把同组资源写进备注。例如 9F 中部资源组从 `MT9 x9y4` 开门后，应点 `MT9 x7y4` 触发自动拾取/清怪，备注 `x5y4 黄钥匙`、`x6y5 红宝石`、`x7y6 红头怪`，再继续点 `x4y5` 黄门。

切换 auto 后读取 `core.status.hero.flags.__auto__` 确认。**关键区分**：要进 `.h5route` 的 walk `SET_AUTO`（设置自动）step **必须走「游戏说明」菜单**（见下「SET_AUTO 录像记录根因」），`setAutoState` 直接改 flag 对录像回放不可见；只有 verifier 启动时的 `--set-auto` 初始状态用 `setAutoState` 直接改即可（回放前的前置设置，不属录像 route）。不要把自动清理造成的额外拾取/杀怪当成模型误差忽略，必须在 route JSON 或 verifier 容忍逻辑中记录和比对。

### SET_AUTO 录像记录根因（必须走游戏说明菜单）

walk 里的 `SET_AUTO` step 要切 `__auto__`，**必须走「游戏说明」commonEvent 菜单**（`core.insertAction([{type:"insert",name:"游戏说明"}])` → 选「自动操作」→ 切 battle/item/wall → 退出设置 → 返回游戏），**不能用 `setAutoState` 直接改 `core.status.hero.flags.__auto__`**。

根因：`.h5route` 录像 = `LZString` 压缩的 `{name,hard,seed,route}`，`route = core.encodeRoute(core.status.route)`，只记录进过 `core.status.route` 缓冲区的命令。菜单路径 push `help` + `choices:N` 进 route 缓冲区；回放时 `doAction` 在 action-chain 对话框打开期间消费 `choices:N`（绕过 `ignoreInput` 对裸 `choices:N` 的跳过），auto 真实切换。`setAutoState` 直接改内存 flag，**不进 route 缓冲区，回放时不可见** -- 录像回放到 SET_AUTO 步 auto 不变。

- 进入入口是工具栏「游戏辅助设置」按钮（`toolbarAction[0][2]` = `insertAction([{type:"insert",name:"游戏说明"}])`），**不是按 H**（H 是 `_drawHelp` 键盘图，`event=help` 无 choices 不 push route）。
- 游戏说明菜单 choices：`[游戏特性, 游戏结局, 游戏榜单, 关闭/开启额外功能, 自动操作, 交易统计, 返回游戏, 详细显伤]`，index 4=自动操作（需 `flag:额外功能开关`）。自动操作子菜单：0=清零伤怪 battle、1=拾取物品 item(true↔false)、2=开暗墙岩浆 wall、3=退出、4=拾取血瓶 item(true↔nopotion)。
- verifier `live_zone3_mouse_replayer_cdp.js` SET_AUTO 分支已用 `setAutoStateViaMenu`（line 2465），日志打印 `auto ... -> ... (via 游戏说明 menu)` 确认走了菜单。`--set-auto` 初始值仍用 `setAutoState`（line 3193，回放前前置，OK）。
- 验证（2026-08-09）：zone4 2atk3atk5def TE33508 step 21 MT42 `item=false->true` 走菜单 `(via 游戏说明 menu)`，403 步 0 值 mismatch，final HP=33508 通关；导出 .h5route 从头回放 auto 8 次切换全生效。save1→关 auto→走 5 楼简单场景同样验证菜单方式回放正确（最终 MT5 x9y3 hp=726 auto 全关，匹配 save5）。

动态 auto 只证明后续点击触发时会拾取当前同层可达血瓶，不证明所有楼层已清空。最终真魔王前仍必须对照离线残余审计，核对 49F 事件奖励、各层药瓶/宝石、黄钥匙售卖与生命商店闭环；web 复验逐步核对这些真实点击及资源变化。

## 校验策略

脚本每步会：

- 读取 live 状态；
- 和 route JSON 的 after 状态比对；
- 对传送、换层、开门、对话、商店等允许忽略最终坐标但不忽略数值；
- 执行前写游戏存档槽 checkpoint，优先使用用户明确允许的 100+ 槽位；
- 出错后读取最近 checkpoint 重试一两次；仍不一致就停止并报告，不要继续猜测。

如果因为真实地图修正导致路线 JSON 与网页不同，先回到 `mota-route-audit` 修正 replay，再重新生成 route JSON，不要长期依赖 `--yk-offset` 一类补丁。

## --out-json 验证结果判读（重要陷阱）

`live_zone3_mouse_replayer_cdp.js --out-json` 写的 JSON 里，**不能直接信以下两个字段当“通过”**：

- `strictWalk.ok` / 顶层 `ok`：**硬编码 `true`**（`buildStrictWalkFromLog` 恒置 `ok:true`），不论有无不匹配。看到 `ok:true` 不代表 0 mismatch。
- `strictMismatch`：`strictMismatchText` 只比对 `floor/x/y/hp/atk/def/yk/bk/rk`，**不含 `gold`/`money`**。金币不匹配不会出现在 strictMismatch 里。

要得出“0 值不匹配（含金币）”的可靠结论，必须**自己扫 `entries[]`**，逐条比对 live `after` vs `expectedAfter` 全字段（含 gold，用 `o.gold ?? o.money` 取值）：

```js
// tmp/check_mismatch.js 模板
const data = JSON.parse(fs.readFileSync(verifyJson));
let val=0, pos=0;
for (const e of data.entries) {
  const l=e.after, x=e.expectedAfter; const bad=[], posBad=[];
  for (const f of ["floor","x","y","hp","atk","def","gold","yk","bk","rk"]) {
    const lv = f==="gold" ? (l.gold??l.money) : l[f];
    const xv = f==="gold" ? (x.gold??x.money) : x[f];
    if (lv!==xv) (["floor","x","y"].includes(f)?posBad:bad).push(`${f}: exp ${xv} got ${lv}`);
  }
  if (bad.length) val++; if (posBad.length) pos++;
}
// val===0 才是“0 值不匹配含金币”；pos 是 target-click-only 坐标偏移（已知边界，可接受）
```

- target-click-only 让游戏自动寻路，hero 常停在目标相邻格 -> `x/y` 差 1-2 是**已知边界**（见 CLAUDE.md「h5mota 回放边界情况」），可接受；但 `hp/atk/def/gold/yk/bk/rk` 任何一条不一致都是真不匹配。
- 通过判定 = `val===0`（值全匹配）且最终 `finalState` 与 `expected_final` 全等。`pos>0`（纯坐标偏移）不影响通过。
- 反例（2026-07-16 实证）：2攻0防 KILL 线 skip362 walk，`strictWalk.ok=true` 但逐 entry 扫出 24 条 `strictMismatch`——全是 `x/y` 偏移、0 条值不匹配（含金币），最终 HP=1301 与 expected 全等，才算真通过。

## 当前二区实机注意点

- 当前 zone1-2 最优（2攻0防 KILL 线，recording_to_game converter 版）复现命令：

  ```powershell
  node scripts\live\live_zone3_mouse_replayer_cdp.js --walk outputs\results\zone12_2atk0def_recording_walk.json --load-slot 1 --target-click-only --set-auto battle=true,item=true,wall=true
  ```

  预期：358 步、0 值不匹配（含金币），final `HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298`（MT20 x6y5）。人看 walk 与判读：`best/zone12_2atk0def_recording_walk.md`。
- `MT1 x4y3` 已在 replay 中显式记录；新路线不应再需要 `--yk-offset -1`。
- `MT1 x1y3 红血瓶` 应在开 `MT1 x4y3` 后顺路吃掉。
- `MT14` 三兽人武士后，真实游戏会生成红钥匙物品；脚本会实际拾取，不当作凭空加 RK。
- 商店选择使用 `event.ui.choices` 的 action 插入，避免菜单焦点偏移。

## 1区 / 10F Boss 实机注意点

- 10F Boss 事件后，清完生成怪并打开 `MT10 x6y3` 后，`MT10 x6y2` 是骷髅队长剧情事件格。必须先真实点击/走到 `MT10 x6y2` 触发并处理事件，再点击 `MT10 x6y1` 打骷髅队长。
- 不要从远处直接点击 `MT10 x6y1`。真实寻路会经过 `x6y2` 并触发事件，容易让 verifier 以为目标是队长战斗，实际却停在剧情事件中。
- `clearMt10BossDyn`（`live_zone3_mouse_replayer_cdp.js` 内）已实现此顺序：阶段1 只清 spawned（x4-8/y4-7，**不含 captain 6,1**），阶段2 等 `x6y3` 事件墙开后先点 `x6y2` 处理骷髅队长剧情文本，再点 `x6y1` 打 captain。不要把 captain 纳入动态清怪循环，否则寻路经过 `x6y2` 会卡在 `lock=true event=action:text`。boss trigger 后若 `x6y5→x6y1` 路径上还存在其它事件格，同样要先点事件位置再点战斗目标，不要远距直点。
- Boss 后生成怪位置以 live 地图为准动态读取；不要只按本地静态地图坐标清怪。

## 回放器事件等待节奏（`live_zone3_mouse_replayer_cdp.js`）

### auto 机制（关键：远程吃，不走路）

`core.plugin.auto` 的 bfs 从 hero 位置一趟扫描，对可达的 enemy/item/wall **全部远程处理，hero 不走过去**：
```js
if (type==="enemy") core.battle(id,x,y)          // 远程战斗
else if (type==="item")  core.getItem(id,1,x,y)  // 远程拾取 + 200ms 飞行动画
else if (type==="wall")  core.removeBlock(x,y)   // 远程破墙
```
所以 walk JSON 一步带 N 个 auto 是对的；**hero 不会绕路到每个拾取点**。诊断回放慢步时不要假设"auto 在走路拾取"。

### Space 节奏（非文本动作步不按 Space）

verifier 在 `lock`/`eventId` 期间推进事件队列靠**真实按 Space**（禁用 `core.doAction`）。h5mota 源码 `_keyUpAction` 证明：**只有 `text`/`wait`/`choices`/`confirm` 四类动作步响应 Space**；`sleep`/`waitAsync`/`openDoor`/`move`/`generateMove`/`setCurtain`/`setBlock`/`hide`/`show` 等都靠定时器/动画回调自动推进，按 Space 是纯 no-op。

- `SPACE_DISMISSABLE_ACTION_TYPES = {text, wait, choices, confirm}`：4 处等待循环遇非这 4 类动作步**只 120ms 轮询、不按 Space**（旧版无差别按 Space + 450ms sleep，afterBattle 的 `waitAsync`/`openDoor`、`generateMove`/`move` 期间空按，每次 pressKey 自身耗 ~150ms）。
- 文本步 Space 节奏 200ms（旧 450）；`_label` 同步点 250ms（旧 600）。文本步降速安全：`_clickAction_text` 有 `if (core.status.event.animateUI) return` 守卫，hide 动画期间第二次 Space 被忽略，双击不可能。

### pre-lock breakOnIdle（修过的大坑：PASS 步干等 15s）

`runOneStep` 的 pre-lock 分支：某步启动时若前一步遗留事件还在（`pre.lock||eventId||moving||choices`），先 `waitForCandidates` 等状态匹配（coalesced）。**bug**：非 KILL 步用 `preTimeout=15000`，PASS 步（如 boss 后通过/拾取）在前一步 afterBattle 遗言文本还在时进入 pre-lock，但本步还没点击、状态永不匹配 -> **hero 空闲干等 15s 超时才 fall through 去点击**。实测 MT10 队长后 [151] 通过 x6y9 因此耗时 18.76s（15s 空等 + 3s 真活）。

- 修复：`waitForCandidates` 加 `breakOnIdle` 参数。pre-lock 调用传 `true`：等待中一旦遗留事件清掉、状态变空闲（`!lock&&!eventId&&!moving&&!choices`）但无候选匹配，**立即 throw 跳出去 executeStep 点击**，不等 15s。coalesced 情况在空闲前就匹配返回，不受影响。post-click 调用保持默认 `false`（点击后空闲不匹配 = 真失败，走超时）。
- 结果：[151] 18.76s->3.93s，总 129.7s->115.8s，0 mismatch 保持。MT20 宝物房同理。

### strict 模式点击前等 automaticRoute 走完（busy 等待修复）

`mouseClickTile` strict 模式（`--target-click-only`/`--strict-human-input`）原版：读 `before` 状态，若 `lock||moving||eventId||hasChoices` 直接 `throw cannot click while busy`。**坑**：英雄从上一步的 automaticRoute 还在走时（damage/checkBlock 格不停路线，hero 继续走向目的地），下一步点击时 `moving=true` 是瞬态，直接 throw 误杀。zone4 2atk3atk5def TE33508 复验在 step 160（MT45 downFloor）因此挂：hero 从 x6y3 checkBlock 的 automaticRoute 还在走，停在 x4y1 `moving=true`。

- 修复：strict 模式下若**只有 `moving` busy**（无 lock/eventId/hasChoices）先 `waitMovementSettled(cdp)` 等走完动画再点（人类也是等走完再点）；仅非瞬态 busy（lock/eventId/hasChoices，或等完仍 moving）才 throw。通用修复覆盖所有 step 类型，不只 downFloor 分支。
- `waitMovementSettled`（line 653）等 `moving=false` 最多 60s，非 strictHumanInput 时还 `clearStaleMoving` 兜底。
- 验证：修复后 zone4 403 步全跑完，0 值 mismatch，final HP=33508 通关。此 race 是非确定性时序 flake（同一 walk 之前 ok:true 是 timing 运气，菜单 SET_AUTO 对话框延迟可能略微偏移 automaticRoute 时序），此修复使其确定化。
- 2026-08-30 追加：`event=action:_label` 瞬态事件壳（如 MT45→MT43 换层落点剧情 label 还在自动推进时）同样先等（最多 5s）再判 busy，否则 repeatTargetClick 的重试点击竞态误杀（41200 复验 step 949 实证：上一轮该步通过、下一轮挂，加等待后确定通过）。

### 开门步确定性走门格（2026-08-30 41200 修复）

游戏对开门的 route-resume（hero 续走踏上刚开的门格 → `control.moveOneStep` 补丁插入 `core.auto()` → auto BFS **从门格起跑**收集门后 0 伤怪+道具）时机**不确定**：0.3s 内或随下一次移动才发生（依赖事件壳残留），同一 walk 不同轮表现不同。verifier 现在对每个 `开门` 步在首击后确定性补一次「走进门格」点击（门块已消失且 hero 空闲且未在门格上时），把 sweep 归属固定在门步——与 Game `_apply_door_live` 的「开门后以门格为起点自动BFS」模型逐字段一致。配合 converter coalesce 的 `is_door_approach` 例外（门前定位步保留）使用。

~~已知残留（2026-08-30）~~ → **已解决（2026-08-31）**：41200 二访 MT47 (1,6) 到达窗口 live 多收 +50G（x11y6 redBat）——最终根因是 Game auto_sweep 的 BFS 用 `check_damage_at`（法术场地图伤害）做扩展/拾取阻挡与 deep 压制，而 web 的 `hasBlockDamage` 读的是 checkBlock 的 damage/ambush/repulse/chase 四图（**不含法术场**，MT47 实测 damage=[]）。已删 BFS 内的法术场阻挡与 deep 压制；开门踏格清火（`_apply_door_live` 调 `_check_fire_retreat`）补齐。诊断方法论沉淀：
- **读火格必须用双参 `core.getFgNumber(x,y)` 或原始 fgmap 数组**——三参调用返回错值、`core.status.fgmaps`（显示层）与运行时判定是两回事。
- **live 的 `hero.statistics`**（battle 计数/money 累计）+ **60ms gold-trace 轮询**（verifier `--debug-door` 内置）+ **块存在性轮询**三者组合，可把任何一笔金币入账钉到具体步窗口与具体资源块（本轮 +50G 就是这样钉到 x11y6 redBat 的）。
- **回退续跑**：复验一律带 `--checkpoint-start 101 --checkpoint-every 50`，失败后 `--load-slot <N> --start-step <M>` 从最近检查点续跑（9 分钟复现 → 20 秒）；strict 的 saveData 禁令仅 strict-human-input 生效。
- **walk 重生成后从旧 checkpoint 续跑前，先做「新 walk vs 已验 live 日志」等价性校验**（2026-09-05 40145）：walk 因模型修复重生成后，旧 checkpoint 的实机状态属于旧 walk 的步号空间——必须先把新 walk 每步 after 与失败前那轮 verify 日志的 live 状态逐条 diff（值字段 hp/atk/def/yk/bk/rk/gold 0 差、变更点之前的步号未移位），0 差才可从旧 checkpoint `--start-step <M+1>` 续跑；否则从 slot 1 重跑。判读注意：日志里 coalesced 组（`-> coalesced through step M`）的 after 行属于组内最后一步，但值字段在组内不变，按组首步号 diff 值字段仍成立。本轮 819 步头全 diff 0 差后从 save117@901 续跑，省掉前 900 步重跑。

### 每步时间戳

step 日志带墙钟 `[YYYY-MM-DD HH:MM:SS][NNN] ...`（`runOneStep` + record-only 两处），便于从日志算相邻步间隔定位慢步/空等。诊断慢步：看相邻 step 时间戳之差 = 上一步耗时；若 hero 长时间 `lock=false moving=false event=-:-` 又没点击，就是 pre-lock/等待类问题。

### 真正不可压缩的等待

只有游戏强制实时动画：MT10 小偷 `generateMove` 12 格×200ms+fadeIn500≈2.9s、MT20 trigger 3×`move time:1000`=3s、各 `sleep`/`setCurtain`。这些是 `setTimeout`/动画回调，禁用 doAction 下只能等。**auto 拾取/战斗/破墙是远程瞬时的，不算等待**（旧结论"拾取走路不可压缩"已作废）。

### 录像缓冲区 `core.status.route` 保留（下载录像完整性的关键）

`core.status.route` 是 h5mota 的**录像缓冲区**（命令数组，`encodeRoute` 在存档/下载录像时 dump 它），**和 `core.status.automaticRoute`（自动寻路队列）是两个字段**。verifier 的状态校验只读 hero hp/atk/keys/gold，**从不读 `core.status.route`**。

- `clearRuntimeRoute` / `clearStaleMoving` 旧版顺手写了 `core.status.route = []`，把**录像缓冲区**当自动寻路队列清了 -> 每次飞行（`flyTo` 调 `clearRuntimeRoute`）都清空录像，下载到的 `.h5route` 只剩最近一次飞行后的尾巴（如 `FMT20:UM6:9UM5:6RU`），"从头回访录像"因首命令 `fly:MT20` 在新局未访问该层而报"录像文件出错"。
- **已修复**：`clearRuntimeRoute` / `clearStaleMoving` 只保留 `stopAutomaticRoute` + `clearContinueAutomaticRoute`（清 `automaticRoute` 自动寻路队列，正确字段）+ replay 状态清理，**不再清 `core.status.route`**。`stopAutomaticRoute` / `clearContinueAutomaticRoute` 只动 `core.status.automaticRoute`，不碰录像缓冲区，保留它们无负面影响；清 `core.status.route` 是清错字段。
- 为什么要清自动寻路队列：hero 自动寻路途中遇战斗/开门/NPC/商店被事件中断时，游戏把剩余步数存进 `automaticRoute.moveStepBeforeStop`，事件后 `continueAutomaticRoute` 恢复。`flyTo` / `useItem` / 商店接近这类**直接调游戏函数**绕过点击入口（点击新格会自己 `stopAutomaticRoute` 重新寻路），若残余 `moveStepBeforeStop` 还在，换层/用道具后可能恢复指向旧楼层旧坐标的寻路 -> 状态冲突。所以这两清理是给直接函数调用兜底，不是"等寻路走完"。
- 验证：zone12 358 步 0 mismatch（含金币），`core.status.route` 650 命令完整，下载录像可从头回访。

### 已知未解：原生回放偶发"黄门没开、人穿过去、yk 不匹配"（暂忽略）

verifier 跑完下载的 `.h5route` 从头回访时，偶发某黄门（如 x8y11）没开、hero 穿过去、终局 yk 少消耗 1。**flaky**（同一 walk 时好时坏）。根因分析（web 源码确认，本塔 `enableMoveDirectly=true` + `enableRouteFolding=true`，`project/data.js:666-667`）：

- **录像折叠**（`enableRouteFolding=true`）：`checkRouteFolding`（`control.js:2620-2640`）在**录制期间**（非回放）若 hero 回到之前到过的 (x,y,dir)+全数值属性相同的状态，就 `core.status.route = core.status.route.slice(0, one.length)` 截断，删掉两次访问间的命令（可能含开门步）。是否触发随 auto-BFS 时机变化 -> flaky。
- **moveDirectly 瞬移**（`enableMoveDirectly=true`）：`move:x:y` 回放时 `moveDirectly`（`functions.js:1566`）是纯瞬移（`hero.loc.x=x; hero.loc.y=y`），不开门不打怪。`canMoveDirectly` BFS（`maps.js:866`）挡 noPass 门，但若有**不经过该门的备用路径**（挡路怪被 auto 清）就返回 ≥0，hero 瞬移到目标、门没开、yk 没消耗 = "穿过去"。
- **回放合并连续 move**（`control.js:1879-1883`）：回放时连续 `move:` 合并，中间的只 push 进 route 不执行（次要，非 flaky）。

**尝试过的修复（不生效，已回退）**：给 verifier 加 `--no-route-folding` flag 设 `core.flags.enableRouteFolding=false`。验证后**未解决**门跳过问题（关折叠后录像仍 flaky 丢门或门仍被绕过），已从代码回退。若后续重访此问题，方向：可能需关 `enableMoveDirectly` 强制走路开门（但改变移动时序，风险大），或从 converter/walk 侧保证开门步是显式走步而非 `move:x:y` 瞬移。

**当前结论**：verifier JSON walk（每步 before/after 实机对照，0 mismatch 含金币）是规范复现证据；下载的 `.h5route` 原生回访只作辅助，其 flaky 门跳过不阻塞验证结论。

## 结束报告

实机跑完后，用中文报告：

- 最终楼层和坐标；
- HP/攻/防/黄钥匙/蓝钥匙/红钥匙/金币；
- 大阶段分数：`dmg`、开门数、`final-score` 或当前综合分、关键评分组成。1区看 10F Boss 后，2区看 20F Boss 后，3区看 40F Boss 后，4区按地震卷轴、盾、双倍金币/49F、魔龙雪花、最终真魔王等策略节点拆分；
- 详细步骤只列动作和变化属性；完整状态用 `快照@步数` 行插入详细步骤中，普通间隔约 50 步以上，关键道具/Boss/大事件后可立即插入，不要每步重复前后状态；
- 保存位；
- 是否有本地模型和网页不同的修正；
- 哪些存档位是干净 checkpoint，哪些应忽略。

## 三区实机复现笔记

- 当前 31F-50F 网页复现用 `scripts/live/live_zone3_mouse_replayer_cdp.js`。它连接 CDP 端口 9222,用游戏的地图点击 handler（`_sys_ondown` / `_sys_onup`）做目标点击。
- 当前已验证的 save37/post-40 生命榜单路线:`best/post40_hp_leaderboard_walk.json`,最终 `HP=22264 ATK=418 DEF=517 YK=4 BK=0 RK=0 G=1235`,最终红魔王战后存到 42 号槽。把它当作 save37 的延续,不是从 1F 连续的完整证明。
- 不要用 `core.moveHero`、`core.setHeroLoc`、`core.changeFloor`、`core.doAction` 强推路线进度。即使是空的 `waitAsync` 状态也要靠真实 canvas/地图点击推进;若点击和等待都无法推进事件,停下报告。
- 地图点击可能停在 NPC、门、假墙、怪、楼梯目标的相邻格。若第一次点击只是走到相邻格、目标仍可交互/noPass,再点一次同一目标,然后再判断是否不匹配。
- 已经与 noPass 战斗目标相邻时,可能需要真实方向输入;50F 最终红魔王 x6y5 从 x6y6 必须用键盘/游戏键事件触发,不能用强制移动。
- **50F redKing keyboard-trigger 前需 hero 已相邻**：verifier 检查 `|dx|+|dy|==1`（hero 须在
  (5,5)/(6,6)/(6,4)/(7,5)）。walk 换层落点（MT50 x6y7）≠ redKing 事件 (x6y5) 相邻要求；
  若缺走位步会 throw "must be adjacent"。须在 walk 加显式 `到达` (5,5)（recording 是
  move:5:5 后 right）。
- **MT12 (11,1) 实为 specialTrader(web id=124)，非本地 map 的 fakeWall2(tile 3)**：若 walk 在
  MT12 有 `破墙 fakeWall2` 步且 web 卡 choices 对话框，检查是否 converter 把录像 `right`
  转向误导出破墙——hero 实际只到 (10,1) 就飞走，不该破/上 (11,1)。
- 有些路线步骤是逻辑目标,不是英雄最终坐标。只有当属性匹配且目标副作用在实机地图上可见(比如目标怪/道具/门消失)时才接受。
- 点击门、假墙、NPC、怪、楼梯目标时,小幅坐标差异是正常的(只要副作用可见,如门开了、假墙消失)。
- 重大地图/事件生成差异必须停掉复现。例如:隐藏路径缺失、奖励道具(如 34F 红钥匙)没生成、预期楼梯/事件没出现、某层事件似乎被跳过。不要因一次失败就断定本地地图数据错了;重载最近检查点、重试,仍失败再报告。
- `TALK` 步骤不一定暴露 choices。已禁用/已完成的对话可能 no-op;活跃文本对话可能 `lock=true` 但无 choices。让后续 `EVENT` 步骤用 canvas 点击推进文本。
- 39F 拾取道具是 `centerFly3`,但可用的工具 id 是 `centerFly`(计数 3)。40F 中心对称跳跃用 `core.useItem("centerFly")`。
- 48F 镐子道具在工具栏隐藏,其道具效果自动破坏相邻可破墙,然后等异步开门动画结束。用完 `pickaxe` 后不要点击目标墙;等实机状态回到 idle,核对预期墙消失了即可。
- 40F 主动清掉 12 守卫后的 Boss 事件,仍从 `x6y1` 与 captain 战斗;当前 DEF 下是 0 伤害,但实机会给 `+100G`。
- 纯 TE post-40 路线,在右上红法师后核对 MT41 连通性。若 `MT41 x8y7 slimelord` 仍在,即使目标房间本地看似可达,实机里 `flyTo`/楼层转移也可能失败。
- MT43 圣盾相关事件,保留 2026 触发规则:打开右上魔法守卫左边的黄门、在该守卫仍存在时走到其左边,可能很关键;大黄钥匙路线不等价,除非实机复现证明。
- 最终红魔王战可能在 HP/金币已匹配、目标块已消失后,仍留下 `lock=true event=action:text`。验证器可接受为路线完成;只在检查通关后确认框时才推进文本。
- `confirmBox` 支持键盘选择。先读 `core.status.event.selection`（`0`=左/是,`1`=右/否）;`ArrowLeft`/`ArrowRight` 切换选项,`Space`/`Enter`/`C` 确认。本项目用 `agent-browser connect 9222` 附加后,裸 `agent-browser press ArrowLeft` / `press ArrowRight` / `press Space`（**不要用 `--cdp 9222` flag**）。最终通关确认框要先设/核对 `selection=1` 再按 `Space` 选右/否,回到起始页。
- 实机小错时,优先用游戏回退键(`a`)退一两步,或重载 100+ 检查点存档槽。不要依赖脚本侧的 window/global 备份。
- 若某步留下半应用状态(比如道具被消耗或地图块变了,但 `event.id` 仍卡在 `action:waitAsync` 之类)且回退恢复不了,就停。刷新浏览器页、重载最近干净存档/检查点后再试。不要从那个脏实机状态继续复现。
- 2区 2ATK1DEF 的 2026-07-10 验证经验：可以从 `save57` 的 10F boss 后状态用 `--start-step 132` 验证 2区 JSON；若中途修复了局部步（例如 19F 十字架前 fakeWall 不能被 auto_sweep 折叠），优先重载最近的 100+ 干净检查点（本次为 save112）并从对应 step 续跑 tail，验证通过后清掉 Boss 文本并另存新终点槽（本次为 save113）。
- 20F boss 后到 31F 桥接的 29F 小偷事件：不要把 MT23 撞字/whiteWall2 文本触发作为前置条件。实机从 MT29 入口到 `x6y2` 小偷处连续交互两次即可打开 `MT29 x6y3` 暗道；随后直接点 `x6y11` 上楼。2026-07-10 已从 `save113` 验证到 `MT31 x6y2 HP=1211 ATK=76 DEF=72 YK=4 BK=0 RK=0 G=1138`，验证输出见 `outputs/results/zone2_2atk1def_current_20_to31_bridge_verified.json`。
