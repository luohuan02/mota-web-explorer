# 任务16: boss 段全 A* Pareto + 任务17: BK=200HP 排序

## 背景(已验证)

任务13/14/15 + move_adjacent 修复完成:
- talk_trader 补 MT6(50G->1BK)/MT7(50G->5YK)(game_route.py)
- 可达矩阵 trader 源(reachability_matrix.py TRADER_KEY_MAP + _flood_floor 登记)
- _fetch_keys_until 买 trader(trader fallback:transition + _flood_floor 查邻居 + talk_trader)
- move_adjacent strict_click=True 修复(loose path 含门/怪时 go_to strict fail 的 bug)

run_boss_subgoals 线性 sub-goal 自动买 trader 达 27/27(HP=213 > walk 122, dmg=1713 < walk 2454)。
但 sub-goal 3-5(RK/HP/boss)fail:RK=0(需 MT8 yellowGuard 378dmg),HP=213<634(需锁区药水)。

walk 完整 boss 调度:27/27(HP=400) -> MT10 bluePotion(+200) -> MT6 bluePriest(+1YK) -> MT8 yellowGuard x2(378dmg)+bluePotion(+200,RK+1,auto redKey) -> MT1 kill bat + MT7 bluePriest+bluePotion(补 HP 到 756) -> boss(634dmg,HP 756->122)。

## 任务16: 全 A* Pareto(从 gem done,用户选定)

### 改动

1. **run_boss_subgoals** 重写成单 GameAStar(从 start_g 起,goal=boss cleared):
   - 删除线性 sub-goal 1-5 顺序(YK>=4 -> 27/27 -> RK -> HP -> boss)。
   - GameAStar(actions=skeleton_actions, goal=goal, heuristic=heuristic, state_key=_state_key, pareto_metrics=_pareto_metrics(), max_expansions=16000)。
   - 链式衔接选 top_goals[0](Pareto 最优);top_goals 空时返回失败。

2. **skeleton_actions 扩展**(boss 段 _BOSS_PHASE):
   - 加 **buy trader** 动作:遍历 TRADER_KEY_MAP,optional_talk_trader(MT6/MT7)(BK<2 或 YK<4 时,且 gold>=50)。
   - 扩展 **acquire potion**:不限 HP<300,boss 段常试锁区药水(_static_potions + acquire_resource 跨层,经门/怪)。当前 2b 只 HP<300。
   - acquire redKey(MT8 (10,2) 经 yellowGuard)- 已有 1b,确认 RK<1 时加。
   - boss trigger(go_to MT10 (6,5) + SPAWNED_BOSS + clear)- 已有。
   - acquire gem(MT10 blueGem/redGem)- 已有(_static_skeleton)。
   - kill monster(补 YK/gold)- 已有。

3. **heuristic** 扩展(含 RK/HP 缺口):
   - atk/def 缺口(现有 max(0,27-atk)*3 + max(0,27-def)*3)
   - RK 缺:if rk<1: h += 估 redKey 成本(yellowGuard dmg ~378)
   - HP 缺:if atk>=27 and def>=27 and hp<634: h += (634-hp) 估药水成本
   - 上 MT10(现有 max(0,10-fn))

4. **state_key/pareto**: 现有(_state_key: floor+yk/bk/rk+yd/bd/rd+gold//50+ss,Pareto 去 atk/def;_pareto_metrics: dmg/-atk/-def)。

5. **max_expansions**: 16000(--max-expansions 覆盖)。

### 性能策略
- state_key 强去重(去 x/y + hp//20 + gold//50)。
- 动作空间精简(boss 段只相关:gem/key/trader/potion/kill/boss)。
- heuristic 引导(朝 27/27 + RK + HP + boss)。
- Pareto frontier 保留非支配(刷宝石/买trader/补HP 分支不被 dmg-min 剪)。
- 若慢(>10min):加 cheap top-N 截断 + incumbent(walk 路径作 hint)。

### 验证
- 从 gem_done pickle 跑 run_boss_subgoals,确认 boss cleared(_boss_cleared + HP>0)。
- 对比 walk(HP=122 dmg=2454)。
- py_compile + 跑 strict_live_click/zone3_model/project_docs_sync 测试。

## 任务17: BK=200HP 排序

### 改动
- 链式衔接排序(run_gem_subgoals line 751-754, run_segment line 1074)从 `yk+bk+rk` 改成 key 价值:
  `50*yk + 200*bk + 500*rk + gold*0.5`(1YK=50HP, 1BK=4YK=200HP, 1RK>=500HP per official_41477, 100G=50HP)。
- 和 YK=50HP 对齐(CLAUDE.md 分数模型)。

### 验证
- 链式衔接选 key 价值最高 goal(非简单计数),BK 按 200HP 估值。

## 风险
- 全 A* 性能(diag10 boss A* 1.8s/扩展,16000 扩展可能~8h)。需优化动作空间 + heuristic,可能需 incumbent。
- 若 A* 找不到 boss cleared,加 walk 路径 incumbent 引导(或回退保留 27/27 _fetch + A* RK/HP/boss)。
