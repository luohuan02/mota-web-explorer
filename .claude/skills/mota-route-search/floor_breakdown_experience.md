# walk 按楼层拆分 / 剩余资源对账经验（gen_recording_floor_breakdown.py）

来源 = `scripts/audit/gen_recording_floor_breakdown.py`（2026-08-27 新增；41228 复查中多处
「用户点破 → 修正」教训沉淀）。把已验证 walk.json 按楼层拆成「分层剩余 + 汇总对账」2 sheet xlsx。

## 一条命令通用
- `python scripts/audit/gen_recording_floor_breakdown.py --walk <w.json> --out <xlsx>`。
- 拼接 walk（无单一 provenance）加 `--rem-walk <接续段walk.json>`（见下「实现陷阱」）。
- **自动读 walk 自带 `provenance`** 里的 seed_save/capture/stage（转换时记录的真实参数），
  `start_stat` 再按 walk 起点楼层+HP 自动在 statlog 定位，直接重放共享 Game 得权威剩余。
  （provenance 缺或文件不在时回退 walk 自算，并打印「剩余怪会高估」警告。）
- xlsx 用纯 stdlib(zipfile+XML) 写出，免 openpyxl。产物 `best/*_floor_breakdown*.xlsx`
  （41228 用 v2，因 v1 含错误剩怪 8277）。

## 关键口径（已与用户对齐；凡与旧直觉冲突以本文件为准）
1. **截点 = 最终 50F 真魔王 redKing 击杀 step 的 before(won50=False)**。检测
   `steps[-1]==(击杀 redKing, floor MT50)`；**won50 只在 walk['final']，per-step frame 没有**。
2. **魔法伤害 = Σ action=='地图伤害' 步 dmg**（5区半血陷阱 + 靠近初级/高级巫师，与防御无关）。41228=1523。
3. **金币对账：总获金 = 打怪 + 卖yk + 其它**。打怪金币**必须用 walk 金币增量分类**（含 49F 封印怪/
   首领等**事件生成怪**），**不能用 static grid 怪 money 之和**（漏事件生成怪 → 低估一半错例：10102）。
   41228: 总 20353 = 打怪17653 + 卖yk1600 + 其它1100。
   - 其它 = 事件/NPC 赠送：MT2 老头 +1000、MT32(6,10)骑士队长先攻事件 +100。
   - **恒等校验：收入 − 支出 = final_gold − start_gold**（20353−20220=133=140−7 ✓）。
4. **剩余怪金（及所有 per-floor 剩余）= 必须用「共享 Game 重放 walk 后 g.floors 的未杀怪 money」**，
   **不能 map−walk 消耗**（walk.json 的 `auto_sweep` note 会被**截断**→漏击杀→严重高估）。
   41228: walk-diff 剩 **8277** vs 权威 Game 只剩 **385**（MT34=214/MT33=75/MT11=60/其余~0，MT40/45/48 全清）。
   - **资金逻辑反查剩余**：若「剩余怪金」多到可再买一次 2420 生命店，则该剩余不可信（2420 已是最优资金天花）。
5. **钥匙对账(每色) = 初始 + 裸拾取 + 商人买 − 开门 − 出售 − 最终**。裸拾取=地图裸钥(不含商人买)；
   商人买(MT6/MT15 各+1bk、MT12+1rk、MT7+5yk、MT38+3yk)另列；卖 yk 单列。41228: 黄4+171+8−167−16−0=0、
   蓝1+19+2−22−0=0、红0+9+1−10−0=0。
   **2026-09-05 41200 修正（新版 walk 格式必踩）**：① 裸拾取不能纯用正 delta 计数——同一开门步
   「拾 N 把 + 开 1 扇」净抵消会漏计（41200 漏 38），须优先数 note 条目（`auto:`/`auto_sweep:` 都要认，
   商人/商店步的 note 条目是购买展示不算拾取）；② 卖 yk 只认商人步——开门步 auto_sweep 顺路拾金
   会被「gold 增 + yk 减」误判成卖钥（41200 卖 21 实为 15）。
