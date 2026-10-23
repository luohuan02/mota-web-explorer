# zone2 2攻录像经验（2区2攻 + 买800红钥匙 + 少开门，停 31F）

来源 = 用户手动游戏录像 `2区2攻+买800rk+1yk换100血的门少开停31楼.h5route`
（2026-08-22 提供）。converter (`scripts/search/recording_seed_to_game.py`)
转成 Game walk：`outputs/results/zone2_2atk_1yk100hp_offerroute_walk.json`（507 步，
MT4->MT31，final **HP=1245 ATK=76 DEF=64 YK=7 BK=0 RK=0 G=352**，matches recording
final MT31(6,2) HP=1245 ATK=76 DEF=64 YK=7 G=352）。web 复验
`outputs/results/zone2_2atk_1yk100hp_offerroute_live_verify.json` = **ok:true,
goldMode exact, finalState 全等, exit 0, 无 value mismatch（gold=352），465 个 entry
consumed 507 步**（consumedStep 到 507，与 walk 长度一致）。

这条路线区别于 `zone2_experience.md` 里已有的 KILL 线（2攻0def 杀 zKnight）和
redkey12 买线（买 redKey 201 区饿死）。本线 = 2 攻 + **买 800G redKey** + 少量门少开
（第 88 黄门 vs 全防 90），终态反而比全防/2ATK1DEF 更省门、更高 HP、更多 YK。

## 本线购买 / 资源（录像 statlog 提取）

- `#651` MT12 blueShop 买 2 攻（ATK 30->38）。
- `#705` MT7 商人 50G->5YK。
- `#725` MT15 商人 200G->1BK。
- `#843` MT6 商人 50G->1BK。
- `#1249` MT12(1,1) 商人 800G->1RK（红钥匙）。
- `#1335` MT20 吸血鬼（event 触发）+ 无 redKey 战损 705（cross 有，atk×2）。
- final：HP=1245 ATK=76 DEF=64（vampire afterBattle +6/+6 后）YK=7 G=352。

## 与 39944 全防族 zone2 前缀的对比（关键结论，2026-08-22）

两 prefix 都在 MT31 入口 **ATK=76 DEF=64 全等**（39944 本就是 2区2攻、4区全防），
所以差异纯粹是路线/资金效率，不是属性方向：

| MT31-entry | 2攻录像 | 39944 全防 v5 | Δ |
|---|---|---|---|
| HP | 1245 | 1232 | **+13** |
| ATK/DEF | 76/64 | 76/64 | identical |
| YK | 7 | 5 | **+2** |
| gold | 352 | 375 | −23 |
| cumulative dmg | 6681 | 6894 | **−213** |
| yellow doors | 88 | 90 | −2 |
| blue doors | 9 | 8 | +1 |

- **Score-model net: +101.5 HP-equiv**（13 + 2×50 − 23×0.5）。
- **Endgame funding net: +177G equiv**（+2 YK 在 MT28 specialTrader 100G/yk ->
  +200G，抵消 −23 G 后净 +177G）。按 2420 商店边际 ~2.24 HP/G，+2 YK ≈ **+448
  HP-equiv**。
- **对 41477 冲刺的意义**：2攻录像 prefix 严格优于 39944 族 zone2（HP/钥匙/伤害全
  胜，仅少 23G），且属性路径不变（ATK/DEF 全等）-> 换 zone2 前缀**不需 zone3/4
  from-scratch 重搜**。唯 dmg −213 / HP +13 会改跑动 HP 下限，故 zone3/4 仍须**离线
  replay + web 复验**，不能直接 drop-in splice。

## 用户 2 攻思路沉淀（待 zone3/4 接续验证）

- 2 区 attack shop 优先；8F 商人 1yk→5yk；MT15 200G→1BK；16F 上 17 需 1BK+1YK
  最优（本线购买组合印证）。
- 先 16F 红/蓝宝石，后 17F 剑（复用 D3：blackSlime 39 阈值先于 sword2 卫兵）。
- shield11 / def15 / def12 / atk12 / atk11 优先级（属性购买节奏，供 zone4 接续）。
- 少开门哲学：能绕就绕，故第 88 黄门（比对 89/90），把钥匙留在可售/后置用途。

## 复验记录

`node scripts/live/live_zone3_mouse_replayer_cdp.js --walk
outputs/results/zone2_2atk_1yk100hp_offerroute_walk.json --load-slot 1
--target-click-only --set-auto "battle=true,item=true,wall=true" --out-json
outputs/results/zone2_2atk_1yk100hp_offerroute_live_verify.json`

exit 0 = 每步 value mismatch（含 money）即 throw，run 内 465 个 entry 全部走完、
writeRunLog `ok:true`。4 个 per-entry `strictMismatch` 全是 x/y 位置差（点击落点
偏离一格，`strictValueMismatchText` 不含 x/y），非 value mismatch。

详见 `recording_seed_converter_experience.md`「is_kill_approach / 击杀前定位到达」
例外说明（本线 MT5 (3,3) bat 曾因 coalesce 误删定位步 web 卡死，已根因修复）。
## 已封闭杠杆：MT12 zombie(3,9) cross-first（2026-09-05 实跑封闭）

41218 的 zombie(3,9) 只掉 27 伤（41200/41228 掉 81/108），机制 = 它在 zombie 前已拿
MT19(6,3) 十字架（cross 对 zombie/zombieKnight/vampire atk×2，atk70 → 2 回合 1 反击 = 27）。
尝试把 41200 的 zombie 专趟延后到十字架后（capture 级语义动作重排实跑 converter）：

- **循环依赖**：zombie(3,9) 口袋（蓝钥(2,8)+黄钥(2,7)/(1,8)）唯一入口 = zombie 本格
  （(2,9)/(1,9) 被墙封死）；口袋蓝钥 5 步后开 MT19 蓝门 (6,7)；蓝门是十字架口袋 (6,3)
  必经。zombie 必须先死 → bk 才存在 → 门才开 → cross 才拿。
- 旁路全负：MT15 商人 bk 已在早期承诺 MT18 门（三门三钥平衡）；MT6 商人二连买 50G
  净 +4 无意义；左翼 (5,6) rock 提前打 atk70 hero_hit=2 战损爆表；抄 41218 的
  「9 楼节约 bk」要先付 MT9 +203 伤 > 54。
- **结论**：41218 的「9 楼节约 bk」正是它 cross-first zombie 的钥匙经济代价——每条
  录像线的钥匙流是自洽整体，不能局部抄单点优势。检查同族其它 zombie/zombieKnight
  cross-first 机会时，先验证该怪口袋是否也承担 upstream 蓝门 funding。
