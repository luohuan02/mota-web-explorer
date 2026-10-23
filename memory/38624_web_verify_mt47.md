---
name: 38624_web_verify_mt47
description: 38624 MT47 卡点真因=converter --mt47-fire-clear workaround bypass 掉通用 _check_fire_retreat；通用模型已解决且 33508 web 验证过；修法=去掉 workaround
metadata: 
  node_type: memory
  type: project
  originSessionId: a325fe34-060f-4873-a413-4ae6824ce2e2
  modified: 2026-08-14T00:00:00.000Z
---

38624 路线（`best/zone12_2atk6def_38624_walk.json`，离线 HP=38624 ATK=390 DEF=574）web 复现
步 1-791 全部 0 stat mismatch，唯一失败点 = MT47 步 792。

**根因（重判 2026-08-14，撤回旧"UNRESOLVED"标签）**：通用 MT47 火撤退模型**已解决**——
`src/solver/game_route.py::_check_fire_retreat`（line 2659）实现 web moveOneStep 火撤退，在
`_go_to_body` 路径循环里 `trigger_tile_event` 之后、auto_sweep 之前调用（line 1758），配套
`retreat_wizards`/`_retreat_wizard_trapped_for_auto`/`kill_47_retreat_wizards`。该模型已在
**33508 路线 web 验证通过**（403 步 HP=33508，MT47 fire-retreat 步骤 271-282，0 mismatch）。

38624 一直卡的真因 = converter 的 **`--mt47-fire-clear` workaround**（
`recording_seed_to_game.py` line 1270-1291）在 MT47 auto_sweep 临时清空整层 fire 再恢复。因
`_check_fire_retreat` 触发条件就是 `fg_at(pos)==103`，火被清空后它永不触发——正确语义被完全
bypass。38624 walk 就是用这个 workaround 生成的，MT47 归因错（右侧资源归到 step 792 (7,1)，
实机要 (8,1) 火格到达才收，见 Visit B idx 1230-1231；Visit D idx 1311 依赖 redWizard 火撤退
后 auto_sweep 击杀）。

**修法**：去掉 `--mt47-fire-clear`，让通用 `_check_fire_retreat` 接管 MT47（不动共享 Game 阻火
语义，1257 是对的）。无需新写模型。

**当前阻碍（转换器回归，与火无关）**：去掉 fire-clear 重生成时，转换器 step 13 发散——原始
walk 到达 (8,11) 时 auto_sweep 顺带扫 x9y11 fakeWall + x11y11 sword1(atk10->20)；当前转换器
却显式破墙 (9,11) 且拿不到剑（atk 停 10，后续饿死）。疑与 `[[path_cost_item_epsilon]]` 等模型
修复后 go_to/auto_sweep 行为差异有关，需 root-cause 才能干净重生成。

**过程备注**：web 复现加载种子前必须 dismiss startGame intro 对话框（ev="action",lock=true 时
core.loadData 不 settle；按 3 次 Space 后 idle 再 loadData，hero 到 MT4）。种子用
`save1_mt4_snapshot_raw.json`（`_raw.json` 才是 core.loadData 兼容格式，见
`[[browser_save_slot_loading]]`）。replayer `--target-click-only` strict 禁 core.control.saveData，
故 --checkpoint-start 存槽失败；改用 tmp/saveslot.js（raw CDP）手动分段存槽 101/102/103。
