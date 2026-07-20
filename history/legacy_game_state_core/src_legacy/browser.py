
import os
import json
import subprocess
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional
from src.legacy.game_state import GameState


@dataclass
class BrowserController:
    profile_path: str = None
    session_name: str = "mota-session"
    _daemon_started: bool = False

    def __post_init__(self):
        if self.profile_path is None:
            self.profile_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "browser-profile"
            )
            os.makedirs(self.profile_path, exist_ok=True)

    def _run_cmd(self, cmd: str, args: list = None, extra_args: list = None) -> str:
        """Run an agent-browser command and return output."""
        agent_path = r"D:\nvm4w\nodejs\agent-browser.cmd"
        full_cmd = [agent_path]

        if self.profile_path:
            full_cmd.extend(["--profile", self.profile_path])
        if self.session_name:
            full_cmd.extend(["--session-name", self.session_name])

        full_cmd.append(cmd)

        if args:
            full_cmd.extend(args)
        if extra_args:
            full_cmd.extend(extra_args)

        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=60,
                shell=True,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode != 0 and result.stderr:
                print(f"agent-browser cmd failed: {result.stderr.strip()}")
                return None
            return result.stdout.strip()
        except Exception as e:
            print(f"Error running agent-browser: {e}")
            return None

    def _eval_js(self, js: str) -> Any:
        """Evaluate JavaScript in browser and parse JSON result."""
        output = self._run_cmd("eval", [js])
        if not output:
            return None
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output

    def open_game(self, url: str = "https://h5mota.com/games/51/", auto_connect: bool = False) -> bool:
        """Open the game page in browser, or auto-connect to existing Chrome."""
        if auto_connect:
            print("尝试连接已打开的Chrome...")
            result = self._run_cmd("eval", ["1+1"], extra_args=["--auto-connect"])
            if result:
                print("✓ 连接成功！")
                self._daemon_started = True
                return True
            print("连接失败")
            return False

        print(f"Opening game at {url}...")
        print(f"Using profile: {self.profile_path}")

        self._run_cmd("close", ["--all"])
        time.sleep(1)

        result = self._run_cmd("open", [url], extra_args=["--headed"])
        if result is None:
            return False

        print("Waiting for page to load...")
        time.sleep(5)
        self._daemon_started = True
        return True

    def connect_existing(self) -> bool:
        """连接到你已经打开的Chrome浏览器！"""
        return self.open_game(auto_connect=True)

    def read_game_state(self) -> Optional[GameState]:
        """Read current game state from browser using core API."""
        js = """(function(){
            if (!window.core || !core.status) {
                return {error: "core not found"};
            }
            const h = core.status.hero || {};
            const loc = h.loc || {x:1, y:1};
            const tools = h.items?.tools || {};
            return {
                floor: core.status.floorId || "MT1",
                x: loc.x,
                y: loc.y,
                hp: h.hp || 400,
                yk: tools.yellowKey || 0,
                bk: tools.blueKey || 0,
                rk: tools.redKey || 0,
                atk: h.atk || 10,
                def: h.def || 10
            };
        })()"""

        result = self._eval_js(js)
        if not result or "error" in result:
            return GameState(
                floor="MT1", x=1, y=1,
                hp=400, yk=5, bk=1, rk=0,
                atk=10, def_=10
            )

        return GameState(
            floor=result.get("floor", "MT1"),
            x=result.get("x", 1),
            y=result.get("y", 1),
            hp=result.get("hp", 400),
            yk=result.get("yk", 0),
            bk=result.get("bk", 0),
            rk=result.get("rk", 0),
            atk=result.get("atk", 10),
            def_=result.get("def", 10)
        )

    def export_floor_map(self, floor_id: Optional[str] = None) -> Optional[Dict]:
        """Export current or specified floor map data."""
        floor_arg = floor_id if floor_id else "core.status.floorId"
        js = f"""(function(){{
            const fid = {floor_arg};
            const mapData = core.status.maps?.[fid];
            if (!mapData) return {{error: "floor not found"}};
            return {{
                floorId: fid,
                map: mapData.map || [],
                blocks: mapData.blocks || [],
                width: mapData.map?.[0]?.length || 0,
                height: mapData.map?.length || 0
            }};
        }})()"""

        result = self._eval_js(js)
        return result if result and "error" not in result else None

    def move_to_position(self, x: int, y: int) -> bool:
        """Try to move hero to position using tryMoveDirectly."""
        js = f"""(function(){{
            if (!window.core?.control?.tryMoveDirectly) return false;
            return core.control.tryMoveDirectly({x}, {y});
        }})()"""

        result = self._eval_js(js)
        time.sleep(0.5)
        return result is True

    def move_hero(self, direction: str) -> None:
        """Move hero one step in a direction (up/down/left/right)."""
        key_map = {
            "up": "ArrowUp", "down": "ArrowDown",
            "left": "ArrowLeft", "right": "ArrowRight"
        }
        if direction in key_map:
            self._run_cmd("press", [key_map[direction]])
            time.sleep(0.3)

    def press_key(self, key: str) -> None:
        """Press a key (a=undo, s=save, d=load, etc.)."""
        key = key.lower()
        key_map = {
            "a": "a", "s": "s", "d": "d",
            "enter": "Enter", "space": " "
        }
        if key in key_map:
            self._run_cmd("press", [key_map[key]])

    def save_game(self, slot: int) -> None:
        """Save game to slot."""
        js = f"""(function(){{
            if (!window.core?.control?.saveData) return false;
            const data = core.control.saveData(null);
            core.utils.setLocalForage('save{slot}', data, function(){{}});
            return true;
        }})()"""
        self._eval_js(js)

    def load_game(self, slot: int) -> bool:
        """Load game from slot."""
        js = f"""(function(){{
            if (!window.core?.getSave) return false;
            core.getSave({slot}, function(data){{
                if (data) core.loadData(data, null);
            }});
            return true;
        }})()"""
        result = self._eval_js(js)
        if result:
            time.sleep(2)
        return result is True

    def undo(self) -> None:
        """Press 'a' to undo."""
        self.press_key("a")
        time.sleep(0.5)

    def verify_state(self, expected: GameState) -> bool:
        """Verify current state matches expected."""
        actual = self.read_game_state()
        if not actual:
            return False
        return (actual.floor == expected.floor and
                actual.x == expected.x and
                actual.y == expected.y and
                abs(actual.hp - expected.hp) < 10)

    def close(self) -> None:
        """Close browser."""
        self._run_cmd("close", ["--all"])
        self._daemon_started = False

