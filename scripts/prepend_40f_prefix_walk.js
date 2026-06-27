#!/usr/bin/env node
// Prepend the "40F x6y1 upFloor -> 41F" prefix to the post40 guide walk so the
// replay can start straight from save slot 37 (40F, hero at x9y4) without a
// manual stair click. The prefix is two coalesced steps:
//   1. PASS upFloor at MT40 x6y1  (click the stair; game auto-routes + climbs)
//   2. CHANGE_FLOOR landing at MT41 x6y2 (the guide's real start)
// replayer coalesces PASS->CHANGE_FLOOR, so live state at MT41 x6y2 matches.

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const SRC = path.join(ROOT, "outputs", "results", "post40_guide_probe.json");
const OUT = path.join(ROOT, "outputs", "results", "post40_guide_walk.json");

const walk = JSON.parse(fs.readFileSync(SRC, "utf8"));
const steps = walk.steps;

// 40F start state (save slot 37): hero at x9y4, hp78 atk166 def218 yk4.
const start40 = {
  hp: 78, atk: 166, def: 218, yk: 4, bk: 0, rk: 0, gold: 2269,
  floor: "MT40", x: 9, y: 4, dmg: 0, yd: 0, bd: 0, rd: 0,
};

// After clicking x6y1 upFloor the hero routes there; no stat change before the climb.
const atStair = { ...start40, x: 6, y: 1 };
// After climbing to 41F: landing x6y2 (matches snapshot / guide start), same stats.
const at41 = { ...start40, floor: "MT41", x: 6, y: 2 };

const prefix = [
  {
    segment: "40F 上楼到41F起点",
    floor: "MT40",
    pos: [6, 1],
    action: "通过",
    eid: "upFloor",
    before: start40,
    after: atStair,
    delta: "",
    note: "37号存档40F x6y1上楼(实机起点)",
  },
  {
    segment: "40F 上楼到41F起点",
    floor: "MT41",
    pos: [6, 2],
    action: "换层",
    eid: null,
    before: atStair,
    after: at41,
    delta: "",
    note: "上楼到41F x6y2(攻略起点)",
  },
];

walk.steps = [...prefix, ...steps];
walk.final = walk.final || walk.steps[walk.steps.length - 1].after;
walk.start_note = "从37号存档(40F)开始,x6y1上楼到41F,衔接 post40 攻略";

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(walk, null, 1), "utf8");
console.log(`wrote ${OUT}`);
console.log(`steps: ${walk.steps.length} (prefix 2 + probe ${steps.length})`);
console.log(`start: ${walk.steps[0].floor} x${walk.steps[0].pos[0]}y${walk.steps[0].pos[1]} ${walk.steps[0].action}`);
console.log(`final: ${walk.final.floor} x${walk.final.x}y${walk.final.y} HP=${walk.final.hp} ATK=${walk.final.atk} DEF=${walk.final.def}`);
