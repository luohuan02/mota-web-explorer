#!/usr/bin/env node
// Replay the 4F-10F boss walk in the live h5mota page with the project's
// current auto settings enabled, using real map-click handlers.

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const CDP_LIST = "http://127.0.0.1:9222/json/list";
const DEFAULT_WALK = path.join(ROOT, "best", "current_best_boss_walk.md");
const DEFAULT_JSON = path.join(ROOT, "outputs", "results", "zone1_current_best_live_auto_replay.json");
const DEFAULT_MD = path.join(ROOT, "outputs", "walkthroughs", "zone1_current_best_live_auto_walk_zh.md");

const ENEMY_NAMES = {
  greenSlime: "绿头怪",
  redSlime: "红头怪",
  bluePriest: "初级法师",
  bat: "小蝙蝠",
  skeleton: "骷髅人",
  skeletonSoldier: "骷髅士兵",
  yellowGuard: "初级卫兵",
  skeletonCaptain: "骷髅队长",
};

const ITEM_NAMES = {
  yellowDoor: "黄门",
  blueDoor: "蓝门",
  redDoor: "红门",
  redGem: "红宝石",
  blueGem: "蓝宝石",
  yellowKey: "黄钥匙",
  blueKey: "蓝钥匙",
  redKey: "红钥匙",
  redPotion: "红血瓶",
  bluePotion: "蓝血瓶",
  sword1: "铁剑",
  shield1: "铁盾",
  upFloor: "上楼梯",
  downFloor: "下楼梯",
  fakeWall: "暗墙",
};

const ACTION_NAMES = {
  open: "开",
  kill: "打",
  take: "取",
  pass: "走",
  trigger: "触发",
  event: "事件",
};

