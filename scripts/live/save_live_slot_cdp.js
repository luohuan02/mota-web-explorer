#!/usr/bin/env node
// Save current live game state to a slot (100+) via CDP, using the game's own
// core.control.saveData + core.utils.setLocalForage mechanism (mirrors the
// replayer's saveSlot). Usage: node scripts/live/save_live_slot_cdp.js <slot>
const http = require("node:http");

const CDP_LIST = "http://127.0.0.1:9222/json/list";
function getJson(url) {
  return new Promise((res, rej) => {
    http.get(url, (r) => { let d = ""; r.on("data", (c) => (d += c)); r.on("end", () => res(JSON.parse(d))); }).on("error", rej);
  });
}

async function main() {
  const slot = Number(process.argv[2]);
  if (!Number.isInteger(slot) || slot < 100) throw new Error("slot 100+ required");
  const targets = await getJson(CDP_LIST);
  const target = targets.find((t) => t.url && t.url.includes("h5mota.com/games/51")) || targets.find((t) => t.type === "page" && t.webSocketDebuggerUrl);
  if (!target) throw new Error("no h5mota game tab on port 9222");
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  let id = 1;
  const pending = new Map();
  ws.addEventListener("message", (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m.result); pending.delete(m.id); } });
  await new Promise((rk, rj) => { ws.addEventListener("open", rk, { once: true }); ws.addEventListener("error", rj, { once: true }); });
  const send = (method, params = {}) => new Promise((rk) => { const i = id++; pending.set(i, rk); ws.send(JSON.stringify({ id: i, method, params })); });
  const ev = async (expr) => {
    const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
    return r.result && r.result.value;
  };
  const result = await ev(`new Promise(function(resolve){
    try {
      var data = core.control.saveData(null);
      core.utils.setLocalForage('save${slot}', data, function(){
        var h = core.status.hero || {}, t = h.items && h.items.tools || {}, loc = h.loc || {};
        resolve(JSON.stringify({ok:true, slot:${slot},
          state:{f:core.status.floorId,x:loc.x,y:loc.y,hp:h.hp,atk:h.atk,def:h.def,
            yk:t.yellowKey||0,bk:t.blueKey||0,rk:t.redKey||0,g:h.money||0}}));
      });
    } catch (e) {
      resolve(JSON.stringify({ok:false, slot:${slot}, error:String(e&&e.stack||e)}));
    }
  })`);
  console.log("SAVE RESULT:", result);
  ws.close();
}
main().catch((e) => { console.error(e); process.exit(1); });