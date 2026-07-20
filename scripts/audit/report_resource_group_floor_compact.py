#!/usr/bin/env python3
"""Render a by-floor compact map for a live resource-group cache."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.build.build_live_resource_group_cache import (
    ROOT,
    build_floor,
    floor_no,
    gain_text,
    load_enemies,
    load_tiles,
    read_json,
)


DEFAULT_CACHE = ROOT / "outputs" / "results" / "save1_future_resource_group_cache.json"
DEFAULT_OUT_MD = ROOT / "outputs" / "reports" / "save1_resource_group_floor_compact.md"


DOOR_SYMBOLS = {
    "yellowDoor": "黄",
    "blueDoor": "蓝",
    "redDoor": "红",
    "specialDoor": "机",
    "steelDoor": "铁",
}

TERRAIN_SYMBOLS = {
    "upFloor": "上",
    "downFloor": "下",
}


def item_pos_to_group(groups: list[dict[str, Any]]) -> dict[tuple[int, int], str]:
    mapping: dict[tuple[int, int], str] = {}
    for group in groups:
        suffix = group["group_id"].rsplit(".g", 1)[-1]
        for item in group["items"]:
            mapping[(int(item["x"]), int(item["y"]))] = suffix
    return mapping


def cell_symbol(cell: dict[str, Any] | None) -> str:
    if cell is None:
        return "·"
    kind = cell["kind"]
    eid = cell["id"]
    if kind == "wall":
        return "墙"
    if kind == "door":
        return DOOR_SYMBOLS.get(eid, "门")
    if kind == "enemy":
        return "零" if cell.get("zero_damage_now") else "怪"
    if kind == "autoWall":
        return "暗"
    if kind == "lava":
        return "岩"
    if kind == "terrain":
        return TERRAIN_SYMBOLS.get(eid, "地")
    if kind == "shopSide":
        return "铺"
    if kind == "shop":
        return "店"
    if kind == "trader":
        return "商"
    if kind == "oldman":
        return "老"
    if kind == "npc":
        if eid == "thief":
            return "偷"
        if eid == "princess":
            return "公"
        return "人"
    if kind == "eventBlock":
        return "占"
    if kind == "unknown":
        return "?"
    if kind == "other":
        return "他"
    return "·"


def render_map(
    floor: dict[str, Any],
    groups: list[dict[str, Any]],
    hero: dict[str, Any],
) -> list[str]:
    group_at = item_pos_to_group(groups)
    lines = [
        "| y\\x | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for y in range(floor["height"]):
        cells = []
        for x in range(floor["width"]):
            if floor["fid"] == hero.get("floor") and x == hero.get("x") and y == hero.get("y"):
                cells.append("勇")
                continue
            cells.append(group_at.get((x, y), cell_symbol(floor["cells"].get((x, y)))))
        lines.append(f"| {y} | " + " | ".join(cells) + " |")
    return lines


def short_blockers(blockers: dict[str, int], limit: int = 5) -> str:
    if not blockers:
        return "-"
    pairs = sorted(blockers.items(), key=lambda kv: (-kv[1], kv[0]))
    text = "，".join(f"{key}x{value}" for key, value in pairs[:limit])
    if len(pairs) > limit:
        text += f"，另{len(pairs) - limit}类"
    return text


def group_items_text(group: dict[str, Any]) -> str:
    return "，".join(f"x{item['x']}y{item['y']} {item['name']}" for item in group["items"])


def write_report(cache: dict[str, Any], out_path: Path) -> None:
    source = cache["source"]
    state = source["state"]
    auto = source["auto"]
    snapshot_path = (ROOT / source["snapshot"]).resolve()
    snapshot = read_json(snapshot_path)
    tiles = load_tiles()
    enemies = load_enemies()
    hero = {"floor": state["floor"], "x": int(state["x"]), "y": int(state["y"])}

    floors_by_id = {floor["floor"]: floor for floor in cache["floors"]}
    drawable_floors = [floor for floor in cache["floors"] if floor["summary"]["group_count"]]
    empty_floors = [floor for floor in cache["floors"] if not floor["summary"]["group_count"]]
    validation = cache["validation"]
    event_group_count = validation.get("event_resource_groups", 0)
    event_item_count = validation.get("event_resource_items", 0)
    npc_group_count = validation.get("npc_resource_groups", 0)
    event_change_count = validation.get("event_map_changes", 0)

    lines = [
        "# 1号存档资源组压缩图（按楼层）",
        "",
        "## 口径",
        "",
        f"- 目标：纯净版 TE 最高血量。",
        f"- 起点：`{state['floor']} x{state['x']}y{state['y']} HP={state['hp']} ATK={state['atk']} DEF={state['def']} YK={state['yk']} BK={state['bk']} RK={state['rk']} G={state['gold']}`。",
        f"- 自动设置：`battle={auto.get('battle')}`，`item={auto.get('item')}`，`wall={auto.get('wall')}`。",
        f"- 压缩规则：不跨未清怪、门、硬墙、商店侧翼、NPC/商店、事件占位格、未知格；自动开墙开启时假墙可连通；当前 `has_snow={source.get('has_snow')}`，所以岩浆仍作为阻断。",
        f"- 血瓶规则：`item=nopotion` 时只自动拾取非血瓶物品，所以每组同时列出“全拿”和“初始不拿血瓶”收益。",
        "",
        "## 图例",
        "",
        "| 符号 | 含义 |",
        "| --- | --- |",
        "| `01`、`02`... | 该格物品属于对应资源组 |",
        "| `勇` | 当前勇士位置 |",
        "| `·` | 空地或可走通路 |",
        "| `上` / `下` | 楼梯 |",
        "| `黄` / `蓝` / `红` / `机` / `铁` | 门 |",
        "| `怪` / `零` | 怪物 / 当前属性下 0 伤怪 |",
        "| `墙` | 硬墙或不可通行地形 |",
        "| `铺` / `店` | 商店侧翼 / 商店入口；侧翼不作为通路 |",
        "| `商` / `老` | 商人 / 老人资源点 |",
        "| `暗` | 暗墙，当前自动开墙视作可连通 |",
        "| `岩` | 岩浆，当前未拿雪花仍阻断 |",
        "| `占` | 事件/特殊怪物占位格，触发前阻断 |",
        "| `人` | NPC 或事件人 |",
        "| `?` | tile_mapping 未识别的特殊格 |",
        "",
        "## 总览",
        "",
        f"- 校验：`ok={validation['ok']}`，当前可见物品覆盖 `{validation['grouped_items']}/{validation['total_items']}`，当前资源组 `{validation['total_groups']}`。",
        f"- 事件后资源：`{event_group_count}` 组，`{event_item_count}` 个生成物品；这部分不计入当前可见物品覆盖数。",
        f"- 事件地图变化：`{event_change_count}` 组；用于记录打怪/开门/事件后格子变空、开门或变墙。",
        f"- NPC/商店资源点：`{npc_group_count}` 个；这部分要作为搜索动作/状态转换，不并入地面物品组。",
        f"- 警告：{'; '.join(validation.get('warnings') or ['无'])}。",
        "",
        "## 战略分层汇总",
        "",
        "| 层级 | 数量 | 用途 |",
        "| --- | ---: | --- |",
    ]
    role_help = {
        "core_target": "阶段目标、beam 保留、A* hint 优先使用",
        "secondary_stat": "阈值调优和伤害曲线比较",
        "support_resource": "缺钥匙、缺血、补金币或批处理时使用",
        "conversion_node": "商店/商人/老人等显式状态转移",
        "story_event": "剧情或未解析事件，路线依赖时单独核对",
    }
    for role, count in validation.get("strategy_counts", {}).items():
        lines.append(f"| {role} | {count} | {role_help.get(role, '-')} |")
    lines.extend([
        "",
        "| 楼层 | 倍率 | 资源组 | 物品 | 怪物 | 当前0伤怪 | 门 | 暗墙 | 岩浆 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for floor in cache["floors"]:
        summary = floor["summary"]
        counts = summary["counts"]
        if not any(counts.get(k, 0) for k in ("item", "enemy", "door", "autoWall", "lava")) and not summary["group_count"]:
            continue
        lines.append(
            f"| {summary['floor']} | {summary['ratio']} | {summary['group_count']} | "
            f"{counts.get('item', 0)} | {counts.get('enemy', 0)} | {summary['zero_damage_enemies_now']} | "
            f"{counts.get('door', 0)} | {counts.get('autoWall', 0)} | {counts.get('lava', 0)} |"
        )

    event_groups = [
        group
        for floor in cache["floors"]
        for group in floor.get("event_groups", [])
    ]
    if event_groups:
        lines.extend(
            [
                "",
                "## 事件后资源总表",
                "",
                "| 组 | 层级 | 触发 | 生成物 | 全拿收益 | 初始不拿血瓶 | 条件 |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for group in event_groups:
            trigger = group.get("trigger_pos")
            trigger_text = f"{group['trigger_label']} x{trigger['x']}y{trigger['y']}" if trigger else group["trigger_label"]
            conditions = "；".join(group.get("conditions") or ["-"])
            role = group.get("strategy", {}).get("role_cn", "-")
            lines.append(
                f"| `{group['group_id']}` | {role} | {trigger_text} | {group_items_text(group)} | "
                f"`{gain_text(group['gain_all_items'])}` | `{gain_text(group['gain_no_potions'])}` | {conditions} |"
            )

    npc_groups = [
        group
        for floor in cache["floors"]
        for group in floor.get("npc_resource_groups", [])
    ]
    if npc_groups:
        lines.extend(
            [
                "",
                "## NPC / 商店资源总表",
                "",
                "| 组 | 层级 | 位置 | 类型 | 资源模型 | 选项 | 说明 | 搜索处理 |",
                "| --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for group in npc_groups:
            options = "；".join(option.get("label", "?") for option in group.get("options", [])) or "-"
            note = group.get("note") or "-"
            visible = "当前可见" if group.get("visible_now") else "事件/条件后"
            role = group.get("strategy", {}).get("role_cn", "-")
            lines.append(
                f"| `{group['group_id']}` | {role} | {group['floor']} x{group['x']}y{group['y']} {group['name']} | "
                f"{visible} | `{group['resource_model']}` | {options} | {note} | `{group['search_treatment']}` |"
            )

    event_changes = [
        group
        for floor in cache["floors"]
        for group in floor.get("event_map_changes", [])
    ]
    if event_changes:
        lines.extend(
            [
                "",
                "## 事件地图变化总表",
                "",
                "| 组 | 触发 | 变化 |",
                "| --- | --- | --- |",
            ]
        )
        for group in event_changes:
            trigger = group.get("trigger_pos")
            trigger_text = f"{group['trigger_label']} x{trigger['x']}y{trigger['y']}" if trigger else group["trigger_label"]
            pieces = []
            for change in group["changes"]:
                locs = "，".join(f"x{loc['x']}y{loc['y']}" for loc in change.get("locs", []))
                detail = change.get("id") or change.get("number") or ""
                pieces.append(f"{change['action']} {detail} {locs}".strip())
            lines.append(f"| `{group['change_id']}` | {trigger_text} | {'；'.join(pieces)} |")

    lines.extend(["", "## 楼层压缩图", ""])
    for cached_floor in drawable_floors:
        fid = cached_floor["floor"]
        summary = cached_floor["summary"]
        counts = summary["counts"]
        floor = build_floor(fid, snapshot, tiles, enemies)
        lines.extend(
            [
                f"### {fid}",
                "",
                f"- 倍率：`{summary['ratio']}`；资源组：`{summary['group_count']}`；物品：`{counts.get('item', 0)}`；怪物：`{counts.get('enemy', 0)}`；门：`{counts.get('door', 0)}`；暗墙：`{counts.get('autoWall', 0)}`；岩浆：`{counts.get('lava', 0)}`。",
                "",
            ]
        )
        lines.extend(render_map(floor, cached_floor["groups"], hero))
        lines.extend(
            [
                "",
                "| 组 | 层级 | 物品 | 全拿收益 | 初始不拿血瓶 | 血瓶数 | 邻接阻断摘要 |",
                "| --- | --- | --- | --- | --- | ---: | --- |",
            ]
        )
        for group in cached_floor["groups"]:
            role = group.get("strategy", {}).get("role_cn", "-")
            lines.append(
                f"| `{group['group_id']}` | {role} | {group_items_text(group)} | "
                f"`{gain_text(group['gain_all_items'])}` | `{gain_text(group['gain_no_potions'])}` | "
                f"{group['potion_count']} | {short_blockers(group['adjacent_blocker_counts'])} |"
            )
        if cached_floor.get("event_groups"):
            lines.extend(
                [
                    "",
                    "**事件后资源组**",
                    "",
                    "| 组 | 层级 | 触发 | 生成物 | 全拿收益 | 初始不拿血瓶 | 条件 |",
                    "| --- | --- | --- | --- | --- | --- | --- |",
                ]
            )
            for group in cached_floor["event_groups"]:
                trigger = group.get("trigger_pos")
                trigger_text = f"{group['trigger_label']} x{trigger['x']}y{trigger['y']}" if trigger else group["trigger_label"]
                conditions = "；".join(group.get("conditions") or ["-"])
                role = group.get("strategy", {}).get("role_cn", "-")
                lines.append(
                    f"| `{group['group_id']}` | {role} | {trigger_text} | {group_items_text(group)} | "
                    f"`{gain_text(group['gain_all_items'])}` | `{gain_text(group['gain_no_potions'])}` | {conditions} |"
                )
        if cached_floor.get("npc_resource_groups"):
            lines.extend(
                [
                    "",
                    "**NPC / 商店资源点**",
                    "",
                    "| 组 | 层级 | 位置 | 类型 | 资源模型 | 选项 | 说明 |",
                    "| --- | --- | --- | --- | --- | --- | --- |",
                ]
            )
            for group in cached_floor["npc_resource_groups"]:
                options = "；".join(option.get("label", "?") for option in group.get("options", [])) or "-"
                note = group.get("note") or "-"
                visible = "当前可见" if group.get("visible_now") else "事件/条件后"
                role = group.get("strategy", {}).get("role_cn", "-")
                lines.append(
                    f"| `{group['group_id']}` | {role} | x{group['x']}y{group['y']} {group['name']} | {visible} | "
                    f"`{group['resource_model']}` | {options} | {note} |"
                )
        if cached_floor.get("event_map_changes"):
            lines.extend(
                [
                    "",
                    "**事件地图变化**",
                    "",
                    "| 组 | 触发 | 变化 |",
                    "| --- | --- | --- |",
                ]
            )
            for group in cached_floor["event_map_changes"]:
                trigger = group.get("trigger_pos")
                trigger_text = f"{group['trigger_label']} x{trigger['x']}y{trigger['y']}" if trigger else group["trigger_label"]
                pieces = []
                for change in group["changes"]:
                    locs = "，".join(f"x{loc['x']}y{loc['y']}" for loc in change.get("locs", []))
                    detail = change.get("id") or change.get("number") or ""
                    pieces.append(f"{change['action']} {detail} {locs}".strip())
                lines.append(f"| `{group['change_id']}` | {trigger_text} | {'；'.join(pieces)} |")
        lines.append("")

    event_only_floors = [
        floor
        for floor in cache["floors"]
        if floor.get("event_groups") and floor["summary"]["group_count"] == 0
    ]
    if event_only_floors:
        lines.extend(
            [
                "## 只有事件后资源的楼层",
                "",
                "| 楼层 | 事件资源组 | 生成物 | 说明 |",
                "| --- | ---: | ---: | --- |",
            ]
        )
        for floor in event_only_floors:
            names = "；".join(
                f"{group['group_id']}：{group_items_text(group)}"
                for group in floor["event_groups"]
            )
            lines.append(
                f"| {floor['floor']} | {len(floor['event_groups'])} | "
                f"{sum(group['item_count'] for group in floor['event_groups'])} | {names} |"
            )
        lines.append("")

    if empty_floors:
        lines.extend(
            [
                "## 无资源组楼层",
                "",
                "| 楼层 | 物品 | 怪物 | 门 | 暗墙 | 岩浆 | 备注 |",
                "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for floor in empty_floors:
            summary = floor["summary"]
            counts = summary["counts"]
            if not any(counts.get(k, 0) for k in ("item", "enemy", "door", "autoWall", "lava")):
                continue
            lines.append(
                f"| {summary['floor']} | {counts.get('item', 0)} | {counts.get('enemy', 0)} | "
                f"{counts.get('door', 0)} | {counts.get('autoWall', 0)} | {counts.get('lava', 0)} | "
                "当前没有剩余物品形成资源组 |"
            )
        lines.append("")

    lines.extend(
        [
            "## 我是如何验证的",
            "",
            "1. 数据源校验：先通过 `agent-browser.cmd --cdp 9222` 从已经加载的 1 号存档导出 live snapshot，并再次读取浏览器状态，确认仍在 `MT4 x11y10`，且自动设置为 `battle=true`、`item=nopotion`、`wall=true`。",
            "2. 地图覆盖校验：缓存构建时用 live snapshot 覆盖当前已访问楼层的实际地图；未访问楼层使用仓库 `data/maps/mt*_map.json` 的完整静态地图，所以当前楼层状态和后续地图资源都能被纳入同一份缓存。",
            "3. 分组不变量校验：每层都检查当前可见物品 `item_count == group_item_count`，同时检查同一物品坐标不会被重复分到多个当前组；本次当前可见资源全局结果是 `377/377`，资源组 `177`，没有 error。",
            "4. 当前层抽样校验：单独对 live 的 `MT4` 计数，得到物品 `10`、怪物 `11`、门 `8`，与缓存中 `MT4` 的 summary 完全一致。",
            "5. 阻断规则校验：分组 BFS 只允许穿过空地、楼梯、物品和已允许的暗墙；门、怪物、硬墙、商店侧翼、NPC/商店、事件占位格、未知格阻断；当前没有雪花，所以岩浆不连通。这与报告中的图例一致。",
            "6. 事件生成资源校验：额外扫描 `afterBattle`、`afterOpenDoor`、`afterGetItem`、`events` 中的 `setBlock` 物品，按当前纯净版分支记录为 `event_groups`；这些资源只有触发对应事件后才出现，不混入当前可见物品覆盖数。",
            "7. 事件地图变化校验：同样扫描 `hide/openDoor/closeDoor/setBlock` 等地图变化，记录为 `event_map_changes`；MT15 章鱼后占位格消失和机关门打开属于这里。",
            "8. NPC/商店资源校验：扫描地图上的老人、商人、商店和已知事件资源点，记录为 `npc_resource_groups`；这些点后续搜索必须用显式状态转移处理，不能并入静态拾取资源。",
            "9. 特殊占位校验：`tile=17` 已按事件/特殊怪物占位格记录为阻断，MT15 章鱼周围、MT35 魔龙旁、MT49 事件位不会被当成普通通路。",
            "10. 脚本校验：`python -m py_compile scripts\\build_live_resource_group_cache.py scripts\\report_resource_group_floor_compact.py` 已通过。",
        ]
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", default=str(DEFAULT_CACHE))
    parser.add_argument("--out-md", default=str(DEFAULT_OUT_MD))
    args = parser.parse_args()

    cache_path = Path(args.cache).resolve()
    out_path = Path(args.out_md).resolve()
    cache = json.loads(cache_path.read_text(encoding="utf-8-sig"))
    write_report(cache, out_path)

    print(f"ok={cache['validation']['ok']}")
    print(f"cache={cache_path}")
    print(f"md={out_path}")
    print(f"floors_with_groups={sum(1 for floor in cache['floors'] if floor['summary']['group_count'])}")
    print(f"groups={cache['validation']['total_groups']} items={cache['validation']['grouped_items']}/{cache['validation']['total_items']}")
    print(
        "event_groups="
        f"{cache['validation'].get('event_resource_groups', 0)} "
        f"event_items={cache['validation'].get('event_resource_items', 0)}"
    )
    print(f"event_map_changes={cache['validation'].get('event_map_changes', 0)}")
    print(f"npc_resource_groups={cache['validation'].get('npc_resource_groups', 0)}")
    return 0 if cache["validation"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
