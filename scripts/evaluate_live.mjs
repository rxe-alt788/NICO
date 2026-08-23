import fs from 'node:fs';
import vm from 'node:vm';

global.window = globalThis;
vm.runInThisContext(fs.readFileSync(new URL('../js/config.js', import.meta.url), 'utf8'));
vm.runInThisContext(fs.readFileSync(new URL('../js/rulesEngine.js', import.meta.url), 'utf8'));

const path = new URL('../data/live_state.json', import.meta.url);
const data = JSON.parse(fs.readFileSync(path, 'utf8'));

for (const [beachId, beach] of Object.entries(data.beaches || {})) {
  const ready = Boolean(beach.dataCompleteness?.evaluationReady);
  if (!ready) {
    beach.evaluation = {
      status: 'INSUFFICIENT_ENV_DATA',
      envFlag: null,
      obsState: beach.surveillance?.droneActive || beach.surveillance?.lifeguardActive ? 'PARTIAL_OR_UNKNOWN' : 'BLACKOUT',
      rationale: ['Insufficient normalized environmental inputs; no risk colour issued.']
    };
    continue;
  }
  const result = globalThis.FourNICO.evaluateBeachStatus(beach.env || {}, beach.surveillance || {}, { experimentalSecondaryCues: false });
  beach.evaluation = { status: 'EVALUATED', ...result };
}

data.evaluatedAt = new Date().toISOString();
fs.writeFileSync(path, JSON.stringify(data, null, 2) + '\n');
console.log(`Evaluated ${Object.keys(data.beaches || {}).length} beaches`);
