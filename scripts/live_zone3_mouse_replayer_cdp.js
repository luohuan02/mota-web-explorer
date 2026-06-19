#!/usr/bin/env node
// Replay the generated zone-3 walk in the live h5mota page using map mouse
// clicks for movement/targets. This intentionally does not set hero location
// or synthesize per-tile movement.

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const DEFAULT_WALK = path.join(ROOT, "outputs", "results", "zone3_quick_pass_walk.json");
const CDP_LIST = "http://127.0.0.1:9222/json/list";

const ACT = {
  CHECK: "\u6821\u9a8c",
  KILL: "\u51fb\u6740",
  PASS: "\u901a\u8fc7",
  CHANGE_FLOOR: "\u6362\u5c42",
  ARRIVE: "\u5230\u8fbe",
  EVENT_BATTLE: "\u4e8b\u4ef6\u6218\u6597",
  TALK: "\u5bf9\u8bdd",
  SHOP: "\u5546\u5e97",
  FLY: "\u98de\u884c",
  OPEN_DOOR: "\u5f00\u95e8",
  PICKUP: "\u62fe\u53d6",
  MERCHANT: "\u5546\u4eba",
  EVENT: "\u4e8b\u4ef6",
  EVENT_REWARD: "\u4e8b\u4ef6\u5956\u52b1",
};

function parseArgs(argv) {
  const out = {
    walk: DEFAULT_WALK,
    startStep: 1,
    stopStep: null,
    noRestore: false,
    requireStart: false,
    undoSteps: 0,
    loadSlot: null,
    stepSaveSlot: null,
    progressSaveSlot: null,
    retryOnFailure: false,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--walk") out.walk = path.resolve(argv[++i]);
    else if (arg === "--start-step") out.startStep = Number(argv[++i]);
    else if (arg === "--stop-step") out.stopStep = Number(argv[++i]);
    else if (arg === "--no-restore") out.noRestore = true;
    else if (arg === "--require-start") out.requireStart = true;
    else if (arg === "--undo-steps") out.undoSteps = Number(argv[++i]);
    else if (arg === "--load-slot") out.loadSlot = Number(argv[++i]);
    else if (arg === "--step-save-slot") out.stepSaveSlot = Number(argv[++i]);
    else if (arg === "--progress-save-slot") out.progressSaveSlot = Number(argv[++i]);
    else if (arg === "--retry-on-failure") out.retryOnFailure = true;
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

async function evalValue(cdp, expression, awaitPromise = true) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    returnByValue: true,
    awaitPromise,
  });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}

async function evalJson(cdp, expression, awaitPromise = true) {
  return JSON.parse(await evalValue(cdp, expression, awaitPromise));
}

const STATE_EXPR = String.raw`(function(){
  var h=core.status.hero||{}, loc=h.loc||{}, tools=(h.items&&h.items.tools)||{}, ev=core.status.event||{};
  var current=ev.data&&ev.data.current||{}, ui=ev.ui||{};
  var choices=current.choices||ui.choices||[];
  function countAsync(o) {
    if (!o) return 0;
    if (Array.isArray(o)) return o.length;
    if (typeof o === "object") return Object.keys(o).length;
    return 1;
  }
  return JSON.stringify({
    floor: core.status.floorId,
    x: loc.x,
    y: loc.y,
    hp: h.hp,
    atk: h.atk,
    def: h.def,
    money: h.money,
    yk: tools.yellowKey||0,
    bk: tools.blueKey||0,
    rk: tools.redKey||0,
    lock: !!core.status.lockControl,
    moving: !!core.status.heroMoving,
    eventId: ev.id||null,
    eventType: current.type||ui.type||null,
    eventUi: !!ev.ui,
    hasChoices: !!(choices&&choices.length),
    choices: choices ? choices.map(function(c){ return String(c.text||""); }) : [],
    statusAsyncCount: countAsync(core.status.asyncId),
    animateAsyncCount: countAsync(core.animateFrame&&core.animateFrame.asyncId)
  });
})()`;

