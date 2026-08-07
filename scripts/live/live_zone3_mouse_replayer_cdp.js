#!/usr/bin/env node
// Replay the generated zone-3 walk in the live h5mota page using map mouse
// clicks for movement/targets. This intentionally does not set hero location
// or synthesize per-tile movement.

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..", "..");
const DEFAULT_WALK = path.join(ROOT, "best", "zone3_slot26_clean_walk.json");
const CDP_LIST = "http://127.0.0.1:9222/json/list";
const FLY_POINTS = JSON.parse(fs.readFileSync(path.join(ROOT, "data", "maps", "fly_points.json"), "utf8"));

const RUNTIME = {
  targetClickOnly: false,
  strictHumanInput: false,
};

// Timestamp (ms) the current waitAsync action event first appeared; used to
// force-clear stale asyncId callbacks that hang the waitAsync (game bug).
let waitAsyncStuckSince = 0;

const ACT = {
  CHECK: "\u6821\u9a8c",
  KILL: "\u51fb\u6740",
  PASS: "\u901a\u8fc7",
  CHANGE_FLOOR: "\u6362\u5c42",
  ARRIVE: "\u5230\u8fbe",
  EVENT_BATTLE: "\u4e8b\u4ef6\u6218\u6597",
  TALK: "\u5bf9\u8bdd",
  SHOP: "\u5546\u5e97",
  FLY: "\u98de\u884c",
  OPEN_DOOR: "\u5f00\u95e8",
  PICKUP: "\u62fe\u53d6",
  MERCHANT: "\u5546\u4eba",
  EVENT: "\u4e8b\u4ef6",
  EVENT_REWARD: "\u4e8b\u4ef6\u5956\u52b1",
  MAP_DAMAGE: "\u5730\u56fe\u4f24\u5bb3",
  CENTER_FLY: "\u4e2d\u5fc3\u98de\u884c",
  UP_FLY: "\u4e0a\u697c\u5668",
  DOWN_FLY: "\u4e0b\u697c\u5668",
  BIG_KEY: "\u9b54\u6cd5\u94a5\u5319",
  EARTHQUAKE: "\u5730\u9707\u5377\u8f74",
  BOMB: "\u70b8\u5f39",
  PICKAXE: "\u4f7f\u7528\u9550",
  BREAK_WALL: "\u7834\u5899",
  USE: "\u4f7f\u7528",
  OLDMAN: "\u8001\u4eba",
  SET_AUTO: "\u8bbe\u7f6e\u81ea\u52a8",
};

// Some search outputs emit English action aliases (e.g. "merchant" for the
// specialTrader sell-key action). Normalize them to the Chinese ACT constants so
// the existing MERCHANT/SHOP handlers (and choose() index lookup) cover them.
// "auto_sweep" is an offline bookkeeping marker for a battle=true auto-clear
// group; in live it is already done, so it is handled as a no-op.
const ACTION_ALIASES = {
  merchant: ACT.MERCHANT,
  "用镐": ACT.PICKAXE,
};
function normalizeAction(action) {
  return ACTION_ALIASES[action] || action;
}

function parseArgs(argv) {
  const out = {
    walk: DEFAULT_WALK,
    startStep: 1,
    stopStep: null,
    noRestore: false,
    requireStart: false,
    undoSteps: 0,
    loadSlot: null,
    // Stage checkpoint: write a 100+ save slot every N steps as an exploration
    // chain (101, 102, 103, ...). On a clean full run the chain is a complete
    // live record; on failure, resume from the latest slot; on a fresh run from
    // step 1, the chain restarts at --checkpoint-start (overwriting the old one).
    // NOT a per-step write -- that bloats IndexedDB and can freeze the page.
    // For small live mistakes prefer the game's `a` undo key (see pressUndo).
    checkpointStart: null,
    checkpointEvery: 50,
    // On a step failure, try the game `a` undo key this many times before giving
    // up (default 0 = stop immediately). Cheaper and faster than reload+replay.
    undoOnFailure: 0,
    targetClickOnly: false,
    strictHumanInput: false,
    setAuto: null,
    expectAuto: null,
    outJson: null,
    recordOnly: false,
    allowNotOk: false,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--walk") out.walk = path.resolve(argv[++i]);
    else if (arg === "--start-step") out.startStep = Number(argv[++i]);
    else if (arg === "--stop-step") out.stopStep = Number(argv[++i]);
    else if (arg === "--no-restore") out.noRestore = true;
    else if (arg === "--require-start") out.requireStart = true;
    else if (arg === "--undo-steps") out.undoSteps = Number(argv[++i]);
    else if (arg === "--load-slot") out.loadSlot = Number(argv[++i]);
    else if (arg === "--checkpoint-start") out.checkpointStart = Number(argv[++i]);
    else if (arg === "--checkpoint-every") out.checkpointEvery = Number(argv[++i]);
    else if (arg === "--undo-on-failure") out.undoOnFailure = Number(argv[++i]);
    else if (arg === "--target-click-only") out.targetClickOnly = true;
    else if (arg === "--strict-human-input") out.strictHumanInput = true;
    else if (arg === "--allow-extra-gold") {
      throw new Error("--allow-extra-gold is disabled; gold must match exactly");
    }
    else if (arg === "--set-auto") out.setAuto = parseAutoSpec(argv[++i]);
    else if (arg === "--expect-auto") out.expectAuto = parseAutoSpec(argv[++i]);
    else if (arg === "--out-json") out.outJson = path.resolve(argv[++i]);
    else if (arg === "--record-only") out.recordOnly = true;
    else if (arg === "--allow-not-ok") out.allowNotOk = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  return out;
}

function parseAutoValue(raw) {
  if (raw === "true") return true;
  if (raw === "false") return false;
  if (raw === "nopotion") return "nopotion";
  throw new Error(`unknown auto value ${raw}`);
}

function parseAutoSpec(raw) {
  const out = {};
  for (const part of String(raw || "").split(",")) {
    if (!part.trim()) continue;
    const [key, value] = part.split("=");
    if (!["battle", "item", "wall"].includes(key)) throw new Error(`unknown auto key ${key}`);
    if (value == null) throw new Error(`missing value for auto key ${key}`);
    out[key] = parseAutoValue(value);
  }
  return out;
}

function autoSpecText(spec) {
  if (!spec) return "-";
  return ["battle", "item", "wall"]
    .filter((key) => Object.prototype.hasOwnProperty.call(spec, key))
    .map((key) => `${key}=${spec[key]}`)
    .join(",");
}

function normalizeAutoSpec(raw) {
  if (!raw) return null;
  if (typeof raw === "string") return parseAutoSpec(raw);
  if (typeof raw !== "object" || Array.isArray(raw)) {
    throw new Error(`bad auto spec: ${JSON.stringify(raw)}`);
  }
  const out = {};
  for (const [key, value] of Object.entries(raw)) {
    if (!["battle", "item", "wall"].includes(key)) throw new Error(`unknown auto key ${key}`);
    if (![true, false, "nopotion"].includes(value)) {
      throw new Error(`unknown auto value for ${key}: ${value}`);
    }
    out[key] = value;
  }
  return out;
}

function stepAutoSpec(step) {
  return normalizeAutoSpec(step.auto || step.setAuto || step.autoSpec);
}

async function getJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`GET ${url} failed: ${res.status}`);
  return res.json();
}

async function connectGameTarget() {
  const targets = await getJson(CDP_LIST);
  const target =
    targets.find((t) => t.url && t.url.includes("h5mota.com/games/51")) ||
    targets.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
  if (!target) throw new Error("No h5mota CDP target found on port 9222");

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  let nextId = 1;
  const pending = new Map();
  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (!msg.id || !pending.has(msg.id)) return;
    const entry = pending.get(msg.id);
    pending.delete(msg.id);
    if (msg.error) entry.reject(new Error(JSON.stringify(msg.error)));
    else entry.resolve(msg.result);
  });
  await new Promise((resolve, reject) => {
    ws.addEventListener("open", resolve, { once: true });
    ws.addEventListener("error", reject, { once: true });
  });
  return {
    close: () => ws.close(),
    send(method, params = {}) {
      const id = nextId++;
      return new Promise((resolve, reject) => {
        pending.set(id, { resolve, reject });
        ws.send(JSON.stringify({ id, method, params }));
      });
    },
  };
}

async function ensurePageActive(cdp) {
  try { await cdp.send("Page.setWebLifecycleState", { state: "active" }); } catch (_) { /* best effort */ }
  try { await cdp.send("Emulation.setFocusEmulationEnabled", { enabled: true }); } catch (_) { /* best effort */ }
  try { await cdp.send("Page.bringToFront"); } catch (_) { /* best effort */ }
}

async function evalValue(cdp, expression, awaitPromise = true) {
  if (RUNTIME.strictHumanInput || RUNTIME.targetClickOnly) {
    // target-click-only is the verification mode: forbid state-changing forces
    // (core.doAction/moveHero/changeFloor/...) per skill -- never use these to
    // advance route progress; rely on real map clicks + natural event settle.
    // The cleanup helpers (stopAutomaticRoute/unlockControl/heroMoving=) are
    // only forbidden under --strict-human-input; target-click-only keeps them
    // so stale route/lock/moving state can still be cleared between clicks.
    const forbidden = [
      "core.doAction(",
      "core.moveHero(",
      "core.setHeroLoc(",
      "core.changeFloor(",
      "core.control.saveData(",
    ];
    if (RUNTIME.strictHumanInput) {
      forbidden.push(
        "core.status.heroMoving=",
        "core.unlockControl(",
        "core.stopAutomaticRoute(",
        "core.clearContinueAutomaticRoute(",
      );
    }
    const hit = forbidden.find((pattern) => expression.includes(pattern));
    if (hit) throw new Error(`strict mode forbids state-changing eval: ${hit}`);
  }
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise,
  });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}

async function evalJson(cdp, expression, awaitPromise = true) {
  return JSON.parse(await evalValue(cdp, expression, awaitPromise));
}

const STATE_EXPR = String.raw`(function(){
  var h=core.status.hero||{}, loc=h.loc||{}, tools=(h.items&&h.items.tools)||{}, ev=core.status.event||{};
  var data=ev.data||{}, rawCurrent=data.current, ui=ev.ui||{};
  var currentObj=rawCurrent&&typeof rawCurrent==="object" ? rawCurrent : null;
  var currentType=currentObj ? currentObj.type : null;
  var inferredType=typeof rawCurrent==="string" ? "text" : null;
  var pending=(data.list&&data.list[0]&&data.list[0].todo&&data.list[0].todo[0])||null;
  var pendingType=!rawCurrent&&pending ? (typeof pending==="string" ? "text" : pending.type||null) : null;
  var eventType=currentType||ui.type||data.type||inferredType||pendingType||null;
  var choices=[];
  if (currentObj&&currentObj.choices) choices=currentObj.choices;
  else if (eventType==="choices") choices=ui.choices||[];
  function countAsync(o) {
    if (!o) return 0;
    if (Array.isArray(o)) return o.length;
    if (typeof o === "object") return Object.keys(o).length;
    return 1;
  }
  return JSON.stringify({
    floor: core.status.floorId,
    x: loc.x,
    y: loc.y,
    hp: h.hp,
    atk: h.atk,
    def: h.def,
    money: h.money,
    yk: tools.yellowKey||0,
    bk: tools.blueKey||0,
    rk: tools.redKey||0,
    lock: !!core.status.lockControl,
    moving: !!core.status.heroMoving,
    eventId: ev.id||null,
    eventType: eventType,
    pendingType: pendingType,
    eventUi: !!ev.ui,
    hasChoices: !!(choices&&choices.length),
    choices: choices ? choices.map(function(c){ return String(c.text||""); }) : [],
    selection: typeof ev.selection==="number" ? ev.selection :
      (typeof data.selection==="number" ? data.selection :
      (typeof ui.selection==="number" ? ui.selection : null)),
    autoHeroMove: !!(core.status.automaticRoute&&core.status.automaticRoute.autoHeroMove),
    pendingAction: !!(!rawCurrent&&pending),
    hasAsyncAnimate: !!(core.hasAsyncAnimate&&core.hasAsyncAnimate()),
    statusAsyncCount: countAsync(core.status.asyncId),
    animateAsyncCount: countAsync(core.animateFrame&&core.animateFrame.asyncId)
  });
})()`;

async function state(cdp) {
  return evalJson(cdp, STATE_EXPR);
}

async function autoState(cdp) {
  return evalJson(
    cdp,
    String.raw`(function(){
      var h=core.status.hero||{}, flags=h.flags||{}, auto=flags.__auto__||{};
      function norm(v) {
        if (v === true) return true;
        if (v === "nopotion") return "nopotion";
        return false;
      }
      return JSON.stringify({
        battle: norm(auto.battle),
        item: norm(auto.item),
        wall: norm(auto.wall)
      });
    })()`
  );
}

async function setAutoState(cdp, spec) {
  if (!spec) return autoState(cdp);
  const assignments = Object.entries(spec)
    .map(([key, value]) => `auto[${JSON.stringify(key)}]=${JSON.stringify(value)};`)
    .join("");
  await evalValue(
    cdp,
    `(function(){
      if (!core.status.hero.flags) core.status.hero.flags={};
      var flags=core.status.hero.flags;
      if (!flags.__auto__) flags.__auto__={};
      var auto=flags.__auto__;
      ${assignments}
      return true;
    })()`
  );
  return autoState(cdp);
}

