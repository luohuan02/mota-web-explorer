#!/usr/bin/env node
/**
 * Floor-aware live state reader for the h5mota game.
 *
 * Connection model: chrome is launched EXTERNALLY on real port 9222 with the
 * browser-profile (powershell Start-Process chrome.exe --remote-debugging-port=9222
 * --user-data-dir=D:/claude/mota-web-explorer/browser-profile https://h5mota.com/games/51/).
 * This script attaches via `agent-browser connect 9222` then bare `eval`.
 * The external launch is REQUIRED because `agent-browser --cdp 9222 ... open`
 * ignores --profile/--user-data-dir and uses a TEMP profile (saves missing).
 * Never --auto-connect (attaches to the wrong tab).
 * See skills/mota-live-browser/SKILL.md "Launch & Connect".
 *
 * Why this exists: `core.getBlock(x, y)` with NO floorId reads the hero's
 * CURRENT floor. If you think the hero is on MT8 but they are actually on MT1,
 * you get MT1's block (e.g. yellowWall) and mis-diagnose. This helper makes
 * floor explicit and always echoes the real current floor, so floor confusion
 * is impossible.
 *
 * Usage:
 *   node scripts/live_read_state.js
 *       -> current floor + hero stats (hp/atk/def/keys/gold/loc)
 *   node scripts/live_read_state.js --floor MT8
 *       -> same, plus `floorOk` flag (true only if current floor === MT8)
 *   node scripts/live_read_state.js --block MT8,10,2
 *       -> same, plus the block at MT8 x10y2 read with EXPLICIT floorId
 *          (format: FLOOR,X,Y -- the floor is mandatory, never implicit)
 *   node scripts/live_read_state.js --floor MT8 --block MT8,10,2
 *       -> assert current floor is MT8 AND read MT8 x10y2
 *
 * The --block floor and the --floor assertion are independent on purpose: you
 * can read a remote floor's block without flying there, but you can also assert
 * the hero is where you think they are.
 */
const { execFileSync } = require('child_process');

const args = process.argv.slice(2);
function opt(name) {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : null;
}

const assertFloor = opt('--floor');
const blockSpec = opt('--block'); // "FLOOR,X,Y"

// Encode a string literal as String.fromCharCode(...) so the generated eval
// expression contains NO quote characters -- this lets it survive shell
// transport (agent-browser.cmd eval <expr>) without word-splitting.
function strExpr(s) {
  const codes = [...s].map(c => c.charCodeAt(0)).join(',');
  return `String.fromCharCode(${codes})`;
}

let blockInit = '';
if (blockSpec) {
  const parts = blockSpec.split(',');
  if (parts.length !== 3) {
    console.error('--block must be FLOOR,X,Y (e.g. MT8,10,2)');
    process.exit(2);
  }
  const [bf, bx, by] = parts;
  if (!/^-?\d+$/.test(bx) || !/^-?\d+$/.test(by)) {
    console.error('--block X and Y must be integers, got: ' + blockSpec);
    process.exit(2);
  }
  blockInit = [
    `var bf=${strExpr(bf)},bx=Number(${bx}),by=Number(${by});`,
    `var bk=null;`,
    `try{bk=core.getBlock(bx,by,bf);}catch(e){bk={error:String(e)};}`,
    `base.block=bk?{floor:bf,x:bx,y:by,id:bk.id,eventName:(bk.event&&(bk.event.name||bk.event.id))||null,noPass:!!bk.noPass,cls:bk.cls||null}:{floor:bf,x:bx,y:by,id:null,note:R(34)};`
  ].join('');
  // R(34) below is built by fromCode for "empty/out-of-range" -- but simpler: inline.
  blockInit = blockInit.replace('R(34)', strExpr('empty/out-of-range'));
}

let assertInit = '';
if (assertFloor) {
  assertInit = `base.floorOk=(f===${strExpr(assertFloor)});base.floorExpected=${strExpr(assertFloor)};`;
}

// Single-line expression, no quote chars -> safe through the shell.
const expr = [
  `(()=>{`,
  `var h=core.status.hero,loc=h.loc,t=h.items.tools,f=core.status.floorId;`,
  `var auto=(core.status.hero&&core.status.hero.flags&&core.status.hero.flags.__auto__)||null;`,
  `var base={floor:f,x:loc.x,y:loc.y,hp:h.hp,atk:h.atk,def:h.def,mdef:h.mdef||0,yk:t.yellowKey||0,bk:t.blueKey||0,rk:t.redKey||0,gold:h.money||0,auto:auto};`,
  assertInit,
  blockInit,
  `return JSON.stringify(base);`,
  `})()`
].join('');

// agent-browser.cmd wraps a native exe and forwards `%*`. Going through cmd.exe
// (shell:true) lets cmd.exe interpret JS operators like `||`, `&&`, `(`, `)` as
// shell syntax, mangling the expression. Call the exe directly with shell:false
// so the eval string is passed to the binary literally (Node quotes args with
// spaces; the expr has no quote chars thanks to strExpr()).
const AGENT_BROWSER_EXE = process.env.AGENT_BROWSER_EXE ||
  'D:/nvm4w/nodejs/node_modules/agent-browser/bin/agent-browser-win32-x64.exe';

// agent-browser returns the eval result, which here is a JSON string, often
// double-wrapped (a quoted JSON string). Unwrap and pretty-print for clarity.
function unwrapAndPrint(text) {
  const raw = text.trim();
  if (!raw) return;
  // Detect agent-browser error markers.
  if (raw.startsWith('✗') || /^Evaluation error/i.test(raw)) {
    process.stderr.write(raw + '\n');
    process.exitCode = 3;
    return;
  }
  try {
    let v = JSON.parse(raw);        // unwrap outer quote-layer -> JSON string
    if (typeof v === 'string') v = JSON.parse(v);  // -> object
    process.stdout.write(JSON.stringify(v, null, 2) + '\n');
  } catch (e) {
    // Not JSON; print as-is.
    process.stdout.write(raw + '\n');
  }
}

// Attach to the chrome launched EXTERNALLY on real port 9222 (powershell
// Start-Process chrome.exe --remote-debugging-port=9222
// --user-data-dir=D:/claude/mota-web-explorer/browser-profile <h5mota-url>).
// `connect 9222` attaches to that existing chrome; bare `eval` uses the linked
// session. Do NOT use `agent-browser --cdp 9222 ... open` to launch -- agent-browser
// ignores --profile/--args --user-data-dir and uses a TEMP profile, so the h5mota
// saves (in browser-profile) are missing and getSave() returns null.
// See skills/mota-live-browser/SKILL.md "Launch & Connect".
try {
  execFileSync(AGENT_BROWSER_EXE, ['connect', '9222'], {
    encoding: 'utf8', shell: false, stdio: ['ignore', 'ignore', 'ignore'],
  });
} catch (e) { /* ignore -- the eval below surfaces real connection errors */ }

let out;
try {
  out = execFileSync(AGENT_BROWSER_EXE, ['eval', expr], {
    encoding: 'utf8',
    shell: false,
  });
} catch (e) {
  // execFileSync throws on non-zero exit; agent-browser prints errors to stdout
  // captured in e.stdout when available.
  const captured = (e.stdout || '').toString();
  if (captured) { unwrapAndPrint(captured); process.exit(e.status ? 1 : 3); }
  console.error('agent-browser call failed:', e.message);
  process.stderr.write('expr was:\n' + expr + '\n');
  process.exit(1);
}
unwrapAndPrint(out);