async function state(cdp) {
  return evalJson(cdp, STATE_EXPR);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function stateText(s) {
  return `${s.floor} x${s.x}y${s.y} HP=${s.hp} ATK=${s.atk} DEF=${s.def} ` +
    `YK=${s.yk} BK=${s.bk} RK=${s.rk} G=${s.money} ` +
    `lock=${s.lock} moving=${s.moving} event=${s.eventId || "-"}:${s.eventType || "-"} ` +
    `choices=${s.hasChoices} async=${s.statusAsyncCount || 0}/${s.animateAsyncCount || 0}`;
}

function sameObservableState(a, b) {
  return a.floor === b.floor &&
    a.x === b.x &&
    a.y === b.y &&
    a.hp === b.hp &&
    a.atk === b.atk &&
    a.def === b.def &&
    a.money === b.money &&
    a.yk === b.yk &&
    a.bk === b.bk &&
    a.rk === b.rk &&
    a.lock === b.lock &&
    a.moving === b.moving &&
    a.eventId === b.eventId &&
    a.eventType === b.eventType &&
    a.hasChoices === b.hasChoices &&
    a.statusAsyncCount === b.statusAsyncCount &&
    a.animateAsyncCount === b.animateAsyncCount;
}

async function clearRuntimeRoute(cdp) {
  await evalValue(
    cdp,
    String.raw`(function(){
      try {
        if (core.stopAutomaticRoute) core.stopAutomaticRoute();
        if (core.clearContinueAutomaticRoute) core.clearContinueAutomaticRoute();
        core.status.route = [];
        if (core.status.replay) {
          core.status.replay.toReplay = [];
          core.status.replay.totalList = [];
          core.status.replay.replaying = false;
          core.status.replay.pausing = false;
        }
      } catch (e) {}
      return true;
    })()`
  );
}

async function tileMetrics(cdp, x, y) {
  return evalJson(
    cdp,
    `(function(){
      var target={x:${x},y:${y}};
      var draw=main.dom.gameDraw;
      var rect=draw.getBoundingClientRect();
      var size=32*core.domStyle.scale;
      var clientX=rect.left+(target.x-0.5)*size;
      var clientY=rect.top+(target.y-0.5)*size;
      var loc=core.actions._getClickLoc(clientX,clientY);
      var tile={x:Math.floor(loc.x/loc.size)+1,y:Math.floor(loc.y/loc.size)+1};
      return JSON.stringify({
        target:target,
        rect:{left:rect.left,top:rect.top,width:rect.width,height:rect.height},
        size:size,
        clientX:clientX,
        clientY:clientY,
        loc:loc,
        tile:tile,
        dpr:window.devicePixelRatio
      });
    })()`
  );
}

async function waitMovementSettled(cdp, timeoutMs = 8000) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  while (Date.now() < end) {
    last = await state(cdp);
    if (!last.moving) return last;
    await sleep(100);
  }
  return last;
}

async function targetEvent(cdp, floor, x, y) {
  return evalJson(
    cdp,
    `(function(){
      var m=core.status.maps[${JSON.stringify(floor)}]||{};
      var block=(m.blocks||[]).find(function(b){return b.x===${x}&&b.y===${y};});
      var ev=block&&block.event;
      return JSON.stringify(ev ? {
        id: ev.id||null,
        cls: ev.cls||null,
        trigger: ev.trigger||null,
        noPass: !!ev.noPass
      } : null);
    })()`
  );
}

function canRetryAdjacentTarget(action, live, floor, x, y, ev) {
  if (!ev || live.floor !== floor || live.lock || live.eventId || live.hasChoices || live.moving) return false;
  if (Math.abs(live.x - x) + Math.abs(live.y - y) !== 1) return false;
  if ([ACT.TALK, ACT.PASS, ACT.OPEN_DOOR, ACT.KILL, ACT.EVENT_BATTLE].includes(action)) return true;
  return ev.noPass && ["action", "openDoor", "battle"].includes(ev.trigger);
}

async function maybeRetryAdjacentTarget(cdp, step) {
  const [x, y] = step.pos;
  let st = await waitMovementSettled(cdp);
  const ev = await targetEvent(cdp, step.floor, x, y);
  if (!canRetryAdjacentTarget(step.action, st, step.floor, x, y, ev)) return;
  await mouseClickTile(cdp, x, y);
}

