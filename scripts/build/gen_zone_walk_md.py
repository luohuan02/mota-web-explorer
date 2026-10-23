#!/usr/bin/env python3
"""从 Game 类输出 (auto_sweep) 重新生成人读 walk .md + summary。

把 `outputs/results/<zone>_game_route.json`（Game 类 auto ON，含 auto_sweep 隐式
击杀/拾取，金币正确）转成人读 .md，标注每步 auto_sweep 后的金币/属性 delta，
行末注明自动清理的怪/道具。action 行英文动词来自 game_route.ACTION_VERB_EN
（.md 仅供人读；实机 verifier live_zone3_mouse_replayer_cdp.js 读 walk JSON
按 pos 点击，不解析 action 字段）。

用法:
  python scripts/build/gen_zone_walk_md.py \
      --game-route-json outputs/results/zone1_game_route.json \
      --md best/current_best_boss_walk.md \
      --summary-json best/current_best_boss_summary.json \
      --zone 1 --old-final-gold 305

旧 .md 金币标注来自不含 auto_sweep 的旧 search（gen_best_current_boss_walk.py），
本生成器用 Game 类输出覆盖。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

import sys
sys.path.insert(0, str(ROOT))
from src.solver.game_route import (
    ACTION_VERB_EN,
    AUTO_KEYS,
    DOOR_KEY,
    FLOOR_TRANSITIONS,
    SKIP_ACTIONS,
    Game,
)
# action 英文名 / SKIP_ACTIONS / FLOOR_TRANSITIONS / DOOR_KEY / AUTO_KEYS /
# trigger-event 描述(Game.TRIGGER_EVENT_DESC) 全部从 game_route 导入，本文件
# 不手写任何游戏知识映射；新增 action/事件点只改 game_route 一处。


def state_text(s: dict[str, Any]) -> str:
    return (
        f"HP={s['hp']} ATK={s['atk']} DEF={s['def']} "
        f"YK={s['yk']} BK={s['bk']} RK={s['rk']} "
        f"G={s['gold']} dmg={s.get('dmg', 0)} "
        f"door={s.get('yd', 0)}/{s.get('bd', 0)}/{s.get('rd', 0)}"
    )


def delta_text(before: dict[str, Any], after: dict[str, Any]) -> str:
    pairs = [
        ("HP", before["hp"], after["hp"]),
        ("ATK", before["atk"], after["atk"]),
        ("DEF", before["def"], after["def"]),
        ("YK", before["yk"], after["yk"]),
        ("BK", before["bk"], after["bk"]),
        ("RK", before.get("rk", 0), after.get("rk", 0)),
        ("G", before["gold"], after["gold"]),
    ]
    parts = [f"{n} {b}->{a}" for n, b, a in pairs if b != a]
    return ", ".join(parts)


def clone_state(s: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(s))


def gold_gain(eid: str, before_gold: int, after_gold: int) -> int:
    """该步金币增量（含 auto_sweep 隐式击杀）。"""
    return after_gold - before_gold


def extract_clear_note(note: str) -> tuple[str, str] | None:
    """从 step.note 提取清理列表，返回 (label, list_str)。

    - `auto_sweep:` / `auto:` 都是 0 伤自动清（auto_sweep BFS），label='auto'。
      Game 类 go_to 在不同分支写这两种前缀（路径内击杀折叠写 `auto:`，其余写
      `auto_sweep:`）；一条 note 可能含多段，全部合并，否则 `auto:` 段会漏显。
    - `动态清:`（clearMt10BossDyn）是 boss 战显式逐个击杀（带伤害，非 0 伤），
      label='boss'，不能混成 auto。
    """
    if not note:
        return None
    i = note.find("动态清:")
    if i >= 0:
        rest = note[i + len("动态清:"):].strip()
        for sep in (";", "；"):
            j = rest.find(sep)
            if j >= 0:
                rest = rest[:j]
        return ("boss", rest.strip().rstrip(","))
    auto_parts: list[str] = []
    for marker in ("auto_sweep:", "auto:"):
        start = 0
        while True:
            k = note.find(marker, start)
            if k < 0:
                break
            rest = note[k + len(marker):].strip()
            for sep in (";", "；"):
                j = rest.find(sep)
                if j >= 0:
                    rest = rest[:j]
            rest = rest.strip().rstrip(",")
            if rest:
                auto_parts.append(rest)
            start = k + len(marker)
    if auto_parts:
        return ("auto", ", ".join(auto_parts))
    return None


def collect_following_arrives(steps: list[dict[str, Any]], start_idx: int) -> list[dict[str, Any]]:
    """Collect immediate hidden ARRIVE steps after the current visible step.

    These usually mean "the path became reachable and the route later walked
    through it", not "the current click auto-picked everything immediately".
    """
    arrived: list[dict[str, Any]] = []
    for step in steps[start_idx + 1:]:
        action = step.get("action")
        if action == "到达":
            arrived.append(step)
            continue
        if action in FLOOR_TRANSITIONS:
            break
        if action in SKIP_ACTIONS:
            continue
        break
    return arrived


def deferred_auto_after(step: dict[str, Any], following_arrives: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Return the state to display after a trigger step before auto resolves.

    Some live strict walks already contain the post-auto state on the trigger
    step. For readability, show event-open/resource-spawn effects on the next
    movement step, because that is when h5mota actually runs auto-BFS.
    """
    if not following_arrives:
        return None
    action = step.get("action")
    before = step["before"]
    after = step["after"]
    display = clone_state(after)
    changed = False
    if action == "击杀":
        for key in ("atk", "def", "yk", "bk", "rk"):
            if before.get(key) != after.get(key):
                display[key] = before.get(key, 0)
                changed = True
    elif action == "开门":
        eid = step.get("eid")
        kk = DOOR_KEY.get(eid)
        for stat in ("atk", "def", "yk", "bk", "rk"):
            if before.get(stat) != after.get(stat):
                display[stat] = before.get(stat, 0)
                changed = True
        if kk:
            display[kk[0]] = before.get(kk[0], 0) - 1
    if not changed:
        return None
    return display


