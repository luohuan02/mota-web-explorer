# zone1-2 KILL 线经验（2atk0def，杀 zKnight 不买红钥匙，MT4-20）

来源 = **当前最优 zone1-2 walk** `best/zone12_2atk0def_recording_walk.md`（358 步，2攻0防 KILL 线，auto ON，web 0 mismatch；源 JSON `outputs/results/zone12_2atk0def_recording_walk.json`，生成器 `scripts/search/recording_to_game.py`，基线录像 `best/2区2攻不买800红钥匙.h5route`）。zone1-2 终态（MT20 vampire+cluster 后）**HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 dmg=7111**。

**演进**：drop753_774（HP=1241，旧录像派生，已删）-> statlog newrec 版（HP=1215，已删）-> **converter 版（当前最优，HP=1215，358 步 web 0 mismatch）**。converter 用 `recording_to_game.py` 逐格复现录像 captured path（KILL 线产物仍用 `--paths`；2026-08-09 V1 买 rk 线已证明无 `--paths` 也能 0 mismatch，见下「两条 converter 模式」），比 statlog 版更精确（PRE-state 0 mismatch）。HP=1215 比 drop753_774 少 26，因延后更多 HP 拾取（如 MT11 blackSlime+redPotion）到 3/4 区 0 伤阶段，eventual HP 更高 = 改进。

**converter Game walk（当前最优，主产物）**：`scripts/search/recording_to_game.py` 把录像解码 + 逐格 captured path 精确复现 + coalesce + 剪枝，生成 **358 步 Game walk** `outputs/results/zone12_2atk0def_recording_walk.json` + 人看 `best/zone12_2atk0def_recording_walk.md`（2攻0def KILL 线，times1=2）。web 复验 0 mismatch（final HP=1215 ATK=76 DEF=66 YK=5 BK=0 RK=0 G=1298 == exp）。3 处冗余已通用规则剪掉：MT8 钥匙 U 型折返（-4 步）、MT6 fly 前零效果 move、MT4 楼梯前死胡同 move（各 -1）。coalesce/剪枝细节见 `recording_converter_experience.md`。

## 录像复现流程 + Game 类限制（关键，避免重踩坑）

**唯一可行流程**（手玩录像 -> walk）：
1. 解码 `.h5route`：LZ 双层（file -> `LZString.decompressFromBase64` -> JSON `{route,seed,hard}`；`route` -> `decompressFromBase64` -> token string -> `decodeRoute` 解析为 action 列表）。解码器 `tmp/decode_new_h5route.js` + `tmp/extract_route.js`。
2. web 回放捕获 statlog：注入 `window.__compressedRoute`(outer.route) + `__seed` -> `tmp/replay_native.js`（钩 `core.control._doReplayAction` 写 `__statLog`，`core.startGame('',seed,decoded)` 回放）-> 轮询 `__replayDone` -> 取 `__statLog`。**此回放即 web 验证**（回放成功无失败 = 录像 web 复现）。
3. walk 从 statlog ground truth 生成（`tmp/gen_newrec_walk_from_statlog.py`）：按楼层访问分组，从逐 step state delta 推断 action（door/take/kill/shop/trader）。

**Game 类无法 action-by-action 复现手玩录像**（已用 autoon + 位置驱动两种方式确认失败）：
- **路径分歧**：Game 模型 `path_to`/`automaticRoute` 与游戏实机 step-by-step 寻路不同。`move:x:y` 终点可能相同但路径杀的怪/拾的道具不同（hero 静默走到不同位置/伤害）。autoon 的 go_to(target) 会发散。
- **autoon skip-if-cleared 失配**：autoon 跳过空格让 hero 停在楼层入口，后续 go_to(录像目标) 从入口不可达（录像逐步走能到，automaticRoute 从入口到不了）-> RouteError。
- **旧录像路径恰好 Game 兼容**所以 autoon 能跑（见 `recording_autoon_skip_cleared` 记忆，MT4-9 零 stat 错）；**用户新手玩调整路径不兼容**，autoon/driver 都败。
- **statlog 楼层抖动**：`_doReplayAction` 钩子抓到楼梯转换中途瞬时 floorId（如 MT8 (6,2) 转身时 floor 瞬时跳 MT9 又回 MT8），`nxt.f != hf` 检测被欺骗致 MT8↔MT9 乒乓。可后处理清 1 步抖动（`tmp/clean_statlog_flicker.js`：floor 与前后邻居都不同且位置不变 -> 改回邻居楼层）。旧 statlog 楼梯过渡单调无乒乓。