function parseArgs(argv) {
  const out = {
    walk: DEFAULT_WALK,
    outJson: DEFAULT_JSON,
    outMd: DEFAULT_MD,
    loadSlot: 1,
    itemMode: true,
    stopClicks: null,
    fromJson: null,
    saveSlot: null,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--walk") out.walk = path.resolve(argv[++i]);
    else if (arg === "--out-json") out.outJson = path.resolve(argv[++i]);
    else if (arg === "--out-md") out.outMd = path.resolve(argv[++i]);
    else if (arg === "--load-slot") out.loadSlot = Number(argv[++i]);
    else if (arg === "--item-mode") {
      const mode = argv[++i];
      if (mode === "true") out.itemMode = true;
      else if (mode === "nopotion") out.itemMode = "nopotion";
      else throw new Error("--item-mode 只能是 true 或 nopotion");
    }
    else if (arg === "--stop-clicks") out.stopClicks = Number(argv[++i]);
    else if (arg === "--from-json") out.fromJson = path.resolve(argv[++i]);
    else if (arg === "--save-slot") out.saveSlot = Number(argv[++i]);
    else throw new Error(`未知参数: ${arg}`);
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
  if (!target) throw new Error("未找到 9222 端口上的 h5mota 页面");

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
  var eventType=currentObj ? currentObj.type : ui.type || data.type || null;
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
    hasChoices: !!(ui.choices&&ui.choices.length),
    routeLen: (core.status.route||[]).length,
    autoHeroMove: !!(core.status.automaticRoute&&core.status.automaticRoute.autoHeroMove),
    auto: h.flags&&h.flags.__auto__ || null
  });
})()`;

async function state(cdp) {
  return evalJson(cdp, STATE_EXPR);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function coreStateText(s) {
  return `${s.floor} x${s.x}y${s.y} 生命=${s.hp} 攻=${s.atk} 防=${s.def} 黄=${s.yk} 蓝=${s.bk} 红=${s.rk} 金币=${s.money}`;
}

function shortStateText(s) {
  return `生命=${s.hp} 攻=${s.atk} 防=${s.def} 黄=${s.yk} 蓝=${s.bk} 红=${s.rk} 金币=${s.money}`;
}

function deltaText(before, after) {
  const pairs = [
    ["生命", before.hp, after.hp],
    ["攻", before.atk, after.atk],
    ["防", before.def, after.def],
    ["黄", before.yk, after.yk],
    ["蓝", before.bk, after.bk],
    ["红", before.rk, after.rk],
    ["金币", before.money, after.money],
  ];
  const out = pairs.filter(([, a, b]) => a !== b).map(([n, a, b]) => `${n} ${a}->${b}`);
  return out.join("，") || "无数值变化";
}

function fmtScore(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  const num = Number(value);
  return Number.isInteger(num) ? String(num) : num.toFixed(1);
}

function sourceWalkPath(args, payload) {
  if (payload.sourceWalk) return path.resolve(ROOT, payload.sourceWalk);
  return args.walk;
}

function candidateSummaryPaths(walkPath) {
  const paths = [];
  if (walkPath.endsWith("_walk.md")) {
    paths.push(walkPath.replace(/_walk\.md$/, "_summary.json"));
  }
  const base = path.basename(walkPath);
  if (base === "current_best_boss_walk.md") {
    paths.push(path.join(path.dirname(walkPath), "current_best_boss_summary.json"));
  }
  return [...new Set(paths)];
}

function loadZone1ScoreSummary(walkPath) {
  for (const candidate of candidateSummaryPaths(walkPath)) {
    if (!fs.existsSync(candidate)) continue;
    const data = JSON.parse(fs.readFileSync(candidate, "utf8"));
    const s = data.summary || data;
    if (!s || s.final_score === undefined || s.dmg === undefined) continue;
    return {
      name: "1区 Boss 后",
      source: path.relative(ROOT, candidate),
      hp: s.hp,
      atk: s.atk,
      def: s.def,
      yk: s.yk,
      bk: s.bk,
      rk: s.rk,
      gold: s.gold,
      dmg: s.dmg,
      yd: s.yd,
      bd: s.bd,
      rd: s.rd,
      finalScore: s.final_score,
      baseFinalStock: s.base_final_stock,
      remainingGroupValue: s.remaining_group_value,
      merchantResidual: s.merchant_residual,
      futureMonsterGoldScore: s.future_monster_gold_score,
      goldScore: s.gold_score,
    };
  }
  return null;
}

function scoreComponentsText(score) {
  if (!score) return "-";
  const parts = [
    ["baseStock", score.baseFinalStock],
    ["剩余资源组", score.remainingGroupValue],
    ["商人残值", score.merchantResidual],
    ["未来怪金币分", score.futureMonsterGoldScore],
    ["金币分", score.goldScore],
  ]
    .filter(([, value]) => value !== undefined && value !== null)
    .map(([name, value]) => `${name}=${fmtScore(value)}`);
  return parts.join("；") || "-";
}

function scoreNote(score, liveState) {
  if (!score || !liveState || score.gold === undefined || score.gold === null) return score ? `来源 ${score.source}` : "-";
  const deltaGold = liveState.money - score.gold;
  if (!deltaGold) return `来源 ${score.source}`;
  const deltaScore = deltaGold * 0.5;
  const refScore = score.finalScore + deltaScore;
  return `来源 ${score.source}；live 金币比本地 ${deltaGold >= 0 ? "+" : ""}${deltaGold}，按 100G=50HP 折算 ${deltaScore >= 0 ? "+" : ""}${fmtScore(deltaScore)}，参考 final-score=${fmtScore(refScore)}，正式分数仍需本地重算确认`;
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
    a.hasChoices === b.hasChoices;
}

async function clearRuntimeRoute(cdp) {
  await evalValue(
    cdp,
    `(function(){
      try {
        if (core.stopAutomaticRoute) core.stopAutomaticRoute();
        if (core.clearContinueAutomaticRoute) core.clearContinueAutomaticRoute();
        core.status.route=[];
      } catch(e) {}
      return true;
    })()`
  );
}

async function continuePendingAction(cdp) {
  return evalJson(
    cdp,
    `(function(){
      var ev=core.status.event||{}, data=ev.data||{}, current=data.current;
      var list=data.list||[], first=list[0]||{}, todo=first.todo||[];
      var currentType=current&&typeof current==="object" ? current.type : null;
      var currentIsText=typeof current==="string";
      var noAsync=!(core.hasAsyncAnimate&&core.hasAsyncAnimate());
      var canStart=ev.id==="action" && !current && todo.length>0;
      var canFinish=ev.id==="action" && noAsync && ["hide","show","setBlock","openDoor","waitAsync","move","sleep","setCurtain"].indexOf(currentType)>=0;
      if (canStart || canFinish || (ev.id==="action" && currentIsText)) {
        if (currentType==="sleep" && core.timeout && core.timeout.sleepTimeout) {
          clearTimeout(core.timeout.sleepTimeout);
          core.timeout.sleepTimeout=null;
        }
        core.doAction();
        return JSON.stringify({ok:true});
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
      if (core.status.heroMoving && !ar.autoHeroMove && !ev.id && !ev.ui && !(core.status.route||[]).length) {
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

async function waitIdle(cdp, before, desc, timeoutMs = 45000) {
  const deadline = Date.now() + timeoutMs;
  let changed = false;
  let last = await state(cdp);
  let movingStableSignature = "";
  let movingStableSince = 0;
  while (Date.now() < deadline) {
    last = await state(cdp);
    changed = changed || !sameObservableState(before, last);
    if (last.lock && !last.moving && last.eventId === "action" && !last.hasChoices) {
      await continuePendingAction(cdp);
    } else if (last.lock && !last.moving && !last.eventId && !last.hasChoices) {
      await clearStaleLock(cdp);
    } else if (last.moving && !last.autoHeroMove && !last.eventId && !last.hasChoices && !last.routeLen) {
      const sig = `${last.floor}:${last.x}:${last.y}:${last.hp}:${last.atk}:${last.def}:${last.money}:${last.yk}:${last.bk}:${last.rk}`;
      if (sig !== movingStableSignature) {
        movingStableSignature = sig;
        movingStableSince = Date.now();
      } else if (changed && Date.now() - movingStableSince > 2500) {
        await clearStaleMoving(cdp);
      }
    }
    if (!last.moving && !last.lock && !last.eventId) {
      if (changed) {
        await sleep(150);
        return state(cdp);
      }
      return last;
    }
    await sleep(120);
  }
  throw new Error(`等待 ${desc} 超时：${coreStateText(last)} lock=${last.lock} event=${last.eventId || "-"} moving=${last.moving}`);
}

async function loadSlot(cdp, slot) {
  const before = await state(cdp);
  const result = await evalJson(
    cdp,
    `new Promise(function(resolve){
      try {
        core.getSave(${slot}, function(data){
          if (!data) return resolve(JSON.stringify({ok:false, reason:"missing"}));
          data.route=[];
          core.loadData(data, null);
          setTimeout(function(){
            try {
              if (core.stopAutomaticRoute) core.stopAutomaticRoute();
              if (core.clearContinueAutomaticRoute) core.clearContinueAutomaticRoute();
              core.status.route=[];
              if (core.status.lockControl && !core.status.heroMoving && !(core.status.event&&core.status.event.id) && !(core.status.event&&core.status.event.ui)) {
                if (core.unlockControl) core.unlockControl();
                else core.status.lockControl=false;
              }
            } catch(e) {}
            resolve(JSON.stringify({ok:true}));
          }, 900);
        });
      } catch(e) {
        resolve(JSON.stringify({ok:false, error:String(e&&e.stack||e)}));
      }
    })`
  );
  if (!result.ok) throw new Error(`读取 ${slot} 号存档失败：${JSON.stringify(result)}`);
  return waitIdle(cdp, before, `读取 ${slot} 号存档`, 15000);
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
  if (!result.ok) throw new Error(`写入 ${slot} 号存档失败：${JSON.stringify(result)}`);
  return result;
}

async function setAuto(cdp, itemMode) {
  const itemValue = itemMode === "nopotion" ? `"nopotion"` : "true";
  await evalValue(
    cdp,
    `(function(){
      if (!core.status.hero.flags) core.status.hero.flags={};
      core.status.hero.flags.__auto__={battle:true,item:${itemValue},wall:true};
      return true;
    })()`
  );
  return state(cdp);
}

async function targetBlock(cdp, fid, x, y) {
  return evalJson(
    cdp,
    `(function(){
      var map=core.status.maps[${JSON.stringify(fid)}]||{};
      var blocks=map.blocks||[];
      var block=blocks.find(function(b){return b.x===${x}&&b.y===${y}&&!b.disable;});
      if(!block||!block.event)return JSON.stringify(null);
      return JSON.stringify({id:block.event.id, cls:block.event.cls, trigger:block.event.trigger||null});
    })()`
  );
}

function canSkipMissingTarget(step) {
  return ["open", "kill", "take"].includes(step.action);
}

async function mt10BossEnemies(cdp) {
  return evalJson(
    cdp,
    `(function(){
      var map=core.status.maps.MT10||{};
      var blocks=(map.blocks||[]).filter(function(b){
        return !b.disable && b.event && b.event.cls==="enemys" &&
          b.x>=4 && b.x<=8 && b.y>=1 && b.y<=7;
      }).map(function(b){
        return {x:b.x,y:b.y,id:b.event.id,cls:b.event.cls,trigger:b.event.trigger||null};
      }).sort(function(a,b){return a.y-b.y || a.x-b.x});
      return JSON.stringify(blocks);
    })()`
  );
}

function bossPriority(enemy) {
  const key = `${enemy.x},${enemy.y}`;
  const order = [
    "5,4", "6,4", "7,4",
    "5,5", "7,5",
    "5,6", "6,6", "7,6",
  ];
  const index = order.indexOf(key);
  return index >= 0 ? index : 100 + enemy.y * 10 + enemy.x;
}

async function appendClickLog(cdp, logs, step) {
  if ((await state(cdp)).floor !== step.fid) {
    await flyTo(cdp, step.fid);
  }
  const { before, after } = await clickTile(cdp, step.x, step.y);
  logs.push({ index: logs.length + 1, step, before, after });
  console.log(`[${logs.length}] ${step.text} -> ${coreStateText(after)}`);
  return after;
}

async function clearMt10BossLive(cdp, logs, phase) {
  const makeStep = (x, y, action, eid, text) => ({
    section: "10F Boss 动态清怪",
    phase,
    fid: "MT10",
    x,
    y,
    action,
    eid,
    text,
    isPotion: false,
    dynamic: true,
  });

  for (let guard = 0; guard < 20; guard += 1) {
    const enemies = await mt10BossEnemies(cdp);
    const nonCaptain = enemies
      .filter((enemy) => enemy.id !== "skeletonCaptain")
      .sort((a, b) => bossPriority(a) - bossPriority(b));
    if (!nonCaptain.length) break;
    const enemy = nonCaptain[0];
    await appendClickLog(
      cdp,
      logs,
      makeStep(
        enemy.x,
        enemy.y,
        "kill",
        enemy.id,
        `点击 MT10 x${enemy.x}y${enemy.y}，目标：动态清理${translateId(enemy.id)}`
      )
    );
  }

  const door = await targetBlock(cdp, "MT10", 6, 3);
  if (door && door.id === "specialDoor") {
    await appendClickLog(
      cdp,
      logs,
      makeStep(6, 3, "open", "specialDoor", "点击 MT10 x6y3，目标：打开 Boss 后事件门")
    );
  }

  // MT10 x6y2 has a story event before the skeleton captain.
  // Click it explicitly, then battle x6y1; clicking x6y1 from farther away can
  // route through x6y2 and leave the replay in an ambiguous event state.
  const captainEvent = await targetBlock(cdp, "MT10", 6, 2);
  if (captainEvent && captainEvent.trigger === "action") {
    await appendClickLog(
      cdp,
      logs,
      makeStep(6, 2, "event", "captainEvent", "点击 MT10 x6y2，目标：触发骷髅队长剧情事件")
    );
  }

  const captain = (await mt10BossEnemies(cdp)).find((enemy) => enemy.id === "skeletonCaptain");
  if (captain) {
    const after = await appendClickLog(
      cdp,
      logs,
      makeStep(captain.x, captain.y, "kill", captain.id, `点击 MT10 x${captain.x}y${captain.y}，目标：打${translateId(captain.id)}`)
    );
    const stillThere = await targetBlock(cdp, "MT10", captain.x, captain.y);
    if (stillThere && stillThere.id === "skeletonCaptain" && after.x === captain.x && after.y > captain.y + 1) {
      await appendClickLog(
        cdp,
        logs,
        makeStep(captain.x, captain.y, "kill", captain.id, `再次点击 MT10 x${captain.x}y${captain.y}，目标：相邻触发${translateId(captain.id)}`)
      );
    }
  }
}

async function flyTo(cdp, floor) {
  await clearRuntimeRoute(cdp);
  const before = await state(cdp);
  if (before.floor === floor) return before;
  await evalValue(cdp, `(function(){ return core.flyTo(${JSON.stringify(floor)}); })()`);
  return waitIdle(cdp, before, `飞到 ${floor}`, 12000);
}

async function clickTile(cdp, x, y) {
  await clearRuntimeRoute(cdp);
  let before = await state(cdp);
  if (before.lock && !before.eventId && !before.hasChoices && !before.moving) {
    await clearStaleLock(cdp);
    before = await state(cdp);
  }
  if (before.moving && !before.eventId && !before.hasChoices) {
    before = await waitIdle(cdp, before, "等待自动移动结束", 15000);
  }
  if (before.lock || before.moving) {
    throw new Error(`点击前状态忙：${coreStateText(before)} lock=${before.lock} moving=${before.moving} event=${before.eventId || "-"}`);
  }
  const result = await evalJson(
    cdp,
    `(function(){
      var target={x:${x},y:${y}};
      var draw=main.dom.gameDraw, group=main.dom.gameGroup;
      var size=32*core.domStyle.scale;
      var left=draw.offsetLeft+group.offsetLeft, top=draw.offsetTop+group.offsetTop;
      var clientX=left+(target.x-0.5)*size, clientY=top+(target.y-0.5)*size;
      var loc=core.actions._getClickLoc(clientX,clientY);
      var tile={x:Math.floor(loc.x/loc.size)+1,y:Math.floor(loc.y/loc.size)+1};
      var actionPx=target.x*32+16-core.bigmap.offsetX;
      var actionPy=target.y*32+16-core.bigmap.offsetY;
      var down=(core.actions.actions.ondown||[]).find(function(a){return a.name==="_sys_ondown";});
      var up=(core.actions.actions.onup||[]).find(function(a){return a.name==="_sys_onup";});
      if (tile.x!==target.x || tile.y!==target.y) return JSON.stringify({ok:false, reason:"tile-mismatch", tile:tile, target:target});
      if (!down || !up) return JSON.stringify({ok:false, reason:"missing-click-handler"});
      down.func.call(core.actions,target.x,target.y,actionPx,actionPy);
      up.func.call(core.actions,target.x,target.y,actionPx,actionPy);
      return JSON.stringify({ok:true});
    })()`
  );
  if (!result.ok) throw new Error(`点击 x${x}y${y} 失败：${JSON.stringify(result)}`);
  await sleep(220);
  let after = await state(cdp);
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
        if (!down || !up) return JSON.stringify({ok:false});
        down.func.call(core.actions,target.x,target.y,actionPx,actionPy);
        up.func.call(core.actions,target.x,target.y,actionPx,actionPy);
        return JSON.stringify({ok:true});
      })()`
    );
    if (!retry.ok) throw new Error(`相邻重试点击 x${x}y${y} 失败`);
  }
  after = await waitIdle(cdp, before, `点击 x${x}y${y}`, 45000);
  const stair = await targetBlock(cdp, before.floor, x, y);
  if (
    stair &&
    (stair.id === "upFloor" || stair.id === "downFloor") &&
    after.floor === before.floor &&
    after.x === x &&
    after.y === y
  ) {
    before = after;
    await evalJson(
      cdp,
      `(function(){
        var target={x:${x},y:${y}};
        var actionPx=target.x*32+16-core.bigmap.offsetX;
        var actionPy=target.y*32+16-core.bigmap.offsetY;
        var down=(core.actions.actions.ondown||[]).find(function(a){return a.name==="_sys_ondown";});
        var up=(core.actions.actions.onup||[]).find(function(a){return a.name==="_sys_onup";});
        if (!down || !up) return JSON.stringify({ok:false});
        down.func.call(core.actions,target.x,target.y,actionPx,actionPy);
        up.func.call(core.actions,target.x,target.y,actionPx,actionPy);
        return JSON.stringify({ok:true});
      })()`
    );
    after = await waitIdle(cdp, before, `二次触发楼梯 x${x}y${y}`, 20000);
  }
  return { before, after };
}

function translateId(id) {
  return ITEM_NAMES[id] || ENEMY_NAMES[id] || id;
}

function translateAction(action) {
  return ACTION_NAMES[action] || action;
}

function parseWalk(file) {
  const lines = fs.readFileSync(file, "utf8").split(/\r?\n/);
  const steps = [];
  let section = "";
  let phase = "";
  for (const line of lines) {
    if (line.startsWith("## Phase1")) section = "1区前缀";
    if (line.startsWith("## Post9 Detailed Steps")) section = "10F 前资源补强";
    const header = line.match(/^###\s+\d+\.\s+(.+)$/);
    if (header) {
      phase = header[1].replace(/`/g, "");
      continue;
    }
    let m = line.match(/^- (MT\d+) x(\d+)y(\d+) (open|kill|take|pass) ([A-Za-z0-9_]+)/);
    if (m) {
      const [, fid, x, y, action, eid] = m;
      steps.push({
        section,
        phase,
        fid,
        x: Number(x),
        y: Number(y),
        action,
        eid,
        text: `点击 ${fid} x${x}y${y}，目标：${translateAction(action)}${translateId(eid)}`,
        isPotion: eid === "redPotion" || eid === "bluePotion",
      });
      continue;
    }
    m = line.match(/^- (MT\d+) x(\d+)y(\d+) trigger boss event/);
    if (m) {
      const [, fid, x, y] = m;
      steps.push({
        section,
        phase,
        fid,
        x: Number(x),
        y: Number(y),
        action: "trigger",
        eid: "bossEvent",
        text: `点击 ${fid} x${x}y${y}，目标：触发 10F Boss 事件`,
        isPotion: false,
      });
    }
  }
  return normalizeAutoEntrySteps(steps);
}

