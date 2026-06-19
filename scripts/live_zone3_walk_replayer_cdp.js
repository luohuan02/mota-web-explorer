#!/usr/bin/env node
// Replay the generated zone-3 walk in the already-open h5mota browser via CDP.

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const DEFAULT_WALK = path.join(ROOT, "outputs", "results", "zone3_quick_pass_walk.json");
const CDP_LIST = "http://127.0.0.1:9222/json/list";

function parseArgs(argv) {
  const out = {
    walk: DEFAULT_WALK,
    startStep: 1,
    stopStep: null,
    noRestore: false,
    strictSteps: new Set(),
  };
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--walk") out.walk = path.resolve(argv[++i]);
    else if (arg === "--start-step") out.startStep = Number(argv[++i]);
    else if (arg === "--stop-step") out.stopStep = Number(argv[++i]);
    else if (arg === "--no-restore") out.noRestore = true;
    else if (arg === "--strict-step") out.strictSteps.add(Number(argv[++i]));
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

const STATE_EXPR = `(function(){var h=core.status.hero,loc=h.loc,t=h.items.tools,e=core.status.event||{};return JSON.stringify({floor:core.status.floorId,x:loc.x,y:loc.y,hp:h.hp,atk:h.atk,def:h.def,money:h.money,yk:t.yellowKey||0,bk:t.blueKey||0,rk:t.redKey||0,lock:!!core.status.lockControl,moving:!!core.status.heroMoving,eventId:e.id||null,hasChoices:!!(e.data&&e.data.current&&e.data.current.choices),choices:e.data&&e.data.current&&e.data.current.choices?e.data.current.choices.map(function(c){return String(c.text||'')}):[]})})()`;

async function state(cdp) {
  return evalJson(cdp, STATE_EXPR);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function stateText(s) {
  return `${s.floor} x${s.x}y${s.y} HP=${s.hp} ATK=${s.atk} DEF=${s.def} YK=${s.yk} BK=${s.bk} RK=${s.rk} G=${s.money} lock=${s.lock} moving=${s.moving} choices=${s.hasChoices}`;
}

async function clearRuntimeRoute(cdp) {
  await evalValue(
    cdp,
    `(function(){try{if(core.stopAutomaticRoute)core.stopAutomaticRoute();if(core.clearContinueAutomaticRoute)core.clearContinueAutomaticRoute();core.status.route=[];if(core.status.replay){core.status.replay.toReplay=[];core.status.replay.totalList=[];core.status.replay.replaying=false;core.status.replay.pausing=false;}}catch(e){}return true})()`
  );
}

async function waitSettle(cdp, { keepChoices = true, timeoutMs = 15000 } = {}) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  let staleLockTicks = 0;
  while (Date.now() < end) {
    last = await state(cdp);
    if (last.moving) {
      await sleep(120);
      continue;
    }
    if (last.hasChoices && keepChoices) return last;
    if (last.lock && !last.eventId && !last.hasChoices) {
      staleLockTicks += 1;
      if (staleLockTicks >= 4) {
        await evalValue(
          cdp,
          `(function(){try{if(core.unlockControl)core.unlockControl();else core.status.lockControl=false;return true}catch(e){return false}})()`
        );
        staleLockTicks = 0;
      }
      await sleep(150);
      continue;
    }
    staleLockTicks = 0;
    if (last.lock || last.eventId || last.hasChoices) {
      await evalValue(cdp, `(function(){try{core.doAction();return true}catch(e){return false}})()`);
      await sleep(150);
      continue;
    }
    return last;
  }
  throw new Error(`timeout waiting for idle; last=${stateText(last)}`);
}

async function stepAdjacent(cdp, x, y) {
  await clearRuntimeRoute(cdp);
  const result = await evalValue(
    cdp,
    `new Promise(function(resolve){var x=${x},y=${y},dx=x-core.getHeroLoc('x'),dy=y-core.getHeroLoc('y');if(Math.abs(dx)+Math.abs(dy)!==1)return resolve({ok:false,reason:'not-adjacent'});if(core.status.lockControl||core.status.heroMoving)return resolve({ok:false,reason:'busy'});var direction=dx===1?'right':dx===-1?'left':dy===1?'down':'up';core.setHeroLoc('direction',direction);if(!core.canMoveHero(direction))return resolve({ok:false,reason:'blocked'});var fromX=core.getHeroLoc('x'),fromY=core.getHeroLoc('y');core.setHeroLoc('x',core.nextX(),true);core.setHeroLoc('y',core.nextY(),true);try{core.status.route.push(direction)}catch(e){}var done=false;var finish=function(){if(done)return;done=true;setTimeout(function(){resolve({ok:true})},80)};try{core.moveOneStep(fromX,fromY,finish)}catch(e){return resolve({ok:false,reason:String(e)})}setTimeout(finish,1200)})`
  );
  if (!result || !result.ok) throw new Error(`stepAdjacent x${x}y${y} failed: ${JSON.stringify(result)}`);
  await sleep(200);
  return waitSettle(cdp);
}

async function pathTo(cdp, x, y) {
  return evalValue(
    cdp,
    `(function(){var target={x:${x},y:${y}},floor=core.status.floorId,map=core.status.maps[floor]||{},w=map.width||13,h=map.height||13,start={x:core.getHeroLoc('x'),y:core.getHeroLoc('y')};var terrain={fakeWall:1,empty:1};function key(p){return p.x+','+p.y}function block(px,py){try{return core.getBlockId(px,py)}catch(e){return 'yellowWall'}}function pass(px,py){if(px<0||py<0||px>=w||py>=h)return false;if(px===target.x&&py===target.y)return true;var id=block(px,py);return !id||terrain[id]}var q=[start],seen={};seen[key(start)]=null;for(var head=0;head<q.length;head++){var cur=q[head];if(cur.x===target.x&&cur.y===target.y)break;var ns=[{x:cur.x+1,y:cur.y},{x:cur.x-1,y:cur.y},{x:cur.x,y:cur.y+1},{x:cur.x,y:cur.y-1}];for(var i=0;i<ns.length;i++){var n=ns[i],k=key(n);if(k in seen||!pass(n.x,n.y))continue;seen[k]=cur;q.push(n)}}var tk=key(target);if(!(tk in seen))return null;var path=[];for(var p=target;p;p=seen[key(p)])path.push([p.x,p.y]);path.reverse();if(path.length&&path[0][0]===start.x&&path[0][1]===start.y)path.shift();return path})()`
  );
}

async function moveTo(cdp, x, y) {
  const before = await state(cdp);
  if (before.x === x && before.y === y) return waitSettle(cdp);
  const dx = x - before.x;
  const dy = y - before.y;
  if (Math.abs(dx) + Math.abs(dy) === 1) return stepAdjacent(cdp, x, y);
  const path = await pathTo(cdp, x, y);
  if (!path || !path.length) {
    throw new Error(`no live path from ${stateText(before)} to x${x}y${y}`);
  }
  let st = before;
  for (const [px, py] of path) {
    st = await stepAdjacent(cdp, px, py);
    if (st.floor !== before.floor) return st;
    if (st.x === x && st.y === y) return st;
  }
  return st;
}

async function waitForFloor(cdp, floor, timeoutMs = 12000) {
  const end = Date.now() + timeoutMs;
  let last = await state(cdp);
  let staleLockTicks = 0;
  while (Date.now() < end) {
    last = await state(cdp);
    if (last.floor === floor) return waitSettle(cdp);
    if (last.moving) {
      await sleep(120);
      continue;
    }
    if (last.lock && !last.eventId && !last.hasChoices) {
      staleLockTicks += 1;
      if (staleLockTicks >= 4) {
        await evalValue(
          cdp,
          `(function(){try{if(core.unlockControl)core.unlockControl();else core.status.lockControl=false;return true}catch(e){return false}})()`
        );
        staleLockTicks = 0;
      }
    } else if (last.lock || last.eventId || last.hasChoices) {
      await evalValue(cdp, `(function(){try{core.doAction();return true}catch(e){return false}})()`);
    }
    await sleep(150);
  }
  throw new Error(`timeout waiting for floor ${floor}; last=${stateText(last)}`);
}

async function flyTo(cdp, floor) {
  await clearRuntimeRoute(cdp);
  const before = await state(cdp);
  if (before.floor === floor) return waitSettle(cdp);
  await evalValue(cdp, `(function(){return core.flyTo(${JSON.stringify(floor)})})()`);
  return waitForFloor(cdp, floor);
}

async function useItem(cdp, item) {
  await evalValue(cdp, `(function(){return core.useItem(${JSON.stringify(item)})})()`);
  return waitSettle(cdp);
}

async function choose(cdp, kind) {
  const defaults = {
    hp: 0,
    atk: 1,
    def: 2,
    exit: 3,
    sellYellowKey: 0,
    yellowKey: 0,
  };
  const hints = {
    hp: ["生命", "血"],
    atk: ["攻击"],
    def: ["防御"],
    exit: ["离开", "下次"],
    sellYellowKey: ["需要", "黄钥匙", "卖"],
    yellowKey: ["黄钥匙", "购买", "买"],
  };
  const st = await state(cdp);
  if (!st.hasChoices) throw new Error(`no choices for ${kind}: ${stateText(st)}`);
  let index = defaults[kind] ?? 0;
  const words = hints[kind] || [];
  for (let i = 0; i < st.choices.length; i++) {
    if (words.some((w) => st.choices[i].includes(w))) {
      index = i;
      break;
    }
  }
  await evalValue(
    cdp,
    `(function(){var cs=core.status.event.data.current.choices;var top=core.actions._getChoicesTopIndex(cs.length);core.actions._clickAction(core.actions.HSIZE,top+${index});return true})()`
  );
  return waitSettle(cdp);
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

function assertExpected(live, expected, label) {
  const bad = [];
  for (const [key, value] of Object.entries(expected)) {
    if (live[key] !== value) bad.push(`${key}: expected ${value}, got ${live[key]}`);
  }
  if (bad.length) throw new Error(`${label} mismatch: ${bad.join("; ")}; live=${stateText(live)}`);
}

async function run() {
  const args = parseArgs(process.argv);
  const walk = JSON.parse(fs.readFileSync(args.walk, "utf8"));
  if (!walk.ok) throw new Error(`walk is not ok: ${walk.errors}`);
  const steps = walk.steps;
  const stop = args.stopStep || steps.length;
  const cdp = await connectGameTarget();
  try {
    await evalValue(cdp, `(function(){window.__codex_zone3_backup=core.control.saveData(null);return true})()`);
    let st = await state(cdp);
    console.log(`start ${stateText(st)}`);
    for (let oneBased = args.startStep; oneBased <= stop; oneBased++) {
      const step = steps[oneBased - 1];
      const action = step.action;
      const eid = step.eid;
      const [x, y] = step.pos;
      console.log(`[${String(oneBased).padStart(3, "0")}] ${step.floor} x${x}y${y} ${action} ${eid || ""}`);

      if (action === "校验" || action === "事件战斗") {
        st = await waitSettle(cdp);
      } else if (action === "事件奖励") {
        st = (await state(cdp)).hasChoices ? await choose(cdp, "confirm") : await waitSettle(cdp);
      } else if (action === "飞行") {
        st = await flyTo(cdp, step.floor);
      } else if (action === "换层") {
        st = await waitSettle(cdp);
      } else if (action === "商店") {
        st = await choose(cdp, eid);
      } else if (action === "商人") {
        st = await choose(cdp, eid);
      } else if (action === "事件" && eid === "centerFly3") {
        st = await useItem(cdp, "centerFly3");
      } else if (action === "事件" && (await state(cdp)).hasChoices) {
        st = await choose(cdp, "confirm");
      } else {
        st = await moveTo(cdp, x, y);
      }

      const next = steps[oneBased];
      if ((action === "商店" && (!next || next.action !== "商店")) || (action === "商人" && (!next || next.action !== "商人"))) {
        if ((await state(cdp)).hasChoices) st = await choose(cdp, "exit");
      }
      if (args.strictSteps.has(oneBased)) {
        assertExpected(await state(cdp), expectedState(step), `step ${oneBased}`);
      }
      console.log(`      -> ${stateText(await state(cdp))}`);
    }
  } finally {
    if (!args.noRestore) {
      await evalValue(
        cdp,
        `new Promise(function(resolve){if(!window.__codex_zone3_backup)return resolve(false);core.loadData(window.__codex_zone3_backup,null);setTimeout(function(){try{if(core.stopAutomaticRoute)core.stopAutomaticRoute();if(core.clearContinueAutomaticRoute)core.clearContinueAutomaticRoute();core.status.route=[];if(core.status.lockControl&&!core.status.heroMoving&&!(core.status.event&&core.status.event.id)&&!(core.status.event&&core.status.event.ui)){if(core.unlockControl)core.unlockControl();else core.status.lockControl=false;}}catch(e){}resolve(true)},700)})`
      );
      await sleep(200);
      console.log(`restored ${stateText(await state(cdp))}`);
    }
    cdp.close();
  }
}

run().catch((err) => {
  console.error(err.stack || String(err));
  process.exit(1);
});
