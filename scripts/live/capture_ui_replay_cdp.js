#!/usr/bin/env node
// Passive capture for the game's own UI replay (设置-同步存档-回放和下载录像-
// 从头回放录像). Installs observer hooks ONLY (no startGame, no flag
// enforcement — the game's own flow initializes everything, proven working by
// the user), then waits for the replay to finish and dumps the statlog.
//
// Usage: node tmp/overnight/ui_replay_capture.js --out outputs/.../capture57_ui.json
//  - install hooks
//  - poll until replaying==false and the statlog stops growing (or timeout)
const fs = require("node:fs");
const path = require("node:path");
const ROOT = path.resolve(__dirname, "..", "..");
const CDP_LIST = "http://127.0.0.1:9222/json/list";

function parseArgs(argv) {
  const out = { out: null, timeout: 1800000 };
  for (let i = 2; i < argv.length; i += 1) {
    if (argv[i] === "--out") out.out = path.resolve(argv[++i]);
    else if (argv[i] === "--timeout-ms") out.timeout = Number(argv[++i]);
    else throw new Error("unknown arg " + argv[i]);
  }
  if (!out.out) throw new Error("--out required");
  return out;
}

async function getJson(url) { const r = await fetch(url); return r.json(); }
async function connect() {
  const targets = await getJson(CDP_LIST);
  const target = targets.find((t) => t.url && t.url.includes("h5mota.com/games/51"));
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  let id = 1; const pending = new Map();
  ws.addEventListener("message", (ev) => {
    const m = JSON.parse(ev.data);
    if (!m.id || !pending.has(m.id)) return;
    const { resolve, reject } = pending.get(m.id);
    pending.delete(m.id);
    m.error ? reject(new Error(JSON.stringify(m.error))) : resolve(m.result);
  });
  await new Promise((res, rej) => {
    ws.addEventListener("open", res, { once: true });
    ws.addEventListener("error", rej, { once: true });
  });
  return { close: () => ws.close(), send(method, params) {
    const i = id++;
    return new Promise((resolve, reject) => {
      pending.set(i, { resolve, reject });
      ws.send(JSON.stringify({ id: i, method, params }));
    });
  } };
}
async function evaluate(cdp, expression) {
  const r = await cdp.send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
  return r.result.value;
}
function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

const HOOKS = `(() => {
  if (window.__uiCapture) return JSON.stringify({already: true});
  const snap = () => {
    const h = core.status.hero, p = h.loc, t = h.items.tools || {};
    return {f: core.status.floorId, x: p.x, y: p.y, hp: h.hp, atk: h.atk, def: h.def,
      yk: t.yellowKey || 0, bk: t.blueKey || 0, rk: t.redKey || 0, g: h.money || 0,
      event: core.status.event && core.status.event.id || null};
  };
  window.__uiCapture = {statlog: [], autoAnswers: [], tolerated: []};
  const cap = window.__uiCapture;
  if (!core.control.__origDRA) core.control.__origDRA = core.control._doReplayAction;
  const original = core.control.__origDRA;
  core.control._doReplayAction = function (action) {
    if (cap.current) cap.current.after = snap();
    cap.current = {index: cap.statlog.length, action: action, before: snap()};
    cap.statlog.push(cap.current);
    let r;
    try { r = original.apply(this, arguments); }
    catch (err) {
      cap.tolerated.push({action: String(action), index: cap.current.index,
        crash: String(err && err.stack || err).slice(0, 150)});
      if (cap.current) cap.current.after = snap();
      cap.current = null;
      setTimeout(function () { try { core.control.replay.call(core.control); } catch (e2) {} }, 60);
      return true;
    }
    if (!r && !(core.status.event && core.status.event.id)) {
      cap.tolerated.push({action: String(action), index: cap.current.index});
      if (cap.current) cap.current.after = snap();
      cap.current = null;
      setTimeout(function () { try { core.control.replay.call(core.control); } catch (e2) {} }, 60);
      return true;
    }
    return r;
  };
  // _replay_error funnel tolerance (save57 lineage misclicks)
  if (!core.control.__origRepErr) core.control.__origRepErr = core.control._replay_error;
  core.control._replay_error = function (action) {
    cap.tolerated.push({action: String(action), at: cap.statlog.length, via: 'replay_error'});
    try {
      if (core.status.event && core.status.event.data
          && typeof core.status.event.data.no === 'function') {
        core.status.event.data.no.call(core.status.event.data);
      }
    } catch (e) {}
    core.status.replay.failed = false;
    core.status.replay.replaying = true;
    setTimeout(function () { try { core.control.replay.call(core.control); } catch (e2) {} }, 60);
  };
  // async confirmBox answerer (mouse-answered boxes leave no route token)
  cap._poll = setInterval(() => {
    try {
      if (!core.status.event || core.status.event.id !== 'confirmBox') return;
      if (!core.status.replay || !core.status.replay.replaying || cap._answering) return;
      const data = core.status.event.data || {};
      const text = String(data.text || core.status.event.text || core.status.event.ui || '');
      const sel = /手册/.test(text) ? 0 : 1;
      cap._answering = true;
      cap.autoAnswers.push({text: text.slice(0, 80), sel: sel});
      cap.current = {index: cap.statlog.length, action: 'auto:confirm:' + sel, before: snap()};
      cap.statlog.push(cap.current);
      try {
        const cb = sel === 0 ? data.yes : data.no;
        if (typeof cb === 'function') cb.call(core.status.event.data);
      } catch (e) {}
      if (cap.current) cap.current.after = snap();
      cap.current = null;
      cap._answering = false;
      setTimeout(function () { try { core.control.replay.call(core.control); } catch (e2) {} }, 60);
    } catch (e) {}
  }, 5);
  return JSON.stringify({installed: true});
})()`;

