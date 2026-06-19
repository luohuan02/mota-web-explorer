---
name: mota-live-verify
description: Use this skill whenever executing a generated Magic Tower / h5mota walk in the live browser, validating a route against real game behavior, checkpointing save slots, resuming from a slot, or comparing live state with a local walkthrough.
---

# 魔塔网页实机验证 Skill

这个 skill 用于把本地生成的 walk 真实跑进网页游戏，并在每步后校验状态。只读取网页状态时用 `mota-live-browser`；只做本地审计时用 `mota-route-audit`。

## 前置检查

1. 确认本地 route JSON 已生成：

```powershell
python scripts\replay_zone2_guide_route.py
python scripts\search_zone2_macro_routes.py
```

2. 读取当前网页状态，确认是否与 route checkpoint 匹配：

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

## 执行二区路线

从当前状态自动匹配 checkpoint 并继续：

```powershell
python scripts\live_zone2_runner.py --checkpoint-slot 101
```

从指定存档位恢复后继续：

```powershell
python scripts\live_zone2_runner.py --load-slot 101 --checkpoint-slot 102
```

只跑到某一步用于试探：

```powershell
python scripts\live_zone2_runner.py --load-slot 101 --max-step 30 --checkpoint-slot 102
```

## 合法移动约束

- 不要在实机路线里直接调用 `core.changeFloor(...)`。
- 到过的楼层使用飞行器行为，脚本封装为 `core.flyTo(...)`。
- 未到过的楼层必须通过楼梯或剧情触发进入，例如首次进 15F 要从 14F 真实走到楼梯触发点。
- 20F 吸血鬼事件触发后，周围大蝙蝠会合并为吸血鬼，不能再按旧资源单独击杀。

## 校验策略

脚本每步会：

- 读取 live 状态；
- 和 route JSON 的 after 状态比对；
- 对传送、换层、开门、对话、商店等允许忽略最终坐标但不忽略数值；
- 执行前写游戏存档槽 checkpoint，优先使用用户明确允许的 100+ 槽位；
- 出错后读取最近 checkpoint 重试一两次；仍不一致就停止并报告，不要继续猜测。

如果因为真实地图修正导致路线 JSON 与网页不同，先回到 `mota-route-audit` 修正 replay，再重新生成 route JSON，不要长期依赖 `--yk-offset` 一类补丁。

## 当前二区实机注意点

- `MT1 x4y3` 已在 replay 中显式记录；新路线不应再需要 `--yk-offset -1`。
- `MT1 x1y3 红血瓶` 应在开 `MT1 x4y3` 后顺路吃掉。
- `MT14` 三兽人武士后，真实游戏会生成红钥匙物品；脚本会实际拾取，不当作凭空加 RK。
- 商店选择使用 `event.ui.choices` 的 action 插入，避免菜单焦点偏移。

## 结束报告

实机跑完后，用中文报告：

- 最终楼层和坐标；
- HP/攻/防/黄钥匙/蓝钥匙/红钥匙/金币；
- 保存位；
- 是否有本地模型和网页不同的修正；
- 哪些存档位是干净 checkpoint，哪些应忽略。

## Zone-3 Live Replay Notes

- Use `scripts/live_zone3_mouse_replayer_cdp.js` for the current 31F-40F web replay. It connects to CDP port 9222 and uses the game's map click handlers (`_sys_ondown` / `_sys_onup`) for target clicks.
- Do not use `core.moveHero`, `core.setHeroLoc`, `core.changeFloor`, or `core.doAction` to force route progress. Even empty `waitAsync` states should be advanced by real canvas/map clicks; if clicks and waiting cannot advance the event, stop and report.
- Map clicks can stop adjacent to NPCs, doors, fake walls, enemies, or stair targets. If the first click merely routes to the adjacent tile and the target is still actionable/noPass, click the same target once more before judging mismatch.
- Some route steps are logical targets, not final hero coordinates. Accept them only when stats match and the target side effect is visible in the live map, for example the target enemy/item/door has disappeared.
- Small coordinate differences are normal for clicks on doors, fake walls, NPCs, enemies, and stair targets when the side effect is visible, such as a door opening or a fake wall disappearing.
- Major map/event-generation differences must stop the replay. Examples: a hidden path is missing, a reward item such as the 34F red key was not generated, an expected stair/event did not appear, or a floor event seems skipped. Do not conclude the local map data is wrong from one failed replay; reload the last checkpoint, retry, and report if it still fails.
- `TALK` steps do not always expose choices. A disabled/already-completed dialogue may no-op; an active text dialogue may be `lock=true` without choices. Let the following `EVENT` step advance text with canvas clicks.
- The 39F pickup item is `centerFly3`, but the usable tool id is `centerFly` with count 3. Use `core.useItem("centerFly")` for the 40F center-symmetry jump.
- The 40F boss event after actively clearing the 12 guards still battles the captain from `x6y1`; at current DEF this is 0 damage but live grants `+100G`.
- If a live mistake is small, prefer the game's undo key (`a`) for one or two steps, or reload a 100+ checkpoint save slot. Do not rely on script-side window/global backups.
