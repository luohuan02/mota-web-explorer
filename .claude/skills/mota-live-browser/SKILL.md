---
name: mota-live-browser
description: 用于读取或操作实机 h5mota 浏览器状态、检查 core.status、保存/读取 h5mota 存档槽、使用 agent-browser,或不执行完整路线而调试网页游戏状态不一致。
---

# 魔塔网页状态操作 Skill

这个 skill 用于连接已经打开的 h5mota 网页、读取状态、保存/读取存档、做小范围状态探查。完整 walk 实机复现请用 `mota-live-verify`。

## 基本原则

- 连接模型见下方「启动与连接」：外部启动 chrome 占 9222，再 `agent-browser connect 9222` 附加。**不要用 `--cdp 9222` FLAG**（它会尝试新启动一个 chrome 占 9222，端口冲突报 "Chrome exited early"），**不要用 `--auto-connect`**（会粘到 agent-browser 自己的空白页/tab）。
- 游戏页是 `https://h5mota.com/games/51/`；官网榜单/论坛入口是 `https://h5mota.com/tower/?name=51`。
- 读取状态优先走 `core.status`，不要依赖截图识别。
- 跨区复现或读档前先看 `best/route_chains.md` / `best/route_chains.json`，确认 save36、slot26、save37、slot42 的分支关系。
- 不要直接用 `core.changeFloor(...)` 当作路线移动；飞楼层要使用游戏道具行为或封装脚本中的 `core.flyTo(...)`。
- 保存位从用户指定的起点之后递增，不覆盖用户明确保留的存档。
- 当前 37 号存档后续生命榜单路线已验证到 `HP=22264 ATK=418 DEF=517 YK=4 BK=0 RK=0 G=1235`，最终态保存到 42 号存档；42 号是最终战后文字事件打开的状态。
- 如果状态不一致，先读取当前状态和最近存档，不要假设还在旧路线。

## 启动与连接 (Launch & Connect)

