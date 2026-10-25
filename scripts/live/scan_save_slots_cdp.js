#!/usr/bin/env node
// Compare live slots 1-59 against the morning exports (detect any mutation).
const fs = require("node:fs");
const path = require("node:path");
const ROOT = path.resolve(__dirname, "..", "..");
const CDP_LIST = "http://127.0.0.1:9222/json/list";

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

async function main() {
  const cdp = await connect();
  try {
    const payload = await evaluate(cdp, `new Promise(function(resolve){
      var out = [];
      var chain = Promise.resolve();
      for (var i = 1; i <= 59; i++) {
        (function (n) {
          chain = chain.then(function () {
            return new Promise(function (res2) {
              try {
                core.getSave(n, function (data) {
                  if (!data) { out.push([n, 'EMPTY']); return res2(); }
                  var h = data.hero || {};
                  var t = (h.items && h.items.tools) || {};
                  out.push([n, data.floorId, h.hp, h.atk, h.def, h.money,
                    t.yellowKey || 0, t.blueKey || 0, t.redKey || 0,
                    data.time || '']);
                  res2();
                });
              } catch (e) { out.push([n, 'ERR']); res2(); }
            });
          });
        })(i);
      }
      chain.then(function () { resolve(JSON.stringify(out)); });
    })`);
    const live = JSON.parse(payload);
    let diffs = 0;
    for (const row of live) {
      const n = row[0];
      const expPath = path.join(ROOT, "outputs", "checkpoints_20261024", `save${String(n).padStart(2, "0")}_slot_raw.json`);
      let exp = null;
      try {
        const d = JSON.parse(fs.readFileSync(expPath, "utf8"));
        const h = d.hero || {};
        exp = [d.floorId, h.hp, h.atk, h.def, h.money,
          (h.items.tools || {}).yellowKey || 0, (h.items.tools || {}).blueKey || 0,
          (h.items.tools || {}).redKey || 0];
      } catch (e) { exp = null; }
      const cur = row.slice(1, 9);
      const same = exp && JSON.stringify(cur) === JSON.stringify(exp);
      if (!exp || !same) {
        diffs += 1;
        console.log(`slot ${n}: LIVE=${JSON.stringify(cur)} time=${row[9]} EXPORT=${JSON.stringify(exp)}`);
      }
    }
    console.log(`scanned 59 slots, ${diffs} differ/missing-export`);
  } finally { cdp.close(); }
}
main().catch((e) => { console.error(e.stack || String(e)); process.exit(1); });