**结论**：手玩录像复现走 **converter** 路线（当前主产物）。早期 statlog ground truth 路线已被 converter 取代（更精确）。

**两条 converter 模式**：
- **逐格 captured path（`--paths`）**：不依赖 Game 自己的 `path_to`/`automaticRoute`（早期 autoon 实测会发散），而是**逐格回放录像 captured path**（exact 路径）+ auto_sweep 对齐 statlog，再 coalesce 成节点级步。KILL（2攻0def）线即此模式：358 步 web 0 mismatch。代价 = coalesce/剪枝逻辑复杂（走门格移除 / 零效果 move 剪枝 / U 型折返提升，见 `recording_converter_experience.md`）。
- **无 `--paths` Game 自寻路（2026-08-09 突破，推翻旧结论）**：V1 买 rk 线（`best/2区2攻800买红钥匙V1.h5route`）**无 `--paths`** 0 mismatch 到 MT31 HP=1232，web 复验全过。证明"Game 自己寻路必发散、须喂 captured path"是**错的**--发散根因是 4 个可修通用模型 bug（事件门没开/触发格没踩/no-op 误跳 spawn trigger/coalesce 折了 shop 目标），修后 Game 自寻路能复现。详见 `recording_converter_experience.md`「无需 captured path 的 4 个模型修复」+ [[game_conversion_no_paths_needed]]。

> **KILL（2攻0def）线尚未无 `--paths` 重测**：本文件记录的 358 步产物仍用 `--paths`。
> 4 修复是通用模型 + converter 逻辑修复，理论上对 KILL 线也适用，但未验证。新录像优先
> 试无 `--paths`，发散再退 `--paths`，发散点先按 4 类模型 bug 排查（别写浏览器 path 捕获）。

## 新录像 11 处冗余清理 + MT14 优化（用户手玩调整，对比 drop753_774）

drop753_774 walk（从旧录像派生）有 11 处冗余，新录像全清：

| # | 类型 | drop753_774 问题 | 新录像处理 | 教训 |
|---|---|---|---|---|
| 1,2,5,6,7 | 空往返 | MT9↔MT1↔MT7↔MT1↔MT7、MT16↔MT15、MT2 pass、MT12↔MT11↔MT10、MT16 pass upFloor（before==after）| 全删 | 从录像/build 派生的 walk 须剥**所有**空 fly/上下楼往返，不只 skip_ranges 里那 3 段 |
| 3,4,10,11 | 不必要金币清扫 | MT10/MT9/MT7/MT6/MT5 下降链 + MT15 bigBat(+44G) + MT19 blackSlime auto-sweep | 删绕路即删清扫 | 零伤怪 auto-sweep 金币是**绕路副产品**非收益；"不缺钱就不要打，后面再来"。删不必要的楼层穿越即消除 |
| 8 | 可延后血瓶 | MT11 x8y7 blackSlime+redPotion（HP 388->486，+98）| 不取（延后到 3/4 区 0 伤）| 固定 HP 补血组（blackSlime 0 伤 + redPotion）应延后到 0 伤阶段，同 [753][774] 教训 |
| 9 | MT14 优化 | drop753_774 MT14 顺序未优化 | 杀 zombieKnight 拿红钥匙 + 早拿 DEF（blueGem auto，DEF 58->60），省别处打怪/拿血 | zKnight 区早拿 DEF 减后续 dmg；redKey 用杀 zKnight 换不买 800G |

