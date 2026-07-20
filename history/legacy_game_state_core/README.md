# 旧 GameState 核心与测试（pre-Game-class 一代，已归档）

这里保存 2026-07-11 前的初代搜索核心 `src/legacy/` 及其专属测试，仅供追溯，
**不是当前管线的一部分**。

## 归档内容

- `src_legacy/`：原 `src/legacy/` 全部（`game_state.py` GameState、`floor_search.py`
  FloorSearch、`floor_map.py` FloorMap、`pareto.py` ParetoFrontier、`flyback.py`、
  `multi_floor.py`、`browser.py`、`backward.py`、`stepwise.py`、`config.py`）。
- `tests_legacy/`：12 个只测 `src.legacy` 的旧测试
  （`run_pareto_test`、`run_floorsearch_test`、`run_gamestate_test`、`run_multifloor_test`、
  `run_flyback_test`、`run_floormap_test`、`run_browser_test`、`run_backward_test`、
  `run_stepwise_test`、`run_config_test`、`test_pareto`、`debug_floormap`）。

## 归档原因

- 这是 `src/solver/`（gen_walkthrough + full_search，post9/phase1 搜索）之前的更老一代，
  且与当前唯一管线（通用 `Game` 类 `src/solver/game_route.py` + zone 适配 +
  `gen_zone_walk_md.py` + `live_zone3_mouse_replayer_cdp.js`）完全无关。
- 调查确认：`scripts/`、`src/solver/`、当前 zone 路线与当前测试均不 import `src.legacy`，
  仅这 12 个旧测试引用它。归档不影响任何活跃代码。
- 原 CLAUDE.md「保留文件」列出 `src/legacy/` 是防止误删；现按"不相关的归档到 history"
  统一收口，内容保留于此，不删除。

## 正确替代

- 当前核心：`src/solver/`（`game_route.py` Game 类、`gen_walkthrough.py`、`full_search.py`）。
- 当前基线测试：`run_merchant_fullmap_score_test`、`run_zone3_game_model_test`、
  `run_strict_live_click_model_test`、`run_zone_walk_md_test`、`run_project_docs_sync_test`。

## 禁止

- 禁止从这里复制 `GameState`/`FloorSearch`/`ParetoFrontier` 用法回活跃 `src/` 或 `scripts/`。
- 禁止把旧测试拉回 `tests/` 参与基线。
