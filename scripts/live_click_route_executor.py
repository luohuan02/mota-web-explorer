#!/usr/bin/env python3
"""Execute a planned h5mota click route in the live browser.

The route file is the planning layer: it names target tiles and expected
checkpoints.  This executor is only the web-replay layer: it sends real mouse
events to the canvas, waits for the game to settle, nudges empty action events,
and records before/after state for audit.
"""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


STATE_JS = r"""
(() => {
  const h = core.status.hero || {};
  const loc = h.loc || {};
  const tools = h.items?.tools || {};
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
    lock: !!core.status.lockControl,
    moving: !!core.status.heroMoving,
    event: ev.id || null,
    ui: !!ev.ui,
    routeLen: (core.status.route || []).length
  };
})()
"""


AUTO_ROUTE_JS = r"""
(() => ({
  floor: core.status.floorId,
  hero: core.status.hero.loc,
  moving: core.status.heroMoving,
  lock: core.status.lockControl,
  event: core.status.event && core.status.event.id,
  ui: !!(core.status.event && core.status.event.ui),
  autoRoute: core.status.automaticRoute,
  routeTail: (core.status.route || []).slice(-20)
}))()
"""


def state_text(state: dict[str, Any]) -> str:
    return (
        f"{state.get('floor')} x{state.get('x')}y{state.get('y')} "
        f"HP={state.get('hp')} ATK={state.get('atk')} DEF={state.get('def')} "
        f"YK={state.get('yk')} BK={state.get('bk')} RK={state.get('rk')} "
        f"G={state.get('money')} lock={state.get('lock')} "
        f"moving={state.get('moving')} event={state.get('event')} ui={state.get('ui')}"
    )