async function expectAutoState(cdp, spec) {
  const live = await autoState(cdp);
  if (!spec) return live;
  const bad = [];
  for (const [key, value] of Object.entries(spec)) {
    if (live[key] !== value) bad.push(`${key}: expected ${value}, got ${live[key]}`);
  }
  if (bad.length) throw new Error(`auto setting mismatch: ${bad.join("; ")}; live=${autoSpecText(live)}`);
  return live;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Wall-clock timestamp "YYYY-MM-DD HH:MM:SS" for per-step logs, so replay timing
// (e.g. a step that idles 15s before its click) can be analyzed from the log.
function tsStamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ` +
    `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

function stateText(s) {
  return `${s.floor} x${s.x}y${s.y} HP=${s.hp} ATK=${s.atk} DEF=${s.def} ` +
    `YK=${s.yk} BK=${s.bk} RK=${s.rk} G=${s.money} ` +
    `lock=${s.lock} moving=${s.moving} event=${s.eventId || "-"}:${s.eventType || "-"} ` +
    `choices=${s.hasChoices} async=${s.statusAsyncCount || 0}/${s.animateAsyncCount || 0}`;
}

function isLabelEvent(s) {
  return s.eventId === "action" && (s.eventType === "_label" || s.pendingType === "_label");
}

// h5mota action-event key handling (from _keyUpAction / _keyDownAction source):
// only step types text/wait/choices/confirm respond to Space/Enter; every other step
// type (sleep/waitAsync/openDoor/move/generateMove/setCurtain/setBlock/hide/show/...)
// auto-advances via timer or animation callback and Space is a proven no-op. So when an
// action event is sitting on a non-dismissable step, we poll quickly WITHOUT pressing
// Space -- pressing it wastes ~150ms (pressKey focus+keydown hold+keyup) per iteration
// and the post-press 450ms sleep made boss afterBattle / MT10 thief generateMove / MT20
// trigger move chains feel sluggish. Space-dispatch for text is still rate-limited below
// to stay above the text-box _animateUI("hide") window (the animateUI guard in
// _clickAction_text also makes double-advance impossible, but we keep a margin).
const SPACE_DISMISSABLE_ACTION_TYPES = new Set(["text", "wait", "choices", "confirm"]);

function sameObservableState(a, b) {
  return a.floor === b.floor &&
    a.x === b.x &&
    a.y === b.y &&
    a.hp === b.hp &&
    a.atk === b.atk &&
    a.def === b.def &&
    a.money === b.money &&
    a.yk === b.yk &&
    a.bk === b.bk &&
    a.rk === b.rk &&
    a.lock === b.lock &&
    a.moving === b.moving &&
    a.eventId === b.eventId &&
    a.eventType === b.eventType &&
    a.hasChoices === b.hasChoices &&
    a.statusAsyncCount === b.statusAsyncCount &&
    a.animateAsyncCount === b.animateAsyncCount;
}

async function continuePendingAction(cdp) {
  // skill mota-live-verify line 120: 禁止 core.doAction 推进事件队列。
  // action 事件 (setBlock/openDoor/waitAsync 等) 靠真实 canvas/地图点击或等待推进；推进不了就停下报告。
  return { ok: false, reason: "doAction disabled; action event must advance via click/wait" };
}

async function clearStaleLock(cdp) {
  if (RUNTIME.strictHumanInput) return { ok: false, reason: "strict-human-input" };
  return evalJson(
    cdp,
    `(function(){
      var ev=core.status.event||{};
      if (core.status.lockControl && !core.status.heroMoving && !ev.id && !ev.ui) {
        if (core.unlockControl) core.unlockControl();
        else core.status.lockControl=false;
        return JSON.stringify({ok:true});
      }
      return JSON.stringify({ok:false});
    })()`
  );
}

async function clearStuckWaitAsync(cdp, force) {
  // A waitAsync action event waits for core.animateFrame.asyncId to empty.
  // Some async openDoor events (e.g. MT2 (8,2) afterBattle opens 6 steelDoors)
  // leave a stale callback in asyncId that is never invoked, so the waitAsync
  // never clears and the replay stalls. First pass: delete falsy stale keys.
  // If `force` is set (the waitAsync has been stuck for several seconds), also
  // delete function-callback keys whose async action will never complete.
  // Do NOT dismiss the event ourselves -- deleting the stale keys lets the
  // game's own waitAsync poll detect asyncId empty and advance the afterBattle
  // queue (which fires the post-openDoor auto-sweep that picks up the now-
  // reachable yellowKeys behind the steelDoors).
  if (RUNTIME.strictHumanInput) return { ok: false, reason: "strict-human-input" };
  return evalJson(
    cdp,
    `(function(){
      try {
        var af=core.animateFrame||{}, aid=af.asyncId||{}, cleaned=0, forced=0;
        for (var k in aid) {
          if (!aid[k]) { delete aid[k]; cleaned++; }
          else if (${force ? "true" : "false"}) { delete aid[k]; forced++; }
        }
        return JSON.stringify({ok:(cleaned+forced)>0, cleaned:cleaned, forced:forced, remain:Object.keys(aid).length});
      } catch(e) { return JSON.stringify({ok:false, err:e.message}); }
    })()`
  );
}

async function continueCurrentChangeFloor(cdp, live) {
  // skill mota-live-verify line 120: 禁止 core.doAction 强推换层。
  // 换层必须靠点击楼梯目标 (upFloor/downFloor) 触发；doAction 已禁用。
  return { ok: false, reason: "doAction disabled; changeFloor must be triggered by stair click" };
}

async function clearStaleMoving(cdp) {
  if (RUNTIME.strictHumanInput) return { ok: false, reason: "strict-human-input" };
  return evalJson(
    cdp,
    `(function(){
      function compact() {
        var h=core.status.hero, loc=h.loc, t=h.items.tools, ev=core.status.event||{}, ar=core.status.automaticRoute||{};
        return {
          floor: core.status.floorId, x: loc.x, y: loc.y,
          hp: h.hp, atk: h.atk, def: h.def, money: h.money,
          yk: t.yellowKey||0, bk: t.blueKey||0, rk: t.redKey||0,
          moving: !!core.status.heroMoving,
          eventId: ev.id||null, eventUi: !!ev.ui,
          autoHeroMove: !!(ar&&ar.autoHeroMove)
        };
      }
      function same(a,b) {
        return a.floor===b.floor && a.x===b.x && a.y===b.y &&
          a.hp===b.hp && a.atk===b.atk && a.def===b.def && a.money===b.money &&
          a.yk===b.yk && a.bk===b.bk && a.rk===b.rk &&
          a.moving===b.moving && a.eventId===b.eventId && a.eventUi===b.eventUi &&
          a.autoHeroMove===b.autoHeroMove;
      }
      var ev=core.status.event||{}, ar=core.status.automaticRoute||{};
      if (!(core.status.heroMoving && !ar.autoHeroMove && !ev.id && !ev.ui)) {
        return Promise.resolve(JSON.stringify({ok:false}));
      }
      var first=compact();
      return new Promise(function(resolve){
        setTimeout(function(){
          var ev2=core.status.event||{}, ar2=core.status.automaticRoute||{};
          var second=compact();
          if (core.status.heroMoving && !ar2.autoHeroMove && !ev2.id && !ev2.ui && same(first, second)) {
            core.status.heroMoving=0;
            // 不要清 core.status.route（录像缓冲区），原因见 clearRuntimeRoute。
            if (core.status.lockControl) {
              if (core.unlockControl) core.unlockControl();
              else core.status.lockControl=false;
            }
            resolve(JSON.stringify({ok:true}));
          }
          else resolve(JSON.stringify({ok:false}));
        }, 900);
      });
    })()`
  );
}

async function clearRuntimeRoute(cdp) {
  if (RUNTIME.strictHumanInput) return;
  await evalValue(
    cdp,
    String.raw`(function(){
      try {
        if (core.stopAutomaticRoute) core.stopAutomaticRoute();
        if (core.clearContinueAutomaticRoute) core.clearContinueAutomaticRoute();
        // 不要清 core.status.route：它是 h5mota 的录像缓冲区（"下载录像"/存档时
        // encodeRoute 会 dump 它），不是自动寻路队列。自动寻路队列是
        // core.status.automaticRoute，上面两行已经清了。这里清 route 会让下载到的
        // .h5route 只剩最近一次 clearRuntimeRoute 之后的尾巴（如 FMT20:...），
        // "从头回访录像"因首命令 fly:MT20 未访问该层而报"录像文件出错"。
        if (core.status.replay) {
          core.status.replay.toReplay = [];
          core.status.replay.totalList = [];
          core.status.replay.replaying = false;
          core.status.replay.pausing = false;
        }
      } catch (e) {}
      return true;
    })()`
  );
}

async function tileMetrics(cdp, x, y) {
  return evalJson(
    cdp,
    `(function(){
      var target={x:${x},y:${y}};
      var draw=main.dom.gameDraw;
      var rect=draw.getBoundingClientRect();
      var size=32*core.domStyle.scale;
      var clientX=rect.left+(target.x-0.5)*size;
      var clientY=rect.top+(target.y-0.5)*size;
      var loc=core.actions._getClickLoc(clientX,clientY);
      var tile={x:Math.floor(loc.x/loc.size)+1,y:Math.floor(loc.y/loc.size)+1};
      return JSON.stringify({
        target:target,
        rect:{left:rect.left,top:rect.top,width:rect.width,height:rect.height},
        size:size,
        clientX:clientX,
        clientY:clientY,
        loc:loc,
        tile:tile,
        dpr:window.devicePixelRatio
      });
    })()`
  );
}

async function waitMovementSettled(cdp, timeoutMs = 60000) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  while (Date.now() < end) {
    last = await state(cdp);
    if (!last.moving) return last;
    if (!RUNTIME.strictHumanInput && last.moving && !last.autoHeroMove && !last.eventId && !last.hasChoices) {
      await clearStaleMoving(cdp);
      last = await state(cdp);
      if (!last.moving) return last;
    }
    await sleep(100);
  }
  return last;
}

async function targetEvent(cdp, floor, x, y) {
  return evalJson(
    cdp,
    `(function(){
      var m=core.status.maps[${JSON.stringify(floor)}]||{};
      var block=(m.blocks||[]).find(function(b){return b.x===${x}&&b.y===${y};});
      if (!block && core.getBlock) block=core.getBlock(${x}, ${y}, ${JSON.stringify(floor)});
      var ev=block&&block.event;
      return JSON.stringify(ev ? {
        id: ev.id||null,
        cls: ev.cls||null,
        trigger: ev.trigger||null,
        noPass: !!ev.noPass
      } : null);
    })()`
  );
}

// General logic: a map-click step's side effect (door opened / enemy killed /
// item taken) may already be visible in the live map because auto-processing
// handled it -- e.g. wall=true auto-opens fakeWalls/dark-walls, or an earlier
// auto-BFS already cleared the target. In that case the block at (x,y) is gone
// and the click has nothing to do; the hero just moves toward (x,y) and stops
// short with no stat change. Accept the step (side effect achieved) instead of
// throwing "target click stopped before target". Per the live-verify skill:
// "Accept them only when stats match and the target side effect is visible in
// the live map, for example the target enemy/item/door has disappeared."
async function targetSideEffectDone(cdp, step, x, y) {
  if (![ACT.OPEN_DOOR, ACT.KILL, ACT.PICKUP, ACT.EVENT_BATTLE].includes(step.action)) return false;
  if (step.floor !== step.floor) return false;
  try {
    const ev = await targetEvent(cdp, step.floor, x, y);
    return !ev; // block gone -> side effect achieved
  } catch (_) {
    return false;
  }
}

function canRetryAdjacentTarget(action, live, floor, x, y, ev) {
  if (live.floor !== floor || live.lock || live.eventId || live.hasChoices || live.moving) return false;
  if (Math.abs(live.x - x) + Math.abs(live.y - y) !== 1) return false;
  if ([ACT.SHOP, ACT.MERCHANT].includes(action) && isShopLikeEvent(ev, true)) return true;
  // Never retry an already-consumed target. A second click on the now-empty
  // enemy/door tile is a new movement action and can trigger auto side effects
  // that are not part of the recorded step (MT32 paired blue guards).
  if ([ACT.KILL, ACT.EVENT_BATTLE].includes(action)) return !!ev && ev.cls === "enemys";
  if (action === ACT.OPEN_DOOR) return !!ev && ev.trigger === "openDoor";
  if (action === ACT.TALK) return !!ev;
  // PASS:hero 相邻即可 retry(走门格)。converter 合并"开门+走门格"成一步 pass X 时,
  // 首次点 X(door_stay 开门 hero stay 邻格)后门 block 清开 ev=null,但 hero 没到 X--
  // 须再点 X 走门格。原 walk pass X(门已开)hero 一步到 X(dist 0,line 562 拦不进 retry)。
  if (action === ACT.PASS) return true;
  if (action === ACT.ARRIVE && (!ev || ev.noPass)) return true;
  if (!ev) return false;
  if (ev.trigger === "changeFloor") return true;
  return ev.noPass && ["action", "openDoor", "battle"].includes(ev.trigger);
}

function isShopLikeEvent(ev, includeGenericAction = false) {
  if (!ev) return false;
  const id = ev.id || "";
  return id === "shop" || id === "blueShop" || id.startsWith("blueShop") ||
    id === "trader" || (includeGenericAction && ev.trigger === "action");
}

async function findItemPos(cdp, floor, eid) {
  // Scan the live floor for an undisabled item block whose event.id matches
  // `eid`. Used when a PICKUP step's recorded pos doesn't match the live map
  // (e.g. the logic verify modeled a reward as an event drop at the killer's
  // tile, but the live game places the item elsewhere). Returns [x, y] or null.
  const pos = await evalJson(
    cdp,
    `(function(){
      var m=core.status.maps[${JSON.stringify(floor)}]||{};
      var blocks=m.blocks||[];
      var found=null;
      for (var i=0;i<blocks.length;i++){
        var b=blocks[i];
        if (b.disable) continue;
        var ev=b.event||{};
        if (ev.cls==="items" && ev.id===${JSON.stringify(eid)}){
          found={x:b.x,y:b.y};
          break;
        }
      }
      return JSON.stringify(found);
    })()`
  );
  return pos ? [pos.x, pos.y] : null;
}

// Multi-tile NPC shops (e.g. MT32 blueShop at x10y10: a 3-wide noPass NPC whose
// left/right parts x9y10/x11y10 have no trigger). Clicking the trigger tile routes
// the hero to the NPC's bounding-box edge (adjacent to a non-trigger part), where
// the action does NOT fire -- the trigger only fires from a tile adjacent to the
// SPECIFIC trigger tile. The only passable tile adjacent to the MT32 trigger is
// x10y11, reachable only through the x8y11 ghostSkeleton. So before opening the
// choices dialog, click a passable tile adjacent to the trigger and let the
// game's own click router handle the route. Has no
// effect when the hero is already on/adjacent to the trigger (single-tile shops).
async function approachShopTrigger(cdp, floor, x, y) {
  let st = await state(cdp);
  if (Math.abs(st.x - x) + Math.abs(st.y - y) <= 1) return st; // on or adjacent
  if (st.lock || st.eventId || st.hasChoices || st.moving) return st;
  const candidates = [[x, y - 1], [x - 1, y], [x + 1, y], [x, y + 1]];
  for (const [ax, ay] of candidates) {
    if (ax < 1 || ay < 1) continue;
    const ev = await targetEvent(cdp, floor, ax, ay);
    if (ev && ev.noPass) continue; // blocked (wall / NPC part)
    await clearRuntimeRoute(cdp);
    await mouseClickTile(cdp, ax, ay);
    await clearRuntimeRoute(cdp);
    await waitMovementSettled(cdp, 8000);
    st = await state(cdp);
    if (st.hasChoices || st.lock || st.eventId) return st; // shop/another event opened en route
    if (Math.abs(st.x - x) + Math.abs(st.y - y) <= 1) return st; // now adjacent to trigger
  }
  return st;
}

async function openChoicesFromActionTarget(cdp, step, x, y, timeoutMs = 15000, includeGenericAction = true) {
  let st = await state(cdp);
  if (st.hasChoices) return st;
  // Multi-tile NPC shops: walk the hero to a passable tile adjacent to the trigger
  // first (click-routing alone stops at the NPC's bounding-box edge). No-op for
  // single-tile shops where the hero is already adjacent after the click.
  await approachShopTrigger(cdp, step.floor, x, y);
  const tryTiles = [[x, y]];
  for (const [dx, dy] of [[-1, 0], [1, 0], [0, 1], [0, -1]]) {
    tryTiles.push([x + dx, y + dy]);
  }
  for (const [tx, ty] of tryTiles) {
    st = await state(cdp);
    if (st.hasChoices || st.lock || st.eventId) break;
    const ev = await targetEvent(cdp, step.floor, tx, ty);
    if (!isShopLikeEvent(ev, includeGenericAction) && !(tx === x && ty === y)) continue;
    await mouseClickTile(cdp, tx, ty);
    try {
      return await waitForChoices(cdp, timeoutMs);
    } catch (_) {
      await maybeRetryAdjacentTarget(cdp, { ...step, pos: [tx, ty] });
      st = await state(cdp);
      if (st.hasChoices) return st;
      try {
        return await waitForChoices(cdp, Math.max(1500, Math.min(timeoutMs, 5000)));
      } catch (_) {
        st = await state(cdp);
      }
    }
  }
  return st;
}

async function maybeRetryAdjacentTarget(cdp, step) {
  const [x, y] = step.pos;
  let st = await waitMovementSettled(cdp);
  if (st.lock && !st.eventId && !st.hasChoices && !st.moving) {
    await clearStaleLock(cdp);
    st = await state(cdp);
  }
  const ev = await targetEvent(cdp, step.floor, x, y);
  if (!canRetryAdjacentTarget(step.action, st, step.floor, x, y, ev)) return;
  await sleep(180);
  st = await waitMovementSettled(cdp);
  const evBeforeRetry = await targetEvent(cdp, step.floor, x, y);
  if (!canRetryAdjacentTarget(step.action, st, step.floor, x, y, evBeforeRetry)) return;
  await mouseClickTile(cdp, x, y);
  st = await waitMovementSettled(cdp);
  if (st.lock && !st.eventId && !st.hasChoices && !st.moving) {
    await clearStaleLock(cdp);
    st = await state(cdp);
  }
  const evAfterClick = await targetEvent(cdp, step.floor, x, y);
  if (!canRetryAdjacentTarget(step.action, st, step.floor, x, y, evAfterClick)) return;
  // A second real map click is the only retry. If the target still does not
  // react, normal per-step verification reports the divergence; never fall
  // back to directional movement.
}

async function assertAutoSweepSideEffects(cdp, step) {
  const note = String(step.note || "");
  const marker = note.indexOf("auto_sweep:");
  if (marker < 0) return;
  const tail = note.slice(marker + "auto_sweep:".length).split(/[;；]/)[0];
  const re = /(?:MT\d+\s+)?x(\d+)y(\d+)\s+([A-Za-z0-9_]+)/g;
  for (const match of tail.matchAll(re)) {
    const x = Number(match[1]);
    const y = Number(match[2]);
    const ev = await targetEvent(cdp, step.floor, x, y);
    if (ev) throw new Error(`auto_sweep side effect missing at ${step.floor} x${x}y${y}: still ${ev.id || ev.cls}`);
  }
}

