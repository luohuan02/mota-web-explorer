# 3 区旧 GuideReplay 实现

这里保存 2026-07-11 前使用的 3 区专用 `GuideReplay` 及其绑定探针，仅供
追溯旧产物和比较历史行为，不是可运行的搜索入口。

归档原因：

- `GuideReplay.Floor` 没有通用 `events` 建模，曾允许 auto BFS 穿过 MT33
  `swordTrap`，再用 `MT33 (10,10)` 坐标跳过补丁掩盖问题。
- 它和 `scripts/search/search_post40_guide_route.py::Game` 独立演化，容易让
  路径、事件、auto 与实机规则再次分叉。
- 后续 1-4 区和 slot26 搜索必须使用通用 `Game`；3 区明确事件放在
  `scripts/search/zone3_game_route.py::Zone3Game` 适配层。

禁止从这里复制单 walk 坐标特判回活跃代码。若通用模型与实机不一致，应先
补通用事件/路径规则和回归测试，再重新搜索和生成产物。