async function mouseClickTile(cdp, x, y) {
  await clearRuntimeRoute(cdp);
  const before = await state(cdp);
  if (before.lock || before.moving) {
    throw new Error(`cannot click while busy: ${stateText(before)}`);
  }
  const result = await evalJson(
    cdp,
    `(function(){
      var target={x:${x},y:${y}};
      var draw=main.dom.gameDraw;
      var group=main.dom.gameGroup;
      var size=32*core.domStyle.scale;
      var left=draw.offsetLeft+group.offsetLeft;
      var top=draw.offsetTop+group.offsetTop;
      var clientX=left+(target.x-0.5)*size;
      var clientY=top+(target.y-0.5)*size;
      var loc=core.actions._getClickLoc(clientX,clientY);
      var tile={x:Math.floor(loc.x/loc.size)+1,y:Math.floor(loc.y/loc.size)+1};
      var actionPx=target.x*32+16-core.bigmap.offsetX;
      var actionPy=target.y*32+16-core.bigmap.offsetY;
      var down=(core.actions.actions.ondown||[]).find(function(a){return a.name==="_sys_ondown";});
      var up=(core.actions.actions.onup||[]).find(function(a){return a.name==="_sys_onup";});
      var metrics={left:left,top:top,size:size,clientX:clientX,clientY:clientY,loc:loc,tile:tile,target:target,actionPx:actionPx,actionPy:actionPy};
      if(tile.x!==target.x||tile.y!==target.y)return JSON.stringify({ok:false,reason:"tile-mismatch",metrics:metrics});
      if(!down||!up)return JSON.stringify({ok:false,reason:"missing-click-handler",metrics:metrics});
      down.func.call(core.actions,target.x,target.y,actionPx,actionPy);
      up.func.call(core.actions,target.x,target.y,actionPx,actionPy);
      return JSON.stringify({ok:true,metrics:metrics});
    })()`
  );
  if (!result.ok) throw new Error(`map click x${x}y${y} failed: ${JSON.stringify(result)}`);
  await sleep(220);
  const after = await state(cdp);
  const adjacent = Math.abs(x - before.x) + Math.abs(y - before.y) === 1;
  if (adjacent && sameObservableState(before, after)) {
    const retry = await evalJson(
      cdp,
      `(function(){
        var target={x:${x},y:${y}};
        var actionPx=target.x*32+16-core.bigmap.offsetX;
        var actionPy=target.y*32+16-core.bigmap.offsetY;
        var down=(core.actions.actions.ondown||[]).find(function(a){return a.name==="_sys_ondown";});
        var up=(core.actions.actions.onup||[]).find(function(a){return a.name==="_sys_onup";});
        if(!down||!up)return JSON.stringify({ok:false,reason:"missing-click-handler"});
        down.func.call(core.actions,target.x,target.y,actionPx,actionPy);
        up.func.call(core.actions,target.x,target.y,actionPx,actionPy);
        return JSON.stringify({ok:true,retry:true});
      })()`
    );
    if (!retry.ok) throw new Error(`map retry click x${x}y${y} failed: ${JSON.stringify(retry)}`);
  }
  return { before, metrics: result.metrics };
}

function expectedState(step) {
  const after = step.after;
  return {
    floor: after.floor,
    x: after.x,
    y: after.y,
    hp: after.hp,
    atk: after.atk,
    def: after.def,
    money: after.gold,
    yk: after.yk,
    bk: after.bk,
    rk: after.rk,
  };
}

function loosePositionAction(action) {
  return new Set([
    ACT.CHECK,
    ACT.CHANGE_FLOOR,
    ACT.TALK,
    ACT.SHOP,
    ACT.FLY,
    ACT.MERCHANT,
    ACT.EVENT,
    ACT.EVENT_REWARD,
    ACT.OPEN_DOOR,
  ]).has(action);
}

function valuesMatch(live, expected) {
  return live.floor === expected.floor &&
    live.hp === expected.hp &&
    live.atk === expected.atk &&
    live.def === expected.def &&
    live.money === expected.money &&
    live.yk === expected.yk &&
    live.bk === expected.bk &&
    live.rk === expected.rk;
}

function alreadyReachedStepLocation(live, step) {
  const expected = expectedState(step);
  if (!valuesMatch(live, expected)) return false;
  if (loosePositionAction(step.action)) {
    if ([ACT.TALK, ACT.EVENT, ACT.EVENT_REWARD, ACT.SHOP, ACT.MERCHANT].includes(step.action)) {
      return live.x === expected.x && live.y === expected.y;
    }
    const [x, y] = step.pos;
    return (live.x === expected.x && live.y === expected.y) ||
      Math.abs(live.x - x) + Math.abs(live.y - y) <= 1;
  }
  return live.x === expected.x && live.y === expected.y;
}