async function mouseClickTile(cdp, x, y) {
  if (RUNTIME.strictHumanInput || RUNTIME.targetClickOnly) {
    let before = await state(cdp);
    if (before.lock || before.moving || before.eventId || before.hasChoices) {
      throw new Error(`strict mode cannot click while busy: ${stateText(before)}`);
    }
    const metrics = await rawMouseClickTile(cdp, x, y);
    await sleep(220);
    const after = await state(cdp);
    const adjacent = Math.abs(x - before.x) + Math.abs(y - before.y) === 1;
    if (adjacent && sameObservableState(before, after)) {
      await rawMouseClickTile(cdp, x, y);
      await sleep(220);
    }
    return { before, metrics };
  }
  await clearRuntimeRoute(cdp);
  let before = await state(cdp);
  if (before.lock && !before.eventId && !before.hasChoices && !before.moving) {
    await clearStaleLock(cdp);
    before = await state(cdp);
  }
  if (before.moving && !before.autoHeroMove && !before.eventId && !before.hasChoices) {
    await clearStaleMoving(cdp);
    before = await state(cdp);
  }
  if (before.lock || before.moving) {
    throw new Error(`cannot click while busy: ${stateText(before)}`);
  }
  const result = await evalJson(
    cdp,
    `(function(){
      var target={x:${x},y:${y}};
      var draw=main.dom.gameDraw;
      var group=main.dom.gameGroup;
      var size=32*core.domStyle.scale;
      var left=draw.offsetLeft+group.offsetLeft;
      var top=draw.offsetTop+group.offsetTop;
      var clientX=left+(target.x-0.5)*size;
      var clientY=top+(target.y-0.5)*size;
      var loc=core.actions._getClickLoc(clientX,clientY);
      var tile={x:Math.floor(loc.x/loc.size)+1,y:Math.floor(loc.y/loc.size)+1};
      var actionPx=target.x*32+16-core.bigmap.offsetX;
      var actionPy=target.y*32+16-core.bigmap.offsetY;
      var down=(core.actions.actions.ondown||[]).find(function(a){return a.name==="_sys_ondown";});
      var up=(core.actions.actions.onup||[]).find(function(a){return a.name==="_sys_onup";});
      var metrics={left:left,top:top,size:size,clientX:clientX,clientY:clientY,loc:loc,tile:tile,target:target,actionPx:actionPx,actionPy:actionPy};
      if(tile.x!==target.x||tile.y!==target.y)return JSON.stringify({ok:false,reason:"tile-mismatch",metrics:metrics});
      if(!down||!up)return JSON.stringify({ok:false,reason:"missing-click-handler",metrics:metrics});
      down.func.call(core.actions,target.x,target.y,actionPx,actionPy);
      up.func.call(core.actions,target.x,target.y,actionPx,actionPy);
      return JSON.stringify({ok:true,metrics:metrics});
    })()`
  );
  if (!result.ok) throw new Error(`map click x${x}y${y} failed: ${JSON.stringify(result)}`);
  await sleep(220);
  const after = await state(cdp);
  const adjacent = Math.abs(x - before.x) + Math.abs(y - before.y) === 1;
  if (adjacent && sameObservableState(before, after)) {
    const retry = await evalJson(
      cdp,
      `(function(){
        var target={x:${x},y:${y}};
        var actionPx=target.x*32+16-core.bigmap.offsetX;
        var actionPy=target.y*32+16-core.bigmap.offsetY;
        var down=(core.actions.actions.ondown||[]).find(function(a){return a.name==="_sys_ondown";});
        var up=(core.actions.actions.onup||[]).find(function(a){return a.name==="_sys_onup";});
        if(!down||!up)return JSON.stringify({ok:false,reason:"missing-click-handler"});
        down.func.call(core.actions,target.x,target.y,actionPx,actionPy);
        up.func.call(core.actions,target.x,target.y,actionPx,actionPy);
        return JSON.stringify({ok:true,retry:true});
      })()`
    );
    if (!retry.ok) throw new Error(`map retry click x${x}y${y} failed: ${JSON.stringify(retry)}`);
  }
  return { before, metrics: result.metrics };
}

async function rawTilePoint(cdp, x, y) {
  return evalJson(
    cdp,
    `(function(){
      var target={x:${x},y:${y}};
      var draw=main.dom.gameDraw || document.getElementById("fg");
      var rect=draw.getBoundingClientRect();
      var tileW=rect.width/(core.bigmap.width-core.bigmap.offsetX/32*2);
      var tileH=rect.height/(core.bigmap.height-core.bigmap.offsetY/32*2);
      var vx=target.x-core.bigmap.offsetX/32;
      var vy=target.y-core.bigmap.offsetY/32;
      var clientX=rect.left+(vx+0.5)*tileW;
      var clientY=rect.top+(vy+0.5)*tileH;
      var loc=core.actions._getClickLoc(clientX,clientY);
      var tile={x:target.x,y:target.y};
      return JSON.stringify({
        target:target,
        rect:{left:rect.left,top:rect.top,width:rect.width,height:rect.height},
        visible:{x:vx,y:vy,tileW:tileW,tileH:tileH},
        clientX:clientX,
        clientY:clientY,
        loc:loc,
        tile:tile,
        dpr:window.devicePixelRatio
      });
    })()`
  );
}

async function dispatchHumanMouseClick(cdp, x, y, holdMs = 60) {
  await ensurePageActive(cdp);
  await cdp.send("Input.dispatchMouseEvent", {
    type: "mouseMoved",
    x,
    y,
    button: "none",
    buttons: 0,
  });
  await cdp.send("Input.dispatchMouseEvent", {
    type: "mousePressed",
    x,
    y,
    button: "left",
    buttons: 1,
    clickCount: 1,
  });
  await sleep(holdMs);
  await cdp.send("Input.dispatchMouseEvent", {
    type: "mouseReleased",
    x,
    y,
    button: "left",
    buttons: 0,
    clickCount: 1,
  });
}

async function rawMouseClickTile(cdp, x, y) {
  const point = RUNTIME.strictHumanInput
    ? await rawTilePoint(cdp, x, y)
    : await tileMetrics(cdp, x, y);
  if (point.tile && (point.tile.x !== x || point.tile.y !== y)) {
    throw new Error(`raw click tile mismatch x${x}y${y}: ${JSON.stringify(point)}`);
  }
  await dispatchHumanMouseClick(cdp, point.clientX, point.clientY, 60);
  return point;
}

function isWaitingForTargetSelection(st) {
  return st.lock && st.eventId === "action" && st.eventType === "waitAsync" && !st.hasChoices;
}

function expectedState(step) {
  const after = step.after;
  return stateFromSnapshot(after);
}

function stateFromSnapshot(snapshot) {
  return {
    floor: snapshot.floor,
    x: snapshot.x,
    y: snapshot.y,
    hp: snapshot.hp,
    atk: snapshot.atk,
    def: snapshot.def,
    money: snapshot.gold,
    yk: snapshot.yk,
    bk: snapshot.bk,
    rk: snapshot.rk,
  };
}

function compactLiveState(s) {
  return {
    floor: s.floor,
    x: s.x,
    y: s.y,
    hp: s.hp,
    atk: s.atk,
    def: s.def,
    gold: s.money,
    yk: s.yk,
    bk: s.bk,
    rk: s.rk,
  };
}

function strictMismatchText(live, expected) {
  const bad = [];
  for (const key of ["floor", "x", "y", "hp", "atk", "def", "yk", "bk", "rk"]) {
    if (live[key] !== expected[key]) bad.push(`${key}: expected ${expected[key]}, got ${live[key]}`);
  }
  if (live.money !== expected.money) bad.push(`money: expected ${expected.money}, got ${live.money}`);
  return bad.join("; ");
}

function strictValueMismatchText(live, expected) {
  const bad = [];
  for (const key of ["floor", "hp", "atk", "def", "yk", "bk", "rk"]) {
    if (live[key] !== expected[key]) bad.push(`${key}: expected ${expected[key]}, got ${live[key]}`);
  }
  if (live.money !== expected.money) bad.push(`money: expected ${expected.money}, got ${live.money}`);
  return bad.join("; ");
}

function autoHandledNote(steps, startStep, consumedStep) {
  if (consumedStep <= startStep) return "";
  const pieces = [];
  for (let idx = startStep + 1; idx <= consumedStep; idx += 1) {
    const step = steps[idx - 1];
    const [x, y] = step.pos || ["?", "?"];
    pieces.push(`${step.floor} x${x}y${y} ${step.eid || step.action}`);
  }
  return pieces.length ? `自动处理：${pieces.join("、")}` : "";
}

function recordOnlyPositionMatchedStep(live, steps, candidateIndexes) {
  const startFloor = steps[candidateIndexes[0] - 1].floor;
  for (let i = candidateIndexes.length - 1; i >= 0; i -= 1) {
    const expected = expectedState(steps[candidateIndexes[i] - 1]);
    if (live.floor === expected.floor && live.x === expected.x && live.y === expected.y) {
      if (live.floor !== startFloor || valuesMatch(live, expected)) {
        return candidateIndexes[i];
      }
    }
  }
  return candidateIndexes[0];
}

function appendSkippedRecordStep(entries, oneBased, step, note) {
  if (!entries.length) return false;
  const last = entries[entries.length - 1];
  const [x, y] = step.pos || ["?", "?"];
  const piece = `${step.floor} x${x}y${y} ${step.eid || step.action}`;
  const autoNote = note || `自动处理：${piece}`;
  last.consumedStep = oneBased;
  last.consumed.push({
    step: oneBased,
    floor: step.floor,
    pos: step.pos,
    action: step.action,
    eid: step.eid || null,
    note: step.note || "",
  });
  last.autoHandledNote = last.autoHandledNote
    ? `${last.autoHandledNote}；${autoNote}`
    : autoNote;
  return true;
}

function stripSourceAutoSweepNote(note) {
  if (!note) return "";
  return String(note)
    .split(/[;；]/)
    .map((part) => part.trim())
    .filter((part) => part && !part.startsWith("auto_sweep:"))
    .join("；");
}

function buildStrictWalkFromLog(walk, entries) {
  const steps = entries.map((entry) => {
    const step = { ...entry.step };
    step.before = compactLiveState(entry.before);
    step.after = compactLiveState(entry.after);
    const notes = [];
    const sourceNote = stripSourceAutoSweepNote(step.note);
    if (sourceNote) notes.push(sourceNote);
    if (entry.autoHandledNote) notes.push(entry.autoHandledNote);
    if (entry.strictMismatch) notes.push(`旧期望差异：${entry.strictMismatch}`);
    step.note = notes.join("；");
    return step;
  });
  return {
    ...walk,
    ok: true,
    source_walk: walk.source || null,
    source_expected_walk: walk.name || null,
    generated_by: "live_zone3_mouse_replayer_cdp.js --out-json",
    steps,
    expected_final: steps.length ? steps[steps.length - 1].after : null,
  };
}

function writeRunLog(args, walk, entries, finalState) {
  if (!args.outJson) return;
  const strictWalk = buildStrictWalkFromLog(walk, entries);
  const payload = {
    ok: true,
    sourceWalk: path.relative(ROOT, args.walk),
    goldMode: "exact",
    targetClickOnly: !!args.targetClickOnly,
    strictHumanInput: !!args.strictHumanInput,
    setAuto: args.setAuto,
    expectAuto: args.expectAuto,
    loadSlot: args.loadSlot,
    startStep: args.startStep,
    stopStep: args.stopStep || walk.steps.length,
    finalState: compactLiveState(finalState),
    entries,
    strictWalk,
  };
  fs.mkdirSync(path.dirname(args.outJson), { recursive: true });
  fs.writeFileSync(args.outJson, JSON.stringify(payload, null, 2), "utf8");
  console.log(`wrote ${path.relative(ROOT, args.outJson)}`);
}

function loosePositionAction(action) {
  return new Set([
    ACT.CHECK,
    ACT.CHANGE_FLOOR,
    ACT.TALK,
    ACT.SHOP,
    ACT.FLY,
    ACT.MERCHANT,
    ACT.EVENT,
    ACT.EVENT_REWARD,
    ACT.OPEN_DOOR,
    ACT.BREAK_WALL,
    ACT.SET_AUTO,
  ]).has(action);
}

function valuesMatch(live, expected) {
  return live.floor === expected.floor &&
    live.hp === expected.hp &&
    live.atk === expected.atk &&
    live.def === expected.def &&
    live.money === expected.money &&
    live.yk === expected.yk &&
    live.bk === expected.bk &&
    live.rk === expected.rk;
}

function alreadyReachedStepLocation(live, step) {
  const expected = expectedState(step);
  if (!valuesMatch(live, expected)) return false;
  if (loosePositionAction(step.action)) {
    if ([ACT.TALK, ACT.EVENT, ACT.EVENT_REWARD, ACT.SHOP, ACT.MERCHANT].includes(step.action)) {
      return live.x === expected.x && live.y === expected.y;
    }
    const [x, y] = step.pos;
    return (live.x === expected.x && live.y === expected.y) ||
      Math.abs(live.x - x) + Math.abs(live.y - y) <= 1;
  }
  // ARRIVE: accept exact or adjacent (move_adjacent landing).
  if (step.action === ACT.ARRIVE) {
    const [x, y] = step.pos;
    return (live.x === expected.x && live.y === expected.y) ||
      Math.abs(live.x - x) + Math.abs(live.y - y) <= 1;
  }
  return live.x === expected.x && live.y === expected.y;
}

function matchesStep(live, step) {
  const expected = expectedState(step);
  if (!valuesMatch(live, expected)) return false;
  const mayRemainLocked = new Set([ACT.ARRIVE, ACT.TALK, ACT.SHOP, ACT.MERCHANT]).has(step.action);
  // A still-moving hero must never match -- the move hasn't settled, so stats/
  // position are mid-transition. But CHANGE_FLOOR and FLY are floor transitions
  // where moving may persist briefly after landing.
  if (live.moving && !(step.action === ACT.CHANGE_FLOOR || step.action === ACT.FLY)) return false;
  if (!mayRemainLocked && (live.lock || live.eventId)) return false;
  if (step.action === ACT.EVENT_BATTLE && (live.lock || live.eventId || live.hasChoices)) return false;
  if (step.action === ACT.OPEN_DOOR) {
    const [x, y] = step.pos;
    return (live.x === expected.x && live.y === expected.y) ||
      Math.abs(live.x - x) + Math.abs(live.y - y) <= 1;
  }
  if (loosePositionAction(step.action)) return true;
  if (step.action === ACT.KILL && String(step.note || "").includes("auto_sweep:")) {
    // Auto resource traversal may leave the live hero at the group's final
    // route tile rather than the logical clicked enemy. Values and the target
    // disappearance are still checked by stepMatches/sideEffectSatisfied.
    return true;
  }
  // ARRIVE: the hero often stops on a tile adjacent to the target (move_adjacent
  // for shops/NPCs, or auto-route stopping one short). Accept exact or adjacent.
  if (step.action === ACT.ARRIVE) {
    const [x, y] = step.pos;
    return (live.x === expected.x && live.y === expected.y) ||
      Math.abs(live.x - x) + Math.abs(live.y - y) <= 1;
  }
  // OLDMAN: the hero often stops on an adjacent tile when the NPC dialog opens
  // (e.g. 16F fakeWall drops the hero at x10y11, oldman at x11y11). Accept adjacent.
  if (step.action === ACT.OLDMAN) {
    const [x, y] = step.pos;
    return (live.x === expected.x && live.y === expected.y) ||
      Math.abs(live.x - x) + Math.abs(live.y - y) <= 1;
  }
  // EARTHQUAKE/BOMB/USE don't move the hero; their recorded position is just the
  // hero's standing tile, which may differ from live after a fly (live flyTo
  // restores the last on-floor position, not the fly_points landing). Accept any
  // position as long as floor + stats match. Individual use actions can add
  // their own short waits before matching if the page needs animation time.
  if (step.action === ACT.USE && step.eid === "snow") {
    return live.floor === expected.floor && live.x === expected.x && live.y === expected.y;
  }
  if ([ACT.EARTHQUAKE, ACT.BOMB, ACT.USE].includes(step.action)) {
    return live.floor === expected.floor;
  }
  return live.x === expected.x && live.y === expected.y;
}

