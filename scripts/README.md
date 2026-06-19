# Scripts Index

脚本保持平铺，是为了继续支持 `python scripts\xxx.py` 直接运行和旧脚本的同目录 import。

## 当前策略链

- `phase1_resource_group_search.py`：4-9 拿盾阶段的资源组排序实验，保留 action search 兼容。
- `continue_delayed_phase1_with_post9_resource.py`：从延后 4-9 最优候选继续跑 9F 后资源组策略。
- `post9_resource_group_search.py`：9F 后资源组评分/选源策略。
- `post9_gem_supply_search.py`：9F 后高层 Dijkstra/A* 多 lane 搜索；27/27 候选使用运行时 top-K 宝石顺序精修、轻量钥匙过滤、前缀缓存和真实楼层重放。
- `gen_delayed_phase1_detailed_walk.py`：把 compact walk 展开成坐标级 detailed walk；支持 `--input` 和 `--output` 指定任意关键线路。
- `compare_delayed_phase1_vs_user_guide.py`：当前最优线路与攻略线路的最终状态、分数、剩余资源差异对比。

## 旧策略/基线

- `phase1_action_search.py`：旧 4-9 action search。
- `post9_action_search.py`：旧 9F 后 action search。
- `fixed_shield_strategy.py`：固定 4-9 拿盾 + 9F 红蓝宝石基准路线重放。
- `replay_user_post9_route.py`：用户攻略线重放。
- `gen_walkthrough_fixed_prefix.py`：固定前缀续搜 walk 生成。
- `gen_natural_best_walk.py`、`gen_key_saving_walks.py`：历史自然/省钥匙路线 walk 生成。

## 分析与对比

- `report_post9_resource_group_pareto_top.py`
- `report_resource_score_top.py`
- `compare_phase1_dmg.py`
- `compare_phase1_door_pareto.py`
- `compare_walk_metrics.py`
- `check_fixed_prefix_in_phase1_pareto.py`
- `analyze_phase1_*.py`
- `inspect_*.py`

## 网页操作

- `download_data.py`
- `extract_maps.py`
- `extract_high_maps_cdp.js`: direct CDP extractor for MT41+ map data; avoids Python/PowerShell capturing `agent-browser.cmd` output.
- `extract_high_maps.py` / `extract_high_maps.ps1`: thin wrappers around `extract_high_maps_cdp.js`.
- `live_zone3_walk_replayer_cdp.js`: direct CDP live replay/checker for `outputs/results/zone3_quick_pass_walk.json`.
- `snapshot_state.py`
- `grab_state.py`
- `read_full_state.py`
- `simple_read.py`
- `close_browser.py`
- `test_browser.py`
- `test_core.py`

网页操作使用 agent-browser 读取或控制已经打开的 h5mota 游戏页时，使用 `--cdp 9222` 直连现有 Chrome DevTools 端口；不要用 `--auto-connect`，它可能连到 agent-browser 自己的空白页。

```powershell
agent-browser.cmd --cdp 9222 eval "(() => ({ floor: core.status.floorId, hero: core.status.hero.loc }))()"
```
## Fixed-prefix JIT supply audit

- `audit_fixed_prefix_user_post9_compressed.py`：逐步验证固定攻略前缀后的攻略路线可以由压缩图表达，最终应为 `HP=25 dmg=2601 door=40/2/1`。
- `post9_gem_supply_search.py --stat-local-refine-jit-supply`：只重排宝石与上楼主干，主干不可达时再动态补钥匙或药水。
- `--stat-extra-key-supply-depth 1`：接近 `27/27` 且黄钥匙紧张时，补给闭包额外多看一层。
