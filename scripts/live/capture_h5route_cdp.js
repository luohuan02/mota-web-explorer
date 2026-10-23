#!/usr/bin/env node
/**
 * Capture a native h5mota .h5route into a provenance bundle.
 *
 * This is an investigation/capture tool, not a route verifier. It uses the
 * game's own LZString + core.decodeRoute implementation, then records the
 * replay action pre-states. The resulting raw route/statlog lets the semantic
 * converter retain action order without treating the recording's values as
 * state corrections.
 *
 * Usage:
 *   node scripts/live/capture_h5route_cdp.js --recording best/foo.h5route \
 *     --out outputs/results/foo_capture.json --speed 100
 */
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const CDP_LIST = "http://127.0.0.1:9222/json/list";

function args(argv) {
  const out = { recording: null, out: null, speed: 100, timeout: 900000 };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--recording") out.recording = path.resolve(argv[++i]);
    else if (arg === "--out") out.out = path.resolve(argv[++i]);
    else if (arg === "--speed") out.speed = Number(argv[++i]);
    else if (arg === "--timeout-ms") out.timeout = Number(argv[++i]);
    else throw new Error(`unknown argument: ${arg}`);
  }
  if (!out.recording || !out.out) throw new Error("--recording and --out are required");
  if (!Number.isFinite(out.speed) || out.speed <= 0) throw new Error("--speed must be positive");
  return out;
}

async function json(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`GET ${url} failed: ${response.status}`);
  return response.json();
}

async function connect() {
  const targets = await json(CDP_LIST);
  const target = targets.find((t) => t.url && t.url.includes("h5mota.com/games/51"));
  if (!target) throw new Error("no h5mota game tab on external port 9222");
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  let nextId = 1;
  const pending = new Map();
  ws.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (!message.id || !pending.has(message.id)) return;
    const entry = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) entry.reject(new Error(JSON.stringify(message.error)));
    else entry.resolve(message.result);
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

async function evaluate(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}

function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

async function reloadAndWait(cdp) {
  // Reload the game tab so stale hooks from a prior capture (setHeroLoc /
  // _doReplayAction / automaticRoute wrappers) are cleared before we install
  // fresh ones. Without this, hooks stack across captures and the statlog
  // doubles (718 -> 1436). Returns when core is defined again.
  try { await cdp.send("Page.enable"); } catch (e) { /* some targets lack Page */ }
  try { await cdp.send("Page.reload", { ignoreCache: false }); } catch (e) { return; }
  for (let i = 0; i < 60; i += 1) {
    await sleep(1000);
    try {
      const ready = await evaluate(cdp, `typeof core!=="undefined" && typeof core.status!=="undefined"`);
      if (ready) return;
    } catch (e) { /* page still reloading */ }
  }
  throw new Error("page did not become ready after reload");
}