async function targetClearedMatch(cdp, live, step) {
  const expected = expectedState(step);
  if (!valuesMatch(live, expected) || live.floor !== expected.floor) return false;
  if (![ACT.KILL, ACT.PICKUP, ACT.PASS, ACT.OPEN_DOOR].includes(step.action)) return false;
  const postKillText = step.action === ACT.KILL &&
    live.lock && live.eventId === "action" && live.eventType === "text" &&
    !live.moving && !live.hasChoices;
  if ((live.lock || live.eventId || live.moving || live.hasChoices) && !postKillText) return false;
  const [x, y] = step.pos;
  const ev = await targetEvent(cdp, step.floor, x, y);
  if (step.action === ACT.KILL) return !ev || ev.cls !== "enemys";
  if (step.action === ACT.PICKUP) {
    // fakeWall/fakeWall2 (animates): the item hasn't spawned yet — a break-wall
    // is required first. Do NOT treat as cleared (would skip the break+pickup,
    // e.g. MT19 x6y3 cross behind fakeWall2, leaving cross un-picked).
    if (ev && ev.cls === "animates" && ["fakeWall", "fakeWall2"].includes(ev.id)) return false;
    return !ev || ev.cls !== "items";
  }
  if (step.action === ACT.OPEN_DOOR) return !ev || ev.trigger !== "openDoor";
  if (step.action === ACT.PASS) {
    if (expected.floor && expected.floor !== step.floor) return live.floor === expected.floor;
    return !!step.eid && (!ev || ev.id !== step.eid);
  }
  return false;
}

async function sideEffectOnlySatisfied(cdp, live, step) {
  if (!RUNTIME.strictHumanInput) return false;
  if (live.lock || live.eventId || live.moving || live.hasChoices) return false;
  const expected = expectedState(step);
  if (step.action === ACT.FLY) return live.floor === step.floor;
  if (step.action === ACT.CHANGE_FLOOR) return live.floor === expected.floor;
  if (live.floor !== step.floor) return false;
  const [x, y] = step.pos || [];
  const ev = await targetEvent(cdp, step.floor, x, y);
  if (step.action === ACT.OPEN_DOOR) return valuesMatch(live, expected) && (!ev || ev.trigger !== "openDoor");
  if (step.action === ACT.KILL || step.action === ACT.EVENT_BATTLE) return valuesMatch(live, expected) && (!ev || ev.cls !== "enemys");
  if (step.action === ACT.PICKUP) {
    if (ev && ev.cls === "animates" && ["fakeWall", "fakeWall2"].includes(ev.id)) return false;
    return valuesMatch(live, expected) && (!ev || ev.cls !== "items");
  }
  if (
    step.floor === "MT29" &&
    step.eid === "thief" &&
    [ACT.TALK, ACT.EVENT].includes(step.action)
  ) {
    return valuesMatch(live, expected) && live.x === x && live.y === y && !ev;
  }
  if (step.floor === "MT30" && step.eid === "specialDoor" && step.action === ACT.EVENT) {
    return valuesMatch(live, expected) && live.x === x && live.y === y && !ev;
  }
  if (step.action === ACT.PASS) {
    if (expected.floor && expected.floor !== step.floor) return valuesMatch(live, expected) && live.floor === expected.floor;
    return valuesMatch(live, expected) && !!step.eid && (!ev || ev.id !== step.eid);
  }
  if (step.action === ACT.ARRIVE) return valuesMatch(live, expected) && live.x === x && live.y === y;
  return false;
}

async function targetAlreadyClearedForAction(cdp, live, step) {
  if (!RUNTIME.strictHumanInput) return false;
  if (step.eid === "postBossSupply") return false;
  if (live.lock || live.eventId || live.moving || live.hasChoices) return false;
  if (live.floor !== step.floor) return false;
  const [x, y] = step.pos || [];
  const ev = await targetEvent(cdp, step.floor, x, y);
  if (step.action === ACT.OPEN_DOOR) return !ev || ev.trigger !== "openDoor";
  if (step.action === ACT.KILL || step.action === ACT.EVENT_BATTLE) return !ev || ev.cls !== "enemys";
  if (step.action === ACT.PICKUP) return !ev || ev.cls !== "items";
  if (step.action === ACT.PASS && step.eid === "autoResourceGroup") return false;
  if (step.action === ACT.PASS) return !!step.eid && (!ev || ev.id !== step.eid);
  return false;
}

function rewardItemNeedsPresence(step) {
  return step.action === ACT.EVENT_REWARD &&
    ["redKey", "yellowKey", "blueKey", "redGem", "blueGem", "centerFly3"].includes(step.eid);
}

async function sideEffectSatisfied(cdp, live, step) {
  const expected = expectedState(step);
  if (step.action === ACT.SET_AUTO) {
    const spec = stepAutoSpec(step);
    if (!spec) return true;
    const auto = await autoState(cdp);
    return Object.entries(spec).every(([key, value]) => auto[key] === value);
  }
  if (step.action === ACT.EVENT && step.eid === "centerFly3") {
    return live.floor === expected.floor && live.x === expected.x && live.y === expected.y;
  }
  if (step.action === ACT.EVENT && step.floor === "MT42" && step.eid === "yellowKnightEscape") {
    const ev = await targetEvent(cdp, "MT42", 5, 10);
    return !ev || ev.trigger !== "action";
  }
  if (step.action === ACT.EVENT_REWARD && step.floor === "MT14" && step.eid === "redKey") {
    const [x, y] = step.pos;
    const ev = await targetEvent(cdp, step.floor, x, y);
    return !!ev && ev.cls === "items" && ev.id === "redKey";
  }
  if (rewardItemNeedsPresence(step)) {
    const [x, y] = step.pos;
    const ev = await targetEvent(cdp, step.floor, x, y);
    if (valuesMatch(live, expected)) return !ev || ev.cls !== "items";
    return !!ev && ev.id === step.eid && ev.cls === "items";
  }
  if (step.action === ACT.EVENT_REWARD && step.floor === "MT40" && step.eid === "yellowKnight") {
    const up = await targetEvent(cdp, "MT40", 6, 1);
    return !!up && up.id === "upFloor";
  }
  if (step.action === ACT.EVENT && step.floor === "MT2" && step.eid === "thief") {
    const tunnel = await targetEvent(cdp, "MT35", 4, 9);
    const thief = await targetEvent(cdp, "MT35", 5, 10);
    return !tunnel && !!thief && thief.id === "thief";
  }
  if (step.action === ACT.EVENT && step.floor === "MT10" && step.eid === "thief") {
    const thief = await targetEvent(cdp, "MT10", 6, 10);
    return !thief;
  }
  if (step.action === ACT.EVENT && step.floor === "MT35" && step.eid === "thief") {
    const thief = await targetEvent(cdp, "MT35", 5, 10);
    return !thief;
  }
  if (step.action === ACT.EVENT && step.floor === "MT26" && step.eid === "princess") {
    const rescued = await evalJson(
      cdp,
      `(function(){ return JSON.stringify({ok: !!core.getFlag(${JSON.stringify("营救公主")}, false)}); })()`
    );
    return rescued.ok;
  }
  if (step.action === ACT.OLDMAN && step.eid === "superPotion") {
    const item = await evalJson(
      cdp,
      `(function(){ return JSON.stringify({ok: !!(core.itemCount&&core.itemCount("superPotion")>0)}); })()`
    );
    return item.ok;
  }
  return true;
}

async function stepMatches(cdp, live, step) {
  // ARRIVE on an action/changeFloor trigger tile (e.g. 49F x6y6 boss trigger)
  // must be reached exactly -- adjacent does not fire the event, so reject the
  // adjacent-tolerance match from matchesStep.
  if (step.action === ACT.ARRIVE) {
    const [x, y] = step.pos;
    const ev = await targetEvent(cdp, step.floor, x, y);
    const hasTrigger = ev && (
      ev.noPass ||
      ev.trigger === "action" ||
      ev.trigger === "changeFloor" ||
      ev.id === "none" ||
      ev.id === "upFloor" ||
      ev.id === "downFloor"
    );
    if (hasTrigger && !isShopLikeEvent(ev, true)) {
      if (live.x !== x || live.y !== y) return false;
      if (live.lock || live.eventId || live.moving || live.hasChoices) return false;
    }
  }
  if (step.action === ACT.OPEN_DOOR) {
    const expected = expectedState(step);
    const [x, y] = step.pos;
    const afterAtDoor = live.floor === expected.floor && live.x === x && live.y === y &&
      live.hp === expected.hp && live.atk === expected.atk && live.def === expected.def &&
      live.yk === expected.yk && live.bk === expected.bk && live.rk === expected.rk &&
      live.money === expected.money && !live.lock && !live.eventId && !live.moving && !live.hasChoices;
    if (afterAtDoor && await sideEffectSatisfied(cdp, live, step)) return true;
    const before = step.before || {};
    const eventOpenedAtDoor = live.floor === step.floor && live.x === x && live.y === y &&
      live.hp === before.hp && live.atk === before.atk && live.def === before.def &&
      live.yk === before.yk && live.bk === before.bk && live.rk === before.rk &&
      live.money === before.gold && !live.lock && !live.eventId && !live.moving && !live.hasChoices;
    if (eventOpenedAtDoor && await sideEffectSatisfied(cdp, live, step)) return true;
  }
  if (matchesStep(live, step) && await sideEffectSatisfied(cdp, live, step)) return true;
  return targetClearedMatch(cdp, live, step);
}

function mismatchText(live, step) {
  const expected = expectedState(step);
  const bad = [];
  for (const key of ["floor", "x", "y", "hp", "atk", "def", "yk", "bk", "rk"]) {
    if (live[key] !== expected[key]) bad.push(`${key}: expected ${expected[key]}, got ${live[key]}`);
  }
  if (live.money !== expected.money) bad.push(`money: expected ${expected.money}, got ${live.money}`);
  return bad.join("; ");
}

function coalesceCandidateIndexes(steps, index) {
  const out = [index];
  const step = steps[index - 1];
  const next = steps[index];
  if (!next) return out;
  const chainActions = new Set([
    ACT.KILL,
    ACT.PASS,
    ACT.ARRIVE,
    ACT.OPEN_DOOR,
    ACT.PICKUP,
    ACT.MAP_DAMAGE,
  ]);
  if (chainActions.has(step.action)) {
    for (let offset = 1; offset <= 6; offset += 1) {
      const cand = steps[index - 1 + offset];
      if (!cand || cand.floor !== step.floor || !chainActions.has(cand.action)) break;
      out.push(index + offset);
    }
  }
  if (step.action === ACT.PASS && next.action === ACT.CHANGE_FLOOR) out.push(index + 1);
  if (step.action === ACT.ARRIVE && next.action === ACT.CHANGE_FLOOR) out.push(index + 1);
  const lastIdx = out[out.length - 1];
  const lastStep = steps[lastIdx - 1];
  const afterLast = steps[lastIdx];
  if (lastStep && afterLast && lastStep.action === ACT.PASS && afterLast.action === ACT.CHANGE_FLOOR) {
    out.push(lastIdx + 1);
  }
  if (
    step.action === ACT.ARRIVE &&
    (next.action === ACT.EVENT_BATTLE || next.action === ACT.EVENT || next.action === ACT.EVENT_REWARD)
  ) {
    const [x1, y1] = step.pos;
    const [x2, y2] = next.pos;
    if (step.floor === next.floor && x1 === x2 && y1 === y2) return [index + 1];
  }
  return out;
}

async function mouseClickCanvas(cdp) {
  const point = await evalJson(
    cdp,
    String.raw`(function(){
      var draw=main.dom.gameDraw;
      var rect=draw.getBoundingClientRect();
      return JSON.stringify({
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
        rect: {left: rect.left, top: rect.top, width: rect.width, height: rect.height}
      });
    })()`
  );
  await dispatchHumanMouseClick(cdp, point.x, point.y, 50);
}

const KEY_SPECS = {
  ArrowUp: ["ArrowUp", "ArrowUp", 38],
  ArrowDown: ["ArrowDown", "ArrowDown", 40],
  ArrowLeft: ["ArrowLeft", "ArrowLeft", 37],
  ArrowRight: ["ArrowRight", "ArrowRight", 39],
  Space: [" ", "Space", 32, " "],
  KeyG: ["g", "KeyG", 71, "g"],
  Digit1: ["1", "Digit1", 49, "1"],
  Digit2: ["2", "Digit2", 50, "2"],
  Digit3: ["3", "Digit3", 51, "3"],
  Digit4: ["4", "Digit4", 52, "4"],
};

async function pressKey(cdp, keyName, holdMs = 60) {
  const spec = KEY_SPECS[keyName];
  if (!spec) throw new Error(`unknown key ${keyName}`);
  const [key, code, windowsVirtualKeyCode] = spec;
  await focusGame(cdp);
  await cdp.send("Input.dispatchKeyEvent", {
    type: "keyDown",
    key,
    code,
    windowsVirtualKeyCode,
    nativeVirtualKeyCode: windowsVirtualKeyCode,
  });
  await sleep(holdMs);
  await cdp.send("Input.dispatchKeyEvent", {
    type: "keyUp",
    key,
    code,
    windowsVirtualKeyCode,
    nativeVirtualKeyCode: windowsVirtualKeyCode,
  });
}

async function pressUndo(cdp, count) {
  for (let i = 0; i < count; i += 1) {
    await cdp.send("Input.dispatchKeyEvent", {
      type: "rawKeyDown",
      key: "a",
      code: "KeyA",
      windowsVirtualKeyCode: 65,
      nativeVirtualKeyCode: 65,
    });
    await cdp.send("Input.dispatchKeyEvent", {
      type: "char",
      key: "a",
      code: "KeyA",
      text: "a",
      unmodifiedText: "a",
      windowsVirtualKeyCode: 65,
      nativeVirtualKeyCode: 65,
    });
    await cdp.send("Input.dispatchKeyEvent", {
      type: "keyUp",
      key: "a",
      code: "KeyA",
      windowsVirtualKeyCode: 65,
      nativeVirtualKeyCode: 65,
    });
    await sleep(650);
  }
}

async function focusGame(cdp) {
  await ensurePageActive(cdp);
  await evalValue(
    cdp,
    String.raw`(function(){
      try { window.focus(); } catch (e) {}
      try {
        var draw = main && main.dom && main.dom.gameDraw;
        if (draw) {
          if (!draw.hasAttribute("tabindex")) draw.setAttribute("tabindex", "0");
          if (draw.focus) draw.focus();
        }
      } catch (e) {}
      return true;
    })()`
  );
}

async function saveSlot(cdp, slot) {
  const result = await evalJson(
    cdp,
    `new Promise(function(resolve){
      try {
        var data = core.control.saveData(null);
        core.utils.setLocalForage('save${slot}', data, function(){
          resolve(JSON.stringify({ok:true, slot:${slot}}));
        });
      } catch (e) {
        resolve(JSON.stringify({ok:false, slot:${slot}, error:String(e&&e.stack||e)}));
      }
    })`
  );
  if (!result.ok) throw new Error(`save slot ${slot} failed: ${JSON.stringify(result)}`);
  return result;
}

async function loadSlot(cdp, slot) {
  const result = await evalJson(
    cdp,
    `new Promise(function(resolve){
      try {
        core.getSave(${slot}, function(data){
          if (!data) return resolve(JSON.stringify({ok:false, slot:${slot}, reason:"missing"}));
          try {
            if (core.dom && core.dom.startPanel) core.dom.startPanel.style.display = "none";
            if (main.dom && main.dom.startPanel) main.dom.startPanel.style.display = "none";
            if (main.dom && main.dom.levelChooseButtons) main.dom.levelChooseButtons.style.display = "none";
            if (main.dom && main.dom.startButtonGroup) main.dom.startButtonGroup.style.display = "none";
            core.loadData(data, function(){
              setTimeout(function(){
                var h = core.status.hero || {};
                var loc = h.loc || {};
                var ev = core.status.event || {};
                var ok = !!(core.isPlaying && core.isPlaying()) &&
                  !!core.status.hero &&
                  !core.status.lockControl &&
                  !core.status.heroMoving &&
                  !ev.id;
                resolve(JSON.stringify({
                  ok: ok,
                  slot: ${slot},
                  isPlaying: !!(core.isPlaying && core.isPlaying()),
                  startPanel: core.dom && core.dom.startPanel ? getComputedStyle(core.dom.startPanel).display : null,
                  floor: core.status.floorId || null,
                  x: loc.x,
                  y: loc.y,
                  lock: !!core.status.lockControl,
                  moving: !!core.status.heroMoving,
                  eventId: ev.id || null
                }));
              }, 800);
            });
          } catch (e) {
            resolve(JSON.stringify({ok:false, slot:${slot}, error:String(e&&e.stack||e)}));
          }
        });
      } catch (e) {
        resolve(JSON.stringify({ok:false, slot:${slot}, error:String(e&&e.stack||e)}));
      }
    })`
  );
  if (!result.ok) throw new Error(`load slot ${slot} failed: ${JSON.stringify(result)}`);
  await waitIdle(cdp, 20000);
  return result;
}

