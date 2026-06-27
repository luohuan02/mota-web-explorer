#!/usr/bin/env node
// Import a raw h5mota save JSON into a browser save slot via the existing CDP page.

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const CDP_LIST = "http://127.0.0.1:9222/json/list";

function parseArgs(argv) {
  const out = {
    slot: null,
    input: null,
    load: false,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--slot") out.slot = Number(argv[++i]);
    else if (arg === "--in") out.input = path.resolve(argv[++i]);
    else if (arg === "--load") out.load = true;
    else throw new Error(`Unknown argument: ${arg}`);
  }
  if (!Number.isInteger(out.slot)) throw new Error("--slot is required");
  if (!out.input) throw new Error("--in is required");
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

async function evalJson(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return JSON.parse(result.result.value);
}

function summarizeSave(data) {
  const h = data.hero || {};
  const loc = h.loc || {};
  const tools = (h.items && h.items.tools) || {};
  return {
    floor: data.floorId,
    x: loc.x,
    y: loc.y,
    hp: h.hp,
    atk: h.atk,
    def: h.def,
    money: h.money,
    yk: tools.yellowKey || 0,
    bk: tools.blueKey || 0,
    rk: tools.redKey || 0,
  };
}

async function main() {
  const args = parseArgs(process.argv);
  const data = JSON.parse(fs.readFileSync(args.input, "utf8"));
  const cdp = await connectGameTarget();
  try {
    const dataLiteral = JSON.stringify(data);
    // Step 1: write the save into the slot (fire-and-forget; resolve on callback).
    const writeResult = await evalJson(
      cdp,
      `new Promise(function(resolve){
        try {
          core.utils.setLocalForage('save${args.slot}', ${dataLiteral}, function(){
            resolve(JSON.stringify({ok:true, slot:${args.slot}, written:true}));
          });
        } catch (e) {
          resolve(JSON.stringify({ok:false, slot:${args.slot}, error:String(e&&e.stack||e)}));
        }
      })`
    );
    if (!writeResult.ok) throw new Error(`save${args.slot} write failed: ${JSON.stringify(writeResult)}`);
    if (!args.load) {
      console.log(JSON.stringify({ input: args.input, slot: args.slot, imported: summarizeSave(data), written: true }));
      return;
    }
    // Step 2: load the data without awaiting the nested callback; store status on window.
    await evalJson(
      cdp,
      `(function(){
        window.__importLoadStatus = {done:false};
        try {
          var data = ${dataLiteral};
          core.loadData(data, function(){
            window.__importLoadStatus.done = true;
          });
        } catch (e) {
          window.__importLoadStatus = {done:true, error:String(e&&e.stack||e)};
        }
        return JSON.stringify({kicked:true});
      })`
    );
    // Step 3: poll until the load completes and the hero settles.
    const deadline = Date.now() + 20000;
    let settled = null;
    while (Date.now() < deadline) {
      await new Promise((r) => setTimeout(r, 300));
      settled = await evalJson(
        cdp,
        `(function(){
          var st = window.__importLoadStatus || {};
          var h = core.status.hero || {};
          var loc = h.loc || {};
          var ready = !!st.done && !!core.isPlaying && core.isPlaying() && !!core.status.hero && loc.x != null && !core.status.heroMoving;
          return JSON.stringify({ready:ready, done:!!st.done, error:st.error||null, floor:core.status.floorId, x:loc.x, y:loc.y, hp:h.hp, atk:h.atk, def:h.def, money:h.money, moving:core.status.heroMoving});
        })()`
      );
      if (settled.ready) break;
    }
    if (!settled || !settled.ready) throw new Error(`save${args.slot} load did not settle: ${JSON.stringify(settled)}`);
    console.log(JSON.stringify({ input: args.input, slot: args.slot, imported: summarizeSave(data), loaded: settled }));
  } finally {
    cdp.close();
  }
}

main().catch((err) => {
  console.error(err.stack || String(err));
  process.exit(1);
});
