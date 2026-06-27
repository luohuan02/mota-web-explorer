#!/usr/bin/env node
// Export current h5mota runtime save data from the already-open Chrome CDP target.

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const CDP_LIST = "http://127.0.0.1:9222/json/list";

function parseArgs(argv) {
  const out = {
    out: path.join(ROOT, "outputs", "results", "current_snapshot.json"),
  };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--out") out.out = path.resolve(argv[++i]);
    else throw new Error(`Unknown argument: ${arg}`);
  }
  return out;
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
    const { resolve, reject } = pending.get(msg.id);
    pending.delete(msg.id);
    if (msg.error) reject(new Error(JSON.stringify(msg.error)));
    else resolve(msg.result);
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

async function evalJson(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return JSON.parse(result.result.value);
}

function normalize(raw) {
  const h = raw.hero || {};
  const loc = h.loc || h;
  const items = h.items || {};
  const tools = items.tools || {};
  const constants = items.constants || h.constants || {};
  const flags = h.flags || {};
  return {
    exportedAt: new Date().toISOString(),
    floorId: raw.floorId,
    hero: {
      x: loc.x,
      y: loc.y,
      hp: h.hp,
      atk: h.atk,
      def: h.def,
      money: h.money,
      yk: tools.yellowKey || h.yk || 0,
      bk: tools.blueKey || h.bk || 0,
      rk: tools.redKey || h.rk || 0,
      tools,
      constants,
      flags,
    },
    maps: raw.maps || {},
    values: raw.values || {},
    hard: raw.hard,
    route: raw.route,
    version: raw.version,
    guid: raw.guid,
    time: raw.time,
  };
}

async function main() {
  const args = parseArgs(process.argv);
  const cdp = await connectGameTarget();
  try {
    const raw = await evalJson(
      cdp,
      `(function(){
        try {
          return JSON.stringify(core.control.saveData(null));
        } catch (e) {
          return JSON.stringify({error:String(e&&e.stack||e)});
        }
      })()`
    );
    if (raw.error) throw new Error(raw.error);
    const data = normalize(raw);
    fs.mkdirSync(path.dirname(args.out), { recursive: true });
    fs.writeFileSync(args.out, JSON.stringify(data, null, 2), "utf8");
    const rawOut = args.out.replace(/\.json$/i, "_raw.json");
    fs.writeFileSync(rawOut, JSON.stringify(raw, null, 2), "utf8");
    console.log(JSON.stringify({
      out: args.out,
      rawOut,
      floor: data.floorId,
      x: data.hero.x,
      y: data.hero.y,
      hp: data.hero.hp,
      atk: data.hero.atk,
      def: data.hero.def,
      money: data.hero.money,
      yk: data.hero.yk,
      bk: data.hero.bk,
      rk: data.hero.rk,
    }));
  } finally {
    cdp.close();
  }
}

main().catch((err) => {
  console.error(err.stack || String(err));
  process.exit(1);
});