async function waitForCandidates(cdp, steps, candidateIndexes, desc, timeoutMs = 90000, breakOnIdle = false) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  while (Date.now() < end) {
    last = await state(cdp);
    if (isLabelEvent(last)) {
      await sleep(250);
      continue;
    }
    for (const idx of candidateIndexes) {
      const step = steps[idx - 1];
      if (await stepMatches(cdp, last, step)) {
        return { state: last, matchedStep: idx };
      }
    }
    for (const idx of candidateIndexes) {
      const step = steps[idx - 1];
      if (await sideEffectOnlySatisfied(cdp, last, step)) {
        return { state: last, matchedStep: idx };
      }
    }
    // Pre-lock context (breakOnIdle): the previous step's lingering event (e.g. boss
    // afterBattle text) has now settled -- state is idle -- but this step's target
    // hasn't been achieved. That means this step needs its own click; don't sit idle
    // for the full preTimeout (was 15s for non-KILL steps). Throw so the caller falls
    // through to executeStep. Coalesced cases match above before reaching here.
    if (breakOnIdle && !last.lock && !last.eventId && !last.moving && !last.hasChoices) {
      throw new Error(`pre-lock idle no-match for ${desc}; last=${stateText(last)}`);
    }
    if (last.eventId === "action" && (!last.eventType || last.pendingAction || last.eventType === "hide" || last.eventType === "show" || last.eventType === "sleep" || last.eventType === "setCurtain" || last.eventType === "setBlock" || last.eventType === "setBgFgBlock" || last.eventType === "openDoor" || last.eventType === "waitAsync" || last.eventType === "move" || last.eventType === "generateMove")) {
      if (last.eventType && !SPACE_DISMISSABLE_ACTION_TYPES.has(last.eventType)) {
        if (last.eventType === "waitAsync") {
          // SteelDoor async openDoor (e.g. MT2 (8,2) afterBattle) can leave a
          // stale callback in asyncId that never fires, hanging the waitAsync.
          // First try clearing falsy stale keys; if still stuck after 6s, force
          // -clear function-callback keys whose async will never complete.
          if (!waitAsyncStuckSince) waitAsyncStuckSince = Date.now();
          const force = Date.now() - waitAsyncStuckSince > 6000;
          const cleared = await clearStuckWaitAsync(cdp, force);
          if (cleared && cleared.ok) { await sleep(250); continue; }
          await sleep(120);
          continue;
        }
        await sleep(120);
        continue;
      }
      const progressed = await continuePendingAction(cdp);
      if (progressed.ok) {
        await sleep(250);
        continue;
      }
    } else {
      waitAsyncStuckSince = 0;
    }
    if (last.moving && !last.autoHeroMove && !last.eventId && !last.hasChoices) {
      await clearStaleMoving(cdp);
      await sleep(80);
      continue;
    }
    if (last.moving || last.eventType === "move") {
      await sleep(120);
      continue;
    }
    if (last.hasChoices) {
      const shopCandidate = candidateIndexes.some((idx) => {
        const candidate = steps[idx - 1];
        return [ACT.SHOP, ACT.MERCHANT].includes(candidate.action) ||
          (candidate.action === ACT.TALK && ["shop", "blueShop", "trader"].includes(candidate.eid || ""));
      });
      if (!shopCandidate) {
        await choose(cdp, "confirm");
        await sleep(450);
      } else {
        await sleep(120);
      }
      continue;
    }
    if (last.lock && !last.eventId && !last.hasChoices) {
      const continued = await continueCurrentChangeFloor(cdp, last);
      if (continued.ok) {
        await sleep(250);
        continue;
      }
      const cleared = await clearStaleLock(cdp);
      await sleep(cleared.ok ? 80 : 150);
      continue;
    }
    // changeFloor / floor-transition actions are automatic animations -- do NOT
    // click the canvas (it interrupts the transition). Just wait for the floor
    // to change. Only click for dialogue/shop/choice events.
    if (last.eventType === "changeFloor") {
      await sleep(200);
      continue;
    }
    if (last.lock || last.eventId) {
      await pressKey(cdp, "Space");
      await sleep(200);
      continue;
    }
    await sleep(120);
  }
  const details = candidateIndexes
    .map((idx) => `step ${idx}: ${mismatchText(last, steps[idx - 1])}`)
    .join(" | ");
  throw new Error(`timeout waiting for ${desc}; last=${stateText(last)}; ${details}`);
}

async function waitIdle(cdp, timeoutMs = 15000) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  while (Date.now() < end) {
    last = await state(cdp);
    if (isLabelEvent(last)) {
      await sleep(250);
      continue;
    }
    if (last.eventId === "action" && (!last.eventType || last.pendingAction || last.eventType === "hide" || last.eventType === "show" || last.eventType === "sleep" || last.eventType === "setCurtain" || last.eventType === "setBlock" || last.eventType === "setBgFgBlock" || last.eventType === "openDoor" || last.eventType === "waitAsync" || last.eventType === "move" || last.eventType === "generateMove")) {
      if (last.eventType && !SPACE_DISMISSABLE_ACTION_TYPES.has(last.eventType)) {
        await sleep(120);
        continue;
      }
      const progressed = await continuePendingAction(cdp);
      if (progressed.ok) {
        await sleep(250);
        continue;
      }
    }
    if (last.moving && !last.autoHeroMove && !last.eventId && !last.hasChoices) {
      await clearStaleMoving(cdp);
      await sleep(80);
      continue;
    }
    if (last.moving || last.eventType === "move") {
      await sleep(120);
      continue;
    }
    if (last.hasChoices) return last;
    if (last.lock && !last.eventId && !last.hasChoices) {
      const continued = await continueCurrentChangeFloor(cdp, last);
      if (continued.ok) {
        await sleep(250);
        continue;
      }
      const cleared = await clearStaleLock(cdp);
      await sleep(cleared.ok ? 80 : 150);
      continue;
    }
    if (last.eventType === "changeFloor") {
      await sleep(200);
      continue;
    }
    if (last.lock || last.eventId) {
      await pressKey(cdp, "Space");
      await sleep(200);
      continue;
    }
    return last;
  }
  throw new Error(`timeout waiting for idle; last=${stateText(last)}`);
}

async function waitForChoices(cdp, timeoutMs = 15000) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  while (Date.now() < end) {
    last = await state(cdp);
    if (isLabelEvent(last)) {
      await sleep(250);
      continue;
    }
    if (last.hasChoices) return last;
    if (last.eventId === "action" && (!last.eventType || last.pendingAction || last.eventType === "hide" || last.eventType === "show" || last.eventType === "sleep" || last.eventType === "setCurtain" || last.eventType === "setBlock" || last.eventType === "setBgFgBlock" || last.eventType === "openDoor" || last.eventType === "waitAsync" || last.eventType === "move")) {
      if (last.eventType && !SPACE_DISMISSABLE_ACTION_TYPES.has(last.eventType)) {
        await sleep(120);
        continue;
      }
      const progressed = await continuePendingAction(cdp);
      if (progressed.ok) {
        await sleep(250);
        continue;
      }
    }
    if (last.moving && !last.autoHeroMove && !last.eventId && !last.hasChoices) {
      await clearStaleMoving(cdp);
      await sleep(80);
      continue;
    }
    if (last.moving || last.eventType === "move") {
      await sleep(120);
      continue;
    }
    if (last.lock && !last.eventId && !last.hasChoices) {
      const continued = await continueCurrentChangeFloor(cdp, last);
      if (continued.ok) {
        await sleep(250);
        continue;
      }
      const cleared = await clearStaleLock(cdp);
      await sleep(cleared.ok ? 80 : 150);
      continue;
    }
    if (last.lock || last.eventId) {
      await sleep(150);
      continue;
    }
    await sleep(120);
  }
  throw new Error(`timeout waiting for choices; last=${stateText(last)}`);
}

async function settleAlreadyCompletedStep(cdp, step) {
  let st = await state(cdp);
  // The 50F thief/redKing reveal is a side-effect-only adjacent event: its
  // recorded before/after hero values are identical. Never let the generic
  // position matcher call it complete while the live thief event still exists.
  if (step.floor === "MT50" && step.eid === "redKing" && step.action === ACT.EVENT) {
    const reveal = await targetEvent(cdp, "MT50", step.pos[0], step.pos[1]);
    if (reveal && reveal.trigger === "action") return null;
  }
  // Stair PASS: if the changeFloor action is already in progress (from a
  // previous attempt), wait for it to settle instead of trying to re-click.
  if (step.action === ACT.PASS && (step.eid === "upFloor" || step.eid === "downFloor")
      && st.lock && st.eventId === "action" && Math.abs(st.x - step.pos[0]) + Math.abs(st.y - step.pos[1]) <= 1) {
    await sleep(2500); // let the floor-change animation complete
    st = await state(cdp);
  }
  if (await targetClearedMatch(cdp, st, step)) return st;
  // MT15 thief opens [8,2] yellowWall (side-effect-only: no HP/pos/key/gold
  // change). State-match would falsely skip it before the wall is opened, then
  // the upFloor x6y1 step fails ("target click stopped before stair"). If the
  // wall is still present, the thief event must execute.
  if (step.floor === "MT15" && step.eid === "thief" && step.action === ACT.EVENT) {
    const wall = await targetEvent(cdp, "MT15", 8, 2);
    if (wall) return null;
  }
  // MT20 vampire event: hero steps on [6,8] to spawn vampire at [6,6]. Side-
  // effect-only (no HP/key/gold change; hero pos changes [6,9]->[6,8]). State-
  // match on HP/keys would falsely skip it before the vampire spawns, then the
  // kill-vampire step fails (hero stuck at [6,9]). If vampire not yet spawned,
  // the event must execute.
  if (step.floor === "MT20" && step.eid === "vampire" && step.action === ACT.EVENT) {
    const vamp = await targetEvent(cdp, "MT20", 6, 6);
    if (!vamp || vamp.cls !== "enemys") return null;
  }
  // MT29 thief (6,2): hero talks to open (6,3) + remove thief. Side-effect-only
  // (no HP/key/gold change; hero stays at (5,2)). State-match would falsely
  // skip it before (6,3) opens, then the upFloor x6y11 step fails ("target
  // click stopped before stair"). If the thief is still present or (6,3) is
  // still closed, the event must execute.
  if (step.floor === "MT29" && step.eid === "thief" && step.action === ACT.EVENT) {
    const thief = await targetEvent(cdp, "MT29", 6, 2);
    const door = await targetEvent(cdp, "MT29", 6, 3);
    if (thief || door) return null;
  }
  // Pickaxe: only "already completed" if the target wall is actually gone.
  // The hero's stats/position are unchanged by using a pickaxe, so a pure
  // position match would falsely skip it.
  if (step.action === ACT.PICKAXE) {
    const [x, y] = step.pos;
    const ev = await targetEvent(cdp, step.floor, x, y);
    if (ev && (ev.cls === "animates" || ev.id === "yellowWall" || ev.id === "whiteWall")) return null;
  }
  // Earthquake/bomb/bigKey: they only destroy walls / open doors and do not
  // change hero stats or position, so a position+values match would falsely
  // mark them done. Always execute them.
  if (step.action === ACT.EARTHQUAKE || step.action === ACT.BOMB || step.action === ACT.BIG_KEY || step.action === ACT.USE) return null;
  if (step.action === ACT.SET_AUTO) {
    return await stepMatches(cdp, st, step) ? st : null;
  }
  // ARRIVE means "walk onto this tile". It must always execute even if the
  // hero is adjacent (e.g. stepping onto an opened-door tile to reach the
  // lava edge, or reaching a boss trigger). Never skip ARRIVE from adjacent
  // position -- only an EXACT match means it is genuinely already completed.
  if (step.action === ACT.ARRIVE && (st.x !== step.pos[0] || st.y !== step.pos[1])) {
    return null;
  }
  if (!alreadyReachedStepLocation(st, step)) return null;
  return await stepMatches(cdp, st, step) ? st : null;
}

async function flyTo(cdp, floor) {
  if (RUNTIME.strictHumanInput) return humanFlyTo(cdp, floor);
  await clearRuntimeRoute(cdp);
  const before = await state(cdp);
  if (before.floor === floor) return before;
  // core.flyTo requires hasVisitedFloor, but the 楼层跳跃 (fly panel) allows any
  // canFlyTo floor including unvisited (e.g. zone2 first fly to MT15). The panel
  // marks the floor visited on fly, so set visited first to make this shortcut
  // match panel behavior. Not a web patch — the panel would fly + mark visited.
  const visited = await evalJson(
    cdp,
    `(function(){var f=core.status.hero.flags;return !!(f&&f.__visited__&&f.__visited__[${JSON.stringify(floor)}])})()`
  );
  if (!visited) {
    throw new Error(`flyTo ${floor} blocked: floor not visited (skill forbids flying to unvisited floors; use upFloor/downFloor stair click)`);
  }
  await evalValue(cdp, `(function(){return core.flyTo(${JSON.stringify(floor)})})()`);
}

async function useItem(cdp, item) {
  if (RUNTIME.strictHumanInput || RUNTIME.targetClickOnly) return humanUseItem(cdp, item);
  await clearRuntimeRoute(cdp);
  await evalValue(cdp, `(function(){return core.useItem(${JSON.stringify(item)})})()`);
}

async function flyPanelInfo(cdp, targetFloor) {
  return evalJson(
    cdp,
    `(function(){
      var ev=core.status.event||{}, data=ev.data;
      var index=typeof data==="number" ? data : null;
      var targetIndex=core.floorIds.indexOf(${JSON.stringify(targetFloor)});
      return JSON.stringify({
        eventId: ev.id||null,
        index: index,
        selectedFloor: index==null ? null : core.floorIds[index],
        targetIndex: targetIndex,
        canFly: !!(core.status.maps[${JSON.stringify(targetFloor)}]&&core.status.maps[${JSON.stringify(targetFloor)}].canFlyTo)
      });
    })()`
  );
}

async function waitFlyPanel(cdp, floor, timeoutMs = 8000) {
  const end = Date.now() + timeoutMs;
  let info = await flyPanelInfo(cdp, floor);
  while (Date.now() < end) {
    info = await flyPanelInfo(cdp, floor);
    if (info.eventId === "fly" && typeof info.index === "number") return info;
    await sleep(120);
  }
  throw new Error(`timeout opening fly panel to ${floor}: ${JSON.stringify(info)}`);
}

async function humanFlyTo(cdp, floor) {
  const before = await state(cdp);
  if (before.floor === floor) return before;
  await moveToFlyUsePointIfNeeded(cdp);
  await pressKey(cdp, "KeyG");
  let info = await waitFlyPanel(cdp, floor);
  if (info.targetIndex < 0 || !info.canFly) {
    throw new Error(`floor ${floor} is not selectable in fly panel: ${JSON.stringify(info)}`);
  }
  let guard = 0;
  while (info.index !== info.targetIndex && guard < 80) {
    const diff = info.targetIndex - info.index;
    if (Math.abs(diff) >= 10) await pressKey(cdp, diff > 0 ? "ArrowRight" : "ArrowLeft");
    else await pressKey(cdp, diff > 0 ? "ArrowUp" : "ArrowDown");
    await sleep(120);
    info = await flyPanelInfo(cdp, floor);
    guard += 1;
  }
  if (info.index !== info.targetIndex) {
    throw new Error(`failed to select fly target ${floor}: ${JSON.stringify(info)}`);
  }
  await pressKey(cdp, "Space");
}

async function canUseFlyItem(cdp) {
  return evalJson(
    cdp,
    `(function(){ return JSON.stringify({ok: !!(core.canUseItem && core.canUseItem("fly"))}); })()`
  );
}

async function moveToFlyUsePointIfNeeded(cdp) {
  let usable = await canUseFlyItem(cdp);
  if (usable.ok) return;
  let st = await state(cdp);
  const points = FLY_POINTS[st.floor] || {};
  const candidates = [points.downFloor, points.upFloor].filter(Boolean);
  if (!candidates.length) return;
  candidates.sort((a, b) =>
    (Math.abs(st.x - a[0]) + Math.abs(st.y - a[1])) -
    (Math.abs(st.x - b[0]) + Math.abs(st.y - b[1]))
  );
  for (const [x, y] of candidates) {
    st = await state(cdp);
    if (st.lock || st.eventId || st.hasChoices || st.moving) return;
    for (let attempt = 0; attempt < 6 && (st.x !== x || st.y !== y); attempt += 1) {
      await mouseClickTile(cdp, x, y);
      await waitMovementSettled(cdp);
      st = await state(cdp);
      if (st.lock || st.eventId || st.hasChoices || st.moving) return;
    }
    usable = await canUseFlyItem(cdp);
    if (usable.ok) return;
  }
}