async function main() {
  const opt = parseArgs(process.argv);
  const cdp = await connect();
  try {
    const inst = await evaluate(cdp, HOOKS);
    console.log("hooks:", inst);
    // wait for the replay to start and finish
    const deadline = Date.now() + opt.timeout;
    let lastLen = -1;
    let lastChange = Date.now();
    let sawReplaying = false;
    while (Date.now() < deadline) {
      await sleep(1000);
      const st = JSON.parse(await evaluate(cdp, `(() => JSON.stringify({
        replaying: !!(core.status.replay && core.status.replay.replaying),
        failed: !!(core.status.replay && core.status.replay.failed),
        len: window.__uiCapture ? window.__uiCapture.statlog.length : -1,
        floor: core.status.floorId
      }))()`));
      if (st.len !== lastLen) { lastLen = st.len; lastChange = Date.now(); }
      if (st.replaying) sawReplaying = true;
      process.stdout.write(`\rstatlog=${st.len} replaying=${st.replaying} floor=${st.floor}   `);
      if (sawReplaying && !st.replaying && Date.now() - lastChange > 5000) {
        console.log("\nreplay finished");
        break;
      }
      if (!sawReplaying && st.len > 0 && Date.now() - lastChange > 20000) {
        console.log("\nno replay started but statlog growing stopped — dumping anyway");
        break;
      }
    }
    const bundle = JSON.parse(await evaluate(cdp, `(() => {
      const cap = window.__uiCapture;
      if (cap && cap.current && !cap.current.after) {
        cap.current.after = {f: core.status.floorId};
      }
      return JSON.stringify({statlog: cap.statlog, autoAnswers: cap.autoAnswers,
        tolerated: cap.tolerated,
        failed: !!(core.status.replay && core.status.replay.failed)});
    })()`));
    fs.mkdirSync(path.dirname(opt.out), { recursive: true });
    fs.writeFileSync(opt.out, JSON.stringify({
      schema: "mota.recording.capture.v1",
      capture: { speed: "ui", nativeReplayFailed: bundle.failed },
      statlog: bundle.statlog,
      autoAnswers: bundle.autoAnswers,
      tolerated: bundle.tolerated,
    }, null, 2), "utf8");
    console.log("saved:", opt.out, "statlog:", bundle.statlog.length,
      "answers:", bundle.autoAnswers.length, "tolerated:", bundle.tolerated.length);
  } finally { cdp.close(); }
}
main().catch((e) => { console.error(e.stack || String(e)); process.exit(1); });
