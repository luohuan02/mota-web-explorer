# mota-web-explorer

这是一个用于搜索、审计和实机验证《魔塔 50 层》h5mota 版本路线的工作区。

游戏地址：https://h5mota.com/games/51/

官网榜单/论坛入口：https://h5mota.com/tower/?name=51

攻略基线来源：https://www.taptap.cn/moment/15225056477054087

后续项目报告、walk、阶段说明和人工阅读文档默认使用中文；脚本名、JSON 字段名、坐标和资源 id 可保留英文，方便程序处理。

## Skill 模式

项目已经按功能固化为本地 skills，后续协作时优先按任务选择对应 skill，再读取其中的最小必要说明。

| skill | 适用场景 |
|---|---|
| `skills/mota-route-search/SKILL.md` | 本地寻路、最优路线搜索、攻略线和最优线策略解释 |
| `skills/mota-route-audit/SKILL.md` | 路线重放、路径合法性审计、中文 walk 和剩余资源差异报告 |
| `skills/mota-live-browser/SKILL.md` | 读取网页状态、存档/读档、小范围网页状态探查 |
| `skills/mota-live-verify/SKILL.md` | 把本地 walk 跑进真实网页游戏并逐步校验 |

推荐工作流：

1. 用 `mota-route-search` 选择搜索脚本和目标。
2. 用 `mota-route-audit` 生成/审计 walk 和剩余资源差异。
3. 用 `mota-live-verify` 在网页游戏中复现路线。
4. 若只是查状态或存档，用 `mota-live-browser`。

## 当前探索目标

当前阶段主目标是 `50层魔塔（H5）-2026全新复刻版` 的 `纯净版-TE（生命/最高血量）` 最优。

外部参考：
- 官网榜单/评论：https://h5mota.com/tower/?name=51
- 版本说明：https://h5mota.com/bbs/thread/?tid=1790&p=1
- 2026-06-28 读取到的生命榜单参考：`纯净版-NE=26164`，`纯净版-TE=41477`，`特性版-NE=29848`，`特性版-TE=50675`。

这些榜单值只作为攻略和搜索方向参考；项目内“最优”仍以 `best/` 中可 replay、可审计、必要时可网页实机复现的 walk 为准。

## 当前稳定结果

稳定 artifact 以 `best/` 为准。

完整路线家族入口：

- `best/route_chains.json`：1-4 区攻略线/非攻略线的机器可读 manifest
- `best/route_chains.md`：同一内容的人读版，包含每段起点、终点、artifact 和能否接上

当前可连贯跟踪的两条主线：

```text
guide_chain_to_22264:
zone1.guide_baseline -> zone2.guide_canonical -> save36 bridge
-> zone3.guide_slot36_to40 -> zone4.save37_hp_leaderboard

non_guide_current_best_branch:
zone1.current_best -> zone2.current_best_2atk1def_branch
-> current 2ATK1DEF bridge -> zone3.current_2atk1def_preserve_pickaxe
-> zone4.current_2atk1def_te_hp23076
related sibling: zone2.current_best_canonical
```

当前 non-guide 4 区胜者由共享 `Game` 从槽150生成并完成451步 target-click-only 网页复验：`MT50 HP=23076 ATK=417 DEF=475 YK=5 BK=1 G=906`。路线提前取31F红蓝与32F红蓝宝石，商店序列为防/防/防/攻/生命；同target261逐伤害组审计净省2365纯伤。规范产物见 `best/zone4_2atk1def_te_hp23076_{summary,walk,live_verify,resource_audit,gem_damage_audit,macro_astar,terminal_astar}.*`。

注意：`guide_chain_to_22264` 的 4 区尾段已网页验证并保存到 42 号存档，但 20F->31F 仍是 checkpoint/save 桥接；完整 1F->50F 单条 stitched web replay 还未完成。`slot26` 非攻略分支不能直接套用 save37 的 22264 尾段。

### 生命榜单路线（37 号存档 / 40F 后续）

```text
HP=22264 ATK=418 DEF=517 YK=4 BK=0 RK=0 G=1235
dmg=27134 door=53/10/7
source save=37 verified save=42
```

对应文件：

- `best/post40_hp_leaderboard_summary.json`
- `best/post40_hp_leaderboard_walk.json`
- `best/post40_hp_leaderboard_walk.md`

注意：这是从 37 号存档继续的 40F 后路线，已网页实机复现并保存到 42 号存档；完整关联见 `best/route_chains.md`。

### 1 区到 10F Boss 最优

```text
current best:
HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=305 dmg=2454 door=41/2/1 final-score=1376.5

guide baseline:
HP=25 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=304 dmg=2601 door=40/2/1 final-score=1327.5
```

对应文件：

- `best/current_best_boss_walk.md`
- `best/current_best_boss_summary.json`
- `best/guide_boss_walk.md`

旧 `1482.5` 结果无效，不要作为当前最优引用。它允许了 MT10 特殊动作在 MT9 上楼实际可达之前发生；现在 `scripts/search/post9_resource_group_search.py` 已加入合法性保护。

## 评分模型

- `1YK = 50HP`
- `1BK = 4YK = 200HP`
- `100G = 1YK = 50HP`
- 红血瓶 = `50`
- 蓝血瓶 = `200`
- 红钥匙和宝石默认不计剩余分，除非某个脚本明确采用其他目标
- `final-score` 包括当前 HP/钥匙/金币库存和全图剩余资源组
- 剩余怪物按未来零伤金币收入处理
- 未开的黄门/蓝门仍扣除钥匙价值
- 未使用商人只按未来净资源计入；实际购买会消耗真实金币

