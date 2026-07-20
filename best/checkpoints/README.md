# 阶段性存档 (stage checkpoints)

每区 web 验证全过后存一个阶段性存档，后续会话从该存档恢复继续探索，不再从 4F 重跑。

## 存档两件套

1. **Web 浏览器存档槽**：游戏内存档到专用槽（记录槽号）。web 验证下一区时 `--load-slot <N>` 加载，跳过重放本区。
2. **离线 save 快照 JSON**：用 `scripts/live/export_save_slot_cdp.js --slot <N> --out best/checkpoints/<zone>_end_save.json` 把该槽导出。`zoneN_game_route.py --from-checkpoint <path>` 直接 `Game(read_json(...))` 加载，跳过本区离线重放。

导出 JSON 与 `outputs/results/save1_current_snapshot.json` 同格式（`Game.__init__` 直接消费）。

## 当前存档

见 `manifest.json`。zone1_end 待下一次 1区 web 验证全过后导出（浏览器当前不在 1区末）。

## 工作流（每区末）

当前新增：`zone3_2atk1def_end` 已于 2026-07-12 完成 234 步真实目标点击复验，浏览器槽 123，离线快照为 `best/checkpoints/zone3_2atk1def_end_save.json`；边界是 MT41 x6y2，HP=65 ATK=174 DEF=166 YK=8 G=1858。

1. 本区 web 验证 0 mismatch（含金币，0 容忍）。
2. 浏览器存档到专用槽（避开 save36=2区末、save37=3区末等已用槽）。
3. 导出：`node scripts/live/export_save_slot_cdp.js --slot <N> --out best/checkpoints/<zone>_end_save.json`
4. 更新 `manifest.json`（slot、final state、verified date、source walk）。
5. 下一区：`python scripts/search/<zone+1>_game_route.py --from-checkpoint best/checkpoints/<zone>_end_save.json`；web 用 `--load-slot <N>`。

## 边界

- zone1_end = boss 后、补给前（hero MT10 [6,1] HP=122 ATK=27 DEF=27 G=313）。加载后仍要 `apply_mt10_supply` + `run_zone2`。
- zone2_end = MT20 vampire 后（对应 save36）。
- zone3_end = MT40（对应 save37）。