function cloneStep(step, patch) {
  return { ...step, ...patch };
}

function mt9MiddleAutoGroupPatch(step) {
  return cloneStep(step, {
    x: 7,
    y: 4,
    text: "点击 MT9 x7y4，目标：触发中部资源组自动拾取/清怪",
    autoGroupNote: "自动处理：MT9 x5y4 黄钥匙、MT9 x6y5 红宝石、MT9 x7y6 红头怪",
    autoGroupTargets: [
      { fid: "MT9", x: 5, y: 4, eid: "yellowKey" },
      { fid: "MT9", x: 6, y: 5, eid: "redGem" },
      { fid: "MT9", x: 7, y: 6, eid: "redSlime" },
    ],
    normalizedFrom: step.normalizedFrom || "MT9 x5y4 黄钥匙",
  });
}

function normalizeAutoEntrySteps(steps) {
  return steps.map((step) => {
    if (
      step.fid === "MT9" &&
      step.phase === "MT9:shield1+redGem+blueGem:new" &&
      step.action === "take" &&
      step.eid === "yellowKey" &&
      step.x === 5 &&
      step.y === 4
    ) {
      return mt9MiddleAutoGroupPatch(step);
    }
    if (
      step.fid === "MT9" &&
      step.phase === "MT9:shield1+redGem+blueGem:new" &&
      step.action === "take" &&
      step.eid === "yellowKey" &&
      step.x === 7 &&
      step.y === 4 &&
      step.autoGroupNote
    ) {
      return mt9MiddleAutoGroupPatch(step);
    }
    return step;
  });
}