async function statusItemPoint(cdp, item) {
  return evalJson(
    cdp,
    `(function(){
      var vertical = !!core.domStyle.isVertical;
      var layout = vertical
        ? {
            mx: core.ui.statusBar.itemMxVertical,
            left: 8,
            top: 538,
            colStep: 33,
            rowStep: 32
          }
        : {
            mx: core.getFlag("fly") ? core.ui.statusBar.itemMx : core.ui.statusBar.itemMx2,
            left: 13,
            top: 190,
            colStep: 33,
            rowStep: 32
          };
      var hit = null;
      for (var y = 0; y < layout.mx.length; y++) {
        for (var x = 0; x < layout.mx[y].length; x++) {
          if (layout.mx[y][x] === ${JSON.stringify(item)}) hit = {x:x, y:y};
        }
      }
      if (!hit) return JSON.stringify({ok:false, reason:"missing-layout", item:${JSON.stringify(item)}});
      if (!core.hasItem(${JSON.stringify(item)})) {
        return JSON.stringify({ok:false, reason:"missing-item", item:${JSON.stringify(item)}});
      }
      var rect = main.dom.outerUI.getBoundingClientRect();
      var logicalX = layout.left + (hit.x + 0.5) * layout.colStep;
      var logicalY = layout.top + (hit.y + 0.5) * layout.rowStep;
      return JSON.stringify({
        ok: true,
        item: ${JSON.stringify(item)},
        vertical: vertical,
        grid: hit,
        logicalX: logicalX,
        logicalY: logicalY,
        clientX: rect.left + logicalX * core.domStyle.scale,
        clientY: rect.top + logicalY * core.domStyle.scale,
        selectedItem: core.ui.statusBar.selectedItem || null
      });
    })()`
  );
}

async function clickStatusItem(cdp, item) {
  const point = await statusItemPoint(cdp, item);
  if (!point.ok) throw new Error(`cannot click status item ${item}: ${JSON.stringify(point)}`);
  await dispatchHumanMouseClick(cdp, point.clientX, point.clientY, 60);
  return point;
}

async function hasItem(cdp, item) {
  return evalValue(cdp, `(function(){ return !!core.hasItem(${JSON.stringify(item)}); })()`);
}

async function humanUseCenterFly(cdp, x, y) {
  const before = await state(cdp);
  try {
    await clickStatusItem(cdp, "centerFly");
  } catch (_) {
    await pressKey(cdp, "Digit3");
  }
  await sleep(300);
  let mid = await state(cdp);
  if (mid.floor === before.floor && mid.x === x && mid.y === y) return;
  if (
    mid.floor === before.floor &&
    mid.x === before.x &&
    mid.y === before.y &&
    !mid.lock &&
    !mid.eventId &&
    !mid.hasChoices &&
    !mid.moving
  ) {
    try {
      await clickStatusItem(cdp, "centerFly");
      await sleep(300);
      mid = await state(cdp);
      if (mid.floor === before.floor && mid.x === x && mid.y === y) return;
    } catch (_) {
      // Fall through to target-click mode below.
    }
  }
  await rawMouseClickTile(cdp, x, y);
  await sleep(250);
}

async function humanUseItem(cdp, item) {
  const shortcut = {
    pickaxe: "Digit1",
    bomb: "Digit2",
    centerFly: "Digit3",
    centerFly3: "Digit3",
    earthquake: "Digit4",
    upFly: "Digit4",
    downFly: "Digit4",
  }[item];
  if (item === "snow") {
    await clickStatusItem(cdp, item);
    await sleep(250);
    return;
  }
  if (item === "superPotion") {
    await clickStatusItem(cdp, item);
    await sleep(180);
    if (await hasItem(cdp, item)) await clickStatusItem(cdp, item);
    await sleep(350);
    return;
  }
  if (item === "bigKey") {
    await clickStatusItem(cdp, item);
    await sleep(180);
    if (await hasItem(cdp, item)) await clickStatusItem(cdp, item);
    await sleep(350);
    return;
  }
  if (item === "earthquake") {
    await clickStatusItem(cdp, item);
    await sleep(180);
    if (await hasItem(cdp, item)) await clickStatusItem(cdp, item);
    await sleep(180);
    // Advance a possible empty action shell with a real non-movement key.
    // A canvas-center click can leak through after the tool settles and move
    // the hero to x6y6, which is not part of the earthquake action.
    await pressKey(cdp, "Space");
    await sleep(1200);
    return;
  }
  if (!shortcut) throw new Error(`strict mode has no human shortcut for item ${item}`);
  await pressKey(cdp, shortcut);
  await sleep(250);
}

async function choiceInfo(cdp) {
  return evalJson(
    cdp,
    `(function(){
      var ev=core.status.event||{}, data=ev.data||{}, ui=ev.ui||{};
      var current=data.current&&typeof data.current==="object" ? data.current : null;
      var choices=(current&&current.choices)||(ui&&ui.choices)||[];
      var selection=typeof ev.selection==="number" ? ev.selection :
        (typeof data.selection==="number" ? data.selection :
        (typeof ui.selection==="number" ? ui.selection : 0));
      return JSON.stringify({
        eventId: ev.id||null,
        eventType: current ? current.type : (ui.type||data.type||null),
        choices: choices.map(function(c){return String(c.text||"");}),
        selection: selection
      });
    })()`
  );
}

async function choose(cdp, kind) {
  const defaults = {
    hp: 0,
    atk: 1,
    def: 2,
    exit: 3,
    confirm: 0,
    sellYellowKey: 0,
    yellowKey: 0,
    specialTrader: 0,
    hp2000: 0,
    keyBundle31: 0,
  };
  const index = defaults[kind] ?? 0;
  if (RUNTIME.strictHumanInput || RUNTIME.targetClickOnly) {
    let info = await choiceInfo(cdp);
    if (!info.choices.length || !info.choices[index]) {
      throw new Error(`choose ${kind} failed: ${JSON.stringify({ ok: false, reason: "no-choice", index, choices: info.choices })}`);
    }
    let guard = 0;
    while (info.selection !== index && guard < 20) {
      await pressKey(cdp, info.selection < index ? "ArrowDown" : "ArrowUp");
      await sleep(100);
      info = await choiceInfo(cdp);
      guard += 1;
    }
    if (info.selection !== index) {
      throw new Error(`choose ${kind} failed to select index ${index}: ${JSON.stringify(info)}`);
    }
    await pressKey(cdp, "Space");
    return { ok: true, index, text: info.choices[index], strictHumanInput: true };
  }
  const result = await evalJson(
    cdp,
    `(function(){
      var ev=core.status.event||{};
      var choices=(ev.data&&ev.data.current&&ev.data.current.choices)||(ev.ui&&ev.ui.choices)||[];
      if (!choices.length || !choices[${index}]) {
        return JSON.stringify({ok:false, reason:"no-choice", index:${index}, choices:choices.map(function(c){return String(c.text||"");})});
      }
      var top=core.actions._getChoicesTopIndex(choices.length);
      core.actions._clickAction(core.actions.HSIZE, top+${index});
      return JSON.stringify({ok:true, index:${index}, text:String(choices[${index}].text||"")});
    })()`
  );
  if (!result.ok) throw new Error(`choose ${kind} failed: ${JSON.stringify(result)}`);
  return result;
}

async function closeChoiceMenu(cdp, timeoutMs = 8000) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  while (Date.now() < end) {
    last = await state(cdp);
    if (isLabelEvent(last)) {
      await sleep(250);
      continue;
    }
    if (!last.hasChoices) {
      if (!last.lock && !last.eventId && !last.moving) return last;
      await waitIdle(cdp, 2000);
      last = await state(cdp);
      if (!last.hasChoices) return last;
    }
    if (last.hasChoices) {
      await choose(cdp, "exit");
      await sleep(250);
      continue;
    }
    if (last.eventId === "action" && (!last.eventType || last.pendingAction || last.eventType === "hide" || last.eventType === "show" || last.eventType === "sleep" || last.eventType === "setCurtain" || last.eventType === "setBlock" || last.eventType === "setBgFgBlock" || last.eventType === "openDoor" || last.eventType === "waitAsync" || last.eventType === "move")) {
      if (last.eventType && !SPACE_DISMISSABLE_ACTION_TYPES.has(last.eventType)) {
        await sleep(120);
        continue;
      }
      const progressed = await continuePendingAction(cdp);
      if (progressed.ok) {
        await sleep(250);
        continue;
      }
    }
    if (last.lock || last.eventId) {
      await pressKey(cdp, "Space");
      await sleep(200);
      continue;
    }
    return last;
  }
  throw new Error(`timeout closing choices; last=${stateText(last)}`);
}

function isMapClickAction(action) {
  return new Set([
    ACT.KILL,
    ACT.PASS,
    ACT.ARRIVE,
    ACT.EVENT_BATTLE,
    ACT.TALK,
    ACT.OPEN_DOOR,
    ACT.BREAK_WALL,
    ACT.PICKUP,
    ACT.MAP_DAMAGE,
    ACT.OLDMAN,
  ]).has(action);
}

async function repeatTargetClick(cdp, step, baseFloor, attempts = 3) {
  const [x, y] = step.pos;
  let current = await state(cdp);
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    if (current.floor !== step.floor || current.floor !== baseFloor) return current;
    if (current.lock || current.eventId || current.hasChoices || current.moving) return current;
    const dist = Math.abs(current.x - x) + Math.abs(current.y - y);
    if (dist < 1) return current;
    await mouseClickTile(cdp, x, y);
    await maybeRetryAdjacentTarget(cdp, step);
    current = await state(cdp);
    if (current.floor !== baseFloor) return current;
    if (current.lock || current.eventId || current.hasChoices || current.moving) return current;
    if (Math.abs(current.x - x) + Math.abs(current.y - y) < 1) return current;
  }
  return current;
}

// 10F boss 动态清怪：boss trigger 后 8 spawned 包围 hero(x6y5)，captain 在 x6y1。
// 阶段1：清 spawned（x4-8/y4-7），hero 相邻优先，否则按 bossPriority 顺序。
// 阶段2：spawned 清完后 x6y3 事件墙打开。x6y2 是骷髅队长剧情事件格，从远处直接点 x6y1
//        寻路会经过 x6y2 触发剧情事件卡在 lock=text。必须先点 x6y2 触发并处理剧情文本，
//        再点 x6y1 打 captain。见 skills/mota-live-verify/SKILL.md「1区/10F Boss 实机注意点」。
async function clearMt10BossDyn(cdp) {
  const spawnedOrder = ["5,4", "6,4", "7,4", "5,5", "7,5", "5,6", "6,6", "7,6"];
  const waitForIdle = async () => {
    for (let w = 0; w < 60; w += 1) {
      const s = await state(cdp);
      if (!s.lock && !s.eventId && !s.moving) break;
      if (s.lock && (s.eventId === "action" || s.eventType === "text")) {
        await pressKey(cdp, "Space");
        await sleep(400);
        continue;
      }
      await sleep(300);
    }
  };
  // 等 boss trigger 的 waitAsync/lock 释放（boss 对话文本按 Space 确认）
  await waitForIdle();
  // 阶段1：清 spawned（不含 captain 6,1）
  for (let guard = 0; guard < 30; guard += 1) {
    const enemies = await evalJson(
      cdp,
      String.raw`(function(){
        var map=core.status.maps.MT10||{};
        var blocks=(map.blocks||[]).filter(function(b){
          return !b.disable && b.event && b.event.cls==="enemys" &&
            b.x>=4 && b.x<=8 && b.y>=4 && b.y<=7;
        }).map(function(b){return {x:b.x,y:b.y,id:b.event.id};});
        return JSON.stringify(blocks);
      })()`
    );
    if (!enemies.length) break;
    const heroState = await state(cdp);
    // 优先点击 hero 相邻 enemy（hero 站相邻打），否则按 bossPriority 顺序
    enemies.sort((a, b) => {
      const da = Math.abs(a.x - heroState.x) + Math.abs(a.y - heroState.y);
      const db = Math.abs(b.x - heroState.x) + Math.abs(b.y - heroState.y);
      if (da === 1 && db !== 1) return -1;
      if (db === 1 && da !== 1) return 1;
      const ia = spawnedOrder.indexOf(`${a.x},${a.y}`);
      const ib = spawnedOrder.indexOf(`${b.x},${b.y}`);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    });
    const enemy = enemies[0];
    await mouseClickTile(cdp, enemy.x, enemy.y);
    await waitMovementSettled(cdp);
    await waitForIdle();
  }
  // 阶段2：等 x6y3 事件墙打开（spawned 清完后自动开）
  for (let w = 0; w < 40; w += 1) {
    const wall = await evalJson(
      cdp,
      String.raw`(function(){
        var map=core.status.maps.MT10||{};
        var hit=(map.blocks||[]).some(function(b){
          return !b.disable && b.x===6 && b.y===3 && b.event;
        });
        return JSON.stringify({hasWall:hit});
      })()`
    );
    if (!wall.hasWall) break;
    await sleep(300);
  }
  // 先点 x6y2 触发骷髅队长剧情事件并处理文本（hero 走到 x6y2/相邻触发）
  await mouseClickTile(cdp, 6, 2);
  await waitMovementSettled(cdp);
  await waitForIdle();
  // 再点 x6y1 打 captain
  await mouseClickTile(cdp, 6, 1);
  await waitMovementSettled(cdp);
  await waitForIdle();
}

