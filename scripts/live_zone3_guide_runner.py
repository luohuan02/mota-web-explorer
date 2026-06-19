#!/usr/bin/env python3
"""Live browser runner for the guide-style zone-3 route.

This script intentionally drives the real h5mota game state: floor travel uses
the fly item API, movement uses hero movement / direct walking, and tools use
core.useItem.  It does not use core.changeFloor to skip map replay.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from live_zone2_runner import Browser, state_text  # noqa: E402


DIR_TO_KEY = {
    "up": "ArrowUp",
    "down": "ArrowDown",
    "left": "ArrowLeft",
    "right": "ArrowRight",
}

DIR_DELTA = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

DIR_KEYCODE = {
    "left": 37,
    "up": 38,
    "right": 39,
    "down": 40,
}

CLICK_TILE_JS = r"""
new Promise(resolve => {
  const target = { x: TARGET_X, y: TARGET_Y };
  const draw = main.dom.gameDraw;
  const group = main.dom.gameGroup;
  const size = 32 * core.domStyle.scale;
  const left = draw.offsetLeft + group.offsetLeft;
  const top = draw.offsetTop + group.offsetTop;
  const clientX = left + (target.x - 0.5) * size;
  const clientY = top + (target.y - 0.5) * size;
  const loc = core.actions._getClickLoc(clientX, clientY);
  const actionPx = target.x * 32 + 16 - core.bigmap.offsetX;
  const actionPy = target.y * 32 + 16 - core.bigmap.offsetY;
  const tile = {
    x: Math.floor(loc.x / loc.size) + 1,
    y: Math.floor(loc.y / loc.size) + 1
  };
  const before = {
    floor: core.status.floorId,
    x: core.status.hero.loc.x,
    y: core.status.hero.loc.y,
    hp: core.status.hero.hp,
    atk: core.status.hero.atk,
    def: core.status.hero.def,
    money: core.status.hero.money,
    moving: !!core.status.heroMoving,
    lock: !!core.status.lockControl,
    event: core.status.event && core.status.event.id,
    ui: core.status.event && core.status.event.ui
  };
  const metrics = {
    left,
    top,
    size,
    clientX,
    clientY,
    actionPx,
    actionPy,
    loc,
    tile,
    dpr: window.devicePixelRatio,
    target
  };
  if (tile.x !== target.x || tile.y !== target.y) {
    return resolve({ ok: false, reason: 'tile-mismatch', metrics, before });
  }
  if (core.status.lockControl || core.status.heroMoving) {
    return resolve({ ok: false, reason: 'busy', metrics, before });
  }
  const down = (core.actions.actions.ondown || []).find(a => a.name === '_sys_ondown');
  const up = (core.actions.actions.onup || []).find(a => a.name === '_sys_onup');
  if (!down || !up) {
    return resolve({ ok: false, reason: 'missing-click-handler', metrics, before });
  }
  down.func.call(core.actions, target.x, target.y, actionPx, actionPy);
  up.func.call(core.actions, target.x, target.y, actionPx, actionPy);
  setTimeout(() => resolve({
    ok: true,
    metrics,
    before,
    after: {
      floor: core.status.floorId,
      x: core.status.hero.loc.x,
      y: core.status.hero.loc.y,
      hp: core.status.hero.hp,
      atk: core.status.hero.atk,
      def: core.status.hero.def,
      money: core.status.hero.money,
      moving: !!core.status.heroMoving,
      lock: !!core.status.lockControl,
      event: core.status.event && core.status.event.id,
      ui: core.status.event && core.status.event.ui
    }
  }), 150);
})
"""

STATE_DETAIL_JS = r"""
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
    tools,
    constants,
    flags: {
      times1: core.getFlag('times1'),
      money1: core.getFlag('money1'),
      ratio: core.getFlag('ratio'),
      soldYellowKeys: core.getFlag('黄钥匙出售次数') || 0
    },
    lock: !!core.status.lockControl,
    moving: !!core.status.heroMoving,
    eventId: ev.id || null,
    eventUi: ev.ui || null,
    routeLen: (core.status.route || []).length
  };
})()
"""


def text_state(state: dict[str, Any]) -> str:
    return (
        f"{state.get('floor')} x{state.get('x')}y{state.get('y')} "
        f"HP={state.get('hp')} ATK={state.get('atk')} DEF={state.get('def')} "
        f"YK={state.get('yk')} BK={state.get('bk')} RK={state.get('rk')} "
        f"G={state.get('money')} flags={state.get('flags')}"
    )


class Zone3GuideRunner:
    def __init__(self, browser: Browser, checkpoint_slot: int | None = None) -> None:
        self.b = browser
        self.checkpoint_slot = checkpoint_slot

    def state(self) -> dict[str, Any]:
        return self.b.eval(STATE_DETAIL_JS)

    def log_state(self, label: str) -> dict[str, Any]:
        state = self.state()
        print(f"{label}: {text_state(state)}", flush=True)
        return state

    def checkpoint(self, label: str) -> None:
        if self.checkpoint_slot is None:
            return
        ok = self.b.save_slot(self.checkpoint_slot)
        print(f"checkpoint {label}: slot={self.checkpoint_slot} ok={ok}", flush=True)
        self.checkpoint_slot += 1
        time.sleep(1.0)

    def flush_motion(self) -> dict[str, Any]:
        self.b.eval(
            """new Promise(resolve => {
  if (!core.status.heroMoving) {
    return resolve({ moving: core.status.heroMoving, lock: core.status.lockControl });
  }
  let done = false;
  core.control.waitHeroToStop(() => {
    done = true;
    setTimeout(() => resolve({
      moving: core.status.heroMoving,
      lock: core.status.lockControl,
      x: core.status.hero.loc.x,
      y: core.status.hero.loc.y
    }), 100);
  });
  setTimeout(() => {
    if (!done) resolve({
      timeout: true,
      moving: core.status.heroMoving,
      lock: core.status.lockControl,
      x: core.status.hero.loc.x,
      y: core.status.hero.loc.y
    });
  }, 2500);
})""",
            timeout=6,
        )
        time.sleep(0.2)
        return self.state()

    def wait_idle_after_progress(
        self,
        before: dict[str, Any],
        desc: str,
        timeout: float = 10,
        interval: float = 0.2,
    ) -> dict[str, Any]:
        end = time.time() + timeout
        progressed = False
        idle_ticks = 0
        last: dict[str, Any] | None = None
        while time.time() < end:
            last = self.state()
            if (
                last.get("floor") != before.get("floor")
                or (last.get("x"), last.get("y")) != (before.get("x"), before.get("y"))
                or last.get("lock") != before.get("lock")
                or last.get("eventId") != before.get("eventId")
                or last.get("eventUi") != before.get("eventUi")
                or any(last.get(k) != before.get(k) for k in ("hp", "atk", "def", "money", "yk", "bk", "rk"))
            ):
                progressed = True
            busy = bool(last.get("moving")) or (bool(last.get("lock")) and not last.get("eventUi"))
            if progressed and not busy:
                idle_ticks += 1
                if idle_ticks >= 2:
                    return last
            else:
                idle_ticks = 0
            time.sleep(interval)
        raise RuntimeError(f"timeout waiting for {desc}; last={text_state(last or {})}")

    def focus_canvas(self) -> None:
        try:
            self.b._run(["click", "canvas"], timeout=10)
        except Exception as exc:
            print(f"focus canvas warning: {exc}", flush=True)
        time.sleep(0.6)

    def wait_until(
        self,
        pred: Callable[[dict[str, Any]], bool],
        desc: str,
        timeout: float = 12,
        interval: float = 0.35,
    ) -> dict[str, Any]:
        end = time.time() + timeout
        last: dict[str, Any] | None = None
        while time.time() < end:
            last = self.state()
            if pred(last):
                return last
            time.sleep(interval)
        raise RuntimeError(f"timeout waiting for {desc}; last={text_state(last or {})}")

    def settle(self, max_presses: int = 40) -> dict[str, Any]:
        state = self.state()
        for _ in range(max_presses):
            if (state.get("eventUi") or {}).get("choices"):
                return state
            if not state.get("lock") and not state.get("eventId") and not state.get("eventUi"):
                return state
            self.b.press("Enter", delay=0.12)
            state = self.state()
        return state

    def step(self, direction: str, expected_floor: str | None = None) -> dict[str, Any]:
        before = self.state()
        if before.get("moving"):
            before = self.flush_motion()
        result = self.b.eval(
            f"""(() => {{
  if (core.status.heroMoving || core.status.lockControl) return {{ ok: false, busy: true }};
  const ok = core.moveHero({json.dumps(direction)});
  return {{
    ok,
    floor: core.status.floorId,
    x: core.status.hero.loc.x,
    y: core.status.hero.loc.y,
    lock: !!core.status.lockControl,
    moving: !!core.status.heroMoving
  }};
}})()""",
            timeout=5,
        )
        print(f"step {direction}: {result}", flush=True)
        state = self.wait_idle_after_progress(before, f"step {direction}")
        time.sleep(0.45)
        if expected_floor:
            state = self.wait_until(
                lambda s: s.get("floor") == expected_floor,
                f"floor {expected_floor}",
                interval=0.8,
            )
            time.sleep(0.6)
            self.settle()
            return state
        if (
            state.get("floor") == before.get("floor")
            and (state.get("x"), state.get("y")) == (before.get("x"), before.get("y"))
            and not state.get("lock")
            and all(state.get(k) == before.get(k) for k in ("hp", "atk", "def", "money", "yk", "bk", "rk"))
        ):
            raise RuntimeError(f"step {direction} did not move; before={text_state(before)} after={text_state(state)}")
        time.sleep(0.2)
        return self.settle()

    def walk(self, *dirs: str, expected_floor: str | None = None) -> None:
        for i, direction in enumerate(dirs):
            self.step(direction, expected_floor=expected_floor if i == len(dirs) - 1 else None)

    def step_until(self, direction: str, x: int, y: int, limit: int = 12) -> None:
        for _ in range(limit):
            state = self.state()
            if (state.get("x"), state.get("y")) == (x, y):
                return
            self.step(direction)
        state = self.state()
        raise RuntimeError(f"failed to reach x{x}y{y}; got {text_state(state)}")

    def fly(self, floor: str) -> None:
        self.b.fly_to(floor)
        self.settle()
        self.log_state(f"fly {floor}")

    def go(self, x: int, y: int, expected_floor: str | None = None) -> None:
        self.click_go(x, y, expected_floor=expected_floor)

    def click_tile(self, x: int, y: int) -> dict[str, Any]:
        js = CLICK_TILE_JS.replace("TARGET_X", str(x)).replace("TARGET_Y", str(y))
        result = self.b.eval(js, timeout=8)
        if not isinstance(result, dict) or not result.get("ok"):
            raise RuntimeError(f"click tile x{x}y{y} failed: {json.dumps(result, ensure_ascii=False)}")
        metrics = result.get("metrics", {})
        print(
            "click x{}y{} at ({:.1f},{:.1f}) metrics left={} top={} size={}".format(
                x,
                y,
                float(metrics.get("clientX", 0)),
                float(metrics.get("clientY", 0)),
                metrics.get("left"),
                metrics.get("top"),
                metrics.get("size"),
            ),
            flush=True,
        )
        return result

    def click_go(
        self,
        x: int,
        y: int,
        expected_floor: str | None = None,
        timeout: float = 12,
    ) -> dict[str, Any]:
        before = self.state()
        if (before.get("x"), before.get("y")) == (x, y) and (
            expected_floor is None or before.get("floor") == expected_floor
        ):
            return before
        result = self.click_tile(x, y)
        if expected_floor:
            state = self.wait_until(
                lambda s: s.get("floor") == expected_floor,
                f"click x{x}y{y} -> floor {expected_floor}",
                timeout=timeout,
                interval=0.25,
            )
        else:
            state = self.wait_until(
                lambda s: (
                    (s.get("x"), s.get("y")) == (x, y)
                    or s.get("floor") != before.get("floor")
                    or bool((s.get("eventUi") or {}).get("choices"))
                ),
                f"click x{x}y{y}",
                timeout=timeout,
                interval=0.25,
            )
        time.sleep(0.3)
        state = self.settle()
        if expected_floor and state.get("floor") != expected_floor:
            raise RuntimeError(f"expected floor {expected_floor}; got {text_state(state)}")
        if (state.get("eventUi") or {}).get("choices"):
            return state
        if expected_floor is None and state.get("floor") == before.get("floor"):
            current = self.state()
            if (current.get("eventUi") or {}).get("choices"):
                return current
            if (current.get("x"), current.get("y")) != (x, y):
                metrics = result.get("metrics", {})
                raise RuntimeError(
                    f"click x{x}y{y} did not arrive; metrics={json.dumps(metrics, ensure_ascii=False)} "
                    f"before={text_state(before)} after={text_state(current)}"
                )
            state = current
        return state

    def open_shop_here(self) -> dict[str, Any]:
        state = self.wait_until(
            lambda s: bool((s.get("eventUi") or {}).get("choices")),
            "shop choices",
            timeout=8,
        )
        choices = [
            {"idx": i, "text": c.get("text")}
            for i, c in enumerate((state.get("eventUi") or {}).get("choices") or [])
        ]
        print("shop choices: " + json.dumps(choices, ensure_ascii=False), flush=True)
        return state

    def choice_index(self, preferred: int, text_contains: str | None = None) -> int:
        state = self.state()
        choices = (state.get("eventUi") or {}).get("choices") or []
        if text_contains:
            for i, choice in enumerate(choices):
                if text_contains in str(choice.get("text", "")):
                    return i
        return preferred

    def choose(self, index: int) -> None:
        state = self.state()
        ui = state.get("eventUi") or {}
        choices = ui.get("choices") or []
        if not choices:
            raise RuntimeError(f"no choices to select: {text_state(state)}")
        self.b.eval(
            f"""new Promise(resolve => {{
  const topIndex = core.actions._getChoicesTopIndex(core.status.event.data.current.choices.length);
  core.actions._clickAction(core.actions.HSIZE, topIndex + {index});
  setTimeout(() => resolve({{
    floor: core.status.floorId,
    x: core.status.hero.loc.x,
    y: core.status.hero.loc.y,
    hp: core.status.hero.hp,
    atk: core.status.hero.atk,
    def: core.status.hero.def,
    money: core.status.hero.money,
    event: core.status.event && core.status.event.id,
    selection: core.status.event && core.status.event.selection
  }}), 250);
}})""",
            timeout=8,
        )
        time.sleep(0.1)

    def buy_shop(self, kind: str, count: int) -> None:
        self.open_shop_here()
        default = {"hp": 0, "atk": 1, "def": 2}[kind]
        text_hint = {"hp": "生命", "atk": "攻击", "def": "防御"}[kind]
        for i in range(count):
            idx = self.choice_index(default, text_hint)
            print(f"shop buy {kind} #{i + 1}: choice={idx}", flush=True)
            self.choose(idx)
            self.open_shop_here()
        exit_idx = self.choice_index(3, "离开")
        self.choose(exit_idx)
        self.settle()

    def sell_yellow_keys_to_at_least(self, target_money: int) -> None:
        self.wait_until(lambda s: bool((s.get("eventUi") or {}).get("choices")), "MT28 trader choices")
        while True:
            state = self.state()
            if state.get("money", 0) >= target_money:
                break
            if state.get("yk", 0) <= 0:
                raise RuntimeError(f"not enough yellow keys to sell: {text_state(state)}")
            need = target_money - state.get("money", 0)
            if need >= 500 and state.get("yk", 0) >= 5:
                idx = self.choice_index(1, "卖5把")
            else:
                idx = self.choice_index(0, "我太需要了")
            print(f"sell yellow key: choice={idx}", flush=True)
            self.choose(idx)
            self.wait_until(lambda s: bool((s.get("eventUi") or {}).get("choices")), "trader loop")
        self.choose(self.choice_index(3, "下次"))
        self.settle()

    def use_item(self, item: str) -> None:
        result = self.b.eval(
            f"""(() => {{
  const before = {{ floor: core.status.floorId, x: core.status.hero.loc.x, y: core.status.hero.loc.y }};
  const ok = core.useItem({json.dumps(item)});
  return {{ ok, before, after: {{ floor: core.status.floorId, x: core.status.hero.loc.x, y: core.status.hero.loc.y }} }};
}})()"""
        )
        print(f"use {item}: {result}", flush=True)
        time.sleep(0.5)
        self.settle()

    def reach_first_shop_menu(self) -> None:
        self.log_state("start")
        self.checkpoint("zone3-start")
        state = self.state()
        if state.get("floor") != "MT31" or (state.get("x"), state.get("y")) != (6, 2):
            raise RuntimeError(f"expected MT31 x6y2 start; got {text_state(state)}")

        # MT31: kill the two blocking zombieKnights and step up to MT32.
        self.walk("down", "down", "down", "down", "down", "down", "down", "down", "down", expected_floor="MT32")
        self.log_state("after MT31 to MT32")

        # MT32: trigger yellowKnight event, then kill the right-bottom ghostSkeleton to reach shop.
        self.walk("up")
        self.log_state("after MT32 yellowKnight event")
        self.go(8, 11)
        self.log_state("after MT32 ghostSkeleton")
        self.go(10, 10)

    def phase_to_shop(self) -> None:
        self.reach_first_shop_menu()
        self.open_shop_here()
        details = self.b.eval(
            """(() => ({
  HSIZE: core.actions.HSIZE,
  SIZE: core.actions.SIZE,
  LEFT: core.actions.CHOICES_LEFT,
  RIGHT: core.actions.CHOICES_RIGHT,
  selection: core.status.event && core.status.event.selection,
  ui: core.status.event && core.status.event.ui,
  top: core.status.event && core.status.event.data && core.status.event.data.current
    ? core.actions._getChoicesTopIndex(core.status.event.data.current.choices.length)
    : null,
  choices: core.status.event && core.status.event.data && core.status.event.data.current
    ? core.status.event.data.current.choices.map((c, i) => ({ i, text: c.text }))
    : null
}))()"""
        )
        print("shop details: " + json.dumps(details, ensure_ascii=False), flush=True)

    def phase_first_shop(self) -> None:
        self.reach_first_shop_menu()
        self.buy_shop("def", 3)
        end = self.log_state("after MT32 shop def x3")
        if end.get("atk") != 78 or end.get("def") != 112:
            raise RuntimeError(f"unexpected first shop stats: {text_state(end)}")
        self.checkpoint("after-32-shop-def3")

    def phase_early_resources(self) -> None:
        start = self.log_state("early start")
        if start.get("atk") != 78 or start.get("def") != 112:
            raise RuntimeError(f"expected after first shop start; got {text_state(start)}")

        # MT14: middle two bigBats + rock, then lower-left blue key.
        self.fly("MT14")
        self.click_go(6, 7)
        self.walk("up", "up", "up")
        self.click_go(7, 5)
        self.step("right")
        self.click_go(5, 5)
        self.step("left")
        self.click_go(1, 6)
        self.walk("down", "down", "down", "down", "down", "down")
        self.log_state("after MT14 middle and blue key")

        # MT16: right-side blue key.
        self.fly("MT16")
        self.click_go(7, 2)
        self.walk("right", "right", "right")
        self.click_go(10, 3)
        self.walk("down", "down", "down", "down", "down", "right")
        self.log_state("after MT16 right blue key")

        # MT17: lower-right pair of zombies opens the lower special door.
        self.fly("MT17")
        self.click_go(10, 11)
        self.walk("up", "up", "up", "up", "left", "right", "right")
        self.log_state("after MT17 lower-right zombies")

        # MT18: spend one blue key and take the lower-left red gem and lower-right blue gem.
        self.fly("MT18")
        self.click_go(6, 5)
        self.walk("down", "down", "down")
        self.click_go(3, 7)
        self.walk("left", "left", "down", "down", "down", "down", "down", "right")
        self.click_go(9, 7)
        self.walk("right", "right", "down", "down", "down", "down", "down", "left")
        gems = self.log_state("after MT18 lower gems")
        if gems.get("atk") != 80 or gems.get("def") != 114:
            raise RuntimeError(f"unexpected MT18 gem stats: {text_state(gems)}")

        # MT32: buy one more defense, reaching DEF 130.
        self.fly("MT32")
        self.go(10, 10)
        self.buy_shop("def", 1)
        end = self.log_state("after MT32 shop def x1")
        if end.get("atk") != 80 or end.get("def") != 130:
            raise RuntimeError(f"unexpected second shop stats: {text_state(end)}")
        self.checkpoint("after-early-resources-def4")

    def phase_14_17_resources(self) -> None:
        start = self.log_state("14/17 start")
        if start.get("atk") != 80 or start.get("def") != 130:
            raise RuntimeError(f"expected after early resources start; got {text_state(start)}")

        # MT14: open the middle blue door to the blue gem, then clear the
        # upper-right yellow-key pocket guarded by the zombieKnight.
        self.fly("MT14")
        self.click_go(5, 5)
        self.walk("up", "up", "up", "up", "up")
        self.log_state("after MT14 blue gem")
        self.click_go(10, 5)
        self.walk("up", "up", "up", "up", "up")
        self.walk("left", "right", "right", "down")
        self.log_state("after MT14 upper-right keys")

        # MT17: kill the right upper pair to open the special door, then take
        # the right-side red/blue gems.  The two yellow keys are on the gem
        # approach paths and are useful for the later MT28 sale.
        self.fly("MT17")
        self.click_go(10, 6)
        self.walk("up", "left", "right", "right", "left", "up", "up")
        self.walk("left", "up", "up", "down", "down", "right", "right", "up", "up")
        end = self.log_state("after MT17 right gems")
        if end.get("atk") != 82 or end.get("def") != 134:
            raise RuntimeError(f"unexpected MT17 gem stats: {text_state(end)}")
        self.checkpoint("after-14-17-resources")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=["first-shop", "to-shop", "early-resources", "14-17-resources"],
        default="first-shop",
    )
    parser.add_argument("--checkpoint-slot", type=int, default=None)
    parser.add_argument("--load-slot", type=int, default=None)
    args = parser.parse_args()

    browser = Browser()
    if args.load_slot is not None:
        if not browser.load_slot(args.load_slot):
            raise RuntimeError(f"failed to load slot {args.load_slot}")
        time.sleep(2.0)
        print(f"loaded slot {args.load_slot}: {state_text(browser.state())}", flush=True)
    runner = Zone3GuideRunner(browser, checkpoint_slot=args.checkpoint_slot)
    if args.phase == "first-shop":
        runner.phase_first_shop()
    elif args.phase == "to-shop":
        runner.phase_to_shop()
    elif args.phase == "early-resources":
        runner.phase_early_resources()
    elif args.phase == "14-17-resources":
        runner.phase_14_17_resources()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
