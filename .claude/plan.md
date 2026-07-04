# 离线模型改 TE 真结尾 + 重搜方案

## 目标
把 strict20 4F→50F 连续线从 NE（普通结局，HP=11441，拿双倍金币+50F 直杀强真魔王）改成 TE（真结尾），重搜后预期 HP 显著提升。对标 TE 榜 41477（NE 榜 26164）。

## 现状（已核实）
- **TE endgame 建模已存在** `scripts/probe_post40_te_late49_route.py`：
  - `post_shield_no49`：跳过 0F 双倍金币行程，保留 downFly（line 120-122 注释明确）
  - `late49_endgame`：救公主(25F/26F) → 24F → 50F 小偷(`trigger_mt50_thief`) → downFly@50F→49F(`downfly_to_mt49_event`) → 49F 封印战(`trigger_mt49_event` 设 redKing@6,3+8 whiteKing；`clear_mt49_from_center` 杀 4 十字警卫→`49sealed`→属性 5000→500，再杀 4 角+假魔王) → 回 24F→50F(`trigger_mt24_to_mt50`) → 杀封印真魔王(500/158/19)
  - 设 `TE=True`、`addhp=True`，符合你描述的完整 TE 流程
- **strict20 4-50 stitch 用的是 NE endgame**：`scripts/run_post40_from_zone3_candidate.py::run_stages` 调 `post.post_shield_49` + `post.post_49_endgame`（来自 `search_post40_guide_route.py`）。这俩做 0F 双倍金币+49F 弱直杀+50F 强直杀(22407 伤)。`export_strict20_preserve_pickaxe` 的 note 写"pure-TE"是误导，实际是 NE。
- **TE probe（6/29）结果差**：HP=500，dmg=46059。原因：(1) 用 slot26 变体起点(`post40_focused_slice5_mid_center`)，不是 strict20 4-50 起点；(2) `late49_endgame` 路由未优化（单阶段 31643 伤）；(3) 无双倍金币导致 def=422 < NE 513。

## 改动方案

### 1. 把 TE endgame 接进 strict20 export
- 文件：`scripts/run_post40_from_zone3_candidate.py`
- `run_stages`（line 421-429）：stages 末两段从 `post_shield_49` + `post_49_endgame` 换成 `post_shield_no49` + `late49_endgame`（从 `probe_post40_te_late49_route` 导入，或把这两个函数+四个 helper 提升到 `search_post40_guide_route.py` 共享）
- `export_strict20_preserve_pickaxe`（line 469）note 改成准确 TE 描述
- 效果：`strict20_preserve_pickaxe_31to50_local_walk.json` 变 TE 流程

### 2. 确认战斗数值建模
- 50F 真魔王：封印前 5000/1580/190（NE 直杀 22407 伤），封印后 500/158/19（TE，hero def>158 → 0 伤）。`clear_mt49_from_center` 已建模封印触发，需确认 50F 杀封印真魔王时用 500/158/19（不是 5000）
- 49F 假魔王：TE 先和 50F 小偷对话→假魔王变 5000/1580/190，封印后 500/158/19。`trigger_mt49_event`+`clear_mt49_from_center` 已处理，确认封印后杀用 500/158/19
- **won50 flag**：TE 杀封印真魔王后设 `won50=true`（当前 walk 是 false，要修）

### 3. 49F 禁 upFly 约束
- `late49_endgame` 已用 `trigger_mt24_to_mt50` 回 50F（没用 upFly），符合"49F 禁上楼器"。确认 Game 层不调用 upFly 离开 49F

### 4. 重搜 zone 4 路由（TE 约束，核心工作）
- 无双倍金币 → 怪金币 1x → 少金币 → 少买属性 → 需重调 shop/gem/怪选择路由
- **起点换回 strict20 4-50**（zone1 current_best → zone2 strict20 → 20-31 bridge → zone3），不用 slot26 变体
- `late49_endgame` 当前是手写路由（非搜索），31643 伤未优化。优化方向：
  - shop 顺序/数量（atk/def/hp shop 重新平衡，def 优先保证 >158 封印 0 伤）
  - gem 拾取顺序
  - 非 0 伤怪打/跳选择（magicDragon/blackMagician/redKnight/soldier）
  - 药水保留/使用时机
- 先跑一版看 HP baseline，再用 beam/Pareto 迭代优化

### 5. 重 stitch + 重 audit
- 跑 `run_post40_from_zone3_candidate.py` 生成 TE tail
- 跑 `stitch_strict20_preserve_pickaxe_4to50_walk.py` 重 stitch 4-50
- audit 要求 `errors=0`、`continuity_warnings=[]`
- 最终态校验：MT50 x6y5，`coin=false`（无双倍金币）、`downFly=0`（用在 50F→49F）、`won50=true`

### 6. 对比
- TE HP vs NE 11441：应显著高（省 ~22407 boss 伤，扣掉无双倍金币的损失）
- TE HP vs 榜 41477：看差距，迭代

## 风险
- **可行性**：strict20 起点的关键 shop 可能依赖双倍金币才买得起。去掉双倍金币后路由可能报错（买不到必需 atk/def）。若报错，需调整 shop 顺序或补金币 farming
- **HP 上限**：即使跑通，TE HP 可能仍远低于 41477（榜高度优化）。第一阶段目标：跑通 + HP > NE 11441，再迭代
- **web 验证**：留到离线 TE 稳定后做，不重复之前一步步 web 补的错误

## 执行顺序
1. 改 `run_post40` stages 为 TE（接 `post_shield_no49` + `late49_endgame`），修 won50
2. 跑 `run_post40` 生成 TE tail，看 baseline HP（预期 >500；若 <11441 或报错进 3）
3. 若 HP 不理想/报错：优化 `late49_endgame` 路由（shop/gem/怪/药水），beam 迭代
4. 重 stitch + audit（errors=0, continuity=[]）
5. 报告 TE HP，对比 NE 11441 和 TE 榜 41477，决定是否继续优化
