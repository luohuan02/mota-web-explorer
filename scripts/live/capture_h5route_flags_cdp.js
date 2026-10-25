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
  // fresh ones. Page.reload does NOT reliably clear them (observed 1x->2x->4x
  // statlog doubling and __origDRA capturing an already-wrapped function);
  // drive the reload from the page itself via location.reload().
  try { await evaluate(cdp, `window.__captureHooksDirty = true; 1`); } catch (e) { /* stale page */ }
  try { await evaluate(cdp, `setTimeout(function(){ location.reload(); }, 0); 1`); } catch (e) { /* ignore */ }
  for (let i = 0; i < 90; i += 1) {
    await sleep(1000);
    try {
      // fresh context: core defined AND the pre-reload marker is gone
      const ready = await evaluate(cdp, `typeof core!=="undefined" && typeof core.status!=="undefined" && !window.__captureHooksDirty`);
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
      window.__recordingSeedCapture = {route:tokens, statlog:[], current:null, paths:[], pollTrace:[], autoAnswers:[], tolerated:[], _curMove:null, startedAt:Date.now()};
      // Routes whose head carries the SET_AUTO menu (help + choices:4...)
      // toggle auto ON natively during replay; routes without it (menu set
      // via the settings UI, outside the route buffer) need the flag base
      // enforced during the opening phase (see the per-action injection).
      window.__recordingSeedCapture.__hasAutoMenu = tokens.slice(0, 12).some((t) => t === "help");
      // Hook-stacking guard: Page.reload does NOT reliably clear prior
      // captures' wrappers (observed 1x -> 2x -> 4x statlog doubling), so
      // always resolve the TRUE original through a stable marker and wrap it
      // exactly once per page load.
      if (!core.control.__origDRA) core.control.__origDRA = core.control._doReplayAction;
      const original = core.control.__origDRA;
      if (!original) throw new Error("core.control._doReplayAction is unavailable");
      // Truthy return from _doReplayAction means "I schedule the next replay
      // tick myself" (move/dialog continuations chain core.control.replay()).
      // A failed action schedules nothing — the tolerance path below must
      // reschedule manually or the loop deadlocks (observed: replaying=true,
      // 1400 tokens left, statlog frozen).
      const replayLoop = core.control.replay;
      // Master tolerance: _replay_error is the single funnel for replay
      // failures (the move/fly handlers call it INTERNALLY on route failures
      // — they set replay.failed=true, open the "回到上个节点" box and set
      // replaying=false BEFORE returning, so neither a falsy-return nor a
      // poll can see them). Tolerate = dismiss the dialog, clear the failure
      // state, log, and reschedule the loop. The save-route misclicks being
      // captured were no-ops in the user's own play; real desyncs surface as
      // end-state mismatches vs the save's hero.
      if (!core.control.__origRepErr) core.control.__origRepErr = core.control._replay_error;
      core.control._replay_error = function (action) {
        const capture = window.__recordingSeedCapture;
        capture.tolerated.push({action: String(action), at: capture.statlog.length});
        try {
          if (core.status.event && core.status.event.data
              && typeof core.status.event.data.no === "function") {
            core.status.event.data.no.call(core.status.event.data);
          }
        } catch (e) { /* keep going */ }
        core.status.replay.failed = false;
        core.status.replay.replaying = true;
        setTimeout(function () { try { replayLoop.call(core.control); } catch (e2) { } }, 60);
      };
      core.control._doReplayAction = function(action) {
        const capture = window.__recordingSeedCapture;
        // Lineage flag base, enforced per-action for the whole route when the
        // route has no SET_AUTO menu (the lineage toggled auto via the settings
        // UI, outside the route buffer — save2/57 evidence: auto all-on from
        // game start to MT10+). The injection right after startGame gets
        // overwritten by the opening event's async flag init, hence per-action.
        if (!capture.__hasAutoMenu) {
          const fl = core.status.hero && core.status.hero.flags;
          if (fl && (!fl.__auto__ || fl.__auto__.battle !== true
                     || fl.__auto__.item !== true || fl.__auto__.wall !== true)) {
            fl.__auto__ = {battle: true, item: true, wall: true};
          }
          if (fl && !fl["额外功能开关"]) fl["额外功能开关"] = 1;
        }
        // Answer any PENDING confirmBox (mouse-answered in live play, no token
        // in the route buffer) BEFORE the next token runs, synchronously.
        // Text rules: fight-invitations -> deny(1); key-missed/empty boxes ->
        // dismiss(1); otherwise confirm(0). Every answer is logged for audit;
        // wrong answers surface as end-state mismatches vs the save's hero.
        if (core.status.event && core.status.event.id === "confirmBox") {
          const text = String((core.status.event.text || core.status.event.data && core.status.event.data.text || ""));
          let sel = 0;
          if (/魔王|挑战|进攻|战斗|钥匙|不足|无法/.test(text) || !text) sel = 1;
          capture.autoAnswers.push({text: text.slice(0, 80), sel: sel});
          capture.current = {index:capture.statlog.length, action:"auto:choices:" + sel, before:snap()};
          capture.statlog.push(capture.current);
          try { original.call(core.control, "choices:" + sel); } catch (e) { /* keep going */ }
          if (capture.current) capture.current.after = snap();
          capture.current = null;
        }
        if (capture.current) capture.current.after = snap();
        capture.current = {index:capture.statlog.length, action:action, before:snap()};
        capture.statlog.push(capture.current);
        let r;
        try {
          r = original.apply(this, arguments);
        } catch (err) {
          // Route failures THROW here (automaticRoute cannot reach a locked
          // door / blocked target): tolerate as a no-op, same rationale as the
          // falsy-return case below.
          capture.tolerated.push({action: String(action), index: capture.current.index,
            crash: String(err && err.stack || err).slice(0, 200),
            f: capture.current.before.f, x: capture.current.before.x, y: capture.current.before.y});
          if (capture.current) capture.current.after = snap();
          capture.current = null;
          setTimeout(function () { try { replayLoop.call(core.control); } catch (e2) { } }, 60);
          return true;
        }
        // Tolerate no-op actions: the engine errors ("录像文件出错") whenever
        // _doReplayAction returns falsy, but save-route misclicks (e.g. click
        // on a locked door with 0 yk at MT4 (8,8)) were no-ops in the user's
        // own play. Tolerate a falsy return when NO dialog opened — the state
        // is unchanged, so the replay continues faithfully. Real desyncs
        // surface as end-state mismatches vs the save's hero.
        if (!r && !(core.status.event && core.status.event.id)) {
          capture.tolerated.push({action: String(action), index: capture.current.index,
            f: capture.current.before.f, x: capture.current.before.x, y: capture.current.before.y});
          if (capture.current) capture.current.after = snap();
          capture.current = null;
          setTimeout(function () { try { replayLoop.call(core.control); } catch (e2) { } }, 60);
          return true;
        }
        return r;
      };
      // Lineage flag base is applied AFTER startGame (see below) — startGame
      // resets hero.flags, so injecting earlier is a no-op.
      // Mouse-answered confirmBoxes are handled by the 5ms poll below (the box
      // opens asynchronously, so neither a _doReplayAction post-check nor a
      // drawConfirmBox wrapper can catch it reliably).
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
      // Watchdog: the replay loop relies on each action's handler chaining the
      // next tick; tolerated no-ops / async dialogs can leave it unscheduled
      // (observed: replaying=true, 1400 tokens left, statlog frozen). Re-kick
      // after 1.5s of no statlog progress.
      let _wdLen = -1;
      let _wdChange = Date.now();
      cap0._watchdog = setInterval(() => {
        try {
          if (!core.status.replay || !core.status.replay.replaying) return;
          if (core.status.replay.animate || core.status.replay.failed) return;
          if (core.status.event && core.status.event.id) return;
          if (core.status.heroMoving) return;
          if (cap0.statlog.length !== _wdLen) {
            _wdLen = cap0.statlog.length;
            _wdChange = Date.now();
            return;
          }
          if (Date.now() - _wdChange > 1500) {
            _wdChange = Date.now();
            replayLoop.call(core.control);
          }
        } catch (e) { /* keep going */ }
      }, 300);
      cap0._pollHandle = setInterval(() => {
        if (!core.status || !core.status.hero) return;
        const f = core.status.floorId, h = core.status.hero.loc;
        const cur = {i: cap0.statlog.length, f, x: h.x, y: h.y};
        if (!_lastPoll || _lastPoll.f !== cur.f || _lastPoll.x !== cur.x || _lastPoll.y !== cur.y) {
          cap0.pollTrace.push(cur);
          _lastPoll = cur;
        }
        // Async confirmBox answerer: live-play mouse answers leave no token in
        // a save's route buffer; the box opens asynchronously AFTER the action
        // returns (drawConfirmBox post-check misses it), and the engine errors
        // ("录像文件出错") if the next token arrives while it is open. Poll
        // every 5ms and answer synchronously. Text rules: fight invitations ->
        // deny(1); key-missed/empty -> dismiss(1); else confirm(0). Logged in
        // autoAnswers; wrong answers show up as end-state mismatches.
        if (core.status.event && core.status.event.id === "confirmBox"
            && core.status.replay && core.status.replay.replaying && !cap0._answering) {
          // The box's answer callbacks live in event.data.yes/no (the replay
          // engine's choices:N handler does NOT close confirmBoxes — tested).
          // Default = no/dismiss (misclick boxes were dismissed in live play);
          // 手册-type boxes = yes. Wrong answers surface as end-state
          // mismatches vs the save's hero.
          const data = core.status.event.data || {};
          const text = String((data.text || core.status.event.text || core.status.event.ui || ""));
          const sel = /手册/.test(text) ? 0 : 1;
          cap0._answering = true;
          cap0.autoAnswers.push({text: text.slice(0, 80), sel: sel});
          cap0.current = {index: cap0.statlog.length, action: "auto:confirm:" + sel, before: snap()};
          cap0.statlog.push(cap0.current);
          try {
            const cb = sel === 0 ? data.yes : data.no;
            if (typeof cb === "function") cb.call(core.status.event.data);
          } catch (e) { /* keep going */ }
          if (cap0.current) cap0.current.after = snap();
          cap0.current = null;
          cap0._answering = false;
          // the interrupted action never scheduled the next tick
          setTimeout(function () { try { core.control.replay.call(core.control); } catch (e2) { } }, 60);
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
      // Lineage flag base is enforced per-action in the _doReplayAction
      // wrapper (a one-shot injection here is overwritten by the opening
      // event's async flag init).
      core.status.replay.pausing = false;
      core.status.replay.speed = ${JSON.stringify(opt.speed)};
      return JSON.stringify({seed:outer.seed,hard:outer.hard,routeLength:tokens.length,
        hasAutoMenu:window.__recordingSeedCapture.__hasAutoMenu});
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
      return JSON.stringify({route:cap.route,statlog:cap.statlog,paths:cap.paths,pollTrace:cap.pollTrace||[],autoAnswers:cap.autoAnswers||[],tolerated:cap.tolerated||[],replaying:!!core.status.replay.replaying,failed:!!core.status.replay.failed});
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
      autoAnswers: bundle.autoAnswers || [],
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
