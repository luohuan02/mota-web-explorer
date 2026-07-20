# 项目笔记

本仓库为攻略基线链接的游戏搜索并审计魔塔 / h5mota 路线：
https://www.taptap.cn/moment/15225056477054087

游戏地址：https://h5mota.com/games/51/

官方榜单 / 论坛地址：https://h5mota.com/tower/?name=51

`AGENTS.md` 是唯一规范源；`CLAUDE.md` 以 Windows hardlink 指向同一文件，避免
两份规则分叉。编辑器若采用临时文件替换保存可能断开 hardlink，提交前必须运行
`python tests/run_project_docs_sync_test.py`。

## 项目 Skills

修改 route/search/live-browser 代码前，先读 `skills/` 下相关 skill 并按其工作流执行。这些本地 skill 是项目入口，可能覆盖通用浏览器工具的旧习惯：

- `skills/mota-route-search/SKILL.md`：本地路线搜索、Pareto/beam/A* 探查、策略对比。
- `skills/mota-route-audit/SKILL.md`：回放合法性检查、中文 walk 生成、剩余资源审计。
- `skills/mota-live-browser/SKILL.md`：读取或探查已打开的 h5mota 浏览器状态。
- `skills/mota-live-verify/SKILL.md`：在实机浏览器执行生成的 walk 并对比实机状态。

实机访问 h5mota 时，用 `scripts/live/launch_h5mota_chrome.ps1` 在真实端口 9222 上外部启动 chrome（带 browser-profile），然后 `agent-browser connect 9222` 并用裸 `agent-browser eval`/`get`。**不要用 `--cdp 9222` flag**（它会启动 agent-browser 自管的 chrome，用 TEMP profile，忽略 `--profile`/`--user-data-dir`，导致 browser-profile 存档丢失），**不要用 `--auto-connect`**（会粘到错误的 tab）。见 `skills/mota-live-browser/SKILL.md`「启动与连接」。

## 当前探索目标

当前优化目标：`50层魔塔（H5）-2026全新复刻版` / `纯净版-TE（生命/最高血量）`。

### 阶段性目标（分阶段推进，不跳过任何阶段）

1. **阶段性最终目的**：完全自主探索更好的纯净版+TE+hp最优，尽可能提高最终 hp 分数。
2. **阶段性目标**：先用 auto + 已有可参考的 walk 快速改成可以通关的路径，然后 web 验证通过，让离线通用构建/测试等逻辑正确，为后面自主探索做基础准备。
3. **分阶段处理**：先 1 区，再 2 区、3 区、4 区，逐区跑通 + web 验证。**不要跳过任何阶段**——跳过就无法到达阶段性最终目的。每区用通用 `Game` 类（`src/solver/game_route.py`，含 `auto_sweep`）替代各自手写 Replay，不打补丁。
4. **auto 配置规则**（结合最终 hp 目的）：
   - 1 区、2 区：`__auto__={battle,item,wall}` 全开。
   - 3 区：关闭自动拾取血瓶（`item="nopotion"`，保留 battle/wall），因为 4 区有半血陷阱（special 16，两个相同魔法守卫之间 HP 减半），血多损失大。
   - 只有拿到神圣盾（免魔法伤害，半血陷阱无效）或确定后续线路不会走半血陷阱时，才开自动血瓶。
   - 其它区按需补充。

## 唯一管线（1-4 区 / 4-50 层通用：Game 类 + 所有点击 + auto + 纯净版-TE + hp 最优）

离线正确 -> 一个脚本生成 walk JSON -> 一个脚本生成人看懂 walk.md -> web 仅复验。
离线对了，web 复验理论上不应有 bug；若 web 出 bug，先修通用 `Game` 模型，不在 walk/坐标打补丁。

1. 离线 Game：`scripts/search/zoneN_game_route.py`（通用 `Game` 类 + zone 适配，`strict_live_model` + `auto_sweep`，auto 全开或 3 区起 `item="nopotion"`）-> `outputs/results/zoneN_game_route.json`（每步 `before/after`）。
2. 人看懂 walk：`scripts/build/gen_zone_walk_md.py --game-route-json <json> --md <md> --zone <N>` -> `best/zoneN_..._walk.md`。
3. web 复验：`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk <json> --load-slot <100+> --target-click-only [--set-auto battle=true,item=...,wall=true]`。