function summarizeMilestones(logs) {
  const wanted = [
    [/MT9:shield1\+redGem\+blueGem/, "拿铁盾与 9F 红蓝宝石"],
    [/\('MT9', \['upFloor'\]/, "9F 走蓝门上 10F"],
    [/\('MT10', \['blueGem'\]/, "10F 左侧蓝宝石"],
    [/\('MT8', \['redKey'\]/, "8F 红钥匙"],
    [/\('MT10', \['redDoor'\]/, "10F 红门 Boss"],
  ];
  const out = [];
  for (const [pattern, name] of wanted) {
    const row = logs.find((item) => pattern.test(item.step.phase));
    if (row) out.push({ name, state: row.after });
  }
  return out;
}

const SNAPSHOT_MILESTONES = [
  [/MT9:shield1\+redGem\+blueGem/, "重要节点：拿铁盾与 9F 红蓝宝石"],
  [/\('MT9', \['upFloor'\]/, "重要节点：9F 蓝门后上 10F"],
  [/\('MT10', \['blueGem'\]/, "重要节点：10F 左侧蓝宝石"],
  [/\('MT8', \['redKey'\]/, "重要节点：8F 红钥匙"],
  [/\('MT10', \['redDoor'\]/, "重要节点：10F 红门 Boss 段"],
];

function addSnapshot(picks, row, reason) {
  if (!row) return;
  const existing = picks.get(row.index);
  if (existing) {
    if (!existing.reason.includes(reason)) existing.reason += `；${reason}`;
    return;
  }
  picks.set(row.index, { row, reason });
}

function hasNearbySnapshot(picks, index, minDistance = 15) {
  return [...picks.keys()].some((existing) => Math.abs(existing - index) <= minDistance);
}

function snapshotRows(logs, minGap = 50) {
  const picks = new Map();
  for (const [pattern, reason] of SNAPSHOT_MILESTONES) {
    const row = logs.find((item) => pattern.test(item.step.phase));
    addSnapshot(picks, row, reason);
  }
  if (logs.length) addSnapshot(picks, logs[logs.length - 1], "终点快照");
  let lastRegular = 0;
  for (const row of logs) {
    if (row.index - lastRegular >= minGap) {
      if (!hasNearbySnapshot(picks, row.index)) {
        addSnapshot(picks, row, `间隔快照：距上次普通快照 ${row.index - lastRegular} 步`);
      }
      lastRegular = row.index;
    }
  }
  return [...picks.values()].sort((a, b) => a.index - b.index);
}

function autoHandledTargetText(row) {
  const step = row.step || {};
  const id = translateId(step.eid);
  return `${step.fid} x${step.x}y${step.y} ${id}`;
}

function buildDisplayRows(logs) {
  const rows = [];
  const consumedByAutoGroup = new Set();
  const normalizedSteps = normalizeAutoEntrySteps(logs.map((row) => row.step));
  for (const [idx, row] of logs.entries()) {
    const normalizedRow = { ...row, step: normalizedSteps[idx] };
    const targetKey = `${normalizedRow.step.fid}:${normalizedRow.step.x}:${normalizedRow.step.y}:${normalizedRow.step.eid}`;
    if (row.skipped && consumedByAutoGroup.has(targetKey)) {
      continue;
    }
    if (row.skipped && rows.length) {
      const prev = rows[rows.length - 1];
      if (!prev.autoHandled) prev.autoHandled = [];
      const target = autoHandledTargetText(normalizedRow);
      const sameAsClick =
        prev.step &&
        prev.step.fid === normalizedRow.step.fid &&
        prev.step.x === normalizedRow.step.x &&
        prev.step.y === normalizedRow.step.y &&
        prev.step.eid === normalizedRow.step.eid;
      const alreadyInManualNote = prev.step && prev.step.autoGroupNote && prev.step.autoGroupNote.includes(target);
      if (!sameAsClick && !alreadyInManualNote) {
        prev.autoHandled.push(target);
      }
      continue;
    }
    for (const target of normalizedRow.step.autoGroupTargets || []) {
      consumedByAutoGroup.add(`${target.fid}:${target.x}:${target.y}:${target.eid}`);
    }
    rows.push({ ...normalizedRow, autoHandled: [] });
  }
  return rows;
}

function writeOutputs(args, payload) {
  fs.mkdirSync(path.dirname(args.outJson), { recursive: true });
  fs.mkdirSync(path.dirname(args.outMd), { recursive: true });
  fs.writeFileSync(args.outJson, JSON.stringify(payload, null, 2), "utf8");

  const final = payload.finalState;
  const milestones = summarizeMilestones(payload.logs);
  const scoreSummary = loadZone1ScoreSummary(sourceWalkPath(args, payload));
  const auto = payload.auto || {};
  const autoItemText = auto.item === true ? "开（含血瓶）" : auto.item === "nopotion" ? "开（不含血瓶）" : "关";
  const lines = [
    "# 1区 4F-10F Boss 网页复现 Walk（自动设置）",
    "",
    "## 核心摘要",
    "",
    `- 起点：${coreStateText(payload.startState)}`,
    `- 终点：${coreStateText(final)}`,
    `- 自动设置：自动清 0 伤怪=${auto.battle === true ? "开" : "关"}；自动拾取物品=${autoItemText}；自动开暗墙岩浆=${auto.wall === true ? "开" : "关"}`,
    "- 本次执行方式：网页实机读取 1 号存档，使用真实地图点击处理器；若目标格已被自动 BFS 处理，walk 记录为“自动处理跳过”。",
    "- 本段没有雪花，因此“自动开暗墙岩浆”只作为开关校验，不触发清岩浆收益。",
    "- 10F 骷髅队长前必须先点 `MT10 x6y2` 触发剧情事件，再点 `MT10 x6y1` 打队长；不要从远处直接点 `x6y1`。",
    "",
    "## 关键节点",
    "",
    "| 节点 | 网页状态 |",
    "|---|---|",
  ];
  for (const row of milestones) {
    lines.push(`| ${row.name} | ${coreStateText(row.state)} |`);
  }
  lines.push(`| Boss 后 | ${coreStateText(final)} |`);
  lines.push("");
  lines.push("## 阶段分数");
  lines.push("");
  lines.push("| 大阶段 | 状态快照 | 纯伤害 dmg | 门 黄/蓝/红 | final-score | 重要分数组成 | 备注 |");
  lines.push("|---|---|---:|---|---:|---|---|");
  if (scoreSummary) {
    lines.push(
      `| ${scoreSummary.name} | ${coreStateText(final)} | ${fmtScore(scoreSummary.dmg)} | ` +
      `${scoreSummary.yd}/${scoreSummary.bd}/${scoreSummary.rd} | ${fmtScore(scoreSummary.finalScore)} | ` +
      `${scoreComponentsText(scoreSummary)} | ${scoreNote(scoreSummary, final)} |`
    );
  } else {
    lines.push(`| 1区 Boss 后 | ${coreStateText(final)} | - | - | - | - | 未找到本地评分摘要 |`);
  }
  lines.push("");
  lines.push("## 固化格式");
  lines.push("");
  lines.push("- 每条 walk 都按“核心摘要 -> 关键节点 -> 阶段分数 -> 自动设置校验 -> 详细步骤 -> 校验结果”输出。");
  lines.push("- 详细步骤统一使用中文动作，保留 `MT楼层 x横坐标y纵坐标` 便于脚本复查；单步只写数值变化，不逐步重复完整状态。");
  lines.push("- 状态快照插入在详细步骤中：普通间隔约 50 步以上，重要结果节点后立即插入；大阶段必须输出 `dmg`、`final-score` 和关键评分组成。");
  lines.push("- 1区/2区缺血阶段可使用 `item=true`，让血瓶自动吃；进入 3区后再切到 `item=\"nopotion\"` 保留血瓶。");
  lines.push("- 自动设置复现时，必须明确血瓶是 `item=true` 自动吃，还是路线显式取得；`nopotion` 不允许把血瓶算作自动收益。");
  lines.push("- 开门后不会立刻触发自动 BFS；需要再移动、战斗、拾取或触发事件一次，才能把门后新增可达资源自动处理掉。");
  lines.push("- 10F Boss 后骷髅队长段按 `MT10 x6y2` 剧情事件 -> `MT10 x6y1` 队长战斗固定输出。");
  lines.push("");
  lines.push("## 自动设置校验");
  lines.push("");
  lines.push("```text");
  lines.push(JSON.stringify(auto, null, 2));
  lines.push("```");
  lines.push("");
  lines.push("## 详细步骤");
  lines.push("");
  lines.push("| # | 阶段 | 网页动作 | 数值变化 | 备注 |");
  lines.push("|---:|---|---|---|---|");
  const displayRows = buildDisplayRows(payload.logs);
  const snapshots = new Map(snapshotRows(displayRows).map((entry) => [entry.row.index, entry]));
  for (const row of displayRows) {
    const notes = [];
    if (row.step.autoGroupNote) notes.push(row.step.autoGroupNote);
    if (row.autoHandled && row.autoHandled.length) {
      notes.push(`自动处理：${[...new Set(row.autoHandled)].join("、")}`);
    }
    if (row.step.isPotion) {
      notes.push(auto.item === true ? "血瓶：item=true 自动/路径取得" : "血瓶：显式路线动作，不是自动拾取");
    }
    const note = notes.join("；");
    lines.push(
      `| ${row.index} | ${row.step.phase || row.step.section} | ${row.step.text} | ` +
      `${deltaText(row.before, row.after)} | ${note} |`
    );
    const snapshot = snapshots.get(row.index);
    if (snapshot) {
      lines.push(
        `| 快照@${row.index} | ${row.step.phase || row.step.section} | 状态快照：${coreStateText(row.after)} | - | ${snapshot.reason} |`
      );
    }
  }
  lines.push("");
  lines.push("## 校验结果");
  lines.push("");
  lines.push(`- 执行点击数：${payload.logs.length}`);
  lines.push(`- 最终状态：${coreStateText(final)}`);
  lines.push(`- 结果：${payload.ok ? "网页复现完成" : "未完成"}`);
  fs.writeFileSync(args.outMd, lines.join("\n").trimEnd() + "\n", "utf8");
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.fromJson) {
    const payload = JSON.parse(fs.readFileSync(args.fromJson, "utf8"));
    writeOutputs(args, payload);
    console.log(`从 ${path.relative(ROOT, args.fromJson)} 重写 ${path.relative(ROOT, args.outMd)}`);
    return;
  }
  const steps = parseWalk(args.walk);
  const cdp = await connectGameTarget();
  const logs = [];
  try {
    const startLoaded = await loadSlot(cdp, args.loadSlot);
    const autoState = await setAuto(cdp, args.itemMode);
    let current = autoState;
    let skipPhase = null;
    for (const step of steps) {
      if (args.stopClicks != null && logs.length >= args.stopClicks) break;
      if (skipPhase && step.phase === skipPhase) {
        continue;
      }
      if (current.floor !== step.fid) {
        current = await flyTo(cdp, step.fid);
      }
      if (canSkipMissingTarget(step)) {
        const block = await targetBlock(cdp, step.fid, step.x, step.y);
        if (!block) {
          const before = await state(cdp);
          logs.push({
            index: logs.length + 1,
            step,
            before,
            after: before,
            skipped: true,
            skipReason: "目标格已消失，通常为自动拾取/自动清理造成",
          });
          console.log(`[${logs.length}] ${step.text} -> 自动处理跳过`);
          current = before;
          continue;
        }
      }
      const { before, after } = await clickTile(cdp, step.x, step.y);
      logs.push({ index: logs.length + 1, step, before, after });
      current = after;
      console.log(`[${logs.length}] ${step.text} -> ${coreStateText(after)}`);
      if (step.fid === "MT10" && step.eid === "bossEvent") {
        await clearMt10BossLive(cdp, logs, step.phase);
        current = await state(cdp);
        skipPhase = step.phase;
      }
    }
    const finalState = await state(cdp);
    const bossDone = args.stopClicks == null
      ? finalState.floor === "MT10" && finalState.hp === 122 && finalState.atk === 27 && finalState.def === 27 && finalState.rk === 0
      : logs.length >= Math.min(args.stopClicks, steps.length);
    const payload = {
      ok: bossDone,
      sourceWalk: path.relative(ROOT, args.walk),
      loadSlot: args.loadSlot,
      startState: startLoaded,
      auto: autoState.auto,
      finalState,
      logs,
    };
    writeOutputs(args, payload);
    console.log(`写出 ${path.relative(ROOT, args.outJson)}`);
    console.log(`写出 ${path.relative(ROOT, args.outMd)}`);
    if (args.saveSlot != null && bossDone) {
      await saveSlot(cdp, args.saveSlot);
      console.log(`写入存档槽 ${args.saveSlot}：${coreStateText(finalState)}`);
    }
  } finally {
    cdp.close();
  }
}

main().catch((err) => {
  console.error(err.stack || String(err));
  process.exit(1);
});
