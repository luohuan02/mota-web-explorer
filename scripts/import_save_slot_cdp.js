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
  const value = result.result.value;
  return typeof value === "string" ? JSON.parse(value) : value;
}

function summarizeSave(data) {
  const h = data.hero || {};
  const loc = h.loc || { x: h.x, y: h.y };
  const tools = (h.items && h.items.tools) || h.tools || {};
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

function normalizeSaveForCurrentEngine(data) {
  const out = JSON.parse(JSON.stringify(data));
  out.route = [];
  const h = out.hero || {};
  if (h.image == null) h.image = "hero.png";
  if (h.animate == null) h.animate = false;
  if (h.name == null) h.name = "勇者";
  if (h.lv == null) h.lv = 1;
  if (h.hpmax == null) h.hpmax = -1;
  if (h.manamax == null) h.manamax = -1;
  if (h.mana == null) h.mana = 0;
  if (h.mdef == null) h.mdef = 0;
  if (h.exp == null) h.exp = 0;
  if (!Array.isArray(h.equipment)) h.equipment = [];
  if (h.steps == null) h.steps = 0;
  if (!h.loc && h.x != null && h.y != null) {
    h.loc = { x: h.x, y: h.y, direction: h.direction || "down" };
  }
  if (!h.items) h.items = {};
  if (!h.items.tools) {
    h.items.tools = Object.assign({}, h.tools || {});
    if (h.yk != null) h.items.tools.yellowKey = h.yk;
    if (h.bk != null) h.items.tools.blueKey = h.bk;
    if (h.rk != null) h.items.tools.redKey = h.rk;
  }
  if (!h.items.constants) h.items.constants = Object.assign({}, h.constants || {});
  if (!h.items.equips) h.items.equips = Object.assign({}, h.equips || h.equipment || {});
  if (!Array.isArray(h.followers)) h.followers = [];
  out.hero = h;
  return out;
}

async function main() {
  const args = parseArgs(process.argv);
  const data = normalizeSaveForCurrentEngine(JSON.parse(fs.readFileSync(args.input, "utf8")));
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
        window.__importLoadStatus = {
          done:false,
          expected:{
            floor:${JSON.stringify(data.floorId)},
            x:${JSON.stringify(data.hero.loc && data.hero.loc.x)},
            y:${JSON.stringify(data.hero.loc && data.hero.loc.y)},
            hp:${JSON.stringify(data.hero.hp)},
            atk:${JSON.stringify(data.hero.atk)},
            def:${JSON.stringify(data.hero.def)},
            money:${JSON.stringify(data.hero.money)}
          }
        };
        try {
          core.getSave(${args.slot}, function(data){
            try {
              if (!data) {
                window.__importLoadStatus = {done:true, error:"missing save${args.slot}"};
                return;
              }
              var finished = false;
              function finishLoad(){
                if (finished) return;
                finished = true;
                setTimeout(function(){
                  try {
                    if (core.stopAutomaticRoute) core.stopAutomaticRoute();
                    if (core.clearContinueAutomaticRoute) core.clearContinueAutomaticRoute();
                    if (core.status) core.status.route = [];
                    if (core.status && !core.status.floor && core.status.maps && core.status.floorId) {
                      core.status.floor = core.status.maps[core.status.floorId];
                    }
                    if (core.status && !core.status.thisMap && core.status.maps && core.status.floorId) {
                      core.status.thisMap = core.status.maps[core.status.floorId];
                    }
                    var h = core.status && core.status.hero || {};
                    if (h.image == null) h.image = "hero.png";
                    if (h.animate == null) h.animate = false;
                    if (h.name == null) h.name = "勇者";
                    if (h.lv == null) h.lv = 1;
                    if (h.hpmax == null) h.hpmax = -1;
                    if (h.manamax == null) h.manamax = -1;
                    if (h.mana == null) h.mana = 0;
                    if (h.mdef == null) h.mdef = 0;
                    if (h.exp == null) h.exp = 0;
                    if (!Array.isArray(h.equipment)) h.equipment = [];
                    if (h.steps == null) h.steps = 0;
                    if (!h.items) h.items = {};
                    h.items.tools = Object.assign({}, h.tools || {});
                    if (h.yk != null) h.items.tools.yellowKey = h.yk;
                    if (h.bk != null) h.items.tools.blueKey = h.bk;
                    if (h.rk != null) h.items.tools.redKey = h.rk;
                    h.items.constants = Object.assign({}, h.constants || {});
                    h.items.equips = Object.assign({}, h.equips || h.equipment || {});
                    if (!Array.isArray(h.followers)) h.followers = [];
                    if (core.updateStatusBar) core.updateStatusBar();
                    if (core.status && core.status.lockControl && !core.status.heroMoving && !(core.status.event&&core.status.event.id) && !(core.status.event&&core.status.event.ui)) {
                      if (core.unlockControl) core.unlockControl();
                      else core.status.lockControl = false;
                    }
                  } catch (e) {}
                  window.__importLoadStatus.done = true;
                }, 400);
              }
              function beginLoad(){
                data.route = [];
                try {
                  if (core.dom && core.dom.startPanel) core.dom.startPanel.style.display = "none";
                  if (main.dom && main.dom.startPanel) main.dom.startPanel.style.display = "none";
                  if (main.dom && main.dom.levelChooseButtons) main.dom.levelChooseButtons.style.display = "none";
                  if (main.dom && main.dom.startButtonGroup) main.dom.startButtonGroup.style.display = "none";
                  if (core.stopAutomaticRoute) core.stopAutomaticRoute();
                  if (core.clearContinueAutomaticRoute) core.clearContinueAutomaticRoute();
                  if (core.status) core.status.route = [];
                  if (core.status && core.status.automaticRoute) {
                    core.status.automaticRoute.autoHeroMove = false;
                    core.status.automaticRoute.autoStep = 0;
                    core.status.automaticRoute.movedStep = 0;
                    core.status.automaticRoute.destStep = 0;
                    core.status.automaticRoute.destX = null;
                    core.status.automaticRoute.destY = null;
                    core.status.automaticRoute.autoStepRoutes = [];
                    core.status.automaticRoute.moveStepBeforeStop = [];
                  }
                  if (core.status) core.status.heroMoving = 0;
                } catch (e) {}
                core.loadData(data, finishLoad);
                setTimeout(finishLoad, 2500);
              }
              if (!(core.isPlaying && core.isPlaying()) || !(core.status && core.status.hero)) {
                try {
                  core.startGame(data.hard, data.hero && data.hero.flags && data.hero.flags.__seed__, []);
                  setTimeout(beginLoad, 800);
                } catch (e) {
                  window.__importLoadStatus = {done:true, error:String(e&&e.stack||e)};
                }
              } else {
                beginLoad();
              }
            } catch (e) {
              window.__importLoadStatus = {done:true, error:String(e&&e.stack||e)};
            }
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
          var exp = {
            floor:${JSON.stringify(data.floorId)},
            x:${JSON.stringify(data.hero.loc && data.hero.loc.x)},
            y:${JSON.stringify(data.hero.loc && data.hero.loc.y)},
            hp:${JSON.stringify(data.hero.hp)},
            atk:${JSON.stringify(data.hero.atk)},
            def:${JSON.stringify(data.hero.def)},
            money:${JSON.stringify(data.hero.money)},
            yk:${JSON.stringify((data.hero.items && data.hero.items.tools && data.hero.items.tools.yellowKey) || data.hero.yk || 0)},
            bk:${JSON.stringify((data.hero.items && data.hero.items.tools && data.hero.items.tools.blueKey) || data.hero.bk || 0)},
            rk:${JSON.stringify((data.hero.items && data.hero.items.tools && data.hero.items.tools.redKey) || data.hero.rk || 0)}
          };
          var matches =
            (exp.floor == null || core.status.floorId === exp.floor) &&
            (exp.x == null || loc.x === exp.x) &&
            (exp.y == null || loc.y === exp.y) &&
            (exp.hp == null || h.hp === exp.hp) &&
            (exp.atk == null || h.atk === exp.atk) &&
            (exp.def == null || h.def === exp.def) &&
            (exp.money == null || h.money === exp.money) &&
            (exp.yk == null || (((h.items&&h.items.tools)||{}).yellowKey||0) === exp.yk) &&
            (exp.bk == null || (((h.items&&h.items.tools)||{}).blueKey||0) === exp.bk) &&
            (exp.rk == null || (((h.items&&h.items.tools)||{}).redKey||0) === exp.rk);
          var coreStatsMatch =
            (exp.floor == null || core.status.floorId === exp.floor) &&
            (exp.hp == null || h.hp === exp.hp) &&
            (exp.atk == null || h.atk === exp.atk) &&
            (exp.def == null || h.def === exp.def) &&
            (exp.money == null || h.money === exp.money);
          if (!matches && coreStatsMatch && exp.x != null && exp.y != null) {
            if (!h.loc) h.loc = {};
            h.loc.x = exp.x;
            h.loc.y = exp.y;
            if (!h.loc.direction) h.loc.direction = "down";
            h.x = exp.x;
            h.y = exp.y;
            loc = h.loc;
            if (core.status) core.status.route = [];
            if (core.status && core.status.automaticRoute) {
              core.status.automaticRoute.autoHeroMove = false;
              core.status.automaticRoute.autoStep = 0;
              core.status.automaticRoute.movedStep = 0;
              core.status.automaticRoute.destStep = 0;
              core.status.automaticRoute.destX = null;
              core.status.automaticRoute.destY = null;
              core.status.automaticRoute.autoStepRoutes = [];
              core.status.automaticRoute.moveStepBeforeStop = [];
            }
            core.status.heroMoving = 0;
            matches = true;
          }
          if (matches) {
            if (!core.status.floor && core.status.maps && core.status.floorId) {
              core.status.floor = core.status.maps[core.status.floorId];
            }
            if (!core.status.thisMap && core.status.maps && core.status.floorId) {
              core.status.thisMap = core.status.maps[core.status.floorId];
            }
            if (!h.items) h.items = {};
            if (h.image == null) h.image = "hero.png";
            if (h.animate == null) h.animate = false;
            if (h.name == null) h.name = "勇者";
            if (h.lv == null) h.lv = 1;
            if (h.hpmax == null) h.hpmax = -1;
            if (h.manamax == null) h.manamax = -1;
            if (h.mana == null) h.mana = 0;
            if (h.mdef == null) h.mdef = 0;
            if (h.exp == null) h.exp = 0;
            if (!Array.isArray(h.equipment)) h.equipment = [];
            if (h.steps == null) h.steps = 0;
            h.items.tools = Object.assign({}, h.tools || {});
            if (h.yk != null) h.items.tools.yellowKey = h.yk;
            if (h.bk != null) h.items.tools.blueKey = h.bk;
            if (h.rk != null) h.items.tools.redKey = h.rk;
            h.items.constants = Object.assign({}, h.constants || {});
            h.items.equips = Object.assign({}, h.equips || h.equipment || {});
            if (!Array.isArray(h.followers)) h.followers = [];
            try { if (core.updateStatusBar) core.updateStatusBar(); } catch (e) { st.error = String(e && e.stack || e); }
            if (!st.error) {
              st.done = true;
              window.__importLoadStatus = st;
            }
          }
          var hasFloor = !!core.status.floor;
          var hasThisMap = !!core.status.thisMap;
          var ready = !!st.done && matches && hasFloor && hasThisMap && !!core.isPlaying && core.isPlaying() && !!core.status.hero && loc.x != null && !core.status.heroMoving;
          var tools = (h.items&&h.items.tools)||{};
          return JSON.stringify({ready:ready, matches:matches, expected:exp, hasFloor:hasFloor, hasThisMap:hasThisMap, done:!!st.done, error:st.error||null, floor:core.status.floorId, x:loc.x, y:loc.y, hp:h.hp, atk:h.atk, def:h.def, money:h.money, yk:tools.yellowKey||0, bk:tools.blueKey||0, rk:tools.redKey||0, moving:core.status.heroMoving});
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
