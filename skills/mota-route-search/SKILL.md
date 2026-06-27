---
name: mota-route-search
description: Use this skill whenever working on Magic Tower / h5mota local route search, optimal pathfinding, guide-vs-best exploration, Pareto/beam/A*/resource-group searches, or explaining the current best strategy. It is the project entry point for choosing and running search scripts, especially for 1区/2区路线优化.
---

# 魔塔本地寻路 Skill

这个 skill 用于本地搜索、候选路线扩展、攻略线与最优线对比。它不负责直接操作网页游戏；网页实机执行请改用 `mota-live-verify`。

## 默认语言

报告、walk、阶段名和给用户的结论默认使用中文。保留脚本名、JSON 字段名、坐标和资源 id，便于机器复查。

## 关键事实

- 追踪稳定结果以 `best/` 为准：
  - `best/route_chains.json`
  - `best/route_chains.md`
  - `best/post40_hp_leaderboard_summary.json`
  - `best/post40_hp_leaderboard_walk.json`
  - `best/post40_hp_leaderboard_walk.md`
  - `best/current_best_boss_walk.md`
  - `best/current_best_boss_summary.json`
  - `best/guide_boss_walk.md`
- 当前 37 号存档 / 40F 后续生命榜单路线：
  - `HP=22264 ATK=418 DEF=517 YK=4 BK=0 RK=0 G=1235`
  - `dmg=27134 door=53/10/7`
  - 已网页实机复现，最终态保存到 42 号存档。
  - 1-4 区关联、攻略线/非攻略线分支和剩余 stitched replay 缺口见 `best/route_chains.md`。
- 当前 guide 链：`zone1.guide_baseline -> zone2.guide_canonical -> save36 bridge -> zone3.guide_slot36_to40 -> zone4.save37_hp_leaderboard`。
- 当前 non-guide 分支：`zone1.current_best -> zone2.current_best_2atk1def_branch -> slot26 bridge -> zone3.slot26_clean_boss8def -> zone4.slot26_tail_pending`；`zone2.current_best_canonical` 是同一 10F 起点下的 sibling 对照分支。
- 不要把 save37 的 22264 尾段直接套到 slot26；slot26 的 4区尾段需要单独搜索和实机验证。
- 旧 `1482.5` 结果无效，不要引用为当前最优。
- 10F 后起点有两类：
  - 攻略起点：`guide_after_mt10_boss_supply`
  - 当前最优起点：`best_after_mt10_boss_supply`
- 二区当前脚本不是完整逐格全局搜索，而是“攻略宏顺序 + 关键分支枚举 + replay 校验”的宏策略搜索。

## 搜索入口

1. 重新生成当前 1区到 10F Boss 最优 artifact：

```powershell
python scripts\gen_local_refined_best_walk.py
```

2. 验证当前 MT7 红宝石优先分支：

```powershell
python scripts\probe_mt7_red_first_swap_sequence.py --variant user-def-before-key --beam 160 --out-json outputs\results\user_def_before_key_probe_after_mt10_guard.json --out-md outputs\reports\user_def_before_key_probe_after_mt10_guard.md
```

3. 跑二区宏策略搜索：

```powershell
python scripts\replay_zone2_guide_route.py
python scripts\search_zone2_macro_routes.py
python scripts\audit_zone2_path_legality.py
python scripts\report_zone2_remaining_diff.py
```

4. 更完整枚举二区宏分支时使用：

```powershell
python scripts\search_zone2_macro_routes.py --full --suffix full
```

5. 重新生成 37 号存档 / 40F 后续生命榜单路线：

```powershell
python scripts\search_post40_guide_route.py
node scripts\prepend_40f_prefix_walk.js
```

## 生成物整理

- 搜索脚本默认写入 `outputs/`；`outputs/` 是临时区，忽略 git，可在结果提升到 `best/` 后清理。
- 一个结果只有满足这些条件才提升到 `best/`：
  - 有 JSON 或 Markdown walk 可以复现；
  - replay/audit 的 `errors=0`，或 manifest 明确标注为 experimental；
  - 起点/终点状态能接到 `best/route_chains.json` 的某个 segment；
  - 生成命令或来源脚本可追溯。
- 提升后同步：
  - `best/route_chains.json`
  - `best/route_chains.md`
  - `best/README.md`
  - 必要时同步 `README.md` / `AGENTS.md` / `CLAUDE.md`
- 不要把旧搜索缓存、失败候选、截图、日志、`.pkl` beam 缓存提升到 `best/`。
- `outputs/results/*.pkl`、`outputs/logs/`、`outputs/screenshots/`、旧 smoke/seeded 报告通常可删；但如果某个脚本仍依赖 ignored snapshot，例如 `slot26_snapshot.json`、`slot36_snapshot.json`、`guide40_current_snapshot.json`，清理前要确认能重新导出或已有 tracked 替代。

## 当前最优搜索方案说明

当前项目同时有两层搜索：

- 1区到 10F Boss：更接近通用策略搜索。脚本会用资源组、阶段目标、Pareto 保留、局部顺序精修、Dijkstra/A* 与 beam/probe 组合搜索。
- 10F Boss 后到 20F Boss：目前是受约束的宏策略搜索。它以用户攻略大顺序作为合法骨架，枚举 12F 商店购买组合和关键可选资源点，再通过 `replay_zone2_guide_route.py` 重放计算状态、伤害、开门和剩余资源。

因此，回答“现在是不是通用策略搜索”时要说明：1区部分较通用，二区部分还不是完整通用逐格搜索；二区的优势是稳定、快、方便实机复现，风险是会漏掉攻略骨架外的全新路线。

## 判断路线优劣

使用项目约定评分：

- `1YK = 50HP`
- `1BK = 200HP`
- `100G = 50HP`
- 红血瓶 `50`，蓝血瓶 `200`
- 红钥匙和宝石默认不计剩余分，除非脚本另有目标
- `stock` 可包含保留圣水的下界价值

比较时同时看：

- 最终 HP/攻/防/钥匙/金币
- 总伤害 `dmg`
- 开门数 `door=黄/蓝/红`
- 剩余资源差异
- 是否可被路径审计和网页实机验证复现

## 风险点

- 不要把资源评分当作 Pareto 保留的替代条件，除非脚本明确证明安全。
- 不要手写“特殊通道”绕过真实楼层可达性；需要说明为什么可以在真实游戏中重放。
- 二区报告里如果出现剩余顺路资源，例如 `MT1 x1y3 红血瓶`，优先检查是不是宏路线漏了真实移动成本或漏了顺手补给。
