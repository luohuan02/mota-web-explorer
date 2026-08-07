# 脚本索引

脚本按功能分到 5 个子文件夹(search/audit/build/live/baseline),`scripts` 是包,每个子文件夹是子包。

运行方式:`python scripts/<子包>/xxx.py`(脚本开头会自处理 sys.path,把项目根加到 path,使 `from scripts.<子包> import` 生效)。跨脚本 import 用 `from scripts.<子包> import xxx`,不要用裸 `import xxx`。

## search/ — 搜索/寻路

- `phase1_action_search.py`:旧 4-9 action search,被 post9_gem_supply_search import
- `post9_action_search.py`:旧 9F 后 action search
- `post9_resource_group_search.py`:9F 后资源组评分/选源策略
- `post9_gem_supply_search.py`:9F 后 Dijkstra/A* 多 lane 搜索(orchestrator)
- `post9_merchant_seed_search.py`:商人种子搜索
- `post9_atomic_resource_dijkstra.py`:atomic 资源 Dijkstra
- `post9_auto_resource_group_pareto.py`:auto 资源组 Pareto
- `post9_compressed_resource_dijkstra.py`:compressed 资源 Dijkstra
- （`search_post40_guide_route.py` 已移到 `src/solver/game_route.py`：通用 Game 类核心 `auto_sweep`/`strict_live_model` + save37/post-40 路线搜索）
- `search_zone2_macro_routes.py`:2 区宏搜索
- `search_zone2_open_compare.py`:2 区更宽本地比较
- `search_zone3_slot26_explore.py`:slot26 搜索底座
- `search_zone3_slot26_guided.py`:slot26 guided 搜索
- `search_zone3_slot26_seeded.py`:slot26 seeded 搜索
- `search_zone3_slot26_post40_seeded.py`:slot26 post-40 搜索
- `probe_mt7_red_first_swap_sequence.py`:MT7 红宝石优先探针
- `probe_zone3_slot26_sword_macro.py`:slot26 剑宏策略探针
- `probe_zone3_slot26_macro_variants.py`:slot26 宏策略探针
- `run_corrected_phase1_best_boss_until_deadline.py`:修正 phase1 best boss
- `continue_delayed_phase1_with_post9_resource.py`:延后 phase1 + post9 资源
- `search/zone3_event_actions.py`：通用 `Game` 搜索使用的 3 区明确事件动作。

## audit/ — 审计/对比/报告

- `compare_merchant_resource_paths.py`:商人资源路径对比
- `merchant_finalscore_audit.py`:商人 final-score 审计
- `compare_post9_order_variants.py`:post9 顺序变体对比
- `compare_mt6_key_variant.py`:MT6 钥匙变体对比
- `compare_delayed_phase1_vs_user_guide.py`:delayed phase1 vs 攻略对比
- `audit_zone2_path_legality.py`:2 区路径合法性审计
- `report_zone2_remaining_diff.py`:2 区剩余资源差异
- `report_zone3_remaining_diff.py`:3 区剩余资源差异
- `report_zone3_slot26_clean_walk.py`:slot26 clean walk 报告
- `report_post9_atomic_resource_graph.py`:post9 atomic 资源图
- `report_post9_compressed_resource_topology.py`:post9 compressed 拓扑
- `report_resource_group_floor_compact.py`:资源组逐层可视化
- `floor_final_score.py`:final-score 计算核心模块

## build/ — walk 生成/拼接/refine

- `gen_local_refined_best_walk.py`:生成跟踪 best artifact
- `gen_best_current_boss_walk.py`:旧 phase1 boss walk 生成（不含 auto_sweep，金币标注过期；仍被 `gen_local_refined_best_walk.py` 引用，zone1 walk 已改用 Game 类 + `gen_zone_walk_md.py`）
- `gen_delayed_phase1_detailed_walk.py`:compact walk 展开成 detailed（post9 搜索/审计依赖）
- `local_order_refine_current_best.py`:本地顺序精修
- `build_live_resource_group_cache.py`:资源组缓存
- （`build_zone2_live_expected_walk.py` pre-Game-class 已于 2026-08-08 pre-cleanup 删除，git tag `pre-cleanup-2026-08-08` 可恢复）
- `prepend_40f_prefix_walk.js`:40F 前缀拼接
- `search/zone3_game_route.py`：通用 `Game` 的 3 区事件适配（Zone3Game 子类，搜索脚本仍引用；converter 已改用 base `Game`）。
- 旧 `GuideReplay` 已于 2026-08-08 pre-cleanup 删除，不得作为新搜索入口。

## live/ — 实机浏览器/数据提取

- `live_read_state.js`:楼层感知状态读取
- `live_load_save.js`:存档加载(走 `_doSL_load` → `loadData` 路径)
- `live_zone3_mouse_replayer_cdp.js`:统一点击 verifier（1-4 区 / 4-50 层通用，CDP 真实点击 handler，唯一推荐入口）
- （1-4 区统一只用 `live_zone3_mouse_replayer_cdp.js`。旧 `live_zone2_runner.py` / `live_zone3_guide_runner.py` / `live_zone1_auto_replay_cdp.js` / `live_zone3_walk_replayer_cdp.js` / `live_click_route_executor.py` 均因 `core.doAction`/`setHeroLoc`/`moveTo`/方向键逐步走强推已禁用，2026-08-08 pre-cleanup 删除，git tag `pre-cleanup-2026-08-08` 可恢复）
- `launch_h5mota_chrome.ps1`:chrome 启动器
- `import_save_slot_cdp.js`:存档导入
- `export_save_slot_cdp.js`:存档导出
- `export_current_cdp.js`:当前状态导出
- `extract_maps.py`:地图提取
- `extract_high_maps_cdp.js`:MT41+ CDP 提取器
- `extract_high_maps.py` / `extract_high_maps.ps1`:薄封装

## baseline/ — 攻略基线/旧策略

- `fixed_shield_strategy.py`:固定 4-9 拿盾基线
- `replay_user_post9_route.py`:用户攻略线重放
- `replay_zone2_guide_route.py`:2 区攻略回放
- `zone2_resource_groups.py`:2 区资源组评分

## 浏览器连接

chrome 必须在真实端口 9222 上外部启动并带 `--user-data-dir=browser-profile`,然后 `agent-browser connect 9222` 并用裸 `agent-browser eval`/`get`;**不要用 `--cdp 9222` flag**,**不要用 `--auto-connect`**。

```powershell
agent-browser connect 9222
agent-browser eval "(function(){return JSON.stringify({floor:core.status.floorId,x:core.status.hero.loc.x,y:core.status.hero.loc.y})})()"
```
