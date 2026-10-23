# 纯净版-TE zone1-2 语义重放搜索经验（V-A 基建 + yk 贪婪吸收定律）

来源 = 2026-09-09 会话（41231 骨架, tmp/zone12_va3.py 及配套 tmp/droptest.py /
door_span_test.py / batch_skip_test2.py / batch_pair_test.py / final_residual.py /
final_reach.py / combo_surgery.py）。本文件记录：把一条已验证录像的 zone1-2 段
转成**可自由增删改排的语义 action 列表**的完整基建方法、在其上做局部编辑搜索的
三类实验、以及由此发现的 **yk 贪婪吸收定律**（局部编辑搜索的根本性壁垒）。

## 1. V-A v3 语义重放基建（录像 zone1-2 -> 可编辑语义 action 列表）

把 walk 的 zone1-2 步（到首个 MT21 步为止）逐转成 `SemanticAction(kind='target')`，
在录像首个 MT21 action（si 4031）处接回原 action 列表。基线要求**完美等价**：
ok=True、final HP 一致、0 noop_routeerror（41231 验证通过）。

### 转换规则（踩坑全集，缺一则级联）

- **跨楼层 target 必须显式转换**：walk 的 `换层` 步 = 在旧楼层插入**楼梯 tile 的
  target**（Game 踩上即转换）；`飞行` 步 = 插 `kind='fly'` 语义动作。楼梯表从
  `data/maps/mtN_map.json` 的 `changeFloor` 解析——**floorId 是 `:next`/`:before`
  相对值**（隐藏层 MT44 要跳数：next(43)=MT45）。若上一 target 已是楼梯 tile
  （walk 的 `通过 upFloor` 步），不要再插（go_to 踩上即已转换，重复插会
  "requires current floor" 报错）。
- **`设置自动` 步 = `kind='set_auto'` 语义动作**，`data.choices` 从 walk 步的目标
  auto 态反推 toggle 序列。**必须以 4 开头**（进「自动操作」子菜单）——没有 4，
  所有 toggle 被忽略（_apply_set_auto_toggles 的 in_submenu 门禁）。toggle：
  0=battle、1=item(true↔false)、2=wall、4=item(true↔nopotion)。三态 item 反推：
  目标 True→[1]；目标 nopotion→[1(若当前非True),4]；目标 False→当前 True:[1]，
  当前 nopotion:[1,1]。
- **商店步（`商店`）的 note 没有 si**（只有 cost=N），且 statlog 的金币字段是
  **`g` 不是 `gold`**，且同位多次购买**合并为一个稀疏条目**（如 MT12 两笔 atk
  合并 si=1955: atk 30→38, g 317→257）。解法：连续同位商店步**分组**，取组首
  before/组尾 after 的 delta，从上一 si 向前扫 statlog 做 delta 匹配（字段别名
  gold↔g，缺失字段用 want 默认值兜底）。`商人` 步的 note 带 si，直接用。
- **其余步的 si 从 note 的 `录像\w+#N` 提取**；无 si 的步给 900000+（statlog 范围外
  → converter 跳过对账）。si 的用途：converter 的 shop/trader purchase-delta 检测
  只认真实 si——**商店步 si 错 = 购买不发生 = atk 缺 8 = 全程级联**。
- **击杀目标直接指向怪格**：converter 走 go_to_decomposed（松路径找首个 blocker
  → 真实点击 → 重规划），一般能过；失败看 diagnostics 的 noop_routeerror detail
  （含完整 hero 状态）。
- statlog 漂移只记 diagnostic 不中止（convert 只在 hp≤0 / 负钥匙 / g.errors 时断），
  所以**语义重排 surgery 是可行**的——漂移容忍是设计空间的一部分。

## 2. 可跳过性插桩扫描（哪些 action 能删）

在 va3 重放中用 patched `R.execute_action` 插桩：每个 action 执行时刻，克隆当前
Game，测试「跳过本 action、直接 go_to 下一个位置 target」是否成功 → drop_ok。
同时记录每 action 的 state delta（dGold/dHP/dKey/dGem）= 收集价值。

- **致命坑：Game.clone 是写时复制**（Floor 对象共享，只 deepcopy state）——
  clone 上的 go_to 走到绕过 COW 的变更路径会**污染原局共享 Floor**（未来怪被
  提前杀/门被提前开 → 基线跑出 HP=760 的假级联）。测试前必须：
  `cand.floors[当前层] = deepcopy(该层); 该层._owned = True`。
- 下一目标是跨楼层的 → drop_ok=True（转换动作兜底）。
- 41231 实测：557 个 zone1-2 action 中 **370 个可跳**，其中 **49 个开门步**。

