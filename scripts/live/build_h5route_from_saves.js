#!/usr/bin/env node
// Build .h5route files from save route buffers (browser LZString).
// outer = {name:"51", version:"Ver 3.0", hard:"", seed:1352540133, route:<save.route>}
const fs = require("node:fs");
const path = require("node:path");
const ROOT = path.resolve(__dirname, "..", "..");
const CDP_LIST = "http://127.0.0.1:9222/json/list";
const SEED = 1352540133;
// Per-lineage RNG seeds (from each save's flags.__seed__):
//   57 (41477 family, 41228-root run) -> 450161387
//   41/55/59 (41410 / 653-def families) -> 611741486 (= the 41400 recording seed)
const SEEDS = { 57: 450161387, 59: 611741486, 41: 611741486, 55: 611741486 };
const SLOTS = [57, 59, 41, 55];

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
  const outDir = path.join(ROOT, "outputs", "recordings_20261025");
  fs.mkdirSync(outDir, { recursive: true });
  try {
    for (const slot of SLOTS) {
      const raw = JSON.parse(fs.readFileSync(
        path.join(ROOT, "outputs/checkpoints_20261024", `save${slot}_slot_raw.json`), "utf8"));
      const seed = SEEDS[slot] || SEED;
      const expr = `LZString.compressToBase64(JSON.stringify({
        name: "51", version: ${JSON.stringify(raw.version || "Ver 3.0")},
        hard: ${JSON.stringify(raw.hard || "")}, seed: ${seed},
        route: ${JSON.stringify(raw.route)}}))`;
      const encoded = await evaluate(cdp, expr);
      const out = path.join(outDir, `line_save${slot}.h5route`);
      fs.writeFileSync(out, encoded, "utf8");
      console.log(`slot ${slot}: route ${raw.route.length} chars -> ${out} (${encoded.length} chars)`);
    }
  } finally { cdp.close(); }
}
main().catch((e) => { console.error(e.stack || String(e)); process.exit(1); });
