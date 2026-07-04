#!/usr/bin/env node
/**
 * 加载 h5mota 存档槽到 LIVE 游戏。
 *
 * 连接方式:外部启动 chrome(真实端口 9222 + browser-profile),
 * 然后 `agent-browser connect 9222` + 裸 eval。
 * 详见 skills/mota-live-browser/SKILL.md「启动与连接」「加载存档」。
 *
 * 实现:走游戏自带的「载入游戏」UI 路径——
 *   core.control._doSL_load(slot, core.control._doSL_load_afterGet)
 *   - 版本匹配 + 无风险事件 → core.loadData(data) 干净快照载入(正常路径)
 *   - 版本不匹配 / 风险事件 → 弹 core.myconfirm 问是否回放录像(降级路径,本脚本不自动点)
 *
 * 旧实现用 getSave + core.startGame 重放,那是降级路径:route 不完整时会变成新游戏,
 * 已弃用。详见 best/route_chains.md 与 skills/mota-live-browser/SKILL.md。
 *
 * 用法:
 *   node scripts/live_load_save.js --slot 1
 *     轮询直到英雄就绪(~15s),输出 {playing, floor, hp, atk, def, x, y}。
 *     若弹 myconfirm(版本不匹配),输出文本并退出,需手动处理。
 */
const { execFileSync } = require('child_process');

const args = process.argv.slice(2);
function opt(name) {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : null;
}

const slot = opt('--slot');
const waitMs = parseInt(opt('--wait-ms') || '15000', 10);

if (!/^\d+$/.test(slot || '')) {
  console.error('用法: node scripts/live_load_save.js --slot <N> [--wait-ms 15000]');
  process.exit(2);
}

const AGENT_BROWSER_EXE = process.env.AGENT_BROWSER_EXE ||
  'D:/nvm4w/nodejs/node_modules/agent-browser/bin/agent-browser-win32-x64.exe';

// 触发载入:走 UI 路径(_doSL_load -> _doSL_load_afterGet -> loadData 或 myconfirm)。
// 无引号字符、无 &&/||、无 $,shell 安全。
const loadExpr = [
  `(()=>{`,
  `core.control._doSL_load(${slot}, core.control._doSL_load_afterGet);`,
  `return 'dispatched';`,
  `})()`
].join('');

// 轮询:读英雄状态 + myconfirm 检测。用 ?: 代替 && 保持 shell 安全。
const pollExpr = [
  `(()=>{`,
  `var h=core.status.hero;`,
  `var r={playing:core.isPlaying(),floor:core.status.floorId,`,
  `hp:h?h.hp:null,atk:h?h.atk:null,def:h?h.def:null,`,
  `x:h?h.loc.x:null,y:h?h.loc.y:null,`,
  `eventId:core.status.event?core.status.event.id:null,lockControl:core.status.lockControl};`,
  `var mc=document.getElementById('myconfirm');`,
  `r.myconfirmVisible=mc?mc.offsetParent!==null:false;`,
  `r.myconfirmText=mc?(mc.innerText||'').trim().slice(0,200):null;`,
  `return JSON.stringify(r);`,
  `})()`
].join('');

function runEval(expr) {
  // 附加到外部启动的 chrome(真实端口 9222),再裸 eval。
  try {
    execFileSync(AGENT_BROWSER_EXE, ['connect', '9222'], {
      encoding: 'utf8', shell: false, stdio: ['ignore', 'ignore', 'ignore'],
    });
  } catch (e) { /* 忽略;eval 会暴露真实错误 */ }
  try {
    return execFileSync(AGENT_BROWSER_EXE, ['eval', expr], {
      encoding: 'utf8', shell: false,
    }).trim();
  } catch (e) {
    const captured = (e.stdout || '').toString().trim();
    if (captured) return captured;
    throw e;
  }
}

function unwrap(text) {
  if (!text) return null;
  try {
    let v = JSON.parse(text);
    if (typeof v === 'string') v = JSON.parse(v);
    return v;
  } catch (e) {
    return text;
  }
}

// 1. 触发载入。
const disp = runEval(loadExpr);
console.error('dispatch:', disp);

// 2. 轮询直到英雄就绪或超时。
const start = Date.now();
let last = null;
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
(async () => {
  do {
    await sleep(1200);
    last = unwrap(runEval(pollExpr));
    if (last && typeof last === 'object') {
      console.log(JSON.stringify(last));
      if (last.myconfirmVisible) {
        console.log('MYCONFIRM(版本不匹配/风险,需手动处理):', last.myconfirmText);
        return;
      }
      const done = last.playing && last.floor && last.hp != null;
      if (done) {
        console.log('LOADED -> floor=' + last.floor + ' hp=' + last.hp + ' atk=' + last.atk + ' def=' + last.def);
        return;
      }
    } else {
      console.log(String(last));
    }
  } while (Date.now() - start < waitMs);
  console.log('TIMEOUT (最后状态见上)');
})();