## 3. 门 skip 的跨度测试（真删一扇门会怎样）

朴素 drop 对**过路门**无效：下一目标在门后，converter 重绕时会**重新开门**
（yk 白省）。精确测试：克隆上**清零 yk/bk**（强制门保持关闭），向后扫同层位置
目标，找**第一个无钥可达者**；span=[门, 该目标) 即被丢弃的口袋，span 价值
（dGold/dHP/dKey 合计）即损失。41231 实测：49 门中 **21 个零损失 VIABLE**
（span=[i,i+1)，下一目标本来就能无钥到达——录像顺路多开的门）。

## 4. yk 贪婪吸收定律（局部编辑搜索的根本壁垒）

三輪实验的收敛结论：

1. **21 个 skip-only 全部 ok=True HP=41231 G=640 yk=0**：省出的 yk 被 pathfinder
   **立即**吸收——下一次 go_to 的最优路径就走门路径（dmg 成本更低）/ 路径拾取
   差异补齐——路线完美自愈，净零。
2. **skip + 即时 tour 配对（fly 到残余药瓶口袋开门拾取再飞回）16 个全灭**：
   tour 花 1 yk，但省出的 yk 已被吸收，净 −1 → **固定 16 次卖 yk 对话**之一断供
   （sale 需要 yk 库存）→ −100G → def#15（slack 仅 40G）崩 → 级联。
   两个失败签名：早期 skip（atk<38）死在 tour 路径战斗；后期 skip 全部同一
   HP=27353 yk 断供级联。
3. **终局残余经济**（全 convert 到终局 + strict path 逐一可达性测试）：
   残余 = 4 红瓶 300HP（**红瓶=50×楼层ratio, 蓝瓶=200×ratio**，见 game_route.py
   apply_item；MT3/8=50、MT11/16=100）+ 385 怪金，**0 个不开门可达**；每扇门 =
   少卖 1 yk = −100G；最便宜药瓶门净 −97G > slack 40G → 数学性锁死。

**定律**：本骨架的 yk 库存在每个 go_to 时刻都被 pathfinder 最优花掉；freed key
即时被花，extra spend 饿死固定销售。**推论：终局残余药瓶在录像骨架内不可达，
拿到它们需要完全不同的 zone1-2 target 序列（路线拓扑级重排），局部编辑
（删/插/换序）全部被吸收机制抵消。**

**定律的边界**：吸收依赖骨架拓扑。并行会话的 41301 线（MT16 减门 1yk 喂 MT36
双门横穿）成立——重构后的路线里省出的钥匙可以没有买主。所以「局部编辑在
录像骨架上必被吸收」不等于「省钥匙无价值」；正确的用法是**把省钥匙和用钥匙
放在同一次拓扑重排里**（这正是官方"黄钥匙逆推"的本质）。

## 5. 手术脚本工程教训

- **拼接切片基准必须统一**：`new_out + actions_full[len(out):tour_at] + tours +
  actions_full[tour_at:]`——曾写成 `actions_full[tour_at - len(out):]`，导致
  zone1-2 尾段 123 个 action 在错误状态（HP=11/G=4196）下**重复执行**，制造
  全部"假失败"（"MT12 trader already used" at HP=11 就是它）。诊断特征：
  不同 skip 位置产生**完全相同**的失败 HP/状态 = 组装 bug 而非机制问题。
- **SemanticAction index 冲突**：capture 的 action 列表本身可能含历史 surgery
  的 80000+ 合成 action；新合成 index 用 95000+/900000+ 避开。
- 批量实验必须把每行结果**落盘 JSON**（后台任务 .output 受读取限制），并打印
  flush=True 便于中途查看。
- 评估一个候选的完整判据：ok=True + won50=True + final HP + final G/yk
  （G 变化 = funding 余量；yk 变化 = 钥匙净流）。

## 6. 与既有经验的衔接

- 录像->walk 的两条主 pipeline 与 coalesce 见 `recording_seed_converter_experience.md`；
  本文件的 V-A 是第三条路：**不动 converter、在 action 列表层做手术**，适合
  「基线完美等价 + 邻域搜索」场景。
- 终局残余对账口径（剩余怪金用共享 Game 重放、逐件列剩余）见
  `floor_breakdown_experience.md`；本文件的 final_residual/final_reach 是其
  逐格可达性深化。
- yk 贪婪吸收定律是 `te_hp_optimization_experience.md`「购买计划 = from-scratch
  硬约束」的钥匙版：**不仅购买计划，连钥匙流也被骨架的寻路贪婪锁死**。