class Browser:
    def __init__(self, hold_ms: int) -> None:
        self.hold_ms = hold_ms

    def _run(self, args: list[str], timeout: int = 30) -> str:
        proc = subprocess.run(
            ["agent-browser.cmd", "--cdp", "9222", *args],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
        return proc.stdout.strip()

    def eval(self, js: str, timeout: int = 30) -> Any:
        payload = base64.b64encode(js.encode("utf-8")).decode("ascii")
        out = self._run(["eval", "-b", payload], timeout=timeout)
        if not out:
            return None
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return out

    def state(self) -> dict[str, Any]:
        return self.eval(STATE_JS)

    def clear_runtime_route(self) -> None:
        self.eval(
            """(() => {
  try {
    if (core.stopAutomaticRoute) core.stopAutomaticRoute();
    if (core.clearContinueAutomaticRoute) core.clearContinueAutomaticRoute();
    core.status.route = [];
    if (core.status.replay) {
      core.status.replay.toReplay = [];
      core.status.replay.totalList = [];
      core.status.replay.replaying = false;
      core.status.replay.pausing = false;
    }
  } catch (e) {}
  return true;
})()"""
        )

    def tile_coord(self, x: int, y: int) -> dict[str, Any]:
        return self.eval(
            f"""(() => {{
  const x = {x}, y = {y};
  const left = main.dom.gameDraw.offsetLeft + main.dom.gameGroup.offsetLeft;
  const top = main.dom.gameDraw.offsetTop + main.dom.gameGroup.offsetTop;
  const size = 32 * core.domStyle.scale;
  const clientX = left + (x - 0.5) * size;
  const clientY = top + (y - 0.5) * size;
  const loc = core.actions._getClickLoc(clientX, clientY);
  const tile = {{
    x: Math.floor(loc.x / loc.size) + 1,
    y: Math.floor(loc.y / loc.size) + 1
  }};
  return {{ left, top, size, clientX, clientY, loc, tile }};
}})()"""
        )

    def load_slot(self, slot: int) -> dict[str, Any]:
        ok = self.eval(
            f"""new Promise(resolve => {{
  core.getSave({slot}, data => {{
    if (!data) return resolve(false);
    data.route = [];
    core.loadData(data, null);
    try {{
      if (core.stopAutomaticRoute) core.stopAutomaticRoute();
      if (core.clearContinueAutomaticRoute) core.clearContinueAutomaticRoute();
      core.status.route = [];
      if (core.status.replay) {{
        core.status.replay.toReplay = [];
        core.status.replay.totalList = [];
        core.status.replay.replaying = false;
        core.status.replay.pausing = false;
      }}
    }} catch (e) {{}}
    setTimeout(() => {{
      try {{
        if (core.stopAutomaticRoute) core.stopAutomaticRoute();
        if (core.clearContinueAutomaticRoute) core.clearContinueAutomaticRoute();
        core.status.route = [];
        if (core.status.replay) {{
          core.status.replay.toReplay = [];
          core.status.replay.totalList = [];
          core.status.replay.replaying = false;
          core.status.replay.pausing = false;
        }}
      }} catch (e) {{}}
      const ev = core.status.event || {{}};
      if (core.status.lockControl && !core.status.heroMoving && !ev.id && !ev.ui) {{
        if (core.unlockControl) core.unlockControl();
        else core.status.lockControl = false;
      }}
      resolve(true);
    }}, 900);
  }});
  setTimeout(() => resolve(false), 4000);
}})""",
            timeout=8,
        )
        if not ok:
            raise RuntimeError(f"failed to load slot {slot}")
        return self.state()

    def save_slot(self, slot: int) -> dict[str, Any]:
        ok = self.eval(
            f"""new Promise(resolve => {{
  const data = core.control.saveData(null);
  core.utils.setLocalForage('save{slot}', data, () => resolve(true));
  setTimeout(() => resolve(false), 3000);
}})""",
            timeout=8,
        )
        if not ok:
            raise RuntimeError(f"failed to save slot {slot}")
        return self.state()

    def fly_to(self, floor: str) -> dict[str, Any]:
        self.clear_runtime_route()
        before = self.state()
        self.eval(
            f"""(() => {{
  if (core.status.floorId === {json.dumps(floor)}) return true;
  return core.flyTo({json.dumps(floor)});
}})()"""
        )
        return self.wait_idle(before, f"fly {floor}", timeout=12)

    def choose(self, index: int) -> dict[str, Any]:
        self.clear_runtime_route()
        before = self.state()
        self.eval(
            f"""(() => {{
  const choices = core.status.event?.data?.current?.choices || [];
  if (!choices.length) return {{ ok: false, reason: 'no-choices' }};
  const top = core.actions._getChoicesTopIndex(choices.length);
  core.actions._clickAction(core.actions.HSIZE, top + {index});
  return {{ ok: true }};
}})()"""
        )
        return self.wait_idle(before, f"choice {index}", timeout=12)

    def advance(self, timeout: float = 20) -> dict[str, Any]:
        before = self.state()
        deadline = time.time() + timeout
        last = before
        while time.time() < deadline:
            last = self.state()
            if not last.get("lock") and not last.get("ui") and not last.get("event"):
                if self.state_changed(before, last):
                    return last
                time.sleep(0.2)
                continue
            self.eval(
                """(() => {
  try { core.doAction(); return true; }
  catch (e) {
    try { core.ui.closePanel(); return true; }
    catch (e2) { return false; }
  }
})()"""
            )
            time.sleep(0.25)
        raise RuntimeError(f"timeout advancing event; last={state_text(last)}")

    def press(self, key: str, timeout: float = 20) -> dict[str, Any]:
        self.clear_runtime_route()
        before = self.state()
        self._run(["press", key], timeout=10)
        time.sleep(0.3)
        return self.wait_idle(before, f"press {key}", timeout=timeout)

    def move(self, direction: str, timeout: float = 20) -> dict[str, Any]:
        self.clear_runtime_route()
        before = self.state()
        result = self.eval(
            f"""new Promise(resolve => {{
  if (core.status.lockControl || core.status.heroMoving) {{
    return resolve({{ ok: false, reason: 'busy' }});
  }}
  const direction = {json.dumps(direction)};
  core.setHeroLoc('direction', direction);
  if (!core.canMoveHero(direction)) {{
    return resolve({{ ok: false, reason: 'blocked' }});
  }}
  const fromX = core.getHeroLoc('x');
  const fromY = core.getHeroLoc('y');
  core.setHeroLoc('x', core.nextX(), true);
  core.setHeroLoc('y', core.nextY(), true);
  core.status.route.push(direction);
  let done = false;
  const finish = () => {{
    if (done) return;
    done = true;
    setTimeout(() => resolve({{ ok: true }}), 80);
  }};
  try {{ core.moveOneStep(fromX, fromY, finish); }}
  catch (e) {{ resolve({{ ok: false, reason: String(e) }}); }}
  setTimeout(finish, 1200);
}})"""
        )
        if not isinstance(result, dict) or not result.get("ok"):
            raise RuntimeError(f"move {direction} failed: {result}; {state_text(before)}")
        time.sleep(0.3)
        return self.wait_idle(before, f"move {direction}", timeout=timeout)

    def nudge_empty_action(self) -> bool:
        return bool(
            self.eval(
                """(() => {
  if (core.status.lockControl && !core.status.heroMoving
      && core.status.event && core.status.event.id === 'action'
      && !core.status.event.ui) {
    try { core.doAction(); return true; } catch (e) { return false; }
  }
  return false;
})()"""
            )
        )

    @staticmethod
    def state_changed(before: dict[str, Any], after: dict[str, Any]) -> bool:
        keys = ("floor", "x", "y", "hp", "atk", "def", "money", "yk", "bk", "rk", "event", "ui")
        return any(before.get(k) != after.get(k) for k in keys)

    def wait_idle(self, before: dict[str, Any], desc: str, timeout: float = 30) -> dict[str, Any]:
        deadline = time.time() + timeout
        changed = False
        nudge_ticks = 0
        last: dict[str, Any] | None = None
        while time.time() < deadline:
            last = self.state()
            changed = changed or self.state_changed(before, last)
            if last.get("lock") and not last.get("moving") and last.get("event") == "action" and not last.get("ui"):
                nudge_ticks += 1
                if nudge_ticks >= 4:
                    self.nudge_empty_action()
                    nudge_ticks = 0
            elif last.get("lock") and not last.get("moving") and not last.get("event") and not last.get("ui"):
                nudge_ticks += 1
                if nudge_ticks >= 4:
                    self.eval(
                        """(() => {
  if (core.status.lockControl && !core.status.heroMoving
      && !(core.status.event && core.status.event.id)
      && !(core.status.event && core.status.event.ui)) {
    if (core.unlockControl) core.unlockControl();
    else core.status.lockControl = false;
    return true;
  }
  return false;
})()"""
                    )
                    nudge_ticks = 0
            else:
                nudge_ticks = 0
            if changed and (not last.get("moving")) and ((not last.get("lock")) or last.get("ui")):
                time.sleep(0.25)
                return self.state()
            time.sleep(0.2)
        detail = self.eval(AUTO_ROUTE_JS)
        raise RuntimeError(f"timeout waiting for {desc}; last={state_text(last or {})}; detail={detail}")

    def click_tile(self, x: int, y: int, hold_ms: int | None = None, timeout: float = 45) -> tuple[dict[str, Any], dict[str, Any]]:
        self.clear_runtime_route()
        before = self.state()
        coord = self.tile_coord(x, y)
        tile = coord.get("tile") or {}
        if tile.get("x") != x or tile.get("y") != y:
            raise RuntimeError(f"tile mismatch for x{x}y{y}: {coord}")
        cx = int(round(coord["clientX"]))
        cy = int(round(coord["clientY"]))
        self._run(["mouse", "move", str(cx), str(cy)], timeout=8)
        self._run(["mouse", "down"], timeout=8)
        time.sleep((hold_ms if hold_ms is not None else self.hold_ms) / 1000)
        self._run(["mouse", "up"], timeout=8)
        stop_deadline = time.time() + min(8, timeout)
        while time.time() < stop_deadline:
            current = self.state()
            if current.get("floor") == before.get("floor") and current.get("x") == x and current.get("y") == y:
                self.clear_runtime_route()
                time.sleep(0.2)
                return coord, self.state()
            if self.state_changed(before, current) and not current.get("moving") and not current.get("lock"):
                break
            time.sleep(0.05)
        time.sleep(0.3)
        after = self.wait_idle(before, f"click x{x}y{y}", timeout=timeout)
        return coord, after


def assert_expect(state: dict[str, Any], expect: dict[str, Any], label: str) -> None:
    for key, value in expect.items():
        if state.get(key) != value:
            raise RuntimeError(
                f"expect failed at {label}: {key} expected {value}, got {state.get(key)}; {state_text(state)}"
            )


def run_plan(plan: dict[str, Any], *, hold_ms: int, start_step: int = 0, stop_step: int | None = None) -> list[dict[str, Any]]:
    browser = Browser(hold_ms=hold_ms)
    logs: list[dict[str, Any]] = []
    steps = plan.get("steps", [])
    if stop_step is None:
        stop_step = len(steps)
    for idx, step in enumerate(steps[start_step:stop_step], start=start_step):
        action = step["action"]
        label = step.get("label", f"step-{idx}")
        before = browser.state()
        print(f"[{idx:03d}] {action} {label}: before {state_text(before)}", flush=True)
        coord = None
        if action == "load_slot":
            after = browser.load_slot(int(step["slot"]))
        elif action == "save_slot":
            after = browser.save_slot(int(step["slot"]))
        elif action == "fly":
            after = browser.fly_to(step["floor"])
        elif action == "click":
            coord, after = browser.click_tile(
                int(step["x"]),
                int(step["y"]),
                hold_ms=step.get("hold_ms"),
                timeout=float(step.get("timeout", 45)),
            )
        elif action == "choice":
            after = browser.choose(int(step["index"]))
        elif action == "advance":
            after = browser.advance(timeout=float(step.get("timeout", 20)))
        elif action == "press":
            after = browser.press(step["key"], timeout=float(step.get("timeout", 20)))
        elif action == "move":
            after = browser.move(step["direction"], timeout=float(step.get("timeout", 20)))
        elif action == "expect":
            after = browser.state()
        else:
            raise RuntimeError(f"unknown action {action!r} at step {idx}")
        if "expect" in step:
            assert_expect(after, step["expect"], label)
        logs.append({"index": idx, "step": step, "before": before, "after": after, "coord": coord})
        print(f"[{idx:03d}] after {state_text(after)}", flush=True)
    return logs


def write_report(plan: dict[str, Any], logs: list[dict[str, Any]], out_json: Path, out_md: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"plan": plan, "logs": logs}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        f"# {plan.get('name', 'live click route')} 执行记录",
        "",
        "| # | 动作 | 标签 | 前状态 | 后状态 |",
        "|---:|---|---|---|---|",
    ]
    lines = [
        f"# {plan.get('name', 'live click route')} 执行记录",
        "",
        "| # | 动作 | 标签 | 前状态 | 后状态 |",
        "|---:|---|---|---|---|",
    ]
    for row in logs:
        step = row["step"]
        lines.append(
            f"| {row['index']} | {step['action']} | {step.get('label', '')} | "
            f"`{state_text(row['before'])}` | `{state_text(row['after'])}` |"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--hold-ms", type=int, default=200)
    parser.add_argument("--start-step", type=int, default=0)
    parser.add_argument("--stop-step", type=int, default=None)
    parser.add_argument("--out-json", type=Path, default=ROOT / "outputs/results/live_click_route_run.json")
    parser.add_argument("--out-md", type=Path, default=ROOT / "outputs/reports/live_click_route_run_zh.md")
    args = parser.parse_args()

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    logs = run_plan(plan, hold_ms=args.hold_ms, start_step=args.start_step, stop_step=args.stop_step)
    write_report(plan, logs, args.out_json, args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