6. **商店分栏 + 累计属性增益**（攻+8/防+232/血+1600）：由 商店 step 的 atk/def/hp delta 累加。
   2区攻×2=+8 攻(MT12 每次+4)、4区防×7=+112(MT32 每次+16)、5区防×6=+120(MT46 每次+20)、5区血×1=+1600。

## 商人 / 事件口径
- **剩余商人 = 剔除已消费（商人/商店/事件 step 位置）+ 纯剧情 NPC**。商店/交易商人必有机制；
  老头(king/child/npc*)若 floor.events 无奖励机制（keyword `setValue status:/item:/道具名`）
  且不在 MERCHANT_FUNC → 忽略。标注用机制作用（`1000G→4黄+1蓝钥`、`2000G→3蓝钥`），**不做默认 +1000G**（只有 MT2 老头）。
- **剩余事件 = 剔除 已触发(事件 step) + step-on 已踩过格(walked_tiles) + 消费商人位置 + 装饰/空data**
  （`trigger:null`、`noPass` 墙体、`data:[]`）。只剩真·未触发机关。
  - MT40 boss @6,7 是 step-on 事件：walk 踩过即触发，须按 walked_tiles 剔出剩余（否则误报 boss 未打）。
  - MT23 大量 floor.events = `trigger:null/noPass` 墙体装饰，纯噪声须过滤。
- MT45 血商人实际 **1000G→+2000HP**（非 2000）；Game `TRADER_TABLE` 已建模 **MT39 = 2000G→3蓝钥**（可做搜索候选）。

## 实现陷阱
- `data/maps/mt*_map.json` stem 是 'mtXX_map'，fid 必须用 json 里 `floorId`(='MTXX')，否则与 walk 的 MTXX 对不上。
- ~21 个 MAP 文件是 UTF-8 BOM，需 utf-8-sig（或读前 3 字节判断）。
- 种子是 floorId+hero.hp（非 plain floor/hp）；start_stat 按 walk 起点楼层+HP 定位(41228=idx 55)。
- **分层 sheet 列权威 Game 重放的全部楼层（g.floors 恒为 50 层），不只列 walk 走到过的楼层**。
  接续段 walk（如 40943 的 zone5 段，seed=save105）未到的楼层，末态继承自种子存档
  （=此前区段验证后的真实末态），数据本来就全，旧版「只列 visited」会把 20 层滤丢
  （40943 只剩 30 层的根因）。未到楼层标注 `*`。
- **拼接 walk（多段 provenance，如 40943_full_combined_walk.json）用 `--rem-walk <接续段walk>`**：
  汇总增量（dmg/金币/钥匙/商店）取 combined walk（全线值），权威重放的 seed/capture/stage/auto
  取自接续段 walk 的 provenance。auto 解析顺序：显式 `--auto` > `provenance.auto_spec`
  （新版 converter 记录的种子 base，2026-08-29 起）> 默认全 false。**绝不能用
  `provenance['auto']`（转换终态 flags）当种子 base**——slot1 录像终态全 true 而种子 base
  全 false，用终态重放发散（39529 实证 action#110 楼层错乱）；旧 zone4/zone5 接续段 walk
  无 auto_spec，须显式 `--auto battle=true,item=true|nopotion,wall=true`；
  consumed_npc/consumed_ev/walked_tiles 仍取 combined walk（全线触发集，剔剩余更准）。
- **截点检测容忍击杀后的零 delta 尾步**：40943 系 walk 末尾在 `击杀 redKing` 后还有一个
  零变化 `[到达](6,5)`，旧「steps[-1] 必须是击杀」检测失效 → 截点落到击杀后（金币多算
  +500、与 41228/39944 的「击杀前」口径不一致）。现改为：从尾部找 MT50 redKing 击杀步，
  其后全是零 delta 步则仍截到击杀前（final gold=140 口径对齐）；击杀后有真实变化则不截。