- 唯一 verifier = `scripts/live/live_zone3_mouse_replayer_cdp.js`（CDP 真实点击 handler `_sys_ondown`/`_sys_onup`，游戏自身寻路一次到位）。1-4 区全用它，不要用 zone 专用 runner。
- 禁用 API（导致人无法通过 web 复现）：`core.doAction` / `core.moveHero` / `core.setHeroLoc` / `core.changeFloor`、方向键逐步走。已归档的旧 runner 见 `history/zone_specific_live_runners/`、`history/old_live_runners/`。
- 50F 相邻 Boss / confirmBox 选择可用真实键盘事件（`dispatchKeyDown` / `agent-browser press`），不算强制移动。

## 阶段性存档（stage checkpoints）

每区网页验证全过（0 容忍，含金币）后保存阶段性存档，后续从该存档继续，
不再从 4F 重跑。注册表为 `best/checkpoints/manifest.json`，说明见
`best/checkpoints/README.md`。

- 游戏内存档使用专用槽；下一区网页验证用 `--load-slot <N>` 加载。
- 离线快照用 `scripts/live/export_save_slot_cdp.js` 导出到 `best/checkpoints/`。
- 恢复时用下一阶段的通用 `Game` 路线入口加载 checkpoint。
- checkpoint 只证明已验证前缀；未经新搜索/回放，不得把别的分支尾段直接拼接。

## 根因优先约束

除非已确认是游戏本身的特殊事件或边界规则，否则必须修正通用模型，不得在
旧 Replay、单条 walk 或单个坐标上打补丁。每次修复前都要确认：问题是否来自
通用路径、事件、auto、资源或状态建模；能否用通用逻辑和回归测试覆盖；修复后
是否仍需要重新搜索，而不是继续相信旧产物。

典型反例包括：为 MT33 `sword3` 添加坐标跳过、用硬编码 `buy_order` 代替策略
搜索、让 Markdown deferred-auto 归因跨越楼层。明确楼层事件可以放在区域适配
层，但不得复制通用 `Game` 或绕过其合法性检查。

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
-> current 2ATK1DEF bridge -> zone3.current_2atk1def_preserve_pickaxe
-> zone4.current_2atk1def_te_hp23076
related sibling: zone2.current_best_canonical
```

save37 的 22264 尾段已通过网页验证，但未经新的 4 区搜索/回放，不得复用到 slot26。

当前 non-guide 2ATK1DEF 留镐分支的独立 4 区胜者为：

```text
best/zone4_2atk1def_te_hp23076_summary.json
best/zone4_2atk1def_te_hp23076_walk.json
best/zone4_2atk1def_te_hp23076_walk.md
best/zone4_2atk1def_te_hp23076_live_verify.json

