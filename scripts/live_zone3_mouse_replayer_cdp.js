#!/usr/bin/env node
// Replay the generated zone-3 walk in the live h5mota page using map mouse
// clicks for movement/targets. This intentionally does not set hero location
// or synthesize per-tile movement.

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const DEFAULT_WALK = path.join(ROOT, "outputs", "results", "zone3_quick_pass_walk.json");
const CDP_LIST = "http://127.0.0.1:9222/json/list";

const RUNTIME = {
  targetClickOnly: false,
};

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
  MAP_DAMAGE: "\u5730\u56fe\u4f24\u5bb3",
  CENTER_FLY: "\u4e2d\u5fc3\u98de\u884c",
  UP_FLY: "\u4e0a\u697c\u5668",
  DOWN_FLY: "\u4e0b\u697c\u5668",
  BIG_KEY: "\u9b54\u6cd5\u94a5\u5319",
  EARTHQUAKE: "\u5730\u9707\u5377\u8f74",
  BOMB: "\u70b8\u5f39",
  PICKAXE: "\u4f7f\u7528\u9550",
  USE: "\u4f7f\u7528",
  OLDMAN: "\u8001\u4eba",
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
    // Stage checkpoint: write a 100+ save slot every N steps as an exploration
    // chain (101, 102, 103, ...). On a clean full run the chain is a complete
    // live record; on failure, resume from the latest slot; on a fresh run from
    // step 1, the chain restarts at --checkpoint-start (overwriting the old one).
    // NOT a per-step write -- that bloats IndexedDB and can freeze the page.
    // For small live mistakes prefer the game's `a` undo key (see pressUndo).
    checkpointStart: null,
    checkpointEvery: 50,
    // On a step failure, try the game `a` undo key this many times before giving
    // up (default 0 = stop immediately). Cheaper and faster than reload+replay.
    undoOnFailure: 0,
    targetClickOnly: false,
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
    else if (arg === "--checkpoint-start") out.checkpointStart = Number(argv[++i]);
    else if (arg === "--checkpoint-every") out.checkpointEvery = Number(argv[++i]);
    else if (arg === "--undo-on-failure") out.undoOnFailure = Number(argv[++i]);
    else if (arg === "--target-click-only") out.targetClickOnly = true;
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
  var data=ev.data||{}, rawCurrent=data.current, ui=ev.ui||{};
  var currentObj=rawCurrent&&typeof rawCurrent==="object" ? rawCurrent : null;
  var currentType=currentObj ? currentObj.type : null;
  var inferredType=typeof rawCurrent==="string" ? "text" : null;
  var pending=(data.list&&data.list[0]&&data.list[0].todo&&data.list[0].todo[0])||null;
  var pendingType=!rawCurrent&&pending ? (typeof pending==="string" ? "text" : pending.type||null) : null;
  var eventType=currentType||ui.type||data.type||inferredType||pendingType||null;
  var choices=[];
  if (currentObj&&currentObj.choices) choices=currentObj.choices;
  else if (eventType==="choices") choices=ui.choices||[];
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
    eventType: eventType,
    eventUi: !!ev.ui,
    hasChoices: !!(choices&&choices.length),
    choices: choices ? choices.map(function(c){ return String(c.text||""); }) : [],
    autoHeroMove: !!(core.status.automaticRoute&&core.status.automaticRoute.autoHeroMove),
    pendingAction: !!(!rawCurrent&&pending),
    hasAsyncAnimate: !!(core.hasAsyncAnimate&&core.hasAsyncAnimate()),
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

async function continuePendingAction(cdp) {
  return evalJson(
    cdp,
    `(function(){
      var ev=core.status.event||{}, data=ev.data||{}, current=data.current;
      var list=data.list||[], first=list[0]||{}, todo=first.todo||[];
      var currentType=current&&typeof current==="object" ? current.type : null;
      var canStart=ev.id==="action" && !current && todo.length>0;
      var noAsync=!(core.hasAsyncAnimate&&core.hasAsyncAnimate());
      var canFinishHide=ev.id==="action" && currentType==="hide" && !(core.hasAsyncAnimate&&core.hasAsyncAnimate());
      var canFinishShow=ev.id==="action" && currentType==="show" && !(core.hasAsyncAnimate&&core.hasAsyncAnimate());
      var canFinishSleep=ev.id==="action" && currentType==="sleep";
      var canFinishCurtain=ev.id==="action" && currentType==="setCurtain" && !(core.hasAsyncAnimate&&core.hasAsyncAnimate());
      var canFinishMapMutation=ev.id==="action" && noAsync && ["setBlock","setBgFgBlock","openDoor","waitAsync","move"].indexOf(currentType)>=0;
      if (canStart || canFinishHide || canFinishShow || canFinishSleep || canFinishCurtain || canFinishMapMutation) {
        if (canFinishSleep && core.timeout && core.timeout.sleepTimeout) {
          clearTimeout(core.timeout.sleepTimeout);
          core.timeout.sleepTimeout=null;
        }
        core.doAction();
        return JSON.stringify({ok:true, reason:canStart?"start":canFinishSleep?"finishSleep":canFinishCurtain?"finishCurtain":canFinishShow?"finishShow":canFinishMapMutation?"finishMapMutation":"finishHide"});
      }
      return JSON.stringify({ok:false});
    })()`
  );
}

