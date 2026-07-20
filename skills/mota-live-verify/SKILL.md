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

## 执行路线（统一点击 verifier，1-4 区 / 4-50 层通用）

**禁止**使用已归档的 `live_zone2_runner.py` / `live_zone3_guide_runner.py`
（方向键逐步走 + `core.doAction`，见 `history/zone_specific_live_runners/`）。
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
- 自动 BFS 不会在开门这一刻立即重新结算；开门后要再移动、战斗、拾取或触发事件一次，门后新增可达资源才会被自动处理。walk 里这类目标应标为“自动处理跳过”，同时用 live 状态核对 HP/钥匙/金币变化。
- 生成实机 walk 时不要照本地逐资源顺序远点一个组内最后目标。应点击真实的自动资源组入口，并把同组资源写进备注。例如 9F 中部资源组从 `MT9 x9y4` 开门后，应点 `MT9 x7y4` 触发自动拾取/清怪，备注 `x5y4 黄钥匙`、`x6y5 红宝石`、`x7y6 红头怪`，再继续点 `x4y5` 黄门。

写 live 脚本时显式设置这些 flag，不要靠菜单焦点；切换后读取 `core.status.hero.flags.__auto__` 确认。不要把自动清理造成的额外拾取/杀怪当成模型误差忽略，必须在 route JSON 或 verifier 容忍逻辑中记录和比对。

动态 auto 只证明后续点击触发时会拾取当前同层可达血瓶，不证明所有楼层已清空。最终真魔王前仍必须对照离线残余审计，核对 49F 事件奖励、各层药瓶/宝石、黄钥匙售卖与生命商店闭环；web 复验逐步核对这些真实点击及资源变化。

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

## 1区 / 10F Boss 实机注意点

- 10F Boss 事件后，清完生成怪并打开 `MT10 x6y3` 后，`MT10 x6y2` 是骷髅队长剧情事件格。必须先真实点击/走到 `MT10 x6y2` 触发并处理事件，再点击 `MT10 x6y1` 打骷髅队长。
- 不要从远处直接点击 `MT10 x6y1`。真实寻路会经过 `x6y2` 并触发事件，容易让 verifier 以为目标是队长战斗，实际却停在剧情事件中。
- `clearMt10BossDyn`（`live_zone3_mouse_replayer_cdp.js` 内）已实现此顺序：阶段1 只清 spawned（x4-8/y4-7，**不含 captain 6,1**），阶段2 等 `x6y3` 事件墙开后先点 `x6y2` 处理骷髅队长剧情文本，再点 `x6y1` 打 captain。不要把 captain 纳入动态清怪循环，否则寻路经过 `x6y2` 会卡在 `lock=true event=action:text`。boss trigger 后若 `x6y5→x6y1` 路径上还存在其它事件格，同样要先点事件位置再点战斗目标，不要远距直点。
- Boss 后生成怪位置以 live 地图为准动态读取；不要只按本地静态地图坐标清怪。

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