**新录像末段重排**：MT14(杀 zKnight+redKey) -> MT15(bluePotion) -> MT17 -> MT18 -> MT11 -> MT20(vampire)，比 drop753_774 末段更直接。


KILL 线 = 官方 2 攻线（见 `zone2_experience.md`）的 redKey 变体：**不买 800G redKey，改杀 MT14 3 zombieKnight 拿 redKey**，保 800G 给 4 区攻商店。times1=2（2 攻 0 防 0 HP 商店买）。cross 必备打 vampire（同 2 攻线 seg3，cross 在 MT19 (6,3) fakeWall2+setBlock）。

## 核心策略：杀 zKnight 替买 redKey（保 800G 给 4 区攻）

见 `zone2_experience.md` 抉择 D8：纯 zone2 杀 zKnight(372伤, +90G 掉落) HP等价 327 < 买 redKey(0伤, -800G) 400；但 end-to-end 买饿死 4 区攻（G 贫 -> 入 4 区 ATK142 vs 166 -> 魔龙 ATK270 多挨 6180 -> redkey12 线 19562 < 2ATK1DEF 23076）。**KILL 线选杀 zKnight，保 800G 给 4 区攻商店**，理论应超 23076（待 zone3/4 跑通验证）。

## vampire 固定伤害模型（special=0，无比例扣血）

MT20 vampire hp444 atk199 def66 **special=0**（不像 zone3/4 魔法师比例扣血）。cross atk×2（hero ATK 70->140）。

- 固定伤害 = max(1, atk-def) × ceil(hp/max(1,hero_hit)) - 1 = (199-DEF) × ceil(444/(140-66)) - 1
- @DEF60: 139×5 = **695**；@DEF66: 133×5 = 665；@DEF≥95: 0。
- **不依赖 hero HP**：vampire 伤害固定，hero 当前 HP 多少都扣固定值。
- cluster auto-sweep（MT20 x4y5 vampire 死后）：**固定 +1200HP +6ATK +6DEF +3YK**。
- **final HP = pre_vampire_HP - 695 + 1200 = pre_vampire_HP + 505**（@DEF60）。每个 pre-vampire HP 点全进 final。

## 三类资源 + drop 教训（关键）

vampire 固定伤害 + cluster 固定补血下，zone1-2 末段资源分三类：

| 类 | 例 | 特性 | 处理 |
|---|---|---|---|
| 固定 HP 补血 | redPotion(+50)/bluePotion(+200) | 不可 SKIP（丢等价），可 DEFER（随时 +固定值）| 延后到 0 伤阶段拿 |
| 战斗伤害 | redPriest/zKnight | DEF 越高 dmg 越低，DEF≥怪atk 则 0 伤 | 延后到高属性 |
| 属性提升 | DEF+2 gem/cluster | 早拿减后续 dmg | 尽早拿 |

**核心教训**：boss 固定伤害下，伴随战斗的补血组（redPriest+redPotion）应**完全延后到 0 伤阶段**（zone3/4 DEF≥95），而非只延后到下一个属性点（cluster DEF66）。

- redPotion **时机无关**（+100 随时拿），但 redPriest dmg DEF 依赖（DEF60=70 / DEF66=58 / DEF≥95=0）。
- 只延后到 cluster(DEF66)：redPriest -58×2，省 24HP（HP 1301->1325）。
- 完全去掉留 zone3/4 0 伤：redPriest 0 伤 + redPotion +100，省 116HP（HP 1241 zone1-2 末 / 1441 eventual）。
- **drop [753]MT19 redPriest / [774]MT20 redPriest（各伴 redPotion）= 当前最优**。final-score vs 1325 延后版 **+16**（zone1-2 剩余估值：redPotion 50×2=100 + redPriest 0伤+44G→22 分 = 122，大于 drop 损失的 HP 差）/ **+116** eventual（zone3/4 DEF≥95 0 伤拿回，HP 1441 vs 1325）。

## 不可优化点（已验证，勿再试）