function matchesStep(live, step) {
  const expected = expectedState(step);
  if (!valuesMatch(live, expected)) return false;
  const mayRemainLocked = new Set([ACT.ARRIVE, ACT.TALK, ACT.SHOP, ACT.MERCHANT]).has(step.action);
  if (!mayRemainLocked && (live.lock || live.eventId || live.moving)) return false;
  if (step.action === ACT.EVENT_BATTLE && (live.lock || live.eventId || live.moving || live.hasChoices)) return false;
  if (loosePositionAction(step.action)) return true;
  return live.x === expected.x && live.y === expected.y;
}

async function targetClearedMatch(cdp, live, step) {
  const expected = expectedState(step);
  if (!valuesMatch(live, expected) || live.floor !== expected.floor) return false;
  if (live.lock || live.eventId || live.moving || live.hasChoices) return false;
  if (![ACT.KILL, ACT.PICKUP, ACT.PASS, ACT.OPEN_DOOR].includes(step.action)) return false;
  const [x, y] = step.pos;
  const ev = await targetEvent(cdp, step.floor, x, y);
  if (step.action === ACT.KILL) return !ev || ev.cls !== "enemys";
  if (step.action === ACT.PICKUP) return !ev || ev.cls !== "items";
  if (step.action === ACT.OPEN_DOOR) return !ev || ev.trigger !== "openDoor";
  if (step.action === ACT.PASS) return !ev || ev.id !== step.eid;
  return false;
}

function rewardItemNeedsPresence(step) {
  return step.action === ACT.EVENT_REWARD &&
    ["redKey", "yellowKey", "blueKey", "redGem", "blueGem", "centerFly3"].includes(step.eid);
}

async function sideEffectSatisfied(cdp, live, step) {
  const expected = expectedState(step);
  if (step.action === ACT.EVENT && step.eid === "centerFly3") {
    return live.floor === expected.floor && live.x === expected.x && live.y === expected.y;
  }
  if (rewardItemNeedsPresence(step)) {
    const [x, y] = step.pos;
    const ev = await targetEvent(cdp, step.floor, x, y);
    return !!ev && ev.id === step.eid && ev.cls === "items";
  }
  if (step.action === ACT.EVENT_REWARD && step.floor === "MT40" && step.eid === "yellowKnight") {
    const up = await targetEvent(cdp, "MT40", 6, 1);
    return !!up && up.id === "upFloor";
  }
  if (step.action === ACT.EVENT && step.floor === "MT2" && step.eid === "thief") {
    const tunnel = await targetEvent(cdp, "MT35", 4, 9);
    const thief = await targetEvent(cdp, "MT35", 5, 10);
    return !tunnel && !!thief && thief.id === "thief";
  }
  if (step.action === ACT.EVENT && step.floor === "MT35" && step.eid === "thief") {
    const thief = await targetEvent(cdp, "MT35", 5, 10);
    return !thief;
  }
  return true;
}

async function stepMatches(cdp, live, step) {
  if (matchesStep(live, step) && await sideEffectSatisfied(cdp, live, step)) return true;
  return targetClearedMatch(cdp, live, step);
}

function mismatchText(live, step) {
  const expected = expectedState(step);
  const bad = [];
  for (const key of ["floor", "x", "y", "hp", "atk", "def", "money", "yk", "bk", "rk"]) {
    if (live[key] !== expected[key]) bad.push(`${key}: expected ${expected[key]}, got ${live[key]}`);
  }
  return bad.join("; ");
}

function coalesceCandidateIndexes(steps, index) {
  const out = [index];
  const step = steps[index - 1];
  const next = steps[index];
  if (!next) return out;
  if (step.action === ACT.PASS && next.action === ACT.CHANGE_FLOOR) out.push(index + 1);
  if (step.action === ACT.ARRIVE && next.action === ACT.CHANGE_FLOOR) out.push(index + 1);
  if (
    step.action === ACT.ARRIVE &&
    (next.action === ACT.EVENT_BATTLE || next.action === ACT.EVENT || next.action === ACT.EVENT_REWARD)
  ) {
    const [x1, y1] = step.pos;
    const [x2, y2] = next.pos;
    if (step.floor === next.floor && x1 === x2 && y1 === y2) return [index + 1];
  }
  return out;
}