一键启动（杀僵尸 chrome + 外部启动 9222 + connect）：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/live/launch_h5mota_chrome.ps1
```

等价的手工步骤（脚本里就是这么做的）：

1. 若 9222 没在听，先杀掉占着 browser-profile 的 agent-browser 僵尸 chrome（不然新启动会被吸进旧实例、没有调试端口）：
   ```powershell
   Get-CimInstance Win32_Process -Filter "name='chrome.exe'" | Where-Object { $_.CommandLine -match 'browser-profile|agent-browser-chrome|remote-debugging-port' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
   ```
2. 直接拉 chrome，显式指定 `--user-data-dir=browser-profile` 和 `--remote-debugging-port=9222`：
   ```powershell
   powershell -Command "Start-Process 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--remote-debugging-port=9222','--user-data-dir=D:/claude/mota-web-explorer/browser-profile','https://h5mota.com/games/51/'"
   ```
3. 附加 agent-browser（用 `connect` 命令，不是 `--cdp` flag）：
   ```powershell
   agent-browser connect 9222
   ```

**关键坑（踩过）**：

- **不要用 `agent-browser --cdp 9222 --profile <browser-profile> open <url> --headed` 启动。** 它能起 chrome、`--cdp 9222` 也能连，但 agent-browser 会**忽略 `--profile` / `--args --user-data-dir`**，自己建一个临时 profile（`agent-browser-chrome-<uuid>`），browser-profile 里的存档全不见了，`getSave()` 返回 null。必须像上面那样直接拉 chrome.exe 显式指定 `--user-data-dir`。
- **`--cdp 9222` 是 flag（启动/管理用），`connect 9222` 是命令（附加已有 chrome 用）。** 外部启动的 chrome 在真实端口 9222 上，必须用 `connect 9222` 附加；用 `--cdp 9222` flag 会试图新启动一个 chrome 占 9222，端口冲突报 "Chrome exited early"。
- **不要 `--auto-connect`**：会粘到 agent-browser 自己的空白 tab。
- 真实 DevTools 端口就是 9222（外部启动指定）；agent-browser 自管模式下端口是随机的（8067 之类），但本项目不用自管模式。
- 连接后用**裸 `agent-browser eval` / `get`**（不带 `--cdp`），它走已 connect 的会话。

## 加载存档 (Load Save)

加载存档槽 N（从标题页冷启动也行）：

```powershell
node scripts/live/live_load_save.js --slot 1
```

原理：走游戏自带「载入游戏」UI 路径——`core.control._doSL_load(slot, core.control._doSL_load_afterGet)`：
- **版本匹配 + 无风险事件** → `core.loadData(data)` 干净快照载入（**正常路径，推荐**）。`loadData` 收的是存档数据对象，`_doSL_load_afterGet` 内部已用 `getSave` 拿好数据传给它。
- **版本不匹配 / 风险事件**（`hero.flags.__events__` 且 guid 不匹配）→ 弹 `core.myconfirm` 问是否回放录像（**降级路径**）；确认后才走 `core.startGame(...)` 重放 route。本脚本不自动点 myconfirm，会打印提示并退出，需手动处理。

**不要直接用 `getSave + core.startGame` 重放当作加载存档**——那是 `_doSL_load_afterGet` 版本不匹配时的降级回放，route 不完整时会变成新游戏（MT1 hp1000），不是恢复存档。旧版 `live_load_save.js` 用过这个错误路径，已改为 `_doSL_load`。

从标题页冷启动也行：`_doSL_load` 内部会自己 `getSave` 拿数据，不要求先 `core.events.load()` 打开面板。脚本轮询到 `playing=true` 或 ~15s 超时，打印 `{playing, floor, hp, atk, def, x, y}`；若弹 myconfirm 会打印其文本。

## 读取当前状态

优先用 `scripts/live/live_read_state.js`（楼层感知、exe+shell:false 避免 cmd.exe 破坏 JS 操作符）：

```powershell
node scripts/live/live_read_state.js
node scripts/live/live_read_state.js --floor MT8
node scripts/live/live_read_state.js --block MT8,10,2
```

裸 `agent-browser eval` 也能用（前提：已 `connect 9222`），但 **JS 里不要写 `||` / `&&`**（cmd.exe 会当 shell 语法破坏），用 `?:` 和 try/catch 代替：

```powershell
agent-browser eval "(function(){var h=core.status.hero,loc=h.loc,t=h.items.tools;return JSON.stringify({floor:core.status.floorId,x:loc.x,y:loc.y,hp:h.hp,atk:h.atk,def:h.def,yk:t.yellowKey?t.yellowKey:0,bk:t.blueKey?t.blueKey:0,rk:t.redKey?t.redKey:0,gold:h.money?h.money:0})})()"
```

## 读取地图块

```powershell
agent-browser eval "(function(){var fid=core.status.floorId,m=core.status.maps[fid];var blocks=m.blocks.map(function(b){var ev=b.event;return {x:b.x,y:b.y,id:ev?ev.id:null}});return JSON.stringify({floorId:fid,blocks:blocks})})()"
```

## 保存和读取

保存位用 `scripts/live/export_save_slot_cdp.js` 导出 / `import_save_slot_cdp.js` 导入（localforage 键 `51_save<N>`；普通槽可录像，100+ 槽无法录像见 [[save-slot-policy]]），不要再用旧 `scripts/live/live_zone2_runner.py`（2026-08-08 pre-cleanup 删除，git tag `pre-cleanup-2026-08-08` 可恢复）。手工探查时可以通过 `core.control.saveData(null)` 读取内存存档，通过 `core.utils.setLocalForage('save101', data, cb)` 保存。

注意：

- 存档属于浏览器 profile 的 localStorage/localForage，不在 git 中。
- `browser-profile/` 是本项目本地资料，不要删除。
- 只在用户同意或明确指定时覆盖已有存档位。

## 小范围移动

- 相邻一格时，`tryMoveDirectly` 有时不会触发事件或暗墙；改用真实键盘方向事件（如 verifier 的 `dispatchKeyDown`）或再点一次目标，不要用 `core.moveHero(direction)` 强制移动（与统一点击策略矛盾，见 `mota-live-verify/SKILL.md`）。
- 远距离直达可先试 `core.control.tryMoveDirectly(x, y)`，失败后读取状态判断是否需要相邻触发。
- 商店菜单不要盲按方向键；读取 `core.status.event.ui.choices` 后插入对应 action 更稳定。

## 自动操作开关

右下角第一排第三个“特殊设置”进入后，可通过“自动操作”菜单控制额外功能。实机菜单对应的状态存在 `core.status.hero.flags.__auto__`：

- `__auto__.battle = true`：自动清零伤怪。
- `__auto__.item = true`：自动拾取物品，并拾取血瓶。
- `__auto__.item = "nopotion"`：自动拾取物品，但不拾取血瓶；这是“自动拾取物品 on / 拾取血瓶 off”的实际状态。
- `__auto__.wall = true`：自动开暗墙岩浆；拿到雪花后会自动清岩浆。

脚本切换时优先显式设置 flag，不要依赖菜单焦点：

```powershell
agent-browser eval "(function(){if(!core.status.hero.flags.__auto__){core.status.hero.flags.__auto__={battle:false,item:false,wall:false};}core.status.hero.flags.__auto__.battle=true;core.status.hero.flags.__auto__.item=true;core.status.hero.flags.__auto__.wall=true;return JSON.stringify(core.status.hero.flags.__auto__)})()"
```

适用条件：

- `__auto__.wall` 原则上可以全程开启；纯净版仍需遵守真实道具/雪花触发条件，不得用脚本强拆地图。
- `__auto__.battle` 可在 TE 真结局流程或拿到双倍金币后开启；用于减少 0 伤怪点击，不应替代路线审计里的金币/怪物计数。
- 1区/2区缺血阶段可以用 `__auto__.item = true`，让红/蓝血瓶随自动拾取一起吃掉；实测可减少显式补血步骤，例如 4F 开门后再打怪会自动吃门后红血瓶。
- 进入 3区或需要保留血瓶应切到 `__auto__.item = "nopotion"`，用于自动拾取非血瓶物品并保留血瓶时机。
- 3区以后若已切成 `"nopotion"` 保留血瓶，只有在拿到圣盾后，或确认后续不会再经过半血/固定扣血检查时，才切回 `true` 来自动拾取血瓶。
- 开门 sweep 归属（2026-08-31 定稿）：hero 点击开门会踏上刚开的门格，auto sweep 从门格起跑、门后可达资源归入**门步本身**（4F 开 `x8y8` 黄门后门侧资源即可在门步结算）。例外：事件开门/Boss 掉落等非 hero 移动的开门不触发 auto，等下一次 hero 移动再结算。
- 自动功能会减少实机步数/点击数；生成或校验 walk 时要允许这些 side effect，但仍要核对最终 HP、钥匙、金币和地图块变化。

## 状态不一致时

1. 读取当前 `floor/x/y/hp/atk/def/key/gold/eventUi/lock`。
2. 检查是否处于对话或商店锁定状态，必要时按 Enter 关闭。
3. 对比最近 route checkpoint。
4. 若刚执行过错误动作，优先用游戏自带回退键或最近保存位恢复；不要依赖脚本写入的 window/global 内存备份。
5. 仍不确定时停止并向用户报告当前状态，不继续猜测。

## 实机状态探查笔记

- 调试卡住的路线时，状态 dump 里要包含 `lockControl`、`heroMoving`、`event.id`、当前事件类型、choices、`core.status.asyncId`、`core.animateFrame.asyncId` 计数。
- 还能响应 CDP `eval` 的页面通常没真正冻死，可能卡在某个事件里（如 `action:waitAsync`）。优先用真实 canvas/地图点击和状态读取，只有当游戏完全不响应时才刷新/重载。
- 手工探查时避免 `core.moveHero`、`setHeroLoc`、`changeFloor`、`doAction`；用真实地图点击或 verify 脚本的 helper，这样 NPC、商店、假墙、楼梯行为才跟页面一致。
- `confirmBox` 支持键盘选择。先读 `core.status.event.selection`（`0`=左/是，`1`=右/否）；`ArrowLeft`/`ArrowRight` 切换选项，`Space`/`Enter`/`C` 确认。本项目用 `agent-browser connect 9222` 附加后，裸 `agent-browser press ArrowLeft` / `press ArrowRight` / `press Space`（**不要用 `--cdp 9222` flag**）。最终通关确认框要先设/核对 `selection=1` 再按 `Space` 选右/否，回到起始页。
- 脏状态恢复：若探查留下了半应用的副作用（比如道具被消耗或墙被拆）而 `lockControl`/`event.id` 仍卡住、游戏回退键也恢复不了，就停掉这条路线。刷新浏览器页、重载最近已知干净的存档槽/检查点、从那里重试。不要从半应用的实机内存状态继续。
