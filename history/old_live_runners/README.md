# 旧 live runner（用 doAction / setHeroLoc / moveTo 强推，已禁用）

这里保存 2026-07-11 前的 zone 专用 live runner，仅供追溯旧产物和比较历史行为，
**不是可运行的实机验证入口**。

归档文件：

- `live_zone1_auto_replay_cdp.js`：1 区（4F-10F boss）live 回放。
- `live_zone3_walk_replayer_cdp.js`：3 区 walk 回放/检查。
- `live_click_route_executor.py`：计划路线点击执行器。

## 归档原因（为什么是错误代码）

全部使用了被 skill / CLAUDE.md 明文禁用的 API 强推路线进度，导致"人无法通过 web
复现"（脚本侧强推出的状态，真实玩家点不出来）：

- `live_click_route_executor.py`：`core.doAction()`（241、299）、`core.setHeroLoc`
  （267、273、274）直接改英雄坐标/方向。
- `live_zone1_auto_replay_cdp.js`：`core.doAction()`（319）推进事件队列。
- `live_zone3_walk_replayer_cdp.js`：`core.doAction()`（130、197）、自写 `moveTo`
  函数（157、313）逐格强移。

`skills/mota-live-verify/SKILL.md` 与 `AGENTS.md` 都要求：验证器用真实地图点击
handler（`_sys_ondown`/`_sys_onup`），不要 `core.doAction`/`core.moveHero`/
`core.setHeroLoc`/`core.changeFloor` 强推。这三个 runner 全部违反。

## 正确替代（唯一 verifier）

1-4 区 / 4-50 层统一用：

```powershell
node scripts/live/live_zone3_mouse_replayer_cdp.js `
  --walk outputs/results/zoneN_..._game_route.json `
  --load-slot <100+ slot> `
  --set-auto battle=true,item=true,wall=true `
  --target-click-only `
  --out-json outputs/results/zoneN_live_verify_latest.json
```

它用游戏地图点击 handler，由游戏自身寻路一次到位，不逐步走、不 `core.doAction`、
不 `core.setHeroLoc`。walk JSON 由通用 `Game` 类（`src/solver/game_route.py`）
+ zone 适配（`scripts/search/zoneN_game_route.py`）离线生成。

## 禁止

- 禁止从这里复制 `core.doAction` / `setHeroLoc` / `moveTo` 用法回活跃 `scripts/live/`。
- 禁止再用这些 runner 做实机回放。
- 若统一 verifier 与实机不一致，应先补通用 `Game` 模型 / 事件 / auto 规则和回归
  测试，再重新生成产物，不要把这些旧 runner 拉回来打补丁。