async function executeStep(cdp, step) {
  let [x, y] = step.pos;
  if (step.action === ACT.SET_AUTO) {
    const spec = stepAutoSpec(step);
    if (!spec) throw new Error("SET_AUTO step requires auto/setAuto/autoSpec");
    const liveAuto = await setAutoState(cdp, spec);
    await expectAutoState(cdp, spec);
    console.log(`      auto ${autoSpecText(spec)} -> ${autoSpecText(liveAuto)}`);
    return;
  }
  if (step.action === ACT.PICKUP && step.eid) {
    // The recorded pickup pos may not match the live map (e.g. a reward the
    // logic verify placed at the killer's tile but the live game places
    // elsewhere). If no item with step.eid sits at step.pos, scan the floor and
    // retarget the real item location.
    const ev = await targetEvent(cdp, step.floor, x, y);
    const hereOk = ev && ev.cls === "items" && ev.id === step.eid;
    if (!hereOk) {
      const live = await state(cdp);
      if (
        live.floor === step.floor &&
        (
          await targetSideEffectDone(cdp, step, x, y) ||
          await sideEffectOnlySatisfied(cdp, live, step)
        )
      ) {
        return;
      }
      const real = await findItemPos(cdp, step.floor, step.eid);
      if (real) {
        console.log(`      [pickup retarget] ${step.eid}: recorded x${x}y${y} not an item, using live x${real[0]}y${real[1]}`);
        x = real[0];
        y = real[1];
      }
    }
  }
  if (step.action === ACT.CHECK || step.action === ACT.CHANGE_FLOOR) {
    return;
  }
  if (step.action === "auto_sweep") {
    // Offline bookkeeping marker: it is a no-op only after proving every
    // claimed map side effect is already visible in live.
    await assertAutoSweepSideEffects(cdp, step);
    return;
  }
  if (step.action === ACT.FLY) {
    await flyTo(cdp, step.floor);
    await waitIdle(cdp, 20000);
    return;
  }
  if (RUNTIME.strictHumanInput) {
    const current = await state(cdp);
    const expectedFloor =
      (step.action === ACT.UP_FLY || step.action === ACT.DOWN_FLY) && step.before && step.before.floor
        ? step.before.floor
        : step.floor;
    if (current.floor !== expectedFloor) {
      throw new Error(`strict mode floor mismatch before ${step.action}: expected ${expectedFloor}, got ${stateText(current)}`);
    }
  }
  const stepTargetEvent = await targetEvent(cdp, step.floor, x, y);
  if (step.action === ACT.TALK && isShopLikeEvent(stepTargetEvent, false)) {
    const st = await openChoicesFromActionTarget(cdp, step, x, y, 15000, false);
    if (!st.hasChoices) throw new Error(`failed to open choices for ${step.eid || step.action} at x${x}y${y}: ${stateText(st)}`);
    return;
  }
  if (step.action === ACT.SHOP || step.action === ACT.MERCHANT) {
    // The shop/trader dialog must be opened first by clicking the NPC tile;
    // only then do choices appear. If already in a choices dialog, choose now.
    let st = await state(cdp);
    if (!st.hasChoices) {
      // step.pos can be the adjacent landing tile or the shop action tile.
      st = await openChoicesFromActionTarget(cdp, step, x, y, 15000, true);
    }
    if (!st.hasChoices) st = await waitForChoices(cdp, 15000);
    await choose(cdp, step.eid || "confirm");
    return;
  }
  if (step.action === ACT.EVENT_REWARD) {
    if (rewardItemNeedsPresence(step)) {
      await mouseClickTile(cdp, x, y);
      return;
    }
    let st = await state(cdp);
    if (st.hasChoices) await choose(cdp, "confirm");
    else if (st.lock || st.eventId) await mouseClickCanvas(cdp);
    else {
      // NPC rewards (for example MT2 oldman +1000G) must be triggered by a
      // real click on the NPC target. Clicking the empty canvas does not start
      // the interaction and can move the hero elsewhere.
      await mouseClickTile(cdp, x, y);
      await waitIdle(cdp, 20000);
    }
    return;
  }
  if (step.action === ACT.EVENT && step.eid === "centerFly3") {
    if (RUNTIME.strictHumanInput || RUNTIME.targetClickOnly) await humanUseCenterFly(cdp, x, y);
    else await useItem(cdp, "centerFly");
    return;
  }
  if (step.action === ACT.CENTER_FLY) {
    if (RUNTIME.strictHumanInput || RUNTIME.targetClickOnly) await humanUseCenterFly(cdp, x, y);
    else await useItem(cdp, "centerFly");
    return;
  }
  if (step.action === ACT.UP_FLY) {
    await useItem(cdp, "upFly");
    await waitIdle(cdp, 20000);
    return;
  }
  if (step.action === ACT.DOWN_FLY) {
    await useItem(cdp, "downFly");
    await waitIdle(cdp, 20000);
    return;
  }
  if (step.action === ACT.BIG_KEY) {
    await useItem(cdp, "bigKey");
    return;
  }
  if (step.action === ACT.EARTHQUAKE) {
    if (RUNTIME.strictHumanInput) {
      await useItem(cdp, "earthquake");
      await waitIdle(cdp, 20000);
      await mouseClickTile(cdp, x, y);
      await waitIdle(cdp, 20000);
      return;
    }
    await useItem(cdp, "earthquake");
    return;
  }
  if (step.action === ACT.BOMB) {
    await useItem(cdp, "bomb");
    return;
  }
  if (step.action === ACT.PICKAXE) {
    // Pickaxe breaks adjacent breakable walls by item effect; it does not open
    // a target selection UI in this game. The recorded pos is the wall expected
    // to disappear, not a tile to click after using the item.
    await useItem(cdp, "pickaxe");
    // useItem inserts an async openDoor + waitAsync action. It may still look
    // idle for a short tick before that queue starts, so waiting for generic
    // idle alone can race into the next route click and interrupt the break.
    const deadline = Date.now() + 20000;
    await sleep(250);
    // Hidden-tool use can enqueue an empty waitAsync shell without immediately
    // starting it. Advance that shell through the real canvas input path; never
    // call core.doAction or mutate the map directly.
    await mouseClickCanvas(cdp);
    await sleep(250);
    while (Date.now() < deadline) {
      const ev = await targetEvent(cdp, step.floor, x, y);
      if (!ev) return;
      const live = await state(cdp);
      if (live.lock || live.eventId || live.moving || (live.animateAsyncCount || 0) > 0) {
        await waitIdle(cdp, 20000);
      } else {
        await sleep(150);
      }
    }
    throw new Error(`pickaxe target did not disappear at ${step.floor} x${x}y${y}`);
  }
  if (step.action === ACT.USE) {
    if (step.eid === "snow") {
      let st = await state(cdp);
      if (st.floor === step.floor && (st.x !== x || st.y !== y) && !st.lock && !st.eventId && !st.hasChoices && !st.moving) {
        await mouseClickTile(cdp, x, y);
        await waitMovementSettled(cdp);
        st = await state(cdp);
        if (st.floor === step.floor && (st.x !== x || st.y !== y) && !st.lock && !st.eventId && !st.hasChoices && !st.moving) {
          if (RUNTIME.targetClickOnly) {
            throw new Error(`target click did not reach USE ${step.eid} tile x${x}y${y}: ${stateText(st)}`);
          }
          throw new Error(`single target click did not reach USE ${step.eid} tile x${x}y${y}: ${stateText(st)}`);
        }
      }
    }
    await useItem(cdp, step.eid || "confirm");
    if (step.eid === "snow") await sleep(2000);
    return;
  }
  if (step.action === ACT.EVENT) {
    const st = await state(cdp);
    if (step.floor === "MT50" && step.eid === "redKing") {
      // The final adjacent NPC/Boss boundary is intentionally driven through
      // a genuine keyboard direction event (allowed by the project contract),
      // not a forced hero move or direct action API.
      const dx = x - st.x;
      const dy = y - st.y;
      if (Math.abs(dx) + Math.abs(dy) !== 1) {
        throw new Error(`MT50 redKing must be adjacent before keyboard trigger: ${stateText(st)}`);
      }
      await pressKey(cdp, dx > 0 ? "ArrowRight" : dx < 0 ? "ArrowLeft" : dy > 0 ? "ArrowDown" : "ArrowUp");
      return;
    }
    if (st.hasChoices) await choose(cdp, "confirm");
    else if (step.floor === "MT10" && step.eid === "bossEvent") {
      // 10F boss trigger: 点击 x6y5 触发 boss（skeletonCaptain 移到 x6y1，spawn 8 怪），
      // 然后动态清 spawned（按 bossPriority 顺序点击，直到清完）。
      await mouseClickTile(cdp, x, y);
      await waitMovementSettled(cdp);
      await clearMt10BossDyn(cdp);
    }
    else if (st.lock || st.eventId) await mouseClickCanvas(cdp);
    else if (step.floor === "MT10" && step.eid === "thief") {
      let live = st;
      if (live.x === x && live.y === y) {
        await pressKey(cdp, "Space");
      } else {
        await mouseClickTile(cdp, x, y);
        await waitMovementSettled(cdp);
        live = await state(cdp);
        if (live.floor === step.floor && live.x === x && live.y === y && !live.lock && !live.eventId) {
          await mouseClickCanvas(cdp);
        }
      }
    }
    else if (step.floor === "MT29" && step.eid === "thief") {
      // 29F thief (6,2): click (6,2) -> hero stops adjacent (5,2) -> multi-segment
      // dialogue -> openDoor (6,3) + thief leaves. Dismiss each dialogue segment
      // (Space) until the event fully settles, or (6,3) stays closed and the
      // upFloor (6,11) step fails.
      let live = st;
      if (live.x === x && live.y === y) {
        await pressKey(cdp, "Space");
      } else {
        await mouseClickTile(cdp, x, y);
        await waitMovementSettled(cdp);
      }
      for (let guard = 0; guard < 16; guard++) {
        live = await state(cdp);
        if (!live.lock && !live.eventId && !live.moving) break;
        if (live.lock || live.eventId) {
          await pressKey(cdp, "Space");
          await sleep(500);
        } else {
          await sleep(200);
        }
      }
    }
    else {
      await mouseClickTile(cdp, x, y);
      const after = await state(cdp);
      if (
        after.floor === st.floor &&
        !after.lock &&
        !after.eventId &&
        !after.hasChoices &&
        !after.moving
      ) {
        await repeatTargetClick(cdp, step, st.floor);
      }
    }
    return;
  }
  if (step.action === ACT.OLDMAN) {
    // The oldman dialog may already be open from the previous step (e.g. walking
    // onto the fakeWall x11y11 tile on 16F). If choices are shown, choose confirm.
    // If the dialog is already closing (action:hide), just let it settle.
    const st = await state(cdp);
    if (st.hasChoices || st.eventType === "hide") {
      if (st.hasChoices && st.eventType !== "hide") await choose(cdp, "confirm");
    } else if (st.lock || st.eventId) {
      await mouseClickCanvas(cdp);
    } else {
      await mouseClickTile(cdp, x, y);
    }
    return;
  }
  if (isMapClickAction(step.action)) {
    let st = await state(cdp);
    if (st.floor === step.floor && await targetSideEffectDone(cdp, step, x, y)) {
      return; // target's side effect already visible (auto-processed); accept step
    }
    if (step.action === ACT.KILL && st.floor === step.floor && st.x === x && st.y === y) {
      const ev = await targetEvent(cdp, step.floor, x, y);
      if (ev && ev.cls === "enemys") {
        for (const [ax, ay] of [[x, y + 1], [x, y - 1], [x - 1, y], [x + 1, y]]) {
          if (ax < 1 || ax > 13 || ay < 1 || ay > 13) continue;
          const adj = await targetEvent(cdp, step.floor, ax, ay);
          if (adj && adj.noPass) continue;
          await mouseClickTile(cdp, ax, ay);
          await waitMovementSettled(cdp);
          st = await state(cdp);
          if (st.x !== x || st.y !== y) break;
        }
      }
    }
    if (step.action === ACT.KILL && st.floor === step.floor && Math.abs(st.x - x) + Math.abs(st.y - y) === 1) {
      const ev = await targetEvent(cdp, step.floor, x, y);
      if (ev && (ev.cls === "enemys" || ev.trigger === "battle")) {
        await mouseClickTile(cdp, x, y);
        return;
      }
    }
    // hero 不相邻怪(Manhattan>1):清 stale action event 后直接点怪格,web automaticRoute
    // 寻路到怪并击杀(穿 yellowWall/门)。原 approach-tile 循环是 converter 漏 MT32 (6,10)
    // 先攻事件时的误诊断(把 (6,10) 当 pass 合并,hero 起点/click 目标全错);根因修后直接点目标。
    if (step.action === ACT.KILL && st.floor === step.floor && Math.abs(st.x - x) + Math.abs(st.y - y) > 1) {
      const ev = await targetEvent(cdp, step.floor, x, y);
      if (ev && (ev.cls === "enemys" || ev.trigger === "battle")) {
        await waitMovementSettled(cdp, 8000);
        st = await state(cdp);
        // 清 automaticRoute action 事件残留(换层/移动后 event=action 未 close,lockControl 拒点)
        if (st.lock && !st.moving && !st.hasChoices && (st.eventId === "action" || !st.eventId)) {
          await evalValue(
            cdp,
            String.raw`(function(){try{core.status.event=null;if(core.unlockControl)core.unlockControl();else core.status.lockControl=false;}catch(e){}return true})()`
          );
          await sleep(300);
        }
        await mouseClickTile(cdp, x, y);
        await waitMovementSettled(cdp, 10000);
        // 远点单次点击:automaticRoute 可能把 hero 寻路到相邻就停(没自动攻击)。
        // canRetryAdjacentTarget(KILL)=hero 相邻且怪还在 -> 再点一次触发战斗。
        await maybeRetryAdjacentTarget(cdp, step);
        return;
      }
    }
    if (step.action === ACT.EVENT_BATTLE && st.x === x && st.y === y) {
      if (!(st.lock || st.eventId || st.moving || (st.animateAsyncCount || 0) > 0)) {
        await mouseClickCanvas(cdp);
      }
    } else if (step.action === ACT.PASS && (step.eid === "upFloor" || step.eid === "downFloor")) {
      if (step.floor === "MT41" && x === 6 && y === 11 && st.floor === "MT41" && st.x === 6 && st.y === 4) {
        for (const [tx, ty] of [[6, 5], [6, 7], [6, 8], [6, 9], [6, 11]]) {
          st = await state(cdp);
          if (st.floor !== "MT41") break;
          await mouseClickTile(cdp, tx, ty);
          await waitMovementSettled(cdp);
        }
        return;
      }
      // Use only the real map click handler for stairs.
      await mouseClickTile(cdp, x, y);
      await maybeRetryAdjacentTarget(cdp, step);
      const after = await state(cdp);
      const floorChanged = after.floor !== st.floor;
      const dist = Math.abs(after.x - x) + Math.abs(after.y - y);
      if (
        dist >= 1 &&
        !floorChanged &&
        !after.lock &&
        !after.eventId &&
        !after.hasChoices &&
        !after.moving
      ) {
        const changed = after.hp !== st.hp || after.atk !== st.atk || after.def !== st.def ||
          after.money !== st.money || after.yk !== st.yk || after.bk !== st.bk || after.rk !== st.rk;
        if (changed) return;
        if (RUNTIME.targetClickOnly) {
          const retried = await repeatTargetClick(cdp, step, st.floor);
          const retryDist = Math.abs(retried.x - x) + Math.abs(retried.y - y);
          if (
            retryDist >= 1 &&
            retried.floor === st.floor &&
            !retried.lock &&
            !retried.eventId &&
            !retried.hasChoices &&
            !retried.moving
          ) {
            throw new Error(`target click stopped before stair x${x}y${y}: ${stateText(retried)}`);
          }
          return;
        }
        throw new Error(`single target click did not reach stair x${x}y${y}: ${stateText(after)}`);
      }
    } else {
      await mouseClickTile(cdp, x, y);
      await maybeRetryAdjacentTarget(cdp, step);
      let after = await state(cdp);
      if (after.moving) { await waitMovementSettled(cdp); after = await state(cdp); }
      // boss (skeletonCaptain/vampire 等): 从远处点击怪格 hero 走到相邻触发 boss
      // 对话(lock=action)但未战斗,先 Space 确认对话,再用键盘 arrow 朝怪触发战斗
      // (CLAUDE.md:boss 用键盘事件,如 MT50 redKing;MT10 captain 同)。
      if (step.action === ACT.KILL && after.floor === step.floor
          && Math.abs(after.x - x) + Math.abs(after.y - y) === 1
          && after.lock && after.eventId === "action") {
        const ev = await targetEvent(cdp, step.floor, x, y);
        if (ev && (ev.cls === "enemys" || ev.trigger === "battle")) {
          let st = after;
          for (let g = 0; g < 8 && (st.lock || st.eventId); g++) {
            await pressKey(cdp, "Space");
            await sleep(400);
            st = await state(cdp);
          }
          if (st.floor === step.floor && Math.abs(st.x - x) + Math.abs(st.y - y) === 1
              && !st.lock && !st.eventId && !st.moving && !st.hasChoices) {
            const dx = x - st.x, dy = y - st.y;
            await pressKey(cdp, dx > 0 ? "ArrowRight" : dx < 0 ? "ArrowLeft" : dy > 0 ? "ArrowDown" : "ArrowUp");
            await waitMovementSettled(cdp);
            // boss 战后 hero 可能未踏上怪格(击败对话挡),确认对话 + 点击怪格踏上去
            let st2 = await state(cdp);
            for (let g = 0; g < 8 && (st2.lock || st2.eventId); g++) {
              await pressKey(cdp, "Space");
              await sleep(400);
              st2 = await state(cdp);
            }
            if (st2.floor === step.floor && (st2.x !== x || st2.y !== y)
                && !st2.lock && !st2.eventId && !st2.moving && !st2.hasChoices
                && await targetSideEffectDone(cdp, step, x, y)) {
              await mouseClickTile(cdp, x, y);
              await waitMovementSettled(cdp);
            }
            return;
          }
        }
      }
      // fakeWall2 with afterOpenDoor setBlock (e.g. MT19 (6,3): break fakeWall2 ->
      // setBlock cross item). The click breaks fakeWall2 and triggers a setBlock
      // action event; the hero stops adjacent with lock=action:setBlock and the
      // spawned item is not yet collectable. Advance the setBlock action, then
      // re-click the target so the hero steps onto it / picks up the spawned
      // item. Without this the item stays uncollected (cross not picked -> later
      // zombie/vampire damage diverges because cross doubles atk vs them).
      let sawSetBlock = false;
      for (
        let guard = 0;
        guard < 5 && after.floor === step.floor && (after.x !== x || after.y !== y);
        guard += 1
      ) {
        if (
          after.lock &&
          after.eventId === "action" &&
          (after.eventType === "setBlock" || after.eventType === "setBgFgBlock")
        ) {
          sawSetBlock = true;
          await pressKey(cdp, "Space");
          await sleep(220);
          after = await state(cdp);
          continue;
        }
        if (
          sawSetBlock &&
          !after.lock &&
          !after.moving &&
          !after.eventId &&
          !after.hasChoices
        ) {
          await mouseClickTile(cdp, x, y);
          await sleep(300);
          after = await state(cdp);
          continue;
        }
        break;
      }
      const floorChanged = after.floor !== st.floor;
      const dist = Math.abs(after.x - x) + Math.abs(after.y - y);
      if (
        dist >= 1 &&
        !floorChanged &&
        !after.lock &&
        !after.eventId &&
        !after.hasChoices &&
        !after.moving
      ) {
        const changed = after.hp !== st.hp || after.atk !== st.atk || after.def !== st.def ||
          after.money !== st.money || after.yk !== st.yk || after.bk !== st.bk || after.rk !== st.rk;
        if (changed) return;
        if (await targetSideEffectDone(cdp, step, x, y)) return;
        const ev = await targetEvent(cdp, step.floor, x, y);
        if (step.action === ACT.ARRIVE && dist === 1 && isShopLikeEvent(ev, true)) return;
        if (RUNTIME.targetClickOnly) {
          const retried = await repeatTargetClick(cdp, step, st.floor);
          const retryDist = Math.abs(retried.x - x) + Math.abs(retried.y - y);
          const retryEv = await targetEvent(cdp, step.floor, x, y);
          if (step.action === ACT.ARRIVE && retryDist === 1 && isShopLikeEvent(retryEv, true)) return;
          if (
            retryDist >= 1 &&
            retried.floor === st.floor &&
            !retried.lock &&
            !retried.eventId &&
            !retried.hasChoices &&
            !retried.moving
          ) {
            throw new Error(`target click stopped before target x${x}y${y}: ${stateText(retried)}`);
          }
          return;
        }
        throw new Error(`single target click did not reach target x${x}y${y}: ${stateText(after)}`);
      }
    }
    return;
  }
  throw new Error(`unsupported action ${step.action} at ${step.floor} x${x}y${y}`);
}