async function main() {
  const opt = args(process.argv);
  const content = fs.readFileSync(opt.recording, "utf8").trim();
  const recordingSha256 = crypto.createHash("sha256").update(content).digest("hex");
  const cdp = await connect();
  try {
    const init = await evaluate(cdp, `(() => {
      const encoded = ${JSON.stringify(content)};
      const outer = JSON.parse(LZString.decompressFromBase64(encoded));
      const tokens = core.decodeRoute(LZString.decompressFromBase64(outer.route));
      const snap = () => {
        const h = core.status.hero, p = h.loc, t = h.items.tools || {};
        return {f:core.status.floorId,x:p.x,y:p.y,hp:h.hp,atk:h.atk,def:h.def,
          yk:t.yellowKey||0,bk:t.blueKey||0,rk:t.redKey||0,g:h.money||0,
          event:core.status.event && core.status.event.id || null};
      };
      window.__recordingSeedCapture = {route:tokens, statlog:[], current:null, paths:[], pollTrace:[], _curMove:null, startedAt:Date.now()};
      const original = core.control._doReplayAction;
      if (!original) throw new Error("core.control._doReplayAction is unavailable");
      core.control._doReplayAction = function(action) {
        const capture = window.__recordingSeedCapture;
        if (capture.current) capture.current.after = snap();
        capture.current = {index:capture.statlog.length, action:action, before:snap()};
        capture.statlog.push(capture.current);
        return original.apply(this, arguments);
      };
      // Capture per-tile path per move:x:y. recording_to_game.py needs the exact
      // intermediate tiles (incl. fakeWall tiles auto-broken) to reproduce 2atk
      // recordings whose sword-pickup paths go_to_decomposed cannot follow.
      //
      // Mechanism (inspected live): _doReplayAction("move:x:y") -> core.automaticRoute
      // -> sets autoStepRoutes + calls core.moveAction()/setTimeout chain (async,
      // 50ms/step) OR core.moveDirectly (teleport). autoStepRoutes is empty after
      // automaticRoute returns, so reading it post-call (old approach) yields [].
      // Instead hook the lowest-level position setter core.control.setHeroLoc:
      // every x/y set fires (sync within automaticRoute, or async in the setTimeout
      // chain). We keep _curMove non-null across the whole move (not just the sync
      // part) by NOT nulling it in the automaticRoute wrapper; instead the NEXT
      // automaticRoute call closes the previous move. A 5ms pollTrace is the
      // async-safe fallback (catches tiles held ~50ms even if setHeroLoc is missed).
      const cap0 = window.__recordingSeedCapture;
      const origSHL = core.control.setHeroLoc;
      core.control.setHeroLoc = function(name, value, noGather) {
        const ret = origSHL.apply(this, arguments);
        const cm = cap0._curMove;
        if (cm && (name === "x" || name === "y")) {
          const h = core.status.hero.loc;
          const arr = cm.shl;
          const last = arr[arr.length - 1];
          if (!last || last.x !== h.x || last.y !== h.y) arr.push({x: h.x, y: h.y});
        }
        return ret;
      };
      let _lastPoll = null;
      cap0._pollHandle = setInterval(() => {
        if (!core.status || !core.status.hero) return;
        const f = core.status.floorId, h = core.status.hero.loc;
        const cur = {i: cap0.statlog.length, f, x: h.x, y: h.y};
        if (!_lastPoll || _lastPoll.f !== cur.f || _lastPoll.x !== cur.x || _lastPoll.y !== cur.y) {
          cap0.pollTrace.push(cur);
          _lastPoll = cur;
        }
      }, 5);
      const origAR = core.automaticRoute;
      if (typeof origAR === "function") {
        core.automaticRoute = function(tx, ty) {
          // close+drop any still-open move (shouldn't happen if moves are sync)
          cap0._curMove = null;
          const sf = core.status.floorId, sx = core.status.hero.loc.x, sy = core.status.hero.loc.y;
          cap0._curMove = {floor: sf, sx: sx, sy: sy, tx: tx, ty: ty, shl: []};
          const ret = origAR.apply(this, arguments);
          // Close IMMEDIATELY after origAR returns. pollTrace evidence (only
          // endpoints seen across 718 actions at 5ms poll) shows replay movement
          // at speed=100 is synchronous within origAR, so all per-tile setHeroLoc
          // calls fired during origAR are captured in shl. Nulling here prevents
          // async-tail / non-movement setHeroLoc calls from bleeding into this
          // move (the old "keep open" approach produced 22-tile loops = bleed).
          const h = core.status.hero.loc;
          const m = cap0._curMove;
          m.heroAtDest = (h.x === tx && h.y === ty);
          m.endX = h.x; m.endY = h.y;
          cap0.paths.push(m);
          cap0._curMove = null;
          return ret;
        };
      }
      core.startGame(outer.hard || "", outer.seed, tokens);
      core.status.replay.pausing = false;
      core.status.replay.speed = ${JSON.stringify(opt.speed)};
      return JSON.stringify({seed:outer.seed,hard:outer.hard,routeLength:tokens.length});
    })()`);
    console.log("capture started", init);
    const deadline = Date.now() + opt.timeout;
    while (Date.now() < deadline) {
      await sleep(400);
      const state = JSON.parse(await evaluate(cdp, `(() => JSON.stringify({
        replaying:!!(core.status.replay && core.status.replay.replaying),
        failed:!!(core.status.replay && core.status.replay.failed),
        captured:(window.__recordingSeedCapture && window.__recordingSeedCapture.statlog.length)||0
      }))()`));
      if (!state.replaying || state.failed) break;
    }
    const bundle = JSON.parse(await evaluate(cdp, `(() => {
      const cap = window.__recordingSeedCapture;
      if (cap && cap.current && !cap.current.after) {
        const h=core.status.hero,p=h.loc,t=h.items.tools||{};
        cap.current.after={f:core.status.floorId,x:p.x,y:p.y,hp:h.hp,atk:h.atk,def:h.def,
          yk:t.yellowKey||0,bk:t.blueKey||0,rk:t.redKey||0,g:h.money||0,event:core.status.event&&core.status.event.id||null};
      }
      if (cap._pollHandle) { clearInterval(cap._pollHandle); cap._pollHandle = null; }
      // close last move (async tail may leave _curMove open)
      if (cap._curMove) { cap.paths.push(cap._curMove); cap._curMove = null; }
      return JSON.stringify({route:cap.route,statlog:cap.statlog,paths:cap.paths,pollTrace:cap.pollTrace||[],replaying:!!core.status.replay.replaying,failed:!!core.status.replay.failed});
    })()`));
    if (bundle.replaying) throw new Error("capture timed out while native replay was still running");
    const output = {
      schema: "mota.recording.capture.v1",
      recording: { path: opt.recording, sha256: recordingSha256 },
      capture: { speed: opt.speed, nativeReplayFailed: bundle.failed },
      route: bundle.route,
      statlog: bundle.statlog,
      paths: bundle.paths || [],
      pollTrace: bundle.pollTrace || [],
      // Semantic extraction is intentionally a later explicit step: raw capture
      // is immutable evidence and does not guess choices/NPC/tool meanings.
      semantic_actions: [],
    };
    fs.mkdirSync(path.dirname(opt.out), { recursive: true });
    fs.writeFileSync(opt.out, JSON.stringify(output, null, 2), "utf8");
    console.log(JSON.stringify({out:opt.out, route:output.route.length, statlog:output.statlog.length,
      failed:bundle.failed, recordingSha256}, null, 2));
  } finally {
    cdp.close();
  }
}

main().catch((error) => { console.error(error.stack || String(error)); process.exit(1); });
