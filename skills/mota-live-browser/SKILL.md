---
name: mota-live-browser
description: Use this skill whenever reading or manipulating the live h5mota browser state, inspecting core.status, saving/loading h5mota slots, using agent-browser, or debugging web-game state mismatches without executing a full route.
---

# 魔塔网页状态操作 Skill

这个 skill 用于连接已经打开的 h5mota 网页、读取状态、保存/读取存档、做小范围状态探查。完整 walk 实机复现请用 `mota-live-verify`。

## 基本原则

- 使用 `agent-browser.cmd --cdp 9222` 连接已经打开的当前游戏页；不要用 `--auto-connect`，它可能连到 agent-browser 自己的空白页。
- 游戏页是 `https://h5mota.com/games/51/`；官网榜单/论坛入口是 `https://h5mota.com/tower/?name=51`。
- 读取状态优先走 `core.status`，不要依赖截图识别。
- 跨区复现或读档前先看 `best/route_chains.md` / `best/route_chains.json`，确认 save36、slot26、save37、slot42 的分支关系。
- 不要直接用 `core.changeFloor(...)` 当作路线移动；飞楼层要使用游戏道具行为或封装脚本中的 `core.flyTo(...)`。
- 保存位从用户指定的起点之后递增，不覆盖用户明确保留的存档。
- 当前 37 号存档后续生命榜单路线已验证到 `HP=22264 ATK=418 DEF=517 YK=4 BK=0 RK=0 G=1235`，最终态保存到 42 号存档；42 号是最终战后文字事件打开的状态。
- 如果状态不一致，先读取当前状态和最近存档，不要假设还在旧路线。

## 读取当前状态

```powershell
agent-browser.cmd --cdp 9222 eval "(function(){
  const h = core.status.hero, loc = h.loc, t = h.items.tools;
  return JSON.stringify({
    floor: core.status.floorId, x: loc.x, y: loc.y,
    hp: h.hp, atk: h.atk, def: h.def,
    yk: t.yellowKey||0, bk: t.blueKey||0, rk: t.redKey||0,
    gold: h.money||0
  });
})()"
```

## 读取地图块

```powershell
agent-browser.cmd --cdp 9222 eval "(function(){
  const fid = core.status.floorId;
  const m = core.status.maps[fid];
  const blocks = m.blocks.map(b => ({x:b.x,y:b.y,id:b.event&&b.event.id}));
  return JSON.stringify({floorId: fid, blocks});
})()"
```

## 保存和读取

优先让 `scripts/live_zone2_runner.py` 管理保存位。手工探查时可以通过 `core.control.saveData(null)` 读取内存存档，通过 `core.utils.setLocalForage('save101', data, cb)` 保存。

注意：

- 存档属于浏览器 profile 的 localStorage/localForage，不在 git 中。
- `browser-profile/` 是本项目本地资料，不要删除。
- 只在用户同意或明确指定时覆盖已有存档位。

## 小范围移动

- 相邻一格时，`tryMoveDirectly` 有时不会触发事件或暗墙；用方向键/`core.moveHero(direction)` 更可靠。
- 远距离直达可先试 `core.control.tryMoveDirectly(x, y)`，失败后读取状态判断是否需要相邻触发。
- 商店菜单不要盲按方向键；读取 `core.status.event.ui.choices` 后插入对应 action 更稳定。

## 状态不一致时

1. 读取当前 `floor/x/y/hp/atk/def/key/gold/eventUi/lock`。
2. 检查是否处于对话或商店锁定状态，必要时按 Enter 关闭。
3. 对比最近 route checkpoint。
4. 若刚执行过错误动作，优先用游戏自带回退键或最近保存位恢复；不要依赖脚本写入的 window/global 内存备份。
5. 仍不确定时停止并向用户报告当前状态，不继续猜测。

## Live State Probe Notes

- When debugging a stuck route, include `lockControl`, `heroMoving`, `event.id`, current event type, choices, `core.status.asyncId`, and `core.animateFrame.asyncId` counts in the state dump.
- A page that still answers CDP `eval` is often not fully frozen; it may be stuck in an event such as `action:waitAsync`. Prefer real canvas/map clicks and state reads before refreshing, and refresh/reload only if the game no longer responds.
- For manual probes, avoid `core.moveHero`, `setHeroLoc`, `changeFloor`, or `doAction`; use real map clicks or the verifier helpers so NPC, shop, fake-wall, and stair behavior matches the page.
- `confirmBox` supports keyboard selection. Read `core.status.event.selection` first (`0` = left/yes, `1` = right/no); `ArrowLeft` and `ArrowRight` toggle the selected option, and `Space` / `Enter` / `C` confirm it. With `agent-browser.cmd --cdp 9222`, use `press ArrowLeft`, `press ArrowRight`, and `press Space`. For the final clear prompt, set/verify `selection=1` before pressing `Space` to choose the right/no option and return to the start page.
- Dirty-state recovery: if a probe leaves a half-applied side effect (for example an item is consumed or a wall is removed) while `lockControl` / `event.id` remains stuck and the game's undo key does not restore it, stop the route. Refresh the browser page, reload the last known clean save slot/checkpoint, and retry from there. Do not continue from the half-applied live memory state.