- **对账≠0 先查 walk 链自洽性，别急着怀疑 breakdown 生成器**：对每字段验证
  `Σ(before→after delta) == final−init`。实例（2026-08-29）：39529 旧 walk（08-15 旧版
  converter 产物）有 3 处丢帧跳变——`[拾取] MT17(10,2)` 前 +2yk、`[通过] MT25(1,11) upFloor`
  前 +4rk（MT25 blackMagician afterBattle 4 红钥）、`[开门] MT41(5,6)` 前 +200G（紧跟
  MT41 bigKey opened=16）→ 对账黄-2/红-4 是忠实反映坏数据。当前 converter 已自愈（挂
  record 链式断言重放全程 0 violation），根因是旧产物 stale——用现管线重转 walk 即对账
  归零（yk 拾176买12开182售9终1、蓝 1+19+3−23、红 0+10+1−10−1 全 0）。诊断手法：Game.record
  子类断言 `before == 上一步 after`（逐字段）跑全程转换，或对现成 walk 逐字段
  `prev_after[c] != cur_before[c]` 定位断点。39944/40943/41228 walk 链全自洽。

## 2026-09-09/10 增补（41301/40520 线审查中沉淀，脚本均已实现）

### 汇总记录新增指标：药瓶恢复HP / 圣水恢复HP
- **圣水公式（源码实测 core.material.items.superPotion.useItemEffect）**：
  `hp = Math.round(0.74 * (hero.atk + hero.def)) * 10`——**圣水核心是攻防**，与使用位置/时机无关，
  只要求所有攻防增益拿完再用（各线都已是最后一步）。40145 7130(atk+def=964) vs 41301 7290(985)
  的差=纯属性差。**终局每 +1(攻+防) = +7.4 HP 圣水项**，叠加在减伤价值上（1def≈257HP 口径之外）。
- **HP 恒等式（全部线对上）**：`终态HP = 926 + 药瓶(红+蓝) + 圣水 + 商店血1600 + MT45 hp2000商人2000 − dmg`。
  breakdown 的 `potion_hp` 只含红/蓝瓶（floor_bad：红=1 单位、蓝=4 单位 ×50×ratio），
  superPotion 单列（步 eid=='superPotion' 的 hp delta）。
- 注意「拾取血量(=HP−起点+dmg)」（compare 派生值）= 药瓶+圣水+商店血 三者之和，两口径勿混。

### 分层记录新增列：花费yk / 花费bk / 花费rk
- 每层开门耗钥数（开门步 eid 计数），插在掉血量之后。**逐层合计必须等于汇总钥匙对账
  （黄169/蓝22/红10）**——不等=生成器 bug 或 walk 链断裂。与剩余列同行对照，
  「花费 vs 剩余」= 该层钥匙流的完整账。

### 剩余事件：enable:false 过滤（用户口径）
- `enable:false` = 作者禁用，live 永不触发（如 MT1 (7,10) 作者留言、MT2 (1,9) 开场小偷——
  开场对话是开场脚本播的，不是踩格触发），**不算剩余事件**。
- **MT3 (5,9) 魔王布阵是活事件**：原局触发过（削弱+关2楼监狱剧情，seed 存档 atk10/def10 即后果），
  但存档不持久化事件消费——**加载 MT4 存档后 live 里它重新武装**（实测 flag:03 可再置位），
  模型与 live 一致。路线踩上会无收益召唤 redKing+4 whiteKing，搜索必须绕开。
- 1-3F 的这两类都不是优化对象：固定背景噪声，各线一致。

### gen_route_compare.py 两处改版
- **checkpoint 表=只保留首次到达快照，删 完成/最终**；按字段分组、各线相邻
  （到达HP 方案1|方案2 | 到达DEF 方案1|方案2 | ...），两行表头（字段行+线名行）。
  口径仍是「首次到达 before，不能取最后一次离层」。
- 整体对比新增「圣水恢复HP」「药瓶恢复HP(红+蓝)」两行（药瓶=派生拾取血量−圣水−商店血）。