async function mouseClickCanvas(cdp) {
  const point = await evalJson(
    cdp,
    String.raw`(function(){
      var draw=main.dom.gameDraw;
      var rect=draw.getBoundingClientRect();
      return JSON.stringify({
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
        rect: {left: rect.left, top: rect.top, width: rect.width, height: rect.height}
      });
    })()`
  );
  const click = { x: point.x, y: point.y, button: "left", clickCount: 1 };
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: click.x, y: click.y });
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", ...click });
  await sleep(50);
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", ...click });
}

async function pressUndo(cdp, count) {
  for (let i = 0; i < count; i += 1) {
    await cdp.send("Input.dispatchKeyEvent", {
      type: "rawKeyDown",
      key: "a",
      code: "KeyA",
      windowsVirtualKeyCode: 65,
      nativeVirtualKeyCode: 65,
    });
    await cdp.send("Input.dispatchKeyEvent", {
      type: "char",
      key: "a",
      code: "KeyA",
      text: "a",
      unmodifiedText: "a",
      windowsVirtualKeyCode: 65,
      nativeVirtualKeyCode: 65,
    });
    await cdp.send("Input.dispatchKeyEvent", {
      type: "keyUp",
      key: "a",
      code: "KeyA",
      windowsVirtualKeyCode: 65,
      nativeVirtualKeyCode: 65,
    });
    await sleep(650);
  }
}

async function saveSlot(cdp, slot) {
  const result = await evalJson(
    cdp,
    `new Promise(function(resolve){
      try {
        var data = core.control.saveData(null);
        core.utils.setLocalForage('save${slot}', data, function(){
          resolve(JSON.stringify({ok:true, slot:${slot}}));
        });
      } catch (e) {
        resolve(JSON.stringify({ok:false, slot:${slot}, error:String(e&&e.stack||e)}));
      }
    })`
  );
  if (!result.ok) throw new Error(`save slot ${slot} failed: ${JSON.stringify(result)}`);
  return result;
}

async function loadSlot(cdp, slot) {
  const result = await evalJson(
    cdp,
    `new Promise(function(resolve){
      try {
        core.getSave(${slot}, function(data){
          if (!data) return resolve(JSON.stringify({ok:false, slot:${slot}, reason:"missing"}));
          try {
            if (core.dom && core.dom.startPanel) core.dom.startPanel.style.display = "none";
            if (main.dom && main.dom.startPanel) main.dom.startPanel.style.display = "none";
            if (main.dom && main.dom.levelChooseButtons) main.dom.levelChooseButtons.style.display = "none";
            if (main.dom && main.dom.startButtonGroup) main.dom.startButtonGroup.style.display = "none";
            core.loadData(data, function(){
              setTimeout(function(){
                var h = core.status.hero || {};
                var loc = h.loc || {};
                var ev = core.status.event || {};
                var ok = !!(core.isPlaying && core.isPlaying()) &&
                  !!core.status.hero &&
                  !core.status.lockControl &&
                  !core.status.heroMoving &&
                  !ev.id;
                resolve(JSON.stringify({
                  ok: ok,
                  slot: ${slot},
                  isPlaying: !!(core.isPlaying && core.isPlaying()),
                  startPanel: core.dom && core.dom.startPanel ? getComputedStyle(core.dom.startPanel).display : null,
                  floor: core.status.floorId || null,
                  x: loc.x,
                  y: loc.y,
                  lock: !!core.status.lockControl,
                  moving: !!core.status.heroMoving,
                  eventId: ev.id || null
                }));
              }, 800);
            });
          } catch (e) {
            resolve(JSON.stringify({ok:false, slot:${slot}, error:String(e&&e.stack||e)}));
          }
        });
      } catch (e) {
        resolve(JSON.stringify({ok:false, slot:${slot}, error:String(e&&e.stack||e)}));
      }
    })`
  );
  if (!result.ok) throw new Error(`load slot ${slot} failed: ${JSON.stringify(result)}`);
  await waitIdle(cdp, 20000);
  return result;
}

