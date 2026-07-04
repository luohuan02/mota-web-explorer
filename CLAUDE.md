# Claude 项目笔记

本文件镜像 `AGENTS.md`，供 Claude 兼容 agent 使用。当项目级路线、分数或工作流假设变化时，两份文件要保持同步。

攻略基线：
https://www.taptap.cn/moment/15225056477054087

游戏地址：https://h5mota.com/games/51/

官方榜单 / 论坛地址：https://h5mota.com/tower/?name=51

## 项目 Skills

修改 route/search/live-browser 代码前，先读 `skills/` 下相关 skill 并按其工作流执行。这些本地 skill 是项目入口，可能覆盖通用浏览器工具的旧习惯：

- `skills/mota-route-search/SKILL.md`：本地路线搜索、Pareto/beam/A* 探查、策略对比。
- `skills/mota-route-audit/SKILL.md`：回放合法性检查、中文 walk 生成、剩余资源审计。
- `skills/mota-live-browser/SKILL.md`：读取或探查已打开的 h5mota 浏览器状态。
- `skills/mota-live-verify/SKILL.md`：在实机浏览器执行生成的 walk 并对比实机状态。

实机访问 h5mota 时，用 `scripts/launch_h5mota_chrome.ps1` 在真实端口 9222 上外部启动 chrome（带 browser-profile），然后 `agent-browser connect 9222` 并用裸 `agent-browser eval`/`get`。**不要用 `--cdp 9222` flag**（它会启动 agent-browser 自管的 chrome，用 TEMP profile，忽略 `--profile`/`--user-data-dir`，导致 browser-profile 存档丢失），**不要用 `--auto-connect`**（会粘到错误的 tab）。见 `skills/mota-live-browser/SKILL.md`「启动与连接」。

## 当前探索目标

当前优化目标：`50层魔塔（H5）-2026全新复刻版` / `纯净版-TE（生命/最高血量）`。

外部参考：

- 官方榜单与评论：https://h5mota.com/tower/?name=51
- 2026 复刻版/版本说明：https://h5mota.com/bbs/thread/?tid=1790&p=1
- 2026-06-28 观察到的榜单值：`纯净版-NE=26164`、`纯净版-TE=41477`、`特性版-NE=29848`、`特性版-TE=50675`。

这些是外部策略参考，不是本地证明。仓库结果只有在具备可复现 walk、回放/审计证据、以及（需要时）实机验证后，才算规范化结果。

## 当前规范化结果

以 `best/` 下跟踪的产物为真相来源。

完整路线族索引：

```text
best/route_chains.json
best/route_chains.md
```

这两个文件记录 1-4 区攻略与非攻略分支、检查点链接，以及哪些部分可以连续回放。当前链路汇总：

```text
guide_chain_to_22264:
zone1.guide_baseline -> zone2.guide_canonical -> save36 bridge
-> zone3.guide_slot36_to40 -> zone4.save37_hp_leaderboard

non_guide_current_best_branch:
zone1.current_best -> zone2.current_best_2atk1def_branch
-> slot26 bridge -> zone3.slot26_clean_boss8def -> zone4.slot26_tail_pending
related sibling: zone2.current_best_canonical
```

save37 的 22264 尾段已通过网页验证，但未经新的 4 区搜索/回放，不得复用到 slot26。

当前 save37 / post-40 的生命榜单延续：

```text
best/post40_hp_leaderboard_summary.json
best/post40_hp_leaderboard_walk.json
best/post40_hp_leaderboard_walk.md

HP=22264 ATK=418 DEF=517 YK=4 BK=0 RK=0 G=1235 dmg=27134 door=53/10/7
source save=37 verified save=42
```

这是从浏览器存档槽 37 起的网页验证延续。当前 1-4 区链接与剩余的完整拼接回放缺口见 `best/route_chains.md`。

Phase-1 / 10F Boss 产物：

```text
best/current_best_boss_walk.md
best/current_best_boss_summary.json

HP=122 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=305 dmg=2454 door=41/2/1 final-score=1376.5
```

同一分数模型下的攻略基线：

```text
HP=25 ATK=27 DEF=27 YK=0 BK=0 RK=0 G=304 dmg=2601 door=40/2/1 final-score=1327.5
```

旧的 `1482.5` 产物无效，因为它们在 MT9 upFloor 实际可达之前就允许了 MT10 特殊动作。特殊动作守卫现在在 `scripts/post9_resource_group_search.py::apply_action`。

## 分数模型

- `1YK = 50HP`
- `1BK = 4YK = 200HP`
- `100G = 1YK = 50HP`
- 红药水 = `50`，蓝药水 = `200`
- 红钥匙和宝石的剩余分数为 `0`，除非脚本显式使用别的目标
- `final-score` = 当前 HP/钥匙/金币存量 + 全图剩余资源组
- 剩余怪物是未来的零伤害金币收入
- 未开的黄/蓝门仍要扣钥匙价值
- 未用商人只按净未来资源计；实际商人动作消耗实际金币

商人资源：