### 路线交换对比 sheet（参考 41228_floor_breakdown_v2-备注.xlsx 用户工作流）
- 用户手工审计格式：每层「hp转换/金币转换/bk转换/yk转换 + 备注」，估值 1bk=500/1yk=100/
  1rk=1000/怪金 1:1。为省手工，脚本可生成预填版：
  **每层 = 41301 基础列(dmg/剩余怪金/未拾瓶/yk/bk/rk/剩余资源HP值) + vs其它线差值列
  (dmg/剩余yk/剩余bk/剩余怪金/未拾瓶/金币获得，来自权威重放非估算) + 已知杠杆备注列**。
  实现见 `tmp/add_swap_sheet.py`（读各线 breakdown 分层记录+walk 金币，append 到 xlsx）。
- **坑：重跑 breakdown 生成器会覆盖追加的 sheet**——重跑后必须再执行一次追加脚本。
- 已预填的 41301 杠杆备注：MT16 省门交易（已用）、MT36 双门（已用）、MT11 捆绑包
  （funding 墙封闭）、MT38 swordsman 时机门（开放）、MT41/42 对称飞行器、MT31 keyBundle 现金缺口。

相关 [[floor_breakdown_script]] [[te_hp_41228_web_verified]] [[recording_seed_converter_experience]]

## 多线对比报告（gen_route_compare.py，2026-09-05 新增）

`python scripts/audit/gen_route_compare.py --walk 标签=walk.json(可重复) --anchors MT11,MT21,MT41 --out x [--note 结论行(可重复)]`

- 两个 sheet：整体对比（终态/dmg合计/拾取血量/金币/三门/剩余怪金 + checkpoint 表 + --note 结论）+
  逐层差异（**只列有差异的层**；N==2 布局用户 2026-09-17 定稿：dmg×2+diff | 黄门×2+diff |
  蓝门×2+diff | 红门×2 | 金币×2+diff | 门坐标差异 | 击杀差异，diff 列写**具体值**（前一线−后一线；
  不用 Excel 公式——脚本 data_only 读公式列为 None）；门坐标差异=**真 diff**，只列各线独有坐标、
  某色只在一侧开也列出[如 MT33 蓝门 1vs0]）。
  注意门坐标差异比较的是「重放终态已开坐标集合」——两线终态开门集合相同但开门方式不同
  （如 MT41：41301 bigKey 免点击 vs 41228 手点 3 扇）时该列为 `-`，方式差异看黄/蓝/红计数列。
- 门/怪坐标差异 = 静态图块 − 权威重放剩余（与 breakdown 同源 converter 重放，重放 final 与
  walk final 自动比对防漂移）；事件生成怪（MT50 redKing 类）不在静态表，在击杀差异列单列
  「剩余(事件怪)」。
- **checkpoint 口径**：取该层「首次到达(before)」和「首次攻略完（首个连续段最后一步 after）」，
  **不能取最后一次离层**——后期飞行回访会污染（41200 MT11 实证：末次离层 dmg 7799 是 MT16 时代
  的回访值）。walk 的 stat 在层间严格单调（def 单调性可作为 walk 自洽性快检）。
- **门经济口径（用户定稿）**：对比两条线的钥匙策略用「各层开门耗钥差异」（黄/蓝/红门逐层表），
  不要用「留门方式」描述。每扇门=1yk(或bk) 周转资金：开门清 0 伤怪的收入要和钥匙价值
  (1yk=100/1bk=500) 一起看；血瓶拾取时序差异（早拾 vs 5 区内补）用「拾取血量合计 + 到 41F 到达
  HP」两个数呈现。
- 41200/41228/41218 三线实例结论已写入 `best/41200_vs_41228_diff.xlsx` 与
  `best/41200_41228_41218_compare.xlsx` 的 --note 行，可作模板参考。

## 检查点记录 sheet（--checkpoints，2026-09-13 新增）

`--checkpoints <spec,...>` 追加第三个 sheet「检查点记录」——战略节点的**累计**快照，
替代「为单条录像手写一次性 tmp 报告脚本」（41206 教训：一次性脚本产单 sheet 非标
格式，用户判为格式错误；且输出文件名还出过 `41206_41206_` 双写 bug）。