- **MT14 BK-chain 不可跳**：[728]redPriest(拿 BK) -> [729]blueDoor -> [730]blackSlime + auto blueGem(DEF+2)。必须在 vampire 前拿 DEF+2。跳掉 -46 equiv（丢 blueGem DEF+2，HP 1301->1279 DEF=64）。x7y4 黄门后是 rock+bigBat 非血（point 25 位置错）。
- **MT19 zKnight/rock 不可优化**：zKnight(8,3)/rock(5,6)/(7,6) 二选一/三 zKnight 全必杀；go_to(8,1) 必经 (8,3)zKnight（上方区域入口仅 (4,3)zombie / (8,3)zKnight）；rock 二选一都 -378；cross 在 (6,3) 时序受限（fakeWall2+setBlock，见 `zone2_experience.md` D5/D6）。
- **MT20 vampire 触发 = 踩 (6,8)**（同 zone2 D9），8 bigBat 合并进 vampire 无金币；afterBattle spawn 3红3蓝宝石+3蓝血瓶+3黄钥（+6/+6/+HP）。

## skip362 耦合段陷阱 + 空往返 skip

- **[362] MT12 绕路移除**：seg5 fly MT19->MT12 杀 x2y5 -74HP 是买红钥匙线专属绕路，KILL 线不需要。但 seg6（红钥匙商人接近）也经 x2y5--只跳 seg5 会让 seg6 重打 x2y5（无收益）。解法 = `skip_ranges=[359,361)` 跳 seg5 **且** `stop_before_idx=951` 跳 seg6（KILL 不买红钥匙，seg6 整段多余）。+74HP / +2YK / -46G ≈ +151 HP 等价。
- **空往返 skip**：skip362 有 3 段空过往返（MT1↔MT7 / MT15↔MT16 / MT16↔MT17，B段 hp+0 g+0），`skip_ranges=[359,361)/[507,509)/[522,524)` 后 final 不变（HP=1301）步数 407->401。录像复刻步数优化不改分。
- **楼层检测用 hero 实际楼层** `g.state["floor"]`，非 statlog 相对 `cur["f"]`（skip_ranges 飞行绕路失同步，跳段后 statlog cur["f"] 停在绕路起点楼层误判后续换层）。

## HP delta 口径（同 zone2）

walk HP delta 含 auto_sweep 副作用（血瓶/拾取计入同一步），**非纯单怪伤害**。纯伤害看 dmg 增量或 Game `enemy_damage`。dmg = (turns-1)×per，turns=ceil(怪hp/hero_hit)，hero_hit=atk-怪def，per=怪atk-hero_def（hero 先手，怪少打一回合）。

## 验证判断陷阱（同 `mota-live-verify`）

- verifier `--out-json` 的 `strictWalk.ok` 硬编码 true（忽略），`strictMismatch` 排除 gold（忽略）。
- 必须手扫 `entries[]` 找值不匹配（hp/atk/def/gold/yk/bk/rk）；位置-only 不匹配（floor/x/y 偏 1-2）是 target-click-only 边界，可接受。
- 通用扫描器 `tmp/check_verify.js`（`node check_verify.js <verify.json>`）。

## 探索状态

- **zone1-2 KILL 线当前最优（2026-07-16）**：用户手玩录像 `best/2区2攻不买800红钥匙.h5route` -> converter 版 `best/zone12_2atk0def_recording_walk.md`（358 步，HP=1215，web 0 mismatch，11 处冗余全清 + 3 处通用剪枝）。旧 drop753_774（HP=1241）、statlog newrec 版（HP=1215）walk 已删，经验沉淀本文件。
- **下一步接 zone3/4**：converter 版延后的 MT11 blackSlime+redPotion 等 HP 拾取全留 zone3/4 DEF≥95 0 伤拿（eventual HP 应高于旧 drop753_774 的 1441）。
- **vs 2ATK1DEF（当前 best 23076）**：KILL 线保 800G 给 4 区攻 + zone2 不买 1 防（80G ratio2 浪费），理论应超 23076。待 zone3/4 跑通。
- **vs redkey12 线（买 800G，19562）**：KILL 线是其改进（杀 zKnight 保 800G），避开饿死 4 区攻。