def auto_suffix_from_step(step: dict[str, Any], following_arrives: list[dict[str, Any]]) -> str:
    clear = extract_clear_note(step.get("note", ""))
    if clear and clear[0] == "auto":
        return f"(auto: {clear[1]})"
    if following_arrives:
        reached = ", ".join(
            f"{s['floor']} x{s['pos'][0]}y{s['pos'][1]}" for s in following_arrives
        )
        return f"(auto: after previous map change -> {reached})"
    return "(auto: resource group on move)"


def action_line(step: dict[str, Any]) -> str | None:
    """生成 .md action 行；返回 None 表示跳过（换层/飞行/到达 等）。"""
    action = step["action"]
    eid = step.get("eid") or ""
    pos = step["pos"]
    fid = step["floor"]

    if action == "设置自动":
        spec = fmt_auto_config(step.get("auto") or step.get("setAuto") or step.get("autoSpec"))
        return f"- {fid} x{pos[0]}y{pos[1]} 设置自动：{spec or '未指定'}"

    if action == "事件" and eid == "bossEvent":
        return f"- {fid} x{pos[0]}y{pos[1]} trigger boss event"
    if action in SKIP_ACTIONS:
        return None
    # 中->英动词表在 game_route.ACTION_VERB_EN（含 zone2+ 适配层 action）；
    # 未登记的 action fallback 中文——新 action 应在 ACTION_VERB_EN 登记。
    verb = ACTION_VERB_EN.get(action, action)
    # eid 必须是 [A-Za-z0-9_:]+ 才能被 parseWalk 解析（zone1 replayer）；含冒号的
    # 商店 eid（blueShop:attack）也保留。中文 eid 不会出现在 Game 类输出。
    return f"- {fid} x{pos[0]}y{pos[1]} {verb} {eid}".rstrip()


def should_emit_arrive(step: dict[str, Any], delta_before: dict[str, Any]) -> bool:
    if step.get("action") != "到达":
        return True
    if delta_text(delta_before, step["after"]):
        return True
    note = step.get("note", "")
    return "resource" in note or "after special doors" in note or "seed" in note


def fmt_score(v: float) -> str:
    return str(int(v)) if abs(v - int(v)) < 1e-9 else f"{v:.1f}"


