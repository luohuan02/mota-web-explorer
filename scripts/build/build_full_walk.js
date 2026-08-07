// Build a combined MT20->MT41 walk (stage1 + stage2) for the 2atk3atk5def
// recording line, so it can be replayed from save slot 32 in one command.
const fs = require('fs');
const s1 = JSON.parse(fs.readFileSync('best/zone12_2atk_recording_stage1_walk.json', 'utf8'));
const s2 = JSON.parse(fs.readFileSync('best/zone3_2atk3atk5def_recording_walk.json', 'utf8'));

// sanity: stage1.final must equal stage2.step1.before
const keys = ['floor', 'x', 'y', 'hp', 'atk', 'def', 'yk', 'bk', 'rk', 'gold'];
const aligned = keys.every(k => s1.final[k] === s2.steps[0].before[k]);
if (!aligned) {
  console.error('CHAIN NOT ALIGNED:');
  console.error('stage1.final', JSON.stringify(s1.final));
  console.error('stage2.step1.before', JSON.stringify(s2.steps[0].before));
  process.exit(1);
}

const combined = {
  ok: !!(s1.ok && s2.ok),
  final: s2.final,
  steps: s1.steps.concat(s2.steps),
  errors: (s1.errors || []).concat(s2.errors || []),
  stats: {
    stage1_steps: s1.steps.length,
    stage2_steps: s2.steps.length,
    total_steps: s1.steps.length + s2.steps.length,
  },
  provenance: {
    kind: 'combined_stage1_stage2',
    start_slot: 32,
    start_state: s1.steps[0].before,
    stage1: 'outputs/results/2atk_3atk5def_seed_mt20_mt31.json (MT20->MT31, 30 steps)',
    stage2: 'best/zone3_2atk3atk5def_recording_walk.json (MT31->MT41, 257 steps, bounce-cancelled + event-trigger preserved)',
    note: 'combined walk: load save slot 32 (MT20), replay to MT41 in one run',
  },
};
const out = 'best/zone3_2atk3atk5def_recording_full_walk.json';
fs.writeFileSync(out, JSON.stringify(combined, null, 2), 'utf8');
console.log('wrote', out);
console.log('total steps:', combined.steps.length, '(stage1', s1.steps.length, '+ stage2', s2.steps.length, ')');
console.log('final:', JSON.stringify({floor: combined.final.floor, x: combined.final.x, y: combined.final.y, hp: combined.final.hp, atk: combined.final.atk, def: combined.final.def, yk: combined.final.yk, bk: combined.final.bk, g: combined.final.gold}));
console.log('ok:', combined.ok);