async function maybeCloseMenu(cdp, step, next) {
  if (!next || next.action !== step.action) {
    if ((step.action === ACT.SHOP || step.action === ACT.MERCHANT) && (await state(cdp)).hasChoices) {
      try { await closeChoiceMenu(cdp); } catch (_) { /* menu auto-closed */ }
    }
  }
}

async function runOneStep(cdp, steps, oneBased, stop) {
  const step = steps[oneBased - 1];
  const [x, y] = step.pos;
  console.log(`[${tsStamp()}][${String(oneBased).padStart(3, "0")}] ${step.floor} x${x}y${y} ${step.action} ${step.eid || ""}`);
  // Formal verification is step-exact. Coalescing later expected states hid
  // incorrect offline auto attribution; adaptive coalescing belongs only to
  // explicit --record-only runs.
  const candidates = [oneBased];
  const structuralNext = steps[oneBased];
  if (step.action === ACT.PASS && structuralNext && structuralNext.action === ACT.CHANGE_FLOOR) {
    candidates.push(oneBased + 1);
  }
  let execStep = step;
  if (step.floor === "MT41" && step.pos[0] === 6 && [7, 8, 9].includes(step.pos[1])) {
    const stairIdx = candidates.find((idx) => {
      const cand = steps[idx - 1];
      return cand.floor === "MT41" && cand.action === ACT.PASS && cand.pos[0] === 6 && cand.pos[1] === 11;
    });
    if (stairIdx) execStep = steps[stairIdx - 1];
  }
  const already = await settleAlreadyCompletedStep(cdp, step);
  if (already) {
    console.log(`      -> already completed ${stateText(already)}`);
    await maybeCloseMenu(cdp, step, steps[oneBased]);
    return { state: already, consumed: oneBased };
  }
  const liveBeforeExec = await state(cdp);
  if (await sideEffectOnlySatisfied(cdp, liveBeforeExec, step)) {
    console.log(`      -> live side effect already completed ${stateText(liveBeforeExec)}`);
    await maybeCloseMenu(cdp, step, steps[oneBased]);
    return { state: liveBeforeExec, consumed: oneBased };
  }
  if (
    step.action === ACT.PICKUP &&
    steps[oneBased] &&
    steps[oneBased].action === ACT.CENTER_FLY &&
    valuesMatch(liveBeforeExec, expectedState(step)) &&
    liveBeforeExec.floor === step.floor &&
    (liveBeforeExec.x !== x || liveBeforeExec.y !== y) &&
    !liveBeforeExec.lock &&
    !liveBeforeExec.eventId &&
    !liveBeforeExec.moving &&
    !liveBeforeExec.hasChoices
  ) {
    const ev = await targetEvent(cdp, step.floor, x, y);
    if (!ev || ev.cls !== "items") {
      await mouseClickTile(cdp, x, y);
      const result = await waitForCandidates(cdp, steps, candidates, `arrive at cleared pre-centerFly pickup step ${oneBased}`, 8000);
      console.log(`      -> arrived for centerFly ${stateText(result.state)}`);
      return { state: result.state, consumed: oneBased };
    }
  }
  if (await targetAlreadyClearedForAction(cdp, liveBeforeExec, step)) {
    const result = await waitForCandidates(cdp, steps, candidates, `pre-cleared step ${oneBased}`, 1500);
    if (result.matchedStep !== oneBased) {
      console.log(`      -> auto-coalesced cleared target through step ${result.matchedStep}`);
    }
    console.log(`      -> ${stateText(result.state)}`);
    const consumed = result.matchedStep;
    await maybeCloseMenu(cdp, steps[consumed - 1], steps[consumed]);
    return { state: result.state, consumed };
  }
  // An ARRIVE step may carry auto_sweep side effects (e.g. MT19 (6,3) auto-picks
  // cross after breaking fakeWall2). Skipping it just because the next step is a
  // fly leaves those side effects untriggered -- the hero never reaches the tile,
  // the cross is never picked up, and later zombie/vampire damage diverges (cross
  // doubles atk vs those enemies). Only skip when the arrive has no auto side
  // effects. Snapshot does not record the cross flag, so valuesMatch alone cannot
  // detect this; the note is the signal.
  if (step.action === ACT.ARRIVE && steps[oneBased] && steps[oneBased].action === ACT.FLY
      && !(typeof step.note === "string" && step.note.indexOf("auto_sweep") >= 0)) {
    const live = await state(cdp);
    const expected = expectedState(step);
    if (
      live.floor === expected.floor &&
      valuesMatch(live, expected) &&
      !live.lock &&
      !live.eventId &&
      !live.moving &&
      !live.hasChoices
    ) {
      console.log(`      -> skipped pre-fly arrive ${stateText(live)}`);
      return { state: live, consumed: oneBased };
    }
  }
  const pre = await state(cdp);
  const menuStep = [ACT.SHOP, ACT.MERCHANT].includes(step.action);
  if ((pre.lock || pre.eventId || pre.moving || pre.hasChoices) && !(pre.hasChoices && menuStep)) {
    const preTimeout = pre.eventId === "action" && [ACT.KILL, ACT.EVENT_BATTLE, ACT.EVENT].includes(step.action)
      ? 180000
      : 15000;
    try {
      const result = await waitForCandidates(cdp, steps, candidates, `step ${oneBased}`, preTimeout, true);
      if (result.matchedStep !== oneBased) {
        console.log(`      -> coalesced through step ${result.matchedStep}`);
      }
      console.log(`      -> ${stateText(result.state)}`);
      const consumed = result.matchedStep;
      await maybeCloseMenu(cdp, steps[consumed - 1], steps[consumed]);
      return { state: result.state, consumed };
    } catch (e) {
      const settled = await state(cdp);
      if (settled.lock || settled.eventId || settled.moving || settled.hasChoices) throw e;
    }
  }
  await executeStep(cdp, execStep);
  const result = await waitForCandidates(cdp, steps, candidates, `step ${oneBased}`);
  if (result.matchedStep !== oneBased) {
    console.log(`      -> coalesced through step ${result.matchedStep}`);
  }
  console.log(`      -> ${stateText(result.state)}`);
  const consumed = result.matchedStep;
  await maybeCloseMenu(cdp, steps[consumed - 1], steps[consumed]);
  return { state: result.state, consumed };
}

async function runRecordOnly(cdp, walk, steps, args, stop) {
  const entries = [];
  for (let oneBased = args.startStep; oneBased <= stop;) {
    const step = steps[oneBased - 1];
    const [x, y] = step.pos;
    console.log(`[${tsStamp()}][${String(oneBased).padStart(3, "0")}] ${step.floor} x${x}y${y} ${step.action} ${step.eid || ""} [record]`);
    const beforeStep = await state(cdp);
    const candidates = coalesceCandidateIndexes(steps, oneBased).filter((idx) => idx <= stop);
    let after = beforeStep;
    let note = "";
    let consumedStep = oneBased;
    if (step.action === ACT.CHECK || step.action === ACT.CHANGE_FLOOR) {
      after = beforeStep;
    } else if (step.action === "auto_sweep") {
      // Offline bookkeeping marker for a battle=true auto-clear group. In live the
      // auto-sweep already ran; just let any pending sweep settle and read state.
      await waitIdle(cdp, 30000);
      after = await state(cdp);
    } else if (await targetAlreadyClearedForAction(cdp, beforeStep, step)) {
      const skipped = appendSkippedRecordStep(
        entries,
        oneBased,
        step,
        `自动处理：${step.floor} x${x}y${y} ${step.eid || step.action}`
      );
      if (skipped) {
        console.log(`      -> skipped; already covered by previous input ${stateText(beforeStep)}`);
        oneBased += 1;
        continue;
      }
      note = "live target already cleared by prior automatic handling";
      after = beforeStep;
    } else {
      await executeStep(cdp, step);
      const timeout = step.action === ACT.KILL || step.action === ACT.EVENT_BATTLE || step.action === ACT.EVENT
        ? 180000
        : 60000;
      after = await waitIdle(cdp, timeout);
      const next = steps[oneBased];
      const keepChoices = [ACT.SHOP, ACT.MERCHANT].includes(step.action) ||
        (step.action === ACT.TALK && ["shop", "blueShop", "trader"].includes(step.eid || "")) ||
        (next && [ACT.SHOP, ACT.MERCHANT].includes(next.action));
      if (after.hasChoices && !keepChoices) {
        await choose(cdp, "confirm");
        after = await waitIdle(cdp, timeout);
      }
      consumedStep = recordOnlyPositionMatchedStep(after, steps, candidates);
    }
    const handled = autoHandledNote(steps, oneBased, consumedStep);
    if (handled) note = note ? `${note}；${handled}` : handled;
    const expectedStep = steps[consumedStep - 1];
    const expectedAfter = expectedState(expectedStep);
    const strictMismatch = strictValueMismatchText(after, expectedAfter);
    // record-only adapts the walk to live (auto-bfs) states: mismatches are
    // expected (the source walk's expected states are auto-OFF/naive). Log them
    // as warnings but keep recording so strictWalk is built from live states.
    if (strictMismatch) {
      console.log(`      !! record-only value mismatch at step ${consumedStep}: ${strictMismatch} (live wins, adapting)`);
    }
    if (!(await stepMatches(cdp, after, expectedStep))) {
      console.log(`      !! record-only position/side-effect mismatch at step ${consumedStep}: ${mismatchText(after, expectedStep)} (live wins, adapting)`);
    }
    console.log(`      -> ${stateText(after)}${note ? ` (${note})` : ""}`);
    entries.push({
      startStep: oneBased,
      consumedStep,
      step,
      consumed: steps.slice(oneBased - 1, consumedStep).map((consumed, offset) => ({
        step: oneBased + offset,
        floor: consumed.floor,
        pos: consumed.pos,
        action: consumed.action,
        eid: consumed.eid || null,
        note: consumed.note || "",
      })),
      before: beforeStep,
      after,
      expectedAfter,
      strictMismatch,
      autoHandledNote: note,
    });
    await maybeCloseMenu(cdp, steps[consumedStep - 1], steps[consumedStep]);
    oneBased = consumedStep + 1;
  }
  const finalState = await state(cdp);
  writeRunLog(args, walk, entries, finalState);
  return finalState;
}

async function run() {
  const args = parseArgs(process.argv);
  RUNTIME.targetClickOnly = !!args.targetClickOnly;
  RUNTIME.strictHumanInput = !!args.strictHumanInput;
  if (RUNTIME.strictHumanInput) {
    if (args.loadSlot != null) throw new Error("--strict-human-input forbids --load-slot; load the save through the UI before starting proof replay");
    if (args.checkpointStart != null) throw new Error("--strict-human-input forbids checkpoint saves");
    if (args.undoSteps > 0 || args.undoOnFailure > 0) throw new Error("--strict-human-input forbids scripted undo");
  }
  const walk = JSON.parse(fs.readFileSync(args.walk, "utf8"));
  if (!walk.ok && !args.allowNotOk) throw new Error(`walk is not ok (mismatches=${(walk.mismatches||[]).length} errors=${(walk.errors||[]).length}); pass --allow-not-ok to force replay for conversion-logic validation`);
  if (!walk.ok) console.log(`[warn] walk.ok=false (mismatches=${(walk.mismatches||[]).length} errors=${(walk.errors||[]).length}) -- forcing replay per --allow-not-ok`);
  // Normalize English action aliases (e.g. "merchant" -> "商人") in place so all
  // downstream consumers (record-only, strict walk builder, writeRunLog) see the
  // canonical Chinese ACT constants.
  for (const s of walk.steps) s.action = normalizeAction(s.action);
  const steps = walk.steps;
  const stop = args.stopStep || steps.length;
  const cdp = await connectGameTarget();
  try {
    await ensurePageActive(cdp);
    if (args.loadSlot != null) {
      await loadSlot(cdp, args.loadSlot);
      console.log(`loaded save${args.loadSlot} ${stateText(await state(cdp))}`);
    }
    if (args.setAuto) {
      const liveAuto = await setAutoState(cdp, args.setAuto);
      console.log(`set auto ${autoSpecText(args.setAuto)} -> ${autoSpecText(liveAuto)}`);
    }
    if (args.expectAuto) {
      const liveAuto = await expectAutoState(cdp, args.expectAuto);
      console.log(`auto ok ${autoSpecText(liveAuto)}`);
    }
    if (args.undoSteps > 0) {
      console.log(`before undo ${stateText(await state(cdp))}`);
      await pressUndo(cdp, args.undoSteps);
      console.log(`after undo ${stateText(await waitIdle(cdp))}`);
      return;
    }
    let st = await state(cdp);
    console.log(`start ${stateText(st)}`);
    if (args.requireStart) {
      const expectedStart = stateFromSnapshot(steps[args.startStep - 1].before);
      const mismatch = strictMismatchText(st, expectedStart);
      if (mismatch || st.lock || st.eventId || st.moving || st.hasChoices) {
        const busy = st.lock || st.eventId || st.moving || st.hasChoices
          ? `; live is busy lock=${st.lock} moving=${st.moving} event=${st.eventId || "-"} choices=${st.hasChoices}`
          : "";
        throw new Error(`live state does not match start-before step ${args.startStep}: ${mismatch || "values ok"}${busy}; live=${stateText(st)}`);
      }
    }

    if (args.recordOnly) {
      await runRecordOnly(cdp, walk, steps, args, stop);
      return;
    }

    const entries = [];
    for (let oneBased = args.startStep; oneBased <= stop;) {
      let stepResult;
      const beforeStep = await state(cdp);
      try {
        stepResult = await runOneStep(cdp, steps, oneBased, stop);
      } catch (err) {
        if (args.undoOnFailure > 0) {
          console.log(`      !! ${err.message || String(err)}`);
          console.log(`      !! pressing undo x${args.undoOnFailure} then retrying step ${oneBased}`);
          await pressUndo(cdp, args.undoOnFailure);
          await waitIdle(cdp);
          stepResult = await runOneStep(cdp, steps, oneBased, stop);
        } else {
          throw err;
        }
      }
      st = stepResult.state;
      const consumedStep = stepResult.consumed;
      const consumedExpected = expectedState(steps[consumedStep - 1]);
      entries.push({
        startStep: oneBased,
        consumedStep,
        step: steps[oneBased - 1],
        consumed: steps.slice(oneBased - 1, consumedStep).map((step, offset) => ({
          step: oneBased + offset,
          floor: step.floor,
          pos: step.pos,
          action: step.action,
          eid: step.eid || null,
          note: step.note || "",
        })),
        before: beforeStep,
        after: st,
        expectedAfter: consumedExpected,
        strictMismatch: strictMismatchText(st, consumedExpected),
        autoHandledNote: autoHandledNote(steps, oneBased, consumedStep),
      });
      // Stage checkpoint chain: 101, 102, 103, ... every N successful steps.
      if (args.checkpointStart != null && oneBased % args.checkpointEvery === 0) {
        const slot = args.checkpointStart + Math.floor(oneBased / args.checkpointEvery) - 1;
        await saveSlot(cdp, slot);
        console.log(`      :: checkpoint save${slot} @ step ${oneBased}`);
      }
      oneBased = stepResult.consumed + 1;
    }
    writeRunLog(args, walk, entries, st);
  } finally {
    cdp.close();
  }
}

run().catch((err) => {
  console.error(err.stack || String(err));
  process.exit(1);
});
