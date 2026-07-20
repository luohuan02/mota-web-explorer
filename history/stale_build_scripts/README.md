# 旧 build 脚本（pre-Game-class，无活跃引用）

## build_zone2_live_expected_walk.py

2 区"live 期望 walk"生成器，2026-07-11 前使用，现已无任何活跃脚本 import。

归档原因：

- 产出的"live 期望 walk"是 pre-Game-class 概念，已被通用 `Game` 类
  （`scripts/search/zone2_2atk1def_game_route.py`，`strict_live_model` + `auto_sweep`）
  输出的 `outputs/results/zone2_2atk1def_game_route.json` 取代。
- 不属于唯一管线（离线 Game -> `gen_zone_walk_md.py` -> `live_zone3_mouse_replayer_cdp.js`）。

正确替代：`python scripts/search/zone2_2atk1def_game_route.py` 生成 zone2 walk JSON，
再用 `scripts/build/gen_zone_walk_md.py` 生成人看懂 walk.md。

禁止从这里复制逻辑回活跃 `scripts/build/`。
