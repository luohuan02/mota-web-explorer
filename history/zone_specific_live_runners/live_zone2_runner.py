#!/usr/bin/env python3
"""Run the zone-2 best walk in the live h5mota browser with state checks."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ROUTE_JSON = ROOT / "outputs" / "results" / "zone2_guide_route_replay.json"
LABEL = "best_after_mt10_boss_supply"
IGNORE_LOC_ACTIONS = {"商店", "换层", "传送", "开门", "对话", "事件", "商人", "事件开门", "事件奖励"}

STATE_JS = r"""
(() => {
  const h = core.status.hero || {};
  const loc = h.loc || {};
  const tools = h.items?.tools || {};
  const constants = h.items?.constants || {};
  const ev = core.status.event || {};
  return {
    floor: core.status.floorId,
    x: loc.x,
    y: loc.y,
    hp: h.hp,
    atk: h.atk,
    def: h.def,
    money: h.money,
    yk: tools.yellowKey || 0,
    bk: tools.blueKey || 0,
    rk: tools.redKey || 0,
    constants,
    lock: !!core.status.lockControl,
    eventId: ev.id || null,
    eventUi: ev.ui || null,
    selection: ev.selection ?? null
  };
})()
"""
ADJUSTABLE_KEYS = ("hp", "atk", "def", "money", "yk", "bk", "rk")

CLICK_JS = r"""(function(){var target={x:%d,y:%d};var draw=main.dom.gameDraw, group=main.dom.gameGroup;var size=32*core.domStyle.scale;var left=draw.offsetLeft+group.offsetLeft, top=draw.offsetTop+group.offsetTop;var clientX=left+(target.x-0.5)*size, clientY=top+(target.y-0.5)*size;var loc=core.actions._getClickLoc(clientX,clientY);var tile={x:Math.floor(loc.x/loc.size)+1,y:Math.floor(loc.y/loc.size)+1};var actionPx=target.x*32+16-core.bigmap.offsetX;var actionPy=target.y*32+16-core.bigmap.offsetY;var down=(core.actions.actions.ondown||[]).find(function(a){return a.name==="_sys_ondown";});var up=(core.actions.actions.onup||[]).find(function(a){return a.name==="_sys_onup";});if(tile.x!==target.x||tile.y!==target.y)return false;if(!down||!up)return false;down.func.call(core.actions,target.x,target.y,actionPx,actionPy);up.func.call(core.actions,target.x,target.y,actionPx,actionPy);return true;})()"""


def route_state(step_state: dict[str, Any]) -> dict[str, Any]:
    return {
        "floor": step_state["floor"],
        "x": step_state["x"],
        "y": step_state["y"],
        "hp": step_state["hp"],
        "atk": step_state["atk"],
        "def": step_state["def"],
        "money": step_state["gold"],
        "yk": step_state["yk"],
        "bk": step_state["bk"],
        "rk": step_state["rk"],
    }


def state_text(state: dict[str, Any]) -> str:
    return (
        f"{state.get('floor')} x{state.get('x')}y{state.get('y')} "
        f"HP={state.get('hp')} ATK={state.get('atk')} DEF={state.get('def')} "
        f"YK={state.get('yk')} BK={state.get('bk')} RK={state.get('rk')} G={state.get('money')}"
        f" lock={state.get('lock')} event={state.get('eventId')} ui={state.get('eventUi')}"
    )


class Browser:
    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        # 附加到外部启动的 chrome(真实端口 9222 + browser-profile),不要用 --cdp flag。
        subprocess.run(["agent-browser.cmd", "connect", "9222"], cwd=str(ROOT),
                       capture_output=True, timeout=10)

    def _run(self, args: list[str], timeout: int = 30) -> str:
        cmd = ["agent-browser.cmd", *args]
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            timeout=timeout,
        )
        out = proc.stdout.decode("utf-8", errors="replace")
        err = proc.stderr.decode("utf-8", errors="replace")
        if proc.returncode != 0:
            raise RuntimeError(err.strip() or out.strip() or f"command failed: {cmd}")
        return out.strip()

    def eval(self, js: str, timeout: int = 30) -> Any:
        payload = base64.b64encode(js.encode("utf-8")).decode("ascii")
        out = self._run(["eval", "-b", payload], timeout=timeout)
        if not out:
            return None
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return out

    def press(self, key: str, delay: float = 0.08) -> None:
        self._run(["press", key], timeout=10)
        if delay:
            time.sleep(delay)

    def state(self) -> dict[str, Any]:
        return self.eval(STATE_JS)

    def backup_memory(self) -> None:
        self.eval(
            "(() => { window.__codex_live_backup = core.control.saveData(null); return true; })()"
        )

    def restore_memory(self) -> None:
        self.eval(
            "(() => { if (!window.__codex_live_backup) return false; core.loadData(window.__codex_live_backup, null); return true; })()"
        )
        time.sleep(0.5)

    def save_slot(self, slot: int) -> bool:
        return bool(
            self.eval(
                f"""new Promise(resolve => {{
  const data = core.control.saveData(null);
  core.utils.setLocalForage('save{slot}', data, () => resolve(true));
  setTimeout(() => resolve(false), 2000);
}})""",
                timeout=5,
            )
        )

    def load_slot(self, slot: int) -> bool:
        ok = bool(
            self.eval(
                f"""new Promise(resolve => {{
  core.getSave({slot}, data => {{
    if (!data) return resolve(false);
    core.loadData(data, null);
    setTimeout(() => resolve(true), 600);
  }});
  setTimeout(() => resolve(false), 3000);
}})""",
                timeout=5,
            )
        )
        if ok:
            time.sleep(0.8)
        return ok

    def fly_to(self, floor: str) -> None:
        self.eval(
            f"""(() => {{
  if (core.status.floorId === {json.dumps(floor)}) return true;
  return core.flyTo({json.dumps(floor)});
}})()"""
        )
        self.wait(lambda s: s.get("floor") == floor, timeout=8, desc=f"fly to {floor}")

    def move_to(
        self,
        x: int,
        y: int,
        expected_floor: str | None = None,
        allow_no_arrive: bool = False,
    ) -> None:
        keys = {"right": "ArrowRight", "left": "ArrowLeft", "down": "ArrowDown", "up": "ArrowUp"}
        # 检测目标 noPass(商店/NPC),noPass 则走到相邻再点击触发
        no_pass = bool(self.eval(f"core.noPass({x}, {y}, core.status.floorId)"))
        tx, ty = x, y
        if no_pass:
            for ax, ay in [(x, y + 1), (x, y - 1), (x + 1, y), (x - 1, y)]:
                try:
                    if not bool(self.eval(f"core.noPass({ax}, {ay}, core.status.floorId)")):
                        tx, ty = ax, ay
                        break
                except Exception:
                    continue
        # press 方向键逐步到 (tx,ty);_sys_ondown 远距不寻路,press 逐步寻路
        for _ in range(80):
            state = self.state()
            # 换层成功(floor 变)立即 break,不管 x/y(下楼点 ≠ 楼梯 pos,避免徘徊)
            if expected_floor and state.get("floor") == expected_floor:
                break
            if state.get("x") == tx and state.get("y") == ty:
                if expected_floor is None or state.get("floor") == expected_floor:
                    break
                # 在楼梯但 floor 不对,等自动上楼,不要 press
                time.sleep(0.3)
                continue
            if state.get("lock") or state.get("eventId"):
                break
            if state.get("moving"):
                time.sleep(0.1)
                continue
            dx = tx - int(state["x"])
            dy = ty - int(state["y"])
            if dx == 0 and dy == 0:
                break
            before = (state["x"], state["y"])
            d = "right" if dx > 0 else "left" if dx < 0 else "down" if dy > 0 else "up"
            self.press(keys[d], delay=0.15)
            time.sleep(0.3)
            s2 = self.state()
            if (s2["x"], s2["y"]) == before and not s2.get("lock") and not s2.get("eventId"):
                # blocked,试另一轴
                if dx != 0 and dy != 0:
                    d2 = "down" if dy > 0 else "up"
                else:
                    d2 = "right" if dx > 0 else "left"
                self.press(keys[d2], delay=0.15)
                time.sleep(0.3)
        # noPass 目标,点击触发交互(英雄已在相邻)
        if no_pass:
            self.eval(CLICK_JS % (x, y))
            time.sleep(0.3)
        if expected_floor:
            self.wait(lambda s: s.get("floor") == expected_floor, timeout=10, desc=f"floor {expected_floor}")
        elif not allow_no_arrive:
            try:
                self.wait(lambda s: (s.get("x"), s.get("y")) == (x, y) or s.get("lock"), timeout=8, desc=f"x{x}y{y}")
            except RuntimeError:
                pass

    def step_into(self, direction: str, expected_floor: str | None = None) -> None:
        key = {
            "up": "ArrowUp",
            "down": "ArrowDown",
            "left": "ArrowLeft",
            "right": "ArrowRight",
        }[direction]
        self.press(key, delay=0.12)
        if expected_floor:
            self.wait(lambda s: s.get("floor") == expected_floor, timeout=8, desc=f"step {direction} to {expected_floor}")
        else:
            time.sleep(0.25)

    def wait(self, pred, timeout: float, desc: str) -> dict[str, Any]:
        end = time.time() + timeout
        last = None
        while time.time() < end:
            last = self.state()
            if pred(last):
                return last
            time.sleep(0.12)
        raise RuntimeError(f"timeout waiting for {desc}; last={state_text(last or {})}")

    def close_dialogs(self, max_presses: int = 12) -> dict[str, Any]:
        state = self.state()
        for _ in range(max_presses):
            if not state.get("lock") and not state.get("eventId") and not state.get("eventUi"):
                return state
            self.press("Enter", delay=0.12)
            state = self.state()
        return state

    def choose_menu_index(self, target: int) -> None:
        state = self.state()
        ui = state.get("eventUi") or {}
        choices = ui.get("choices") or []
        if not choices:
            self.press("Enter", delay=0.15)
            return
        offset = ui.get("offset")
        try:
            current = int(offset)
        except (TypeError, ValueError):
            current = 0
        for _ in range((target - current) % len(choices)):
            self.press("ArrowDown", delay=0.05)
        self.press("Enter", delay=0.2)

    def insert_current_choice(self, target: int) -> None:
        result = self.eval(
            f"""(() => {{
  const ui = core.status.event && core.status.event.ui;
  if (!ui || !ui.choices || !ui.choices[{target}]) {{
    return {{ ok: false, eventId: core.status.event?.id || null, ui }};
  }}
  core.insertAction(ui.choices[{target}].action);
  core.doAction();
  return {{ ok: true }};
}})()"""
        )
        if not result or not result.get("ok"):
            raise RuntimeError(f"cannot insert choice {target}: {result}")
        time.sleep(0.2)

    def leave_choice_menu(self) -> None:
        state = self.state()
        if not state.get("lock") and not state.get("eventUi"):
            return
        self.insert_current_choice(3)
        self.wait(lambda s: not s.get("lock"), timeout=5, desc="leave shop")


class Runner:
    def __init__(
        self,
        browser: Browser,
        max_step: int | None,
        checkpoint_slot: int | None,
        initial_adjust: dict[str, int] | None = None,
    ) -> None:
        self.browser = browser
        self.max_step = max_step
        self.checkpoint_slot = checkpoint_slot
        self.steps = self.load_steps()
        self.adjust = {key: 0 for key in ADJUSTABLE_KEYS}
        if initial_adjust:
            self.adjust.update(initial_adjust)

    def load_steps(self) -> list[dict[str, Any]]:
        data = json.loads(ROUTE_JSON.read_text(encoding="utf-8"))
        result = next(r for r in data["results"] if r["label"] == LABEL)
        return result["steps"]

    def live_matches(self, live: dict[str, Any], expected: dict[str, Any], ignore_loc: bool = False) -> bool:
        for key, value in expected.items():
            if ignore_loc and key in {"x", "y"}:
                continue
            if live.get(key) != value:
                return False
        return True

    def expected(self, idx: int, when: str = "after") -> dict[str, Any]:
        state = route_state(self.steps[idx][when])
        for key, delta in self.adjust.items():
            state[key] += delta
        return state

    def find_start_index(self) -> int:
        live = self.browser.state()
        matches = []
        for idx, step in enumerate(self.steps):
            if self.live_matches(live, self.expected(idx)):
                matches.append(idx)
            elif step["action"] in IGNORE_LOC_ACTIONS and self.live_matches(
                live, self.expected(idx), ignore_loc=True
            ):
                matches.append(idx)
        if matches:
            idx = matches[-1]
            print(f"resume after step {idx}: {state_text(live)}", flush=True)
            return idx + 1
        raise RuntimeError(f"live state does not match any route checkpoint: {state_text(live)}")

    def validate(self, idx: int, allow_locked: bool = False, ignore_loc: bool = False) -> dict[str, Any]:
        expected = self.expected(idx)
        live = self.browser.wait(
            lambda s: self.live_matches(s, expected, ignore_loc=ignore_loc),
            timeout=6,
            desc=f"step {idx} expected",
        )
        if live.get("lock") and not allow_locked:
            live = self.browser.close_dialogs()
            if not self.live_matches(live, expected, ignore_loc=ignore_loc):
                raise RuntimeError(
                    f"step {idx} changed while closing dialog; expected={expected} live={state_text(live)}"
                )
        return live

    def buy_shop_attack(self, idx: int) -> None:
        step = self.steps[idx]
        before = self.expected(idx, "before")
        state = self.browser.state()
        if not state.get("lock"):
            # x6y9 商店 noPass,move_to 自动走相邻 + 点击触发
            self.browser.move_to(6, 9)
            self.browser.wait(
                lambda s: bool((s.get("eventUi") or {}).get("choices")),
                timeout=8,
                desc="open 12F shop choices",
            )
        self.browser.insert_current_choice(1)
        next_is_shop = idx + 1 < len(self.steps) and self.steps[idx + 1]["action"] == "商店"
        self.validate(idx, allow_locked=True, ignore_loc=True)
        if not next_is_shop:
            self.browser.insert_current_choice(3)
            self.browser.wait(lambda s: not s.get("lock"), timeout=5, desc="leave 12F shop")

    def buy_merchant(self, idx: int) -> None:
        step = self.steps[idx]
        floor = step["floor"]
        x, y = step["pos"]
        state = self.browser.state()
        if state.get("floor") != floor:
            self.browser.fly_to(floor)
        self.browser.move_to(x, y, allow_no_arrive=True)
        self.browser.wait(lambda s: s.get("lock") or self.live_matches(s, self.expected(idx)), timeout=5, desc="merchant prompt")
        if not self.live_matches(self.browser.state(), self.expected(idx)):
            self.browser.press("Enter", delay=0.3)
        self.validate(idx, ignore_loc=True)

    def maybe_open_mt1_left_access(self, idx: int) -> None:
        step = self.steps[idx]
        if step["floor"] != "MT1" or tuple(step["pos"]) != (2, 4):
            return
        probe = self.browser.eval(
            """(() => ({
  floor: core.status.floorId,
  canTarget: core.canMoveDirectly(2, 4),
  door: core.getBlockId(4, 3),
  yk: core.status.hero.items.tools.yellowKey || 0
}))()"""
        )
        if probe.get("canTarget", -1) >= 0 or probe.get("door") != "yellowDoor":
            return
        before = self.browser.state()
        self.browser.move_to(4, 3, allow_no_arrive=True)
        self.browser.wait(
            lambda s: s.get("yk") == before.get("yk") - 1,
            timeout=6,
            desc="open MT1 x4y3 extra yellow door",
        )
        self.adjust["yk"] -= 1
        print("  note opened extra MT1 x4y3 yellowDoor; expected YK offset now -1", flush=True)

    def maybe_pick_event_reward(self, idx: int) -> bool:
        step = self.steps[idx]
        if step["action"] != "事件奖励":
            return False
        if step["floor"] == "MT14" and step.get("eid") == "redKey":
            probe = self.browser.eval("(() => ({ block: core.getBlockId(1, 3) }))()")
            if probe.get("block") == "redKey":
                self.browser.move_to(1, 3)
            self.validate(idx, ignore_loc=True)
            return True
        self.validate(idx, ignore_loc=True)
        return True

    def nudge_adjacent_if_needed(self, x: int, y: int) -> None:
        state = self.browser.state()
        if state.get("floor") != self.steps[self.current_idx]["floor"]:
            return
        if (state.get("x"), state.get("y")) == (x, y):
            return
        dx = x - int(state["x"])
        dy = y - int(state["y"])
        if abs(dx) + abs(dy) != 1:
            return
        direction = "right" if dx == 1 else "left" if dx == -1 else "down" if dy == 1 else "up"
        self.browser.step_into(direction)

    def execute_step(self, idx: int) -> None:
        step = self.steps[idx]
        self.current_idx = idx
        action = step["action"]
        floor = step["floor"]
        x, y = step["pos"]
        expected_after = self.expected(idx)
        state = self.browser.state()
        if self.live_matches(state, expected_after):
            return

        if state.get("lock") and action != "商店":
            self.browser.close_dialogs()

        if action == "商店":
            self.buy_shop_attack(idx)
            return
        if action == "商人":
            self.buy_merchant(idx)
            return
        if action == "事件奖励":
            self.maybe_pick_event_reward(idx)
            return
        if action == "事件开门":
            self.validate(idx, ignore_loc=True)
            return
        if action == "传送":
            try:
                self.browser.fly_to(floor)
            except RuntimeError:
                if floor != "MT15":
                    raise
                self.browser.fly_to("MT14")
                self.browser.move_to(6, 10)
                self.browser.step_into("down", expected_floor="MT15")
            self.validate(idx, ignore_loc=True)
            return
        if action == "换层":
            if state.get("floor") == expected_after["floor"]:
                self.validate(idx, ignore_loc=True)
                return
            self.browser.move_to(x, y, expected_floor=expected_after["floor"])
            self.validate(idx, ignore_loc=True)
            return

        state = self.browser.state()
        if state.get("floor") != floor:
            self.browser.fly_to(floor)
        self.maybe_open_mt1_left_access(idx)
        ignore_loc = action in IGNORE_LOC_ACTIONS
        self.browser.move_to(x, y, allow_no_arrive=ignore_loc)
        if action == "通过":
            self.nudge_adjacent_if_needed(x, y)
        if action in {"对话", "事件"}:
            self.browser.close_dialogs()
        self.validate(idx, ignore_loc=ignore_loc)

    def maybe_checkpoint(self, idx: int, prev_segment: str | None) -> str:
        segment = self.steps[idx]["segment"]
        if prev_segment and segment != prev_segment and self.checkpoint_slot is not None:
            ok = self.browser.save_slot(self.checkpoint_slot)
            print(f"checkpoint slot {self.checkpoint_slot}: {prev_segment} ok={ok}", flush=True)
            self.checkpoint_slot += 1
        return segment

    def run(self) -> None:
        start = self.find_start_index()
        prev_segment = self.steps[start - 1]["segment"] if start > 0 else None
        end = len(self.steps) if self.max_step is None else min(len(self.steps), self.max_step + 1)
        for idx in range(start, end):
            step = self.steps[idx]
            prev_segment = self.maybe_checkpoint(idx, prev_segment)
            self.browser.backup_memory()
            saved_adjust = dict(self.adjust)
            print(
                f"step {idx:03d} {step['segment']} {step['floor']} x{step['pos'][0]}y{step['pos'][1]} "
                f"{step['action']} {step.get('eid') or ''}",
                flush=True,
            )
            try:
                self.execute_step(idx)
            except Exception:
                try:
                    self.browser.restore_memory()
                finally:
                    self.adjust = saved_adjust
                    raise
            live = self.browser.state()
            print("  ok " + state_text(live), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-step", type=int, default=None)
    parser.add_argument("--checkpoint-slot", type=int, default=None)
    parser.add_argument("--load-slot", type=int, default=None)
    parser.add_argument("--yk-offset", type=int, default=0)
    parser.add_argument("--money-offset", type=int, default=0)
    args = parser.parse_args()

    browser = Browser()
    if args.load_slot is not None:
        if not browser.load_slot(args.load_slot):
            raise RuntimeError(f"failed to load slot {args.load_slot}")
        print(f"loaded slot {args.load_slot}: {state_text(browser.state())}", flush=True)
    Runner(browser, args.max_step, args.checkpoint_slot, {"yk": args.yk_offset, "money": args.money_offset}).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
