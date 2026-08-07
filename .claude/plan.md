# zone3 KILL 线 Game 搜索(替代手建 walk,优化 final-score)

## 背景与动机

当前 zone3 KILL 线 `best/zone3_2atk0def_kill_walk.json` 是 **BUILT(手建/半自动)**,HP=609。前面试图通过手改 walk steps 优化(变体 b-p:改商店 eid、挪 swordsman、删血瓶),变体 p(延后 swordsman)失败--MT38 redDoor 路线断 + 顺序乱。**结论:改了策略必须重新用 Game 搜索,手挪必断**(用户判断)。分析只给搜索指定方向,合法路线由搜索找。

目标:从 slot32(MT20 HP=1215 ATK=76 DEF=66 YK=5 G=1298 times1=2)搜到 MT41,优化 **final-score**(终局 HP 最优)。final-score 把未拾血瓶算剩余资源(1:1),搜索自动只拾必须扛伤的血瓶--HP 自然紧(满足 <100 诉求)+ 终局最优,统一两个目标。

## 设计:复用 GameAStar + zone2 P2 / zone4 资源组模板

新脚本 `scripts/search/zone3_kill_astar.py`,复用:
- 引擎:`src/solver/game_astar.py::GameAStar`(A*/Dijkstra + Pareto + top-K + clone)
- actions 模板:`zone2_resource_group_search.py::skeleton_actions`(怪/商店/楼梯 click + 商店 move_adjacent+buy)
- 资源组压缩:`zone4_resource_group_astar_optimize.py` 的 `hp_potential`/`resource_signature`/`target_action`/`build_pool`
- 候选:`reachability_matrix.compute_matrix`/`_flood_floor`/`cross_floor_reachable`
- 事件:`Zone3Game` 方法(thief_mt29_open_passage / event_mt32_yellow_knight / event_mt40_boss / buy_mt38_yellow_keys 等)
- 评估:`reachability_matrix.comparison_score`(HP+钥匙+剩余资源+gold×zone4溢价-times1)

### 起点
```python
g = Zone3Game(read_json("best/checkpoints/zone2_2atk0def_kill_end_save.json"))
g.strict_live_model = True
g.auto_flags = {"battle": True, "item": "nopotion", "wall": True}
```

### actions(g) -- 扩展 skeleton_actions
1. **资源 click**:当前层 + 飞行可达 visited 层的 怪/骨架/道具/门,`go_to_decomposed` 压缩成一条边(怪按 access_dmg 排序前 N)。
2. **楼梯换层**:`change_by_stair`(四邻可达 + 法师陷阱 guard)。
3. **飞行**:`fly(visited 楼层)`(免费跨层收资源)。
4. **商店**:`move_adjacent + buy_shop`,kind ∈ {atk, def}(**不生成 hp**,用户点1:zone3 不买hp)。
5. **zone3 事件**:调用 Zone3Game 方法(MT29 thief / MT32 yellowKnight / MT40 boss / MT38 buy keys / MT2 oldman / MT35 thief),作为显式 action。
6. **策略剪枝**:
   - swordsman:ATK<150 时不生成击杀动作(延后,用户点3:150攻0伤;`enemy_damage` 确认 ATK≥150 一击秒 turns=1 damage=0)。
   - 不买 hp(见上)。

### goal
`floor == "MT41"` 且 MT40 boss 事件已触发(`flags.get("402")`)。

### edge_cost
`max(0, after.dmg - before.dmg)`(HP 损失,同 zone2 P2)。势能损失备选:`hp_potential` 损失(含剩余血瓶)。

### state_key
`(floor, x, y, atk, def, hp//20, times1, gold, yk, bk, rk, flags_402, blocked_items_count)`(同 zone2 P2 风格 + zone3 flags)。

### heuristic
O(1) 向 MT41 引导:`max(0, 41 - floor_no(cur))` + 缺攻防/缺钥匙的估计。

### 搜索参数
- weight=3, max_expansions=10000(可调), top_k=5(收集多个 goal 候选)
- upper_bound = incumbent dmg(变体 g dmg=7108 或 baseline 8806)
- pareto_metrics 可选:(dmg, -atk, -def, -yk, -gold) 多目标保留

### 评估/排序
goal 候选用 `comparison_score`(含 gold×zone4 溢价,对应"省钱带 zone4"点2)排序,选 final-score 最优。报告 HP/ATK/DEF/keys/gold/dmg/final-score + 血瓶拾取清单 + 剩余资源组。

## 输出
- `outputs/results/zone3_kill_astar_walk.json`(最优 walk,MT20->MT41)
- `outputs/reports/zone3_kill_astar.md`(HP 曲线 + 商店序列 + 血瓶 + final-score 对比 baseline)

## web 验证(0 mismatch 前不进 best/)
```
node scripts/live/live_zone3_mouse_replayer_cdp.js --walk outputs/results/zone3_kill_astar_walk.json --load-slot 32 --target-click-only --set-auto battle=true,item=nopotion,wall=true
```
期望 ok=true,0 数值差异,终点 MT41。验证通过后生成 walk.md(`gen_zone_walk_md.py`)+ 提升 best/(替换当前 HP=609 产物)+ 更新 route_chains/memory。

## 风险与边界
- **搜索空间大**(MT20->MT41 + 飞回 zone1-2 收资源):max_expansions 可能不够,需调参/分段(MT20->MT31 离线前缀 + MT31->MT41 搜索)。
- **zone3 事件触发**:MT34 中心8怪事件、MT40 boss 等需搜索正确触发(Zone3Game 方法);若搜索漏触发,web 验证会发散,按根因修事件建模。
- **Game 寻路 vs 实机**:Game `path_to` 与实机寻路不同(记忆:复现录像会发散),但搜索用 Game 找合法路线,web replayer 用真实点击 handler 寻路,只要 Game 路线合法,web 应复现(值匹配,可能位置差)。
- **incumbent**:变体 g(HP=107,dmg=7108)作 upper_bound 参照;搜索应找到 ≤7108 dmg 或更高 final-score 的路线。
- **不声明全局最优**:max_expansions 达上限只写"该预算未发现提升",不写穷尽(skill 约束)。

## 阶段
1. 写 `scripts/search/zone3_kill_astar.py`(复用模板,适配 zone3 事件/剪枝)。
2. 小预算(max_expansions=2000)试跑,确认 actions/goal/事件触发正确(到 MT41 ok)。
3. 调参扩预算(10000+),找最优 final-score 候选。
4. web 验证最优候选(0 mismatch)。
5. 通过则提升 best/ + walk.md + route_chains + memory;不通过按根因修模型。