def fmt_auto_config(auto: Any) -> str | None:
    """把 walk JSON 的 `auto` 字段格式化为人读字符串。

    `{"battle": true, "item": "nopotion", "wall": true}` -> `battle=true, item=nopotion, wall=true`
    """
    if not isinstance(auto, dict) or not auto:
        return None
    parts = []
    for k in AUTO_KEYS:
        if k in auto:
            v = auto[k]
            if isinstance(v, bool):
                parts.append(f"{k}={'true' if v else 'false'}")
            else:
                parts.append(f"{k}={v}")
    return ", ".join(parts) if parts else None


def gen_md(
    game_route: dict[str, Any],
    zone: int,
    old_final_gold: int | None,
    summary: dict[str, Any] | None,
    md_start_step: int = 1,
    prefix_ref: str | None = None,
    auto_config: str | None = None,
    source_json_ref: str | None = None,
    verify_command: str | None = None,
    derivation: str | None = None,
) -> str:
    steps = game_route["steps"]
    if md_start_step < 1:
        raise ValueError("--md-start-step must be >= 1")
    md_steps = steps[md_start_step - 1:]
    final = game_route["final"]
    new_gold = final["gold"]

    lines: list[str] = []
    lines.append(f"# 当前最优 Walk (zone{zone}, auto ON)")
    if md_start_step > 1:
        ref = f"`{prefix_ref}`" if prefix_ref else "the prefix walk"
        lines.append(
            f"- Markdown expands JSON steps from step {md_start_step}; earlier steps reuse {ref}. "
            "The exported JSON remains fully stitched for replay."
        )
    lines.append("")
    lines.append("## 说明")
    lines.append("")
    if derivation:
        lines.append(f"- {derivation}")
    else:
        lines.append(f"- 本 walk 由 Game 类 (`scripts/search/zone{zone}_game_route.py`, "
                    f"auto_sweep, strict_live_model) 离线推导生成。")
    auto_cfg = auto_config or "battle/item/wall 全开"
    lines.append(f"- auto 配置：{auto_cfg}。金币/属性标注为 **auto_sweep 后**"
                "的实机值（含自动击杀/拾取的零伤怪/道具/暗墙）。")
    lines.append("- 显式动作 (open/kill/take/pass/trigger) 由玩家点击触发；隐式/压缩清理在"
                "行末注明：`(auto: ...)` = auto_sweep 清的零伤怪/道具/暗墙；"
                "`(boss 动态清: ...)` = 10F boss 战显式逐杀（带伤害，非 0 伤，HP delta 可见）。")
    lines.append("- 部分自动击杀 Game 类 note 未详（金币已计入 delta，行末标 `(auto: +NG)`）。")
    if verify_command:
        lines.append(f"- 实机验证：`{verify_command}`")
    else:
        lines.append("- 实机验证：`node scripts/live/live_zone3_mouse_replayer_cdp.js "
                    f"--walk outputs/results/zone{zone}_game_route.json --load-slot <100+> "
                    "--target-click-only`（统一点击 verifier，1-4 区通用；3 区起按需 "
                    "`--set-auto battle=true,item=nopotion,wall=true`）")
    src_ref = source_json_ref or f"outputs/results/zone{zone}_game_route.json"
    lines.append(f"- 源 JSON：`{src_ref}`")
    if old_final_gold is not None and old_final_gold != new_gold:
        delta = new_gold - old_final_gold
        lines.append(f"- 旧 .md 标注 G={old_final_gold} 已废弃；新 G={new_gold}，"
                    f"差 {'+' if delta>=0 else ''}{delta}G 来自 auto_sweep 隐式击杀。")
    lines.append("")

    # 摘要
    lines.append("## 摘要")
    lines.append("")
    lines.append(f"- final: {state_text(final)} {final['floor']} x{final['x']}y{final['y']}")
    if summary and summary.get("final_score") is not None:
        old_score = summary["final_score"]
        if old_final_gold is not None:
            new_score = old_score + (new_gold - old_final_gold) * 1.0
        else:
            new_score = old_score
        lines.append(f"- final-score: {fmt_score(new_score)} (旧 {fmt_score(old_score)}"
                    f"{f' + {new_gold-old_final_gold}G*1.0' if old_final_gold and new_gold!=old_final_gold else ''})")
    lines.append("")

    # Walk
    lines.append("## Walk")
    lines.append("")

    cur_floor = None
    prev_after: dict[str, Any] | None = None
    pending_auto_suffix: str | None = None

    def close_floor(after_state):
        if cur_floor is not None:
            lines.append(f"- after: {state_text(after_state)}")
            lines.append("")

    for local_idx, step in enumerate(md_steps):
        idx = md_start_step + local_idx
        fid = step["floor"]
        after = step["after"]
        before = step["before"]
        # delta 基线用上一条已发出步的 after（prev_after），而非本步 before。正常
        # 步 before==prev_after，无影响；但 Game 类 go_to 的延迟 auto_sweep 会把
        # 本步移动中清的零伤怪/道具折进本步 `before`（before==after，步内 delta
        # 为空），用 prev_after 才能把这段 gap auto 计入本步 delta 并避免被
        # should_emit_arrive 当空步抑制（如 MT8 x5y4 到达拾 3 把 yk）。这不是
        # "把上一点击副作用迁移到下一条 move"：gap auto 本就是本步移动的产物，
        # 只是 Game 把它记到了 before；prev_after 把它归位到本步。
        delta_before = prev_after if prev_after is not None else before
        following_arrives: list[dict[str, Any]] = []
        display_after = after
        line = action_line(step)
        if line is None or not should_emit_arrive(step, delta_before):
            prev_after = display_after
            continue
        if fid != cur_floor:
            close_floor(prev_after if prev_after is not None else before)
            cur_floor = fid
            lines.append(f"### {fid}")
            lines.append("")
            lines.append(f"- before: {state_text(delta_before)}")
        delta = delta_text(delta_before, display_after)
        g_gain = display_after["gold"] - delta_before["gold"]
        suffix_parts = []
        if delta:
            suffix_parts.append(f"[{delta}]")
        if pending_auto_suffix:
            suffix_parts.append(pending_auto_suffix)
            pending_auto_suffix = None
        clear = extract_clear_note(step.get("note", ""))
        if clear:
            label, lst = clear
            if label == "auto":
                # 击杀步的 auto 列表剔除被杀目标本身：它是本步点击目标，不是
                # 附带清理（如 MT11 x9y11 bigBat 被 auto 列为 x9y11 bigBat）。
                if step.get("action") == "击杀" and step.get("pos"):
                    tgt = f"x{step['pos'][0]}y{step['pos'][1]} "
                    items = [s.strip() for s in lst.split(",") if s.strip()]
                    items = [it for it in items if not it.startswith(tgt)]
                    lst = ", ".join(items)
                if lst:
                    if following_arrives:
                        pending_auto_suffix = f"(auto: {lst})"
                    else:
                        suffix_parts.append(f"(auto: {lst})")
            else:
                # boss 动态清是带伤害的显式逐杀（非 0 伤 auto），分开标
                suffix_parts.append(f"(boss 动态清: {lst})")
        elif step.get("action") == "到达" and delta:
            # 到达步有 delta 但 note 无 auto 列表（罕见，如延迟事件副作用）：
            # 标注资源组在移动中变化，避免 delta 无解释。有 actual auto 列表时
            # 上面已处理，不会落到这里。
            suffix_parts.append("(auto: resource group on move)")
        elif g_gain > 0 and step["action"] not in ("击杀",):
            # 金币增加但非显式击杀 -> auto_sweep 隐式击杀（Game 类 note 未详）
            suffix_parts.append(f"(auto: +{g_gain}G)")
        if "trigger-event" in (step.get("note", "") or ""):
            # 事件 trigger pass: hero 踩格触发楼层事件（spawn/移动/开门），converter
            # 标 trigger-event。加人读描述让人知道为何走该格（非普通路过）。
            _desc = Game.TRIGGER_EVENT_DESC.get((fid, (step["pos"][0], step["pos"][1])))
            suffix_parts.append(f"(触发: {_desc})" if _desc else "(触发事件)")
        suffix = " " + " ".join(suffix_parts) if suffix_parts else ""
        # gain_tag 只给显式击杀标（敌人金币）；非击杀步的金币增量已在 (auto: +NG) 里
        gain_tag = f" (+{g_gain}G)" if g_gain > 0 and step["action"] == "击杀" else ""
        lines.append(f"{line}{suffix}{gain_tag}")
        if display_after is not after and pending_auto_suffix is None:
            pending_auto_suffix = auto_suffix_from_step(step, following_arrives)
        prev_after = display_after
    close_floor(prev_after)

    return "\n".join(lines).rstrip() + "\n"


