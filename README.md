# mota-web-explorer

这是一个用于搜索、审计和实机验证《魔塔 50 层》h5mota 版本路线的工作区。

游戏地址：https://h5mota.com/games/51/

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

## 当前稳定结果

稳定 artifact 以 `best/` 为准。

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

旧 `1482.5` 结果无效，不要作为当前最优引用。它允许了 MT10 特殊动作在 MT9 上楼实际可达之前发生；现在 `scripts/post9_resource_group_search.py` 已加入合法性保护。

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
python scripts\gen_local_refined_best_walk.py
```

验证当前 MT7 红宝石优先分支：

```powershell
python scripts\probe_mt7_red_first_swap_sequence.py --variant user-def-before-key --beam 160 --out-json outputs\results\user_def_before_key_probe_after_mt10_guard.json --out-md outputs\reports\user_def_before_key_probe_after_mt10_guard.md
```

二区重放、宏搜索、审计和剩余资源差异：

```powershell
python scripts\replay_zone2_guide_route.py
python scripts\search_zone2_macro_routes.py
python scripts\audit_zone2_path_legality.py
python scripts\report_zone2_remaining_diff.py
```

基础检查：

```powershell
python -m py_compile scripts\post9_resource_group_search.py scripts\compare_merchant_resource_paths.py scripts\merchant_finalscore_audit.py scripts\probe_mt7_red_first_swap_sequence.py scripts\local_order_refine_current_best.py scripts\gen_local_refined_best_walk.py scripts\replay_zone2_guide_route.py scripts\search_zone2_macro_routes.py scripts\audit_zone2_path_legality.py scripts\report_zone2_remaining_diff.py scripts\live_zone2_runner.py
python tests\run_merchant_fullmap_score_test.py
python tests\run_pareto_test.py
python tests\run_floorsearch_test.py
```

## 网页游戏访问

网页自动化使用 `agent-browser` 和本地 `browser-profile/`。

读取或控制已经打开的 h5mota 游戏页时，必须直连当前 Chrome 的 CDP 端口：使用 `--cdp 9222`，不要用 `--auto-connect`。`--auto-connect` 可能连到 agent-browser 自己启动的空白页，而不是实际游戏页面。

读取当前英雄状态：

```powershell
agent-browser.cmd --cdp 9222 eval "(() => { const h = core.status.hero, loc = h.loc, t = h.items.tools; return { floor: core.status.floorId, x: loc.x, y: loc.y, hp: h.hp, atk: h.atk, def: h.def, yk: t.yellowKey || 0, bk: t.blueKey || 0, rk: t.redKey || 0, gold: h.money || 0 }; })()"
```

实机执行二区路线：

```powershell
python scripts\live_zone2_runner.py --load-slot 101 --checkpoint-slot 102
```

注意：

- 不要直接用 `core.changeFloor(...)` 当作合法移动。
- 到过的楼层可用飞行器行为，脚本封装为 `core.flyTo(...)`。
- 相邻触发、暗墙、商店菜单需要状态校验，不要只靠固定延时。
- 31F-40F 实机复现优先用 `scripts/live_zone3_mouse_replayer_cdp.js`；详细边界见 `skills/mota-live-verify/SKILL.md` 的 Zone-3 Live Replay Notes。
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