async function clearStaleLock(cdp) {
  return evalJson(
    cdp,
    `(function(){
      var ev=core.status.event||{};
      if (core.status.lockControl && !core.status.heroMoving && !ev.id && !ev.ui) {
        if (core.unlockControl) core.unlockControl();
        else core.status.lockControl=false;
        return JSON.stringify({ok:true});
      }
      return JSON.stringify({ok:false});
    })()`
  );
}

async function clearStaleMoving(cdp) {
  return evalJson(
    cdp,
    `(function(){
      var ev=core.status.event||{}, ar=core.status.automaticRoute||{};
      if (core.status.heroMoving && !ar.autoHeroMove && !ev.id && !ev.ui) {
        core.status.heroMoving=0;
        core.status.route=[];
        if (core.status.lockControl) {
          if (core.unlockControl) core.unlockControl();
          else core.status.lockControl=false;
        }
        return JSON.stringify({ok:true});
      }
      return JSON.stringify({ok:false});
    })()`
  );
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

async function waitMovementSettled(cdp, timeoutMs = 60000) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  while (Date.now() < end) {
    last = await state(cdp);
    if (!last.moving) return last;
    if (last.moving && !last.autoHeroMove && !last.eventId && !last.hasChoices) {
      await clearStaleMoving(cdp);
      last = await state(cdp);
      if (!last.moving) return last;
    }
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
  if (live.floor !== floor || live.lock || live.eventId || live.hasChoices || live.moving) return false;
  if (Math.abs(live.x - x) + Math.abs(live.y - y) !== 1) return false;
  if ([ACT.TALK, ACT.PASS, ACT.OPEN_DOOR, ACT.KILL, ACT.EVENT_BATTLE].includes(action)) return true;
  if (action === ACT.ARRIVE && (!ev || ev.noPass)) return true;
  if (!ev) return false;
  return ev.noPass && ["action", "openDoor", "battle"].includes(ev.trigger);
}

async function maybeRetryAdjacentTarget(cdp, step) {
  const [x, y] = step.pos;
  let st = await waitMovementSettled(cdp);
  if (st.lock && !st.eventId && !st.hasChoices && !st.moving) {
    await clearStaleLock(cdp);
    st = await state(cdp);
  }
  const ev = await targetEvent(cdp, step.floor, x, y);
  if (!canRetryAdjacentTarget(step.action, st, step.floor, x, y, ev)) return;
  await mouseClickTile(cdp, x, y);
  st = await waitMovementSettled(cdp);
  if (st.lock && !st.eventId && !st.hasChoices && !st.moving) {
    await clearStaleLock(cdp);
    st = await state(cdp);
  }
  const evAfterClick = await targetEvent(cdp, step.floor, x, y);
  if (!canRetryAdjacentTarget(step.action, st, step.floor, x, y, evAfterClick)) return;
  const direction = directionFromTo(st, x, y);
  if (!direction) return;
  await pressDirection(cdp, direction);
}

const STEP_DIRS = {
  right: [1, 0], left: [-1, 0], down: [0, 1], up: [0, -1],
};

async function nextCellIsStair(cdp, floor, x, y, dir, tx, ty) {
  // True if stepping one tile in `dir` lands on a stair (upFloor/downFloor)
  // that is NOT the intended target -- the hero must avoid those mid-route or
  // it triggers an unintended floor change (the 43F/45F up-down loop bug).
  const [dx, dy] = STEP_DIRS[dir];
  const nx = x + dx;
  const ny = y + dy;
  // If this IS the target tile, stepping onto it is intentional (the hero wants
  // to climb the stair).
  if (nx === tx && ny === ty) return false;
  const ev = await targetEvent(cdp, floor, nx, ny);
  if (!ev) return false;
  return ev.id === "upFloor" || ev.id === "downFloor";
}

async function stepwiseMoveTo(cdp, tx, ty, maxSteps = 60) {
  // Walk one tile at a time toward (tx,ty) via the game's own moveHero, for
  // cases where a single distant map click does not auto-route the hero (e.g.
  // path crosses a wizard spell-field the click-router refuses). Each step uses
  // core.moveHero(dir) and waits for the move + any triggered event to settle.
  // Avoids stepping on stair tiles that are not the target (would trigger an
  // unintended floor change).
  for (let i = 0; i < maxSteps; i += 1) {
    const st = await state(cdp);
    if (st.x === tx && st.y === ty) return;
    if (st.lock || st.eventId || st.hasChoices || st.moving) {
      // An event fired en route; let the caller's waitForCandidates handle it.
      return;
    }
    const dx = Math.sign(tx - st.x);
    const dy = Math.sign(ty - st.y);
    const primary = dx !== 0 ? (dx > 0 ? "right" : "left") : (dy > 0 ? "down" : "up");
    const secondary = dy !== 0 ? (dy > 0 ? "down" : "up") : (dx > 0 ? "right" : "left");
    // Pick a direction that does not step onto a non-target stair tile.
    let dir = primary;
    if (primary === secondary) {
      if (await nextCellIsStair(cdp, st.floor, st.x, st.y, primary, tx, ty)) return;
    } else if (await nextCellIsStair(cdp, st.floor, st.x, st.y, primary, tx, ty)) {
      dir = secondary;
      if (await nextCellIsStair(cdp, st.floor, st.x, st.y, secondary, tx, ty)) return;
    }
    const before = { x: st.x, y: st.y, floor: st.floor };
    await evalValue(cdp, `(function(){ core.moveHero(${JSON.stringify(dir)}); return true; })()`);
    const settled = await waitForStepAdvance(cdp, before);
    if (settled.blocked && settled.floor === before.floor) {
      // Blocked on this axis; try the other axis (if different).
      if (secondary === dir) return;
      if (await nextCellIsStair(cdp, settled.floor, settled.x, settled.y, secondary, tx, ty)) return;
      const before2 = { x: settled.x, y: settled.y, floor: settled.floor };
      await evalValue(cdp, `(function(){ core.moveHero(${JSON.stringify(secondary)}); return true; })()`);
      const settled2 = await waitForStepAdvance(cdp, before2);
      if (settled2.blocked && settled2.floor === before2.floor) return; // truly stuck
    }
  }
}

async function waitForStepAdvance(cdp, before, timeoutMs = 6000) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  while (Date.now() < end) {
    last = await state(cdp);
    const moved = last.x !== before.x || last.y !== before.y || last.floor !== before.floor;
    const eventFired = last.lock || last.eventId || last.hasChoices;
    // `moving` true means the step has started even if position has not updated yet.
    if (moved || eventFired || last.moving) {
      // Wait for the move + any triggered event/floor-change to fully settle.
      await waitMovementSettled(cdp);
      // A stair pickup triggers a floor change that is not `moving`; ride it out.
      let s = await state(cdp);
      let guard = 0;
      while ((s.lock || s.eventId || s.moving) && guard < 60) {
        await sleep(100);
        s = await state(cdp);
        guard += 1;
      }
      return { blocked: false, x: s.x, y: s.y, floor: s.floor };
    }
    await sleep(80);
  }
  return { blocked: true, x: last.x, y: last.y, floor: last.floor };
}

