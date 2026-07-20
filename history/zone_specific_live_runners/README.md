# 旧 zone 专用 live runner（键盘逐步走）

这里保存 2026-07-11 前用于 2 区 / 3 区 guide 路线的键盘式 live runner，仅供
追溯旧产物和比较历史行为，**不是可运行的实机验证入口**。

归档文件：

- `live_zone2_runner.py`：2 区 live runner。
- `live_zone3_guide_runner.py`：3 区 guide 路线 live runner，`import` 前者的
  `Browser` / `state_text`，两者耦合，一并归档。

## 归档原因（为什么是错误代码）

1. **方向键逐步走**：移动靠 `press("ArrowRight"/"ArrowDown"/...)` 一步一格走到
   目标（`live_zone2_runner.py` 注释 `_sys_ondown 远距不寻路, press 逐步寻路`）。
   这导致实机里"一步一步地走"、在楼梯/楼层附近上下徘徊，既慢又容易在中途触发
   相邻事件格卡住。
2. **用了被 skill 明文禁止的 `core.doAction()`** 强推路线进度
   （`skills/mota-live-verify/SKILL.md`：不要用 `core.moveHero` /
   `core.setHeroLoc` / `core.changeFloor` / `core.doAction` 强推）。
3. **zone 专用、非统一**：2 区 / 3 区各写一个 runner，route 格式各异
   （2 区读 `zone2_guide_route_replay.json` 楼梯合并格式，不是通用 Game 类输出），
   和通用 `Game` 类、统一点击 verifier 各自演化，容易让路线/auto/事件规则分叉。
4. CLAUDE.md 已要求"验证器要用真实地图点击 handler，不要强制移动英雄"；这两个
   runner 用键盘逐步走 + `core.doAction`，直接违反。

## 正确替代（统一通用策略）

1-4 区、4-50 层全部使用**统一 CDP 点击 verifier** + **通用 `Game` 类 walk**：

```powershell
node scripts/live/live_zone3_mouse_replayer_cdp.js `
  --walk outputs/results/zoneN_..._game_route.json `
  --load-slot <100+ slot> `
  --start-step <1-based> `
  --set-auto battle=true,item=true,wall=true `
  --target-click-only `
  --out-json outputs/results/zoneN_live_verify_latest.json
```

- `live_zone3_mouse_replayer_cdp.js` 用游戏地图点击 handler
  （`_sys_ondown` / `_sys_onup`）做目标点击，由游戏自身寻路一次到位，不逐步走、
  不 `core.doAction`、不 `core.moveHero`。
- walk JSON 由通用 `Game` 类
  （`scripts/search/search_post40_guide_route.py`，含 `auto_sweep`、
  `strict_live_model`）生成，`before/after` 直接对照实机状态。
- 3 区起 auto 血瓶按需 `item="nopotion"`（4 区半血陷阱），见 CLAUDE.md。

## 禁止

- 禁止从这里复制 `Browser` / `press` / `core.doAction` 用法回活跃 `scripts/live/`。
- 禁止再用方向键逐步走的方式做实机回放。
- 若统一 verifier 与实机不一致，应先补通用 `Game` 模型 / 事件 / auto 规则和回归
  测试，再重新搜索和生成产物，不要把这两个旧 runner 拉回来打补丁。