- MT7 `x6y1`：花 `50G` 换 `5YK`
- MT6 `x8y4`：花 `50G` 换 `1BK`
- MT6 `x8y3` 红药水和 MT6 `x8y4` 商人要作为单独资源组，因为商人会消耗金币。

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

关键检查点：

```text
after MT7:redGem, MT3:blueGem, MT6:blueGem, MT7 skeleton key pocket:
HP=361 ATK=23 DEF=23 YK=2 BK=1 RK=0 G=93 dmg=915 door=28/0/0
```

## 搜索约定

- 搜索从 4F 开始；1F-3F 是固定前缀，但它们的剩余资源可以之后收集。
- 阶段目标：剑、盾、9F 红蓝宝石、27/27 属性、8F 红钥匙、10F Boss。
- `dmg` 仍是核心路径成本；HP 是可比候选内的 tie-breaker。
- `yk/bk/rk` 是当前可达钥匙存量。
- `_yd/_bd/_rd` 是累计门消耗。
- 资源组分数用于排序和报告，不能替代安全 Pareto 保留。

## 保留文件

- `README.md`、`AGENTS.md`、`CLAUDE.md`、`.gitignore`
- `best/`
- `config/`、`data/`、`src/`、`scripts/`、`tests/`
- `browser-profile/` 仅本地；存放 h5mota 浏览器存档/profile，被 git 忽略

不要删除 `src/solver/`、`src/legacy/`、`data/`、`browser-profile/`、`config/`。

`outputs/` 被 git 忽略，可能含大量临时报告、检查点和过期实验。

## 常用命令

重新生成跟踪的 best 产物：

```powershell
python scripts\gen_local_refined_best_walk.py
```

当前最优的已验证探查：

```powershell
python scripts\probe_mt7_red_first_swap_sequence.py --variant user-def-before-key --beam 160 --out-json outputs\results\user_def_before_key_probe_after_mt10_guard.json --out-md outputs\reports\user_def_before_key_probe_after_mt10_guard.md
```

重新生成并实机验证 save37 post-40 生命路线：

```powershell
python scripts\search_post40_guide_route.py
node scripts\prepend_40f_prefix_walk.js
node scripts\live_zone3_mouse_replayer_cdp.js --walk best\post40_hp_leaderboard_walk.json --load-slot 37 --target-click-only
```

代码改动后的基线检查：

```powershell
python -m py_compile scripts\post9_resource_group_search.py scripts\compare_merchant_resource_paths.py scripts\merchant_finalscore_audit.py scripts\probe_mt7_red_first_swap_sequence.py scripts\local_order_refine_current_best.py scripts\gen_local_refined_best_walk.py
python tests\run_merchant_fullmap_score_test.py
python tests\run_pareto_test.py
python tests\run_floorsearch_test.py
```

## 浏览器说明

h5mota 浏览器交互用 `agent-browser` skill。

重要：读取或控制已打开的 h5mota 游戏时，chrome 必须在真实端口 9222 上外部启动并带 `--user-data-dir=browser-profile`（运行 `scripts/launch_h5mota_chrome.ps1`），然后 `agent-browser connect 9222` 并用裸 `agent-browser eval`/`get`。**不要用 `--cdp 9222` flag**（启动冲突的自管 chrome，用 temp profile——browser-profile 存档丢失），**不要用 `--auto-connect`**（错误 tab）。状态读取优先用 `node scripts/live_read_state.js`（楼层感知，避免 cmd.exe 破坏 JS `||`/`&&`）。

```powershell
agent-browser eval "(function(){var h=core.status.hero,loc=h.loc,t=h.items.tools;return JSON.stringify({floor:core.status.floorId,x:loc.x,y:loc.y,hp:h.hp,atk:h.atk,def:h.def,yk:t.yellowKey?t.yellowKey:0,bk:t.blueKey?t.blueKey:0,rk:t.redKey?t.redKey:0,gold:h.money?h.money:0})})()"
```

本地浏览器 profile 是 `browser-profile/`；不要删除。

实机路线回放优先用 `scripts/live_zone3_mouse_replayer_cdp.js` 和 `skills/mota-live-verify/SKILL.md` 的笔记。验证器要用真实地图点击 handler，不要强制移动英雄。已知 h5mota 回放边界情况包括：空的 `waitAsync` 事件壳、需要第二次点击的相邻 noPass 目标、副作用后实机坐标不同的逻辑路线目标、以及 39F/40F 中心对称道具（`centerFly3` 拾取，`centerFly` 可用工具）。50F 相邻 Boss 触发要用真实键盘/游戏键事件路径；不要用 `core.moveHero` 或直接坐标编辑。

## 注意
- 如果要运行 python 临时脚本，请去掉换行符执行，或者写 tmp/tmp.py 然后执行 tmp/tmp.py
- 禁止 Read(C:\Users\PEIYAN~1.LIA\AppData\Local\Temp\claude\D--claude-mota-web-explorer\eb734ded-6eeb-4a0f-b9fe-955937a952e
    5\tasks\bv3t0dcvq.output)
- 禁止截图,目前用的纯文本模型,直接看内存状态