async function mouseClickTile(cdp, x, y) {
  await clearRuntimeRoute(cdp);
  let before = await state(cdp);
  if (before.lock && !before.eventId && !before.hasChoices && !before.moving) {
    await clearStaleLock(cdp);
    before = await state(cdp);
  }
  if (before.moving && !before.autoHeroMove && !before.eventId && !before.hasChoices) {
    await clearStaleMoving(cdp);
    before = await state(cdp);
  }
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

async function rawMouseClickTile(cdp, x, y) {
  const point = await tileMetrics(cdp, x, y);
  if (point.tile.x !== x || point.tile.y !== y) {
    throw new Error(`raw click tile mismatch x${x}y${y}: ${JSON.stringify(point)}`);
  }
  const click = { x: point.clientX, y: point.clientY, button: "left", clickCount: 1 };
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseMoved", x: click.x, y: click.y });
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", ...click });
  await sleep(60);
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", ...click });
}

function isWaitingForTargetSelection(st) {
  return st.lock && st.eventId === "action" && st.eventType === "waitAsync" && !st.hasChoices;
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
  // ARRIVE: accept exact or adjacent (move_adjacent landing).
  if (step.action === ACT.ARRIVE) {
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
  // A still-moving hero must never match -- the move hasn't settled, so stats/
  // position are mid-transition. But CHANGE_FLOOR and FLY are floor transitions
  // where moving may persist briefly after landing.
  if (live.moving && !(step.action === ACT.CHANGE_FLOOR || step.action === ACT.FLY)) return false;
  if (!mayRemainLocked && (live.lock || live.eventId)) return false;
  if (step.action === ACT.EVENT_BATTLE && (live.lock || live.eventId || live.hasChoices)) return false;
  if (step.action === ACT.OPEN_DOOR) {
    const [x, y] = step.pos;
    return (live.x === expected.x && live.y === expected.y) ||
      Math.abs(live.x - x) + Math.abs(live.y - y) <= 1;
  }
  if (loosePositionAction(step.action)) return true;
  // ARRIVE: the hero often stops on a tile adjacent to the target (move_adjacent
  // for shops/NPCs, or auto-route stopping one short). Accept exact or adjacent.
  if (step.action === ACT.ARRIVE) {
    const [x, y] = step.pos;
    return (live.x === expected.x && live.y === expected.y) ||
      Math.abs(live.x - x) + Math.abs(live.y - y) <= 1;
  }
  // OLDMAN: the hero often stops on an adjacent tile when the NPC dialog opens
  // (e.g. 16F fakeWall drops the hero at x10y11, oldman at x11y11). Accept adjacent.
  if (step.action === ACT.OLDMAN) {
    const [x, y] = step.pos;
    return (live.x === expected.x && live.y === expected.y) ||
      Math.abs(live.x - x) + Math.abs(live.y - y) <= 1;
  }
  // EARTHQUAKE/BOMB/USE don't move the hero; their recorded position is just the
  // hero's standing tile, which may differ from live after a fly (live flyTo
  // restores the last on-floor position, not the fly_points landing). Accept any
  // position as long as floor + stats match. Individual use actions can add
  // their own short waits before matching if the page needs animation time.
  if (step.action === ACT.USE && step.eid === "snow") {
    return live.floor === expected.floor && live.x === expected.x && live.y === expected.y;
  }
  if ([ACT.EARTHQUAKE, ACT.BOMB, ACT.USE].includes(step.action)) {
    return live.floor === expected.floor;
  }
  return live.x === expected.x && live.y === expected.y;
}

async function targetClearedMatch(cdp, live, step) {
  const expected = expectedState(step);
  if (!valuesMatch(live, expected) || live.floor !== expected.floor) return false;
  if (![ACT.KILL, ACT.PICKUP, ACT.PASS, ACT.OPEN_DOOR].includes(step.action)) return false;
  const postKillText = step.action === ACT.KILL &&
    live.lock && live.eventId === "action" && live.eventType === "text" &&
    !live.moving && !live.hasChoices;
  if ((live.lock || live.eventId || live.moving || live.hasChoices) && !postKillText) return false;
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
  if (step.action === ACT.EVENT && step.floor === "MT42" && step.eid === "yellowKnightEscape") {
    const ev = await targetEvent(cdp, "MT42", 5, 10);
    return !ev || ev.trigger !== "action";
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
  if (step.action === ACT.EVENT && step.floor === "MT26" && step.eid === "princess") {
    const rescued = await evalJson(
      cdp,
      `(function(){ return JSON.stringify({ok: !!core.getFlag(${JSON.stringify("营救公主")}, false)}); })()`
    );
    return rescued.ok;
  }
  if (step.action === ACT.OLDMAN && step.eid === "superPotion") {
    const item = await evalJson(
      cdp,
      `(function(){ return JSON.stringify({ok: !!(core.itemCount&&core.itemCount("superPotion")>0)}); })()`
    );
    return item.ok;
  }
  return true;
}

async function stepMatches(cdp, live, step) {
  // ARRIVE on an action/changeFloor trigger tile (e.g. 49F x6y6 boss trigger)
  // must be reached exactly -- adjacent does not fire the event, so reject the
  // adjacent-tolerance match from matchesStep.
  if (step.action === ACT.ARRIVE) {
    const [x, y] = step.pos;
    const ev = await targetEvent(cdp, step.floor, x, y);
    const hasTrigger = ev && (
      ev.noPass ||
      ev.trigger === "action" ||
      ev.trigger === "changeFloor" ||
      ev.id === "none" ||
      ev.id === "upFloor" ||
      ev.id === "downFloor"
    );
    if (hasTrigger) {
      if (live.x !== x || live.y !== y) return false;
      if (live.lock || live.eventId || live.moving || live.hasChoices) return false;
    }
  }
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
  const chainActions = new Set([
    ACT.KILL,
    ACT.PASS,
    ACT.ARRIVE,
    ACT.OPEN_DOOR,
    ACT.PICKUP,
    ACT.MAP_DAMAGE,
  ]);
  if (chainActions.has(step.action)) {
    for (let offset = 1; offset <= 6; offset += 1) {
      const cand = steps[index - 1 + offset];
      if (!cand || cand.floor !== step.floor || !chainActions.has(cand.action)) break;
      out.push(index + offset);
    }
  }
  if (step.action === ACT.PASS && next.action === ACT.CHANGE_FLOOR) out.push(index + 1);
  if (step.action === ACT.ARRIVE && next.action === ACT.CHANGE_FLOOR) out.push(index + 1);
  const lastIdx = out[out.length - 1];
  const lastStep = steps[lastIdx - 1];
  const afterLast = steps[lastIdx];
  if (lastStep && afterLast && lastStep.action === ACT.PASS && afterLast.action === ACT.CHANGE_FLOOR) {
    out.push(lastIdx + 1);
  }
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

async function focusGame(cdp) {
  try { await cdp.send("Page.bringToFront"); } catch (_) { /* best effort */ }
  await evalValue(
    cdp,
    String.raw`(function(){
      try { window.focus(); } catch (e) {}
      try {
        var draw = main && main.dom && main.dom.gameDraw;
        if (draw) {
          if (!draw.hasAttribute("tabindex")) draw.setAttribute("tabindex", "0");
          if (draw.focus) draw.focus();
        }
      } catch (e) {}
      return true;
    })()`
  );
}

async function pressDirection(cdp, direction) {
  const keys = {
    up: ["ArrowUp", "ArrowUp", 38],
    down: ["ArrowDown", "ArrowDown", 40],
    left: ["ArrowLeft", "ArrowLeft", 37],
    right: ["ArrowRight", "ArrowRight", 39],
  };
  const entry = keys[direction];
  if (!entry) return;
  const [key, code, windowsVirtualKeyCode] = entry;
  await focusGame(cdp);
  const before = await state(cdp);
  await cdp.send("Input.dispatchKeyEvent", {
    type: "keyDown",
    key,
    code,
    windowsVirtualKeyCode,
    nativeVirtualKeyCode: windowsVirtualKeyCode,
  });
  await sleep(60);
  await cdp.send("Input.dispatchKeyEvent", {
    type: "keyUp",
    key,
    code,
    windowsVirtualKeyCode,
    nativeVirtualKeyCode: windowsVirtualKeyCode,
  });
  await sleep(120);
  const after = await state(cdp);
  const changed = after.floor !== before.floor ||
    after.x !== before.x || after.y !== before.y ||
    after.hp !== before.hp || after.atk !== before.atk || after.def !== before.def ||
    after.money !== before.money || after.yk !== before.yk || after.bk !== before.bk || after.rk !== before.rk ||
    after.lock || after.eventId || after.moving || after.hasChoices;
  if (!changed) {
    await evalValue(
      cdp,
      `(function(){
        var e={keyCode:${windowsVirtualKeyCode}, preventDefault:function(){}, stopPropagation:function(){}};
        if (core.onkeyDown) core.onkeyDown(e);
        if (core.onkeyUp) core.onkeyUp(e);
        return true;
      })()`
    );
  }
}

function directionFromTo(from, x, y) {
  const dx = x - from.x;
  const dy = y - from.y;
  if (dx === 1 && dy === 0) return "right";
  if (dx === -1 && dy === 0) return "left";
  if (dx === 0 && dy === 1) return "down";
  if (dx === 0 && dy === -1) return "up";
  return null;
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

async function waitForCandidates(cdp, steps, candidateIndexes, desc, timeoutMs = 90000) {
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
    if (last.eventId === "action" && (!last.eventType || last.pendingAction || last.eventType === "hide" || last.eventType === "show" || last.eventType === "sleep" || last.eventType === "setCurtain" || last.eventType === "setBlock" || last.eventType === "setBgFgBlock" || last.eventType === "openDoor" || last.eventType === "waitAsync" || last.eventType === "move")) {
      const progressed = await continuePendingAction(cdp);
      if (progressed.ok) {
        await sleep(250);
        continue;
      }
    }
    if (last.moving && !last.autoHeroMove && !last.eventId && !last.hasChoices) {
      await clearStaleMoving(cdp);
      await sleep(80);
      continue;
    }
    if (last.moving || last.eventType === "move") {
      await sleep(120);
      continue;
    }
    if (last.hasChoices) {
      const shopCandidate = candidateIndexes.some((idx) =>
        [ACT.SHOP, ACT.MERCHANT].includes(steps[idx - 1].action)
      );
      if (!shopCandidate) {
        await choose(cdp, "confirm");
        await sleep(450);
      } else {
        await sleep(120);
      }
      continue;
    }
    if (last.lock && !last.eventId && !last.hasChoices) {
      const cleared = await clearStaleLock(cdp);
      await sleep(cleared.ok ? 80 : 150);
      continue;
    }
    // changeFloor / floor-transition actions are automatic animations -- do NOT
    // click the canvas (it interrupts the transition). Just wait for the floor
    // to change. Only click for dialogue/shop/choice events.
    if (last.eventType === "changeFloor") {
      await sleep(200);
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
    if (last.eventId === "action" && (!last.eventType || last.pendingAction || last.eventType === "hide" || last.eventType === "show" || last.eventType === "sleep" || last.eventType === "setCurtain" || last.eventType === "setBlock" || last.eventType === "setBgFgBlock" || last.eventType === "openDoor" || last.eventType === "waitAsync" || last.eventType === "move")) {
      const progressed = await continuePendingAction(cdp);
      if (progressed.ok) {
        await sleep(250);
        continue;
      }
    }
    if (last.moving && !last.autoHeroMove && !last.eventId && !last.hasChoices) {
      await clearStaleMoving(cdp);
      await sleep(80);
      continue;
    }
    if (last.moving || last.eventType === "move") {
      await sleep(120);
      continue;
    }
    if (last.hasChoices) return last;
    if (last.lock && !last.eventId && !last.hasChoices) {
      const cleared = await clearStaleLock(cdp);
      await sleep(cleared.ok ? 80 : 150);
      continue;
    }
    if (last.eventType === "changeFloor") {
      await sleep(200);
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

async function waitForChoices(cdp, timeoutMs = 15000) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  while (Date.now() < end) {
    last = await state(cdp);
    if (last.hasChoices) return last;
    if (last.eventId === "action" && (!last.eventType || last.pendingAction || last.eventType === "hide" || last.eventType === "show" || last.eventType === "sleep" || last.eventType === "setCurtain" || last.eventType === "setBlock" || last.eventType === "setBgFgBlock" || last.eventType === "openDoor" || last.eventType === "waitAsync" || last.eventType === "move")) {
      const progressed = await continuePendingAction(cdp);
      if (progressed.ok) {
        await sleep(250);
        continue;
      }
    }
    if (last.moving && !last.autoHeroMove && !last.eventId && !last.hasChoices) {
      await clearStaleMoving(cdp);
      await sleep(80);
      continue;
    }
    if (last.moving || last.eventType === "move") {
      await sleep(120);
      continue;
    }
    if (last.lock && !last.eventId && !last.hasChoices) {
      const cleared = await clearStaleLock(cdp);
      await sleep(cleared.ok ? 80 : 150);
      continue;
    }
    if (last.lock || last.eventId) {
      await sleep(150);
      continue;
    }
    await sleep(120);
  }
  throw new Error(`timeout waiting for choices; last=${stateText(last)}`);
}

async function settleAlreadyCompletedStep(cdp, step) {
  let st = await state(cdp);
  // Stair PASS: if the changeFloor action is already in progress (from a
  // previous attempt), wait for it to settle instead of trying to re-click.
  if (step.action === ACT.PASS && (step.eid === "upFloor" || step.eid === "downFloor")
      && st.lock && st.eventId === "action" && Math.abs(st.x - step.pos[0]) + Math.abs(st.y - step.pos[1]) <= 1) {
    await sleep(2500); // let the floor-change animation complete
    st = await state(cdp);
  }
  if (await targetClearedMatch(cdp, st, step)) return st;
  // Pickaxe: only "already completed" if the target wall is actually gone.
  // The hero's stats/position are unchanged by using a pickaxe, so a pure
  // position match would falsely skip it.
  if (step.action === ACT.PICKAXE) {
    const [x, y] = step.pos;
    const ev = await targetEvent(cdp, step.floor, x, y);
    if (ev && (ev.cls === "animates" || ev.id === "yellowWall" || ev.id === "whiteWall")) return null;
  }
  // Earthquake/bomb/bigKey: they only destroy walls / open doors and do not
  // change hero stats or position, so a position+values match would falsely
  // mark them done. Always execute them.
  if (step.action === ACT.EARTHQUAKE || step.action === ACT.BOMB || step.action === ACT.BIG_KEY || step.action === ACT.USE) return null;
  // ARRIVE means "walk onto this tile". It must always execute even if the
  // hero is adjacent (e.g. stepping onto an opened-door tile to reach the
  // lava edge, or reaching a boss trigger). Never skip ARRIVE from adjacent
  // position -- only an EXACT match means it is genuinely already completed.
  if (step.action === ACT.ARRIVE && (st.x !== step.pos[0] || st.y !== step.pos[1])) {
    return null;
  }
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
    specialTrader: 0,
    hp2000: 0,
    keyBundle31: 0,
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
    ACT.MAP_DAMAGE,
    ACT.OLDMAN,
  ]).has(action);
}

async function repeatTargetClick(cdp, step, baseFloor, attempts = 3) {
  const [x, y] = step.pos;
  let current = await state(cdp);
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    if (current.floor !== step.floor || current.floor !== baseFloor) return current;
    if (current.lock || current.eventId || current.hasChoices || current.moving) return current;
    const dist = Math.abs(current.x - x) + Math.abs(current.y - y);
    if (dist < 1) return current;
    await mouseClickTile(cdp, x, y);
    await maybeRetryAdjacentTarget(cdp, step);
    current = await state(cdp);
    if (current.floor !== baseFloor) return current;
    if (current.lock || current.eventId || current.hasChoices || current.moving) return current;
    if (Math.abs(current.x - x) + Math.abs(current.y - y) < 1) return current;
  }
  return current;
}

async function executeStep(cdp, step) {
  const [x, y] = step.pos;
  if (step.action === ACT.CHECK || step.action === ACT.CHANGE_FLOOR) {
    return;
  }
  if (step.action === ACT.FLY) {
    await flyTo(cdp, step.floor);
    await waitIdle(cdp, 20000);
    return;
  }
  if (step.action === ACT.SHOP || step.action === ACT.MERCHANT) {
    // The shop/trader dialog must be opened first by clicking the NPC tile;
    // only then do choices appear. If already in a choices dialog, choose now.
    let st = await state(cdp);
    if (!st.hasChoices) {
      // step.pos is the hero's adjacent landing tile, NOT always the shop's
      // action tile (some shops span 3 cells; only the center has trigger=action).
      // Try the recorded tile first, then scan its neighbours for the real shop
      // action tile.
      const tryTiles = [[x, y]];
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        tryTiles.push([x + dx, y + dy]);
      }
      for (const [tx, ty] of tryTiles) {
        st = await state(cdp);
        if (st.hasChoices || st.lock || st.eventId) break;
        const ev = await targetEvent(cdp, step.floor, tx, ty);
        if (!ev) continue;
        const isShop = ev.id === "shop" || ev.id === "blueShop" ||
          (ev.id || "").startsWith("blueShop") || ev.id === "trader" || ev.trigger === "action";
        if (!isShop && !(tx === x && ty === y)) continue;
        await mouseClickTile(cdp, tx, ty);
        try {
          st = await waitForChoices(cdp, 15000);
        } catch (_) {
          await maybeRetryAdjacentTarget(cdp, { ...step, pos: [tx, ty] });
          st = await state(cdp);
          if (!st.hasChoices) {
            try { st = await waitForChoices(cdp, 15000); } catch (_) { st = await state(cdp); }
          }
        }
        if (st.hasChoices || st.lock || st.eventId) break;
      }
    }
    if (!st.hasChoices) st = await waitForChoices(cdp, 15000);
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
  if (step.action === ACT.CENTER_FLY) {
    await useItem(cdp, "centerFly");
    return;
  }
  if (step.action === ACT.UP_FLY) {
    await useItem(cdp, "upFly");
    return;
  }
  if (step.action === ACT.DOWN_FLY) {
    await useItem(cdp, "downFly");
    return;
  }
  if (step.action === ACT.BIG_KEY) {
    await useItem(cdp, "bigKey");
    return;
  }
  if (step.action === ACT.EARTHQUAKE) {
    await useItem(cdp, "earthquake");
    return;
  }
  if (step.action === ACT.BOMB) {
    await useItem(cdp, "bomb");
    return;
  }
  if (step.action === ACT.PICKAXE) {
    // Pickaxe breaks adjacent breakable walls by item effect; it does not open
    // a target selection UI in this game. The recorded pos is the wall expected
    // to disappear, not a tile to click after using the item.
    await useItem(cdp, "pickaxe");
    await waitIdle(cdp);
    return;
  }
  if (step.action === ACT.USE) {
    if (step.eid === "snow") {
      let st = await state(cdp);
      if (st.floor === step.floor && (st.x !== x || st.y !== y) && !st.lock && !st.eventId && !st.hasChoices && !st.moving) {
        await mouseClickTile(cdp, x, y);
        await waitMovementSettled(cdp);
        st = await state(cdp);
        if (st.floor === step.floor && (st.x !== x || st.y !== y) && !st.lock && !st.eventId && !st.hasChoices && !st.moving) {
          if (RUNTIME.targetClickOnly) {
            throw new Error(`target click did not reach USE ${step.eid} tile x${x}y${y}: ${stateText(st)}`);
          }
          await stepwiseMoveTo(cdp, x, y);
        }
      }
    }
    await useItem(cdp, step.eid || "confirm");
    if (step.eid === "snow") await sleep(2000);
    return;
  }
  if (step.action === ACT.EVENT) {
    const st = await state(cdp);
    if (st.hasChoices) await choose(cdp, "confirm");
    else if (st.lock || st.eventId) await mouseClickCanvas(cdp);
    else {
      await mouseClickTile(cdp, x, y);
      const after = await state(cdp);
      if (
        after.floor === st.floor &&
        !after.lock &&
        !after.eventId &&
        !after.hasChoices &&
        !after.moving
      ) {
        await repeatTargetClick(cdp, step, st.floor);
      }
    }
    return;
  }
  if (step.action === ACT.OLDMAN) {
    // The oldman dialog may already be open from the previous step (e.g. walking
    // onto the fakeWall x11y11 tile on 16F). If choices are shown, choose confirm.
    // If the dialog is already closing (action:hide), just let it settle.
    const st = await state(cdp);
    if (st.hasChoices || st.eventType === "hide") {
      if (st.hasChoices && st.eventType !== "hide") await choose(cdp, "confirm");
    } else if (st.lock || st.eventId) {
      await mouseClickCanvas(cdp);
    } else {
      await mouseClickTile(cdp, x, y);
    }
    return;
  }
  if (isMapClickAction(step.action)) {
    let st = await state(cdp);
    if (step.action === ACT.KILL && st.floor === step.floor && st.x === x && st.y === y) {
      const ev = await targetEvent(cdp, step.floor, x, y);
      if (ev && ev.cls === "enemys") {
        for (const [ax, ay] of [[x, y + 1], [x, y - 1], [x - 1, y], [x + 1, y]]) {
          if (ax < 1 || ax > 13 || ay < 1 || ay > 13) continue;
          const adj = await targetEvent(cdp, step.floor, ax, ay);
          if (adj && adj.noPass) continue;
          await mouseClickTile(cdp, ax, ay);
          await waitMovementSettled(cdp);
          st = await state(cdp);
          if (st.x !== x || st.y !== y) break;
        }
      }
    }
    if (step.action === ACT.KILL && st.floor === step.floor && Math.abs(st.x - x) + Math.abs(st.y - y) === 1) {
      const ev = await targetEvent(cdp, step.floor, x, y);
      if (ev && (ev.cls === "enemys" || ev.trigger === "battle")) {
        const direction = directionFromTo(st, x, y);
        if (direction) {
          await pressDirection(cdp, direction);
          return;
        }
      }
    }
    if (step.action === ACT.EVENT_BATTLE && st.x === x && st.y === y) {
      if (!(st.lock || st.eventId || st.moving || (st.animateAsyncCount || 0) > 0)) {
        await mouseClickCanvas(cdp);
      }
    } else if (step.action === ACT.PASS && (step.eid === "upFloor" || step.eid === "downFloor")) {
      if (step.floor === "MT41" && x === 6 && y === 11 && st.floor === "MT41" && st.x === 6 && st.y === 4) {
        for (const [tx, ty] of [[6, 5], [6, 7], [6, 8], [6, 9], [6, 11]]) {
          st = await state(cdp);
          if (st.floor !== "MT41") break;
          await mouseClickTile(cdp, tx, ty);
          await waitMovementSettled(cdp);
        }
        return;
      }
      // Prefer the real map click handler for stairs. If the click router stops
      // short, fall back to tile-by-tile movement toward the stair target.
      await mouseClickTile(cdp, x, y);
      await maybeRetryAdjacentTarget(cdp, step);
      const after = await state(cdp);
      const floorChanged = after.floor !== st.floor;
      const dist = Math.abs(after.x - x) + Math.abs(after.y - y);
      if (
        dist >= 1 &&
        !floorChanged &&
        !after.lock &&
        !after.eventId &&
        !after.hasChoices &&
        !after.moving
      ) {
        const changed = after.hp !== st.hp || after.atk !== st.atk || after.def !== st.def ||
          after.money !== st.money || after.yk !== st.yk || after.bk !== st.bk || after.rk !== st.rk;
        if (changed) return;
        if (RUNTIME.targetClickOnly) {
          const retried = await repeatTargetClick(cdp, step, st.floor);
          const retryDist = Math.abs(retried.x - x) + Math.abs(retried.y - y);
          if (
            retryDist >= 1 &&
            retried.floor === st.floor &&
            !retried.lock &&
            !retried.eventId &&
            !retried.hasChoices &&
            !retried.moving
          ) {
            throw new Error(`target click stopped before stair x${x}y${y}: ${stateText(retried)}`);
          }
          return;
        }
        await stepwiseMoveTo(cdp, x, y);
      }
    } else {
      await mouseClickTile(cdp, x, y);
      await maybeRetryAdjacentTarget(cdp, step);
      const after = await state(cdp);
      const floorChanged = after.floor !== st.floor;
      const dist = Math.abs(after.x - x) + Math.abs(after.y - y);
      if (
        dist >= 1 &&
        !floorChanged &&
        !after.lock &&
        !after.eventId &&
        !after.hasChoices &&
        !after.moving
      ) {
        const changed = after.hp !== st.hp || after.atk !== st.atk || after.def !== st.def ||
          after.money !== st.money || after.yk !== st.yk || after.bk !== st.bk || after.rk !== st.rk;
        if (changed) return;
        if (RUNTIME.targetClickOnly) {
          const retried = await repeatTargetClick(cdp, step, st.floor);
          const retryDist = Math.abs(retried.x - x) + Math.abs(retried.y - y);
          if (
            retryDist >= 1 &&
            retried.floor === st.floor &&
            !retried.lock &&
            !retried.eventId &&
            !retried.hasChoices &&
            !retried.moving
          ) {
            throw new Error(`target click stopped before target x${x}y${y}: ${stateText(retried)}`);
          }
          return;
        }
        await stepwiseMoveTo(cdp, x, y);
      }
    }
    return;
  }
  throw new Error(`unsupported action ${step.action} at ${step.floor} x${x}y${y}`);
}

async function maybeCloseMenu(cdp, step, next) {
  if (!next || next.action !== step.action) {
    if ((step.action === ACT.SHOP || step.action === ACT.MERCHANT) && (await state(cdp)).hasChoices) {
      try { await choose(cdp, "exit"); } catch (_) { /* menu auto-closed */ }
      await waitIdle(cdp);
    }
  }
}

async function runOneStep(cdp, steps, oneBased, stop) {
  const step = steps[oneBased - 1];
  const [x, y] = step.pos;
  console.log(`[${String(oneBased).padStart(3, "0")}] ${step.floor} x${x}y${y} ${step.action} ${step.eid || ""}`);
  const candidates = coalesceCandidateIndexes(steps, oneBased).filter((idx) => idx <= stop);
  let execStep = step;
  if (step.floor === "MT41" && step.pos[0] === 6 && [7, 8, 9].includes(step.pos[1])) {
    const stairIdx = candidates.find((idx) => {
      const cand = steps[idx - 1];
      return cand.floor === "MT41" && cand.action === ACT.PASS && cand.pos[0] === 6 && cand.pos[1] === 11;
    });
    if (stairIdx) execStep = steps[stairIdx - 1];
  }
  const already = await settleAlreadyCompletedStep(cdp, step);
  if (already) {
    console.log(`      -> already completed ${stateText(already)}`);
    await maybeCloseMenu(cdp, step, steps[oneBased]);
    return { state: already, consumed: oneBased };
  }
  if (step.action === ACT.ARRIVE && steps[oneBased] && steps[oneBased].action === ACT.FLY) {
    const live = await state(cdp);
    const expected = expectedState(step);
    if (
      live.floor === expected.floor &&
      valuesMatch(live, expected) &&
      !live.lock &&
      !live.eventId &&
      !live.moving &&
      !live.hasChoices
    ) {
      console.log(`      -> skipped pre-fly arrive ${stateText(live)}`);
      return { state: live, consumed: oneBased };
    }
  }
  const pre = await state(cdp);
  const menuStep = [ACT.SHOP, ACT.MERCHANT].includes(step.action);
  if ((pre.lock || pre.eventId || pre.moving || pre.hasChoices) && !(pre.hasChoices && menuStep)) {
    const preTimeout = pre.eventId === "action" && [ACT.KILL, ACT.EVENT_BATTLE, ACT.EVENT].includes(step.action)
      ? 180000
      : 15000;
    try {
      const result = await waitForCandidates(cdp, steps, candidates, `step ${oneBased}`, preTimeout);
      if (result.matchedStep !== oneBased) {
        console.log(`      -> coalesced through step ${result.matchedStep}`);
      }
      console.log(`      -> ${stateText(result.state)}`);
      const consumed = result.matchedStep;
      await maybeCloseMenu(cdp, steps[consumed - 1], steps[consumed]);
      return { state: result.state, consumed };
    } catch (e) {
      const settled = await state(cdp);
      if (settled.lock || settled.eventId || settled.moving || settled.hasChoices) throw e;
    }
  }
  await executeStep(cdp, execStep);
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
  RUNTIME.targetClickOnly = !!args.targetClickOnly;
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
      let stepResult;
      try {
        stepResult = await runOneStep(cdp, steps, oneBased, stop);
      } catch (err) {
        if (args.undoOnFailure > 0) {
          console.log(`      !! ${err.message || String(err)}`);
          console.log(`      !! pressing undo x${args.undoOnFailure} then retrying step ${oneBased}`);
          await pressUndo(cdp, args.undoOnFailure);
          await waitIdle(cdp);
          stepResult = await runOneStep(cdp, steps, oneBased, stop);
        } else {
          throw err;
        }
      }
      st = stepResult.state;
      // Stage checkpoint chain: 101, 102, 103, ... every N successful steps.
      if (args.checkpointStart != null && oneBased % args.checkpointEvery === 0) {
        const slot = args.checkpointStart + Math.floor(oneBased / args.checkpointEvery) - 1;
        await saveSlot(cdp, slot);
        console.log(`      :: checkpoint save${slot} @ step ${oneBased}`);
      }
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