商人资源：

- MT7 `x6y1`：`50G -> 5YK`
- MT6 `x8y4`：`50G -> 1BK`

## 当前最优序列

```text
MT7:redGem
MT3:blueGem
MT6:blueGem
MT7:yellowKey
MT1:blueGem
MT8:blueGem
MT3:redGem
MT5:blueGem
MT4:blueKey
MT9:upFloor
MT10:blueGem
MT7:yellowKey
MT10:redGem
MT10:bluePotion
MT6:yellowKey
MT8:redKey
MT1:bluePotion
MT7:bluePotion
MT10:redDoor / boss
```

关键 checkpoint：

```text
after MT7:redGem, MT3:blueGem, MT6:blueGem, MT7 skeleton key pocket:
HP=361 ATK=23 DEF=23 YK=2 BK=1 RK=0 G=93 dmg=915 door=28/0/0
```

## 常用命令

重新生成当前 best artifact：

```powershell
python scripts\build\gen_local_refined_best_walk.py
```

验证当前 MT7 红宝石优先分支：

```powershell
python scripts\search\probe_mt7_red_first_swap_sequence.py --variant user-def-before-key --beam 160 --out-json outputs\results\user_def_before_key_probe_after_mt10_guard.json --out-md outputs\reports\user_def_before_key_probe_after_mt10_guard.md
```

重新生成并复现 37 号存档后续生命榜单路线：

```powershell
python src\solver\game_route.py
node scripts\build\prepend_40f_prefix_walk.js
node scripts\live\live_zone3_mouse_replayer_cdp.js --walk best\post40_hp_leaderboard_walk.json --load-slot 37 --target-click-only
```

二区重放、宏搜索、审计和剩余资源差异：

```powershell
python scripts\baseline\replay_zone2_guide_route.py
python scripts\search\search_zone2_macro_routes.py
python scripts\audit\audit_zone2_path_legality.py
python scripts\audit\report_zone2_remaining_diff.py
```

基础检查：

```powershell
python -m py_compile scripts\search\post9_resource_group_search.py scripts\audit\compare_merchant_resource_paths.py scripts\audit\merchant_finalscore_audit.py scripts\search\probe_mt7_red_first_swap_sequence.py scripts\build\local_order_refine_current_best.py scripts\build\gen_local_refined_best_walk.py scripts\baseline\replay_zone2_guide_route.py scripts\search\search_zone2_macro_routes.py scripts\audit\audit_zone2_path_legality.py scripts\audit\report_zone2_remaining_diff.py
python tests\run_merchant_fullmap_score_test.py
python tests\run_pareto_test.py
python tests\run_floorsearch_test.py
```

## 网页游戏访问

网页自动化使用 `agent-browser` 和本地 `browser-profile/`。

读取或控制已经打开的 h5mota 游戏页时，chrome 必须在真实端口 9222 上外部启动并带 `--user-data-dir=browser-profile`（运行 `scripts/live/launch_h5mota_chrome.ps1`），然后 `agent-browser connect 9222` 并用裸 `agent-browser eval`/`get`。**不要用 `--cdp 9222` flag**（启动 agent-browser 自管 chrome，用 temp profile，browser-profile 存档丢失），**不要用 `--auto-connect`**（粘到错误 tab）。状态读取优先用 `node scripts/live/live_read_state.js`（楼层感知，避免 cmd.exe 破坏 JS `||`/`&&`）。

读取当前英雄状态：

```powershell
node scripts/live/live_read_state.js
```

实机执行路线（1-4 区统一点击 verifier，禁用已归档的 `live_zone2_runner.py`）：

```powershell
node scripts\live\live_zone3_mouse_replayer_cdp.js --walk outputs\results\zone2_2atk1def_game_route.json --load-slot 100 --set-auto battle=true,item=true,wall=true --target-click-only --out-json outputs\results\zone2_live_verify_latest.json
```

注意：

- 不要直接用 `core.changeFloor(...)` 当作合法移动。
- 到过的楼层可用飞行器行为，脚本封装为 `core.flyTo(...)`。
- 相邻触发、暗墙、商店菜单需要状态校验，不要只靠固定延时。
- 31F-50F 实机复现优先用 `scripts/live/live_zone3_mouse_replayer_cdp.js`；详细边界见 `skills/mota-live-verify/SKILL.md` 的「三区实机复现笔记」。
- 最终 50F Boss 相邻触发要走真实方向键/游戏键盘事件入口；不要用 `core.moveHero` 或直接改坐标。
- `browser-profile/` 保存网页存档，本地忽略，不要删除。

## 目录说明

- `best/`：追踪稳定 walk 和 summary JSON
- `skills/`：按功能拆分的项目工作流说明
- `scripts/`：搜索、重放、审计、报告和网页辅助脚本
- `src/solver/`：共享地图和搜索实现
- `src/legacy/`：旧版楼层、Pareto、浏览器等辅助代码
- `data/`、`config/`：地图和配置数据
- `tests/`：轻量回归检查
- `outputs/`：忽略的临时报告、搜索结果和 walk
- `browser-profile/`：忽略的本地浏览器 profile 和 h5mota 存档

不要删除 `src/solver/`、`src/legacy/`、`data/`、`browser-profile/` 或 `config/`。
