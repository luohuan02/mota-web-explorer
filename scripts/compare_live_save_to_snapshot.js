#!/usr/bin/env node
// Read a live save slot through CDP and compare its saved map overrides with a
// local synthetic snapshot. This is read-only: it calls core.getSave but does
// not load or mutate game state.

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const CDP_LIST = "http://127.0.0.1:9222/json/list";

function parseArgs(argv) {
  const out = {
    slot: 100,
    snapshot: path.join(ROOT, "outputs", "results", "zone2_2atk1def_strict20_synthetic_snapshot.json"),
    floorMax: 10,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--slot") out.slot = Number(argv[++i]);
    else if (arg === "--snapshot") out.snapshot = path.resolve(argv[++i]);
    else if (arg === "--floor-max") out.floorMax = Number(argv[++i]);
    else throw new Error(`unknown arg ${arg}`);
  }
  return out;
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8").replace(/^\uFEFF/, ""));
}

function floorNo(fid) {
  return Number(fid.slice(2));
}

function baseGrid(fid) {
  const raw = readJson(path.join(ROOT, "data", "maps", `mt${floorNo(fid)}_map.json`));
  return raw.map || raw.m;
}

function decodeGrid(fid, snapshot) {
  const base = baseGrid(fid);
  const saved = snapshot.maps && snapshot.maps[fid] && snapshot.maps[fid].map;
  if (!saved) return base.map((row) => row.slice());
  return saved.map((row, y) => {
    if (row === 0 || row === -1) return base[y].slice();
    return row.map((value, x) => (value === -1 ? base[y][x] : value));
  });
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

async function evalValue(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}

async function readSave(slot) {
  const cdp = await connectGameTarget();
  try {
    const raw = await evalValue(
      cdp,
      `new Promise(resolve => core.getSave(${slot}, data => resolve(JSON.stringify(data))))`
    );
    const save = JSON.parse(raw);
    if (!save) throw new Error(`save${slot} missing`);
    return save;
  } finally {
    cdp.close();
  }
}

async function main() {
  const args = parseArgs(process.argv);
  const save = await readSave(args.slot);
  const snapshot = readJson(args.snapshot);
  const tiles = readJson(path.join(ROOT, "data", "maps", "tile_mapping.json")).tiles;
  const missing = [];
  const removed = [];
  for (let n = 1; n <= args.floorMax; n += 1) {
    const fid = `MT${n}`;
    const base = baseGrid(fid);
    const saveGrid = decodeGrid(fid, save);
    const snapshotGrid = decodeGrid(fid, snapshot);
    for (let y = 0; y < base.length; y += 1) {
      for (let x = 0; x < base[y].length; x += 1) {
        const tile = base[y][x];
        if (!tile) continue;
        const info = tiles[String(tile)] || {};
        if (!["enemys", "items", "animates", "npcs", "terrains"].includes(info.cls)) continue;
        if (saveGrid[y][x] === tile) continue;
        const row = { fid, x, y, id: info.id || null, cls: info.cls || null, tile, save: saveGrid[y][x], snapshot: snapshotGrid[y][x] };
        removed.push(row);
        if (snapshotGrid[y][x] === tile) missing.push(row);
      }
    }
  }
  const out = {
    save: {
      slot: args.slot,
      floorId: save.floorId,
      hero: {
        x: save.hero.x,
        y: save.hero.y,
        hp: save.hero.hp,
        atk: save.hero.atk,
        def: save.hero.def,
        money: save.hero.money,
      },
    },
    snapshot: path.relative(ROOT, args.snapshot),
    removedCount: removed.length,
    missingCount: missing.length,
    enemyMissing: missing.filter((row) => row.cls === "enemys"),
    resourceMissing: missing.filter((row) => row.cls !== "enemys"),
  };
  console.log(JSON.stringify(out, null, 2));
}

main().catch((err) => {
  console.error(err.stack || String(err));
  process.exit(1);
});