async function waitForCandidates(cdp, steps, candidateIndexes, desc, timeoutMs = 25000) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  while (Date.now() < end) {
    last = await state(cdp);
    for (const idx of candidateIndexes) {
      const step = steps[idx - 1];
      if (await stepMatches(cdp, last, step)) {
        return { state: last, matchedStep: idx };
      }
    }
    if (last.moving || last.eventType === "move" || (last.animateAsyncCount || 0) > 0) {
      await sleep(120);
      continue;
    }
    if (last.hasChoices) {
      await sleep(120);
      continue;
    }
    if (last.lock && !last.eventId && !last.hasChoices) {
      await sleep(150);
      continue;
    }
    if (last.lock || last.eventId) {
      await mouseClickCanvas(cdp);
      await sleep(450);
      continue;
    }
    await sleep(120);
  }
  const details = candidateIndexes
    .map((idx) => `step ${idx}: ${mismatchText(last, steps[idx - 1])}`)
    .join(" | ");
  throw new Error(`timeout waiting for ${desc}; last=${stateText(last)}; ${details}`);
}

async function waitIdle(cdp, timeoutMs = 15000) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  while (Date.now() < end) {
    last = await state(cdp);
    if (last.moving) {
      await sleep(120);
      continue;
    }
    if (last.hasChoices) return last;
    if (last.lock && !last.eventId && !last.hasChoices) {
      await sleep(150);
      continue;
    }
    if (last.lock || last.eventId) {
      await mouseClickCanvas(cdp);
      await sleep(450);
      continue;
    }
    return last;
  }
  throw new Error(`timeout waiting for idle; last=${stateText(last)}`);
}

async function settleAlreadyCompletedStep(cdp, step) {
  let st = await state(cdp);
  if (await targetClearedMatch(cdp, st, step)) return st;
  if (!alreadyReachedStepLocation(st, step)) return null;
  return await stepMatches(cdp, st, step) ? st : null;
}

async function flyTo(cdp, floor) {
  await clearRuntimeRoute(cdp);
  const before = await state(cdp);
  if (before.floor === floor) return before;
  await evalValue(cdp, `(function(){return core.flyTo(${JSON.stringify(floor)})})()`);
}

async function useItem(cdp, item) {
  await clearRuntimeRoute(cdp);
  await evalValue(cdp, `(function(){return core.useItem(${JSON.stringify(item)})})()`);
}

async function choose(cdp, kind) {
  const defaults = {
    hp: 0,
    atk: 1,
    def: 2,
    exit: 3,
    confirm: 0,
    sellYellowKey: 0,
    yellowKey: 0,
  };
  const index = defaults[kind] ?? 0;
  const result = await evalJson(
    cdp,
    `(function(){
      var ev=core.status.event||{};
      var choices=(ev.data&&ev.data.current&&ev.data.current.choices)||(ev.ui&&ev.ui.choices)||[];
      if (!choices.length || !choices[${index}]) {
        return JSON.stringify({ok:false, reason:"no-choice", index:${index}, choices:choices.map(function(c){return String(c.text||"");})});
      }
      var top=core.actions._getChoicesTopIndex(choices.length);
      core.actions._clickAction(core.actions.HSIZE, top+${index});
      return JSON.stringify({ok:true, index:${index}, text:String(choices[${index}].text||"")});
    })()`
  );
  if (!result.ok) throw new Error(`choose ${kind} failed: ${JSON.stringify(result)}`);
  return result;
}

function isMapClickAction(action) {
  return new Set([
    ACT.KILL,
    ACT.PASS,
    ACT.ARRIVE,
    ACT.EVENT_BATTLE,
    ACT.TALK,
    ACT.OPEN_DOOR,
    ACT.PICKUP,
  ]).has(action);
}

async function executeStep(cdp, step) {
  const [x, y] = step.pos;
  if (step.action === ACT.CHECK || step.action === ACT.CHANGE_FLOOR) {
    return;
  }
  if (step.action === ACT.FLY) {
    await flyTo(cdp, step.floor);
    return;
  }
  if (step.action === ACT.SHOP || step.action === ACT.MERCHANT) {
    await choose(cdp, step.eid || "confirm");
    return;
  }
  if (step.action === ACT.EVENT_REWARD) {
    const st = await state(cdp);
    if (st.hasChoices) await choose(cdp, "confirm");
    else await mouseClickCanvas(cdp);
    return;
  }
  if (step.action === ACT.EVENT && step.eid === "centerFly3") {
    await useItem(cdp, "centerFly");
    return;
  }
  if (step.action === ACT.EVENT) {
    const st = await state(cdp);
    if (st.hasChoices) await choose(cdp, "confirm");
    else if (st.lock || st.eventId) await mouseClickCanvas(cdp);
    else await mouseClickTile(cdp, x, y);
    return;
  }
  if (isMapClickAction(step.action)) {
    const st = await state(cdp);
    if (step.action === ACT.EVENT_BATTLE && st.x === x && st.y === y) {
      if (!(st.lock || st.eventId || st.moving || (st.animateAsyncCount || 0) > 0)) {
        await mouseClickCanvas(cdp);
      }
    } else {
      await mouseClickTile(cdp, x, y);
      await maybeRetryAdjacentTarget(cdp, step);
    }
    return;
  }
  throw new Error(`unsupported action ${step.action} at ${step.floor} x${x}y${y}`);
}