HP=23076 ATK=417 DEF=475 YK=5 BK=1 RK=0 G=906 dmg=14479 door=51/11/7
source slot=150 web-verified 451 Game steps, zero value mismatches
```

该胜者提前取得 31F 红蓝和 32F 红蓝宝石，商店序列为防/防/防/攻/生命。同 target261 的逐伤害组审计显示三组全取比不取少 `2365` 纯伤。宏 A* 的当前一跳邻域已全部解析，但不作为全图最优证明。

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

重要：旧的 `1482.5` 产物无效。它们在 MT9 upFloor 实际可达之前就允许了 MT10 特殊动作。`scripts/search/post9_resource_group_search.py::apply_action` 现在会拒绝特殊动作，除非 `special_action_allowed(...)` 通过。

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

`finalStock` / `netStock` 术语：

- `scripts/search/post9_resource_group_search.py::final_resource_stock`：HP + 当前钥匙存量 + 剩余资源价值，残余拾取忽略怪物伤害。
- `scripts/search/post9_gem_supply_search.py::net_final_stock`：HP + 当前钥匙存量 + 可恢复剩余资源净值，含残余门/怪物成本。

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
- `_yd/_bd/_rd` 是累计门消耗，不能只用当前钥匙存量替代。
- 资源组分数用于排序和报告。除非支配条件明确安全，否则不要用它替代 Pareto 保留。
- 不要添加纯手写的特殊通道，除非文档说明它在真实楼层回放下为何仍然合法。

## 保留文件

- `README.md`、`AGENTS.md`、`CLAUDE.md`、`.gitignore`
- `best/`
- `config/`、`data/`、`src/`、`scripts/`、`tests/`
- `browser-profile/` 仅本地；存放 h5mota 浏览器存档/profile，被 git 忽略

不要删除 `src/solver/`、`data/`、`browser-profile/`、`config/`。（`src/legacy/` 已按"不相关归档"移到 `history/legacy_game_state_core/`，内容保留，不在活跃路径。）

`outputs/` 被 git 忽略，可能含大量临时报告、检查点和过期实验。

## 常用命令

重新生成跟踪的 best 产物：

```powershell
python scripts\build\gen_local_refined_best_walk.py
```

当前最优的已验证探查：

```powershell
python scripts\search\probe_mt7_red_first_swap_sequence.py --variant user-def-before-key --beam 160 --out-json outputs\results\user_def_before_key_probe_after_mt10_guard.json --out-md outputs\reports\user_def_before_key_probe_after_mt10_guard.md
```

重新生成并实机验证 save37 post-40 生命路线：

```powershell
python src\solver\game_route.py
node scripts\build\prepend_40f_prefix_walk.js
node scripts\live\live_zone3_mouse_replayer_cdp.js --walk best\post40_hp_leaderboard_walk.json --load-slot 37 --target-click-only
```

代码改动后的基线检查：

```powershell
python -m py_compile src\solver\game_route.py scripts\search\zone1_game_route.py scripts\search\zone2_2atk1def_game_route.py scripts\search\zone3_game_route.py scripts\search\post9_resource_group_search.py scripts\audit\compare_merchant_resource_paths.py scripts\audit\merchant_finalscore_audit.py scripts\search\probe_mt7_red_first_swap_sequence.py scripts\build\local_order_refine_current_best.py scripts\build\gen_local_refined_best_walk.py scripts\build\gen_zone_walk_md.py
python tests\run_merchant_fullmap_score_test.py
python tests\run_zone3_game_model_test.py
python tests\run_strict_live_click_model_test.py
python tests\run_zone_walk_md_test.py
python tests\run_project_docs_sync_test.py
```

## 浏览器说明

h5mota 浏览器交互用 `agent-browser` skill。

重要：读取或控制已打开的 h5mota 游戏时，chrome 必须在真实端口 9222 上外部启动并带 `--user-data-dir=browser-profile`（运行 `scripts/live/launch_h5mota_chrome.ps1`），然后 `agent-browser connect 9222` 并用裸 `agent-browser eval`/`get`。**不要用 `--cdp 9222` flag**（启动冲突的自管 chrome，用 temp profile——browser-profile 存档丢失），**不要用 `--auto-connect`**（错误 tab）。状态读取优先用 `node scripts/live/live_read_state.js`（楼层感知，避免 cmd.exe 破坏 JS `||`/`&&`）。

```powershell
agent-browser eval "(function(){var h=core.status.hero,loc=h.loc,t=h.items.tools;return JSON.stringify({floor:core.status.floorId,x:loc.x,y:loc.y,hp:h.hp,atk:h.atk,def:h.def,yk:t.yellowKey?t.yellowKey:0,bk:t.blueKey?t.blueKey:0,rk:t.redKey?t.redKey:0,gold:h.money?h.money:0})})()"
```

本地浏览器 profile 是 `browser-profile/`；不要删除。

实机路线回放**统一用** `scripts/live/live_zone3_mouse_replayer_cdp.js`（1-4 区 / 4-50 层通用，CDP 真实点击 handler，游戏自身寻路一次到位），配合通用 `Game` 类生成的 walk JSON，详见 `skills/mota-live-verify/SKILL.md`。**禁用**已归档的 `scripts/live/live_zone2_runner.py` / `live_zone3_guide_runner.py`（方向键逐步走 + `core.doAction`，导致"一步一步走 / 楼层附近上下徘徊"，见 `history/zone_specific_live_runners/`）。验证器要用真实地图点击 handler，不要强制移动英雄。已知 h5mota 回放边界情况包括：空的 `waitAsync` 事件壳、需要第二次点击的相邻 noPass 目标、副作用后实机坐标不同的逻辑路线目标、以及 39F/40F 中心对称道具（`centerFly3` 拾取，`centerFly` 可用工具）。50F 相邻 Boss 触发要用真实键盘/游戏键事件路径；不要用 `core.moveHero` 或直接坐标编辑。

## 注意
- 如果要运行 python 临时脚本，请去掉换行符执行，或者写 tmp/tmp.py 然后执行 tmp/tmp.py
- 禁止 Read(C:\Users\PEIYAN~1.LIA\AppData\Local\Temp\claude\D--claude-mota-web-explorer\eb734ded-6eeb-4a0f-b9fe-955937a952e
    5\tasks\bv3t0dcvq.output)
- 禁止截图,目前用的纯文本模型,直接看内存状态