def update_summary(summary: dict[str, Any], final: dict[str, Any],
                   old_final_gold: int | None) -> dict[str, Any]:
    if isinstance(summary, list):
        out = json.loads(json.dumps(summary))
        target = None
        for row in out:
            if str(row.get("label", "")).startswith("best_after_mt10_boss_supply"):
                target = row
                break
        if target is None and out:
            target = out[-1]
        if target is not None:
            dst = target.setdefault("final", {})
            for key in ("hp", "atk", "def", "yk", "bk", "rk", "gold", "floor", "x", "y", "dmg", "yd", "bd", "rd"):
                if key in final:
                    dst[key] = final[key]
        return out

    out = json.loads(json.dumps(summary)) if summary else {"summary": {}}
    s = out.get("summary")
    if not isinstance(s, dict):
        s = {}
    old_gold = s.get("gold")
    s["hp"] = final["hp"]
    s["atk"] = final["atk"]
    s["def"] = final["def"]
    s["yk"] = final["yk"]
    s["bk"] = final["bk"]
    s["rk"] = final["rk"]
    s["gold"] = final["gold"]
    s["dmg"] = final.get("dmg", s.get("dmg", 0))
    s["yd"] = final.get("yd", s.get("yd", 0))
    s["bd"] = final.get("bd", s.get("bd", 0))
    s["rd"] = final.get("rd", s.get("rd", 0))
    if old_gold is not None and s.get("final_score") is not None:
        s["final_score"] = s["final_score"] + (final["gold"] - old_gold) * 1.0
    if "summary" not in out:
        out["summary"] = s
    else:
        out["summary"] = s
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--game-route-json", type=Path, required=True)
    ap.add_argument("--md", type=Path, required=True)
    ap.add_argument("--summary-json", type=Path, default=None)
    ap.add_argument("--walk-out-json", type=Path, default=None,
                    help="把 Game 类 JSON 拷到 best/ 供 zone3 replayer")
    ap.add_argument("--zone", type=int, default=1)
    ap.add_argument("--old-final-gold", type=int, default=None,
                    help="旧 .md final gold（算 delta 用；不传则不显示差值）")
    ap.add_argument("--md-start-step", type=int, default=1,
                    help="1-based first JSON step to expand in Markdown; JSON output remains complete")
    ap.add_argument("--prefix-ref", default=None,
                    help="Reference text for skipped Markdown prefix")
    ap.add_argument("--verify-command", default=None,
                    help="实机验证命令（覆盖默认 replayer 行）；用于 strict / 非 default auto 变体")
    ap.add_argument("--derivation", default=None,
                    help="覆盖头部「本 walk 由 ... 生成」说明（不含前导 '- '）")
    args = ap.parse_args()

    game_route = json.loads(args.game_route_json.read_text(encoding="utf-8"))
    summary = None
    if args.summary_json and args.summary_json.exists():
        summary = json.loads(args.summary_json.read_text(encoding="utf-8"))

    summary_for_md = None
    if isinstance(summary, dict):
        summary_for_md = summary.get("summary", summary)
    # 破墙 等 action 不再归一化：replayer 只按 pos 点击不解析 action，
    # .md 英文动词由 ACTION_VERB_EN 映射（破墙->pass）。
    live_route = game_route
    auto_config = fmt_auto_config(game_route.get("auto"))
    source_json_ref = args.game_route_json.as_posix()
    md_text = gen_md(
        live_route,
        args.zone,
        args.old_final_gold,
        summary_for_md,
        md_start_step=args.md_start_step,
        prefix_ref=args.prefix_ref,
        auto_config=auto_config,
        source_json_ref=source_json_ref,
        verify_command=args.verify_command,
        derivation=args.derivation,
    )
    args.md.parent.mkdir(parents=True, exist_ok=True)
    args.md.write_text(md_text, encoding="utf-8")
    print(f"wrote {args.md} ({len(md_text.splitlines())} lines)")

    if args.summary_json:
        new_summary = update_summary(
            summary, game_route["final"], args.old_final_gold)
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(
            json.dumps(new_summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {args.summary_json} (gold={game_route['final']['gold']})")

    if args.walk_out_json:
        args.walk_out_json.parent.mkdir(parents=True, exist_ok=True)
        args.walk_out_json.write_text(
            json.dumps(live_route, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote {args.walk_out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