- **spec 语法**：`<N>层`/`MTxx`=首次到达该层（换层步 after，含到达已结算的 arrival
  auto）；`before:<eid>`=首个`击杀 eid`步 before；`魔龙前`=before:magicDragon；
  `TE最终boss前`=50F 真魔王 redKing 击杀步 before（**必须限定 floor==MT50**——49F
  假魔王封印怪 eid 同为 redKing，不限定会错配到假魔王（41206 实证错位到步 1206）；
  录像止步于最终 boss 前时退化为末尾）；`end`=全部有效步后。
- **标准检查点集合**（用户定稿）：区界 11 层/31 层/41 层 + 魔龙前 + TE最终boss前。
- **列口径**：恢复血量=HP−起点HP+dmg（=药瓶+圣水+商店血）；药瓶恢复HP=红50×区ratio/
  蓝200×区ratio（不含圣水/商店血，终局行必须等于汇总 potion_hp）；消耗yk/bk/rk=开门
  消耗（出售另见汇总钥匙对账）；剩余(自己)=hero 库存，剩余(地图)=权威重放至检查点步
  的未拾裸钥，合计=两者相加；持有金币=当前存量；地图剩余金币=该时刻未杀怪 money
  （事件生成怪已 spawn 未杀计入）；商店购买情况=按楼层+类型聚合（如 `MT12攻×2 MT32防×7`）。
- **获得金币两个口径**（41206 用户对账定稿）：获得金币(合计)=金币正增量累计
  （打怪+卖钥+事件赠送，41206 boss前=20385）；**获得金币(打怪)=游戏「设置→游戏信息→
  数据统计」显示的金币**（engine `statistics.money` 只在 `eventdata.afterBattle` 累加：
  击杀步+auto 清怪步+带伤害的事件战斗步计入；**卖钥/事件纯赠送（老头+1000）/炸弹炸死
  的怪不计**，41206 boss前=17385+100骑士队长事件战=17485 与实机一致）。
- **地图侧数据源与对齐陷阱**：权威重放每 record 一步全图聚合存 raw_aggs，convert
  返回后按「**coalesced 步对象即 raw 步对象**」（coalesce 只丢弃不合并，`out.append(s)`）
  的身份映射定位检查点的 raw 步。两个已踩的坑：① 快照触发不能按 `len(g.steps)` 直接
  对 walk 步号——Game.steps 是 raw（41206: 1550），coalesce 在重放后进行，直接按
  coalesced 序号触发全部错位（旧一次性 tmp 脚本同病，地图列全虚高）；② 不能按 hero
  当前层做增量缓存——**fly/换层步会顺带结算旧层的 deferred auto sweep**（after.floor
  已是新层而旧层地图变了，41206 MT48 whiteKing sweep 实证差 400），必须全图重算。
- **自检锚点**：TE最终boss前行（或 end 行）的 消耗yk/bk/rk、dmg 必须等于汇总
  记录的 钥匙对账「开门消耗」与 dmg 合计；恢复血量=终态HP−起点HP+dmg；药瓶恢复HP
  =汇总 potion_hp；获得金币(打怪) 可与实机数据统计直接对照；地图剩余金币=权威终态
  剩余怪金（260 静态+500 事件怪=760）。

## 产物固定校验（每次生成后必做）

`python scripts/audit/verify_route_artifacts.py --walk <walk.json>` 六项全 PASS 才算完成：
重放 final==walk final、击杀/拾取格集合==walk、钥匙对账=0、金币恒等式、门闭合残差
（人工确认=bigKey/事件开门）、剩余怪金≤walk-diff 上界。**两个已踩的坑**：
① 击杀格比对不能用「静态图−重放剩余」差集——事件生成怪（MT10 骷髅 tile 17、MT50 redKing）
不在静态图；两侧都要用「击杀步 + auto:/auto_sweep: note 条目」同一套提取（sweep 击杀在
Game 步内折叠进 note）；② 门/钥匙的 eid→颜色映射表各有一套（yellowDoor→yk、yellowKey→yk），
混用会让开门数恒 0、对账虚高（残差恰=开门数是此 bug 的指纹）。

相关 [[floor_breakdown_script]] [[te_hp_41228_web_verified]] [[recording_seed_converter_experience]]