async function maybeCloseMenu(cdp, step, next) {
  if (!next || next.action !== step.action) {
    if ((step.action === ACT.SHOP || step.action === ACT.MERCHANT) && (await state(cdp)).hasChoices) {
      await choose(cdp, "exit");
      await waitIdle(cdp);
    }
  }
}

async function runOneStep(cdp, steps, oneBased, stop) {
  const step = steps[oneBased - 1];
  const [x, y] = step.pos;
  console.log(`[${String(oneBased).padStart(3, "0")}] ${step.floor} x${x}y${y} ${step.action} ${step.eid || ""}`);
  const already = await settleAlreadyCompletedStep(cdp, step);
  if (already) {
    console.log(`      -> already completed ${stateText(already)}`);
    await maybeCloseMenu(cdp, step, steps[oneBased]);
    return { state: already, consumed: oneBased };
  }
  await executeStep(cdp, step);
  const candidates = coalesceCandidateIndexes(steps, oneBased).filter((idx) => idx <= stop);
  const result = await waitForCandidates(cdp, steps, candidates, `step ${oneBased}`);
  if (result.matchedStep !== oneBased) {
    console.log(`      -> coalesced through step ${result.matchedStep}`);
  }
  console.log(`      -> ${stateText(result.state)}`);
  const consumed = result.matchedStep;
  await maybeCloseMenu(cdp, steps[consumed - 1], steps[consumed]);
  return { state: result.state, consumed };
}

async function run() {
  const args = parseArgs(process.argv);
  const walk = JSON.parse(fs.readFileSync(args.walk, "utf8"));
  if (!walk.ok) throw new Error(`walk is not ok: ${walk.errors}`);
  const steps = walk.steps;
  const stop = args.stopStep || steps.length;
  const cdp = await connectGameTarget();
  try {
    if (args.loadSlot != null) {
      await loadSlot(cdp, args.loadSlot);
      console.log(`loaded save${args.loadSlot} ${stateText(await state(cdp))}`);
    }
    if (args.undoSteps > 0) {
      console.log(`before undo ${stateText(await state(cdp))}`);
      await pressUndo(cdp, args.undoSteps);
      console.log(`after undo ${stateText(await waitIdle(cdp))}`);
      return;
    }
    let st = await state(cdp);
    console.log(`start ${stateText(st)}`);
    if (args.requireStart) {
      const first = expectedState(steps[args.startStep - 1]);
      if (!matchesStep(st, steps[args.startStep - 1])) {
        throw new Error(`live state does not match start step ${args.startStep}: ${mismatchText(st, steps[args.startStep - 1])}; live=${stateText(st)}`);
      }
    }

    for (let oneBased = args.startStep; oneBased <= stop;) {
      if (args.retryOnFailure && args.stepSaveSlot != null) {
        await saveSlot(cdp, args.stepSaveSlot);
      }
      let stepResult;
      try {
        stepResult = await runOneStep(cdp, steps, oneBased, stop);
      } catch (err) {
        if (!(args.retryOnFailure && args.stepSaveSlot != null)) throw err;
        console.log(`      !! ${err.message || String(err)}`);
        console.log(`      !! reloading save${args.stepSaveSlot} and retrying step ${oneBased} once`);
        await loadSlot(cdp, args.stepSaveSlot);
        stepResult = await runOneStep(cdp, steps, oneBased, stop);
      }
      st = stepResult.state;
      if (args.progressSaveSlot != null) await saveSlot(cdp, args.progressSaveSlot);
      oneBased = stepResult.consumed + 1;
    }
  } finally {
    cdp.close();
  }
}

run().catch((err) => {
  console.error(err.stack || String(err));
  process.exit(1);
});
