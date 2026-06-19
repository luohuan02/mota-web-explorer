#!/usr/bin/env node
// Extract high-floor h5mota maps through the already-open Chrome CDP port.

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const OUT_DIR = path.join(ROOT, "data", "maps");
const CDP_LIST = "http://127.0.0.1:9222/json/list";

function today() {
  return new Date().toISOString().slice(0, 10);
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
  if (!target) throw new Error("No CDP page target found on port 9222");

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
    target,
    close: () => ws.close(),
    send(method, params = {}) {
      const id = nextId++;
      const payload = JSON.stringify({ id, method, params });
      return new Promise((resolve, reject) => {
        pending.set(id, { resolve, reject });
        ws.send(payload);
      });
    },
  };
}

async function evaluateJson(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: false,
  });
  if (result.exceptionDetails) {
    throw new Error(JSON.stringify(result.exceptionDetails));
  }
  return JSON.parse(result.result.value);
}

async function main() {
  const from = Number(process.argv[2] || 41);
  const to = Number(process.argv[3] || 50);
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const cdp = await connectGameTarget();
  const stamp = today();
  const written = [];
  try {
    for (let n = from; n <= to; n++) {
      const fid = `MT${n}`;
      const data = await evaluateJson(
        cdp,
        `(function(){var fid=${JSON.stringify(fid)},stamp=${JSON.stringify(stamp)},source=core.floors[fid]||core.status.maps[fid],runtime=core.status.maps[fid]||{};if(!source)return null;return JSON.stringify({description:fid+' floor map and events',source:'browser eval core.floors.'+fid,timestamp:stamp,floorId:fid,title:source.title||runtime.title||'',name:source.name||runtime.name||'',width:source.width||runtime.width,height:source.height||runtime.height,ratio:source.ratio||runtime.ratio||4,canFlyTo:!!runtime.canFlyTo,flyPoint:{downFloor:runtime.downFloor||null,upFloor:runtime.upFloor||null},map:source.map,changeFloor:source.changeFloor||{},events:source.events||{},afterBattle:source.afterBattle||{},afterGetItem:source.afterGetItem||{},afterOpenDoor:source.afterOpenDoor||{},cannotMove:source.cannotMove||{},firstArrive:source.firstArrive||[],eachArrive:source.eachArrive||[],notes:source.notes||[]});})()`
      );
      if (!data) throw new Error(`${fid} not found in live core data`);
      const outPath = path.join(OUT_DIR, `mt${n}_map.json`);
      fs.writeFileSync(outPath, JSON.stringify(data, null, 4), "utf8");
      written.push(outPath);
      console.log(outPath);
    }

    const flyPoints = await evaluateJson(
      cdp,
      `(function(){var out={};for(var fid in core.status.maps){if(!/^MT\\d+$/.test(fid))continue;var m=core.status.maps[fid];out[fid]={canFlyTo:!!m.canFlyTo,downFloor:m.downFloor||null,upFloor:m.upFloor||null,width:m.width,height:m.height};}return JSON.stringify(out);})()`
    );
    const flyPath = path.join(OUT_DIR, "fly_points.json");
    fs.writeFileSync(flyPath, JSON.stringify(flyPoints, null, 2), "utf8");
    written.push(flyPath);
    console.log(flyPath);
  } finally {
    cdp.close();
  }
}

main().catch((err) => {
  console.error(err.stack || String(err));
  process.exit(1);
});
