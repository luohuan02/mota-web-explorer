// Decode a .h5route's route tokens via the browser's core.decodeRoute,
// WITHOUT starting a replay (preserves current game state). Writes a
// provenance bundle {route, recording:{path,sha256}}. No statlog: the
// semantic converter derives actions from route order alone and uses
// Game's own position for arrow targets; statlog is optional diagnostics.
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const CDP_LIST = 'http://127.0.0.1:9222/json/list';

function args(argv) {
  const out = { recording: null, out: null };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--recording') out.recording = path.resolve(argv[++i]);
    else if (arg === '--out') out.out = path.resolve(argv[++i]);
    else throw new Error(`unknown argument: ${arg}`);
  }
  if (!out.recording || !out.out) throw new Error('--recording and --out are required');
  return out;
}

async function json(url) { const r = await fetch(url); if (!r.ok) throw new Error(`GET ${url} ${r.status}`); return r.json(); }

async function connect() {
  const targets = await json(CDP_LIST);
  const target = targets.find((t) => t.url && t.url.includes('h5mota.com/games/51'));
  if (!target) throw new Error('no h5mota game tab on port 9222');
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  let nextId = 1; const pending = new Map();
  ws.addEventListener('message', (event) => {
    const m = JSON.parse(event.data);
    if (!m.id || !pending.has(m.id)) return;
    const e = pending.get(m.id); pending.delete(m.id);
    if (m.error) e.reject(new Error(JSON.stringify(m.error))); else e.resolve(m.result);
  });
  await new Promise((res, rej) => { ws.addEventListener('open', res, { once: true }); ws.addEventListener('error', rej, { once: true }); });
  return { close: () => ws.close(), send(method, params = {}) {
    const id = nextId++;
    return new Promise((resolve, reject) => { pending.set(id, { resolve, reject }); ws.send(JSON.stringify({ id, method, params })); });
  }};
}

async function evalExpr(cdp, expression) {
  const result = await cdp.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}

async function main() {
  const opt = args(process.argv);
  const content = fs.readFileSync(opt.recording, 'utf8').trim();
  const sha256 = crypto.createHash('sha256').update(content).digest('hex');
  const cdp = await connect();
  try {
    const expr = `(function(){
      var b64 = ${JSON.stringify(content)};
      var obj = JSON.parse(LZString.decompressFromBase64(b64));
      var tokens = LZString.decompressFromBase64(obj.route);
      var decoded = core.decodeRoute(tokens);
      return JSON.stringify({seed:obj.seed, hard:obj.hard, route:decoded});
    })()`;
    const result = JSON.parse(await evalExpr(cdp, expr));
    const output = {
      schema: 'mota.recording.capture.v1',
      recording: { path: opt.recording, sha256, seed: result.seed, hard: result.hard },
      route: result.route,
      statlog: [],
      semantic_actions: [],
      note: 'route-only decode (no native replay). Semantic converter derives targets from route order; arrows use Game position. choices/item/event need manual annotation or event-model coverage.',
    };
    fs.mkdirSync(path.dirname(opt.out), { recursive: true });
    fs.writeFileSync(opt.out, JSON.stringify(output, null, 2), 'utf8');
    console.log(JSON.stringify({ out: opt.out, route: result.route.length, seed: result.seed, sha256 }, null, 2));
  } finally { cdp.close(); }
}

main().catch((e) => { console.error(e.stack || String(e)); process.exit(1); });
