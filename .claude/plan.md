# 39944 基准骨架节点交换搜索（可达矩阵 + Game 重放即评估）

## 已核实的事实（本轮探查）

- **离线重放引擎已闭环且极快**：`convert(seed=save1_mt4_snapshot, capture=2atk_alldef_39944_capture,
  stage='mt4-mt31', start_stat=55)` -> ok=True，final HP=39944 精确复现，**0.5 秒/次**
  （tmp/plan_baseline_timing.py 实测）。
- 动作列表 1462 条（target 631 / arrow 755 / set_auto 7 / fly 116 / tool 10），每条带
  `floor` + `data.stat_index`。
- **商店购买可移植**：购买 (kind,count) 从原 statlog delta 推导（`_shop_purchase_from_delta`），
  挂在 action.stat_index 上 -> 单元整体搬移后购买语义保留。陷阱：验证用重放时 `times1`，
  变体中不匹配会**静默不买**（当作 approach waypoint），必须加守卫显式核对购买 delta。
- 可达矩阵基建就绪：`src/solver/reachability_matrix.py`（skeleton/shop/supplement 分类、
  钥匙门感知 flood、`cross_floor_reachable` 飞行边 + 法师陷阱 guard）。

## 方法：重放即评估（replay-as-evaluation）

搜索不 clone、不估伤——每个候选 = 修改动作列表 -> `convert()` 全程重放 ->
`(ok, final HP, errors)`。Game 是 web-parity 已验证模型：合法性（路径/钥匙/事件）、
生存（饿死/资金不足）自动拒绝，终值 HP 直接可比。0.5s/次 -> 数千候选可跑。
stat_diagnostic 对变体是噪声（对照原录像 statlog），非致命、忽略；只有 ValueError/g.errors 算拒绝。

## Phase A：评估器 + 访问单元分割（新脚本 `scripts/search/skeleton_swap_search.py`）

1. `replay(actions) -> result` 封装 convert()；先断言基线复现 39944。
2. 动作列表按 fly 边界切 ~117 个「访问单元」：unit = `fly(F)` + 后续同楼层 run
   （set_auto 按 floor 锚定；**tool 动作及其依赖下一动作方向的单元（pickaxe 目标推断）
   不参与搬移**）。
3. 单元元数据：floor、目的标签（shop-buy / potion / gem / event / battle / traversal，
   从基线重放步 delta 推断）。
4. 商店守卫：重放后核对每个含购买单元的 atk/def/hp/gold delta 与基线购买一致。

## Phase B：候选生成

- **搬移族（骨架交换，主攻）**：每个可搬单元 U：与相邻单元交换、后移/前移 K 个位置
  （全窗口）。含商店单元（时序换血：MT32 def 商店提前/延后、MT46 防店系列重排——
  atk/def 购买时点变化改变前后所有战斗伤害，正是 [[shop_change_requires_from_scratch_search]]
  要求的 from-scratch 重搜，此处重放=全量重模拟，天然满足）。
  优先级：先跑「回访/绕行单元」（fly 到比当前更低楼层、或同层多次访问的，
  如 MT34 药水绕行 ×2、MT38/MT36 回收访问），主进度单元（fly 递增爬塔）靠后。
- **插入族（矩阵驱动）**：在单元边界取重放状态快照，跑 `compute_matrix` /
  `cross_floor_reachable`，枚举可达未收集 skeleton 条目（宝石/药水/装备/商店），
  生成 `[fly F, target pos]` 插入单元（auto_sweep 到达即拾）。
- **商店拆分族**：大额购买单元拆 (k, N-k) 两个时点（合成购买动作，复用
  `_execute_shop` 的 purchase spec）。

## Phase C：爬山搜索

- 合法性判定：`ok=True` 且 final floor=MT50 且 won50 且商店守卫通过。
- HP 严格升 -> 接受为新 incumbent，从新动作列表继续生成候选；至无改进或预算用尽。
- 首轮预算 ~1500 候选（≈13 分钟）；全量日志（move, ΔHP, error/reject 原因）写
  `outputs/results/skeleton_swap_search_roundN.json`。

## Phase D：落地验证

1. 最优变体 -> walk JSON（steps + provenance 标注 variant-of-39944）先离线复放确认。
2. `gen_zone_walk_md.py` 生成 .md；`live_zone3_mouse_replayer_cdp.js --walk <json>
   --load-slot 1 --target-click-only` web 复验 0 mismatch（含金币）。
3. 通过后 best/ 固化（新文件名带 HP，**不覆盖 39944 产物**）+ route_chains 登记 +
   skill（te_hp_optimization_experience.md）/memory 更新。
4. web 若 mismatch：按根因优先约束修通用 Game 模型，不在坐标/walk 打补丁。

## 风险与对策

- 商店静默不买（times1 校验失败）-> Phase A 守卫核对购买 delta，拒绝可疑变体。
- set_auto 锚定：单元搬移跨越 auto 切换点改变 sweep 行为 -> 重放如实评估，不打补丁。
- 动作隐式依赖（pickaxe 目标推断等）-> tool 相关单元排除出搬移族。
- 全部候选被拒/无改进：负结果也固化（证明 39944 在该交换邻域局部最优），
  更新 te_hp_41477_bounds 记忆。

## 不改的东西

- 不改 Game/模型/verifier（纯新增搜索脚本 + tmp 探查脚本）；AGENTS/CLAUDE 不动；
  39944 现有产物不动；无模型改动则无需跑回归套件（py_compile 新脚本即可）。
