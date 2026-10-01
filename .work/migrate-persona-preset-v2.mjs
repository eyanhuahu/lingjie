// Take 2 of the migration. The first attempt ported the 0.1.5 entry list row-by-row,
// and the host reported the preset as activation-failed. This version instead takes
// the *shipped 0.2.0* `standard` preset's plugin list verbatim — every tool row that
// the working preset already proves mountable in this deployment — and swaps in only
// the `persona` identity row's text from the legacy preset. Row-for-row parity is the
// point: nothing else may differ from a preset that mounts today.
//
// Reads:  the legacy persona dir, the shipped standard patch inside app.asar
// Writes: OUT_DIR (overwriting), with the previous output kept as a backup file
import { createRequire } from 'node:module';
import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const require = createRequire('D:/aideepseek/data/profiles/web/package.json');
const YAML = require('yaml');

const LEGACY = 'D:\\aideepseek\\data\\.agent-presets\\persona';
const OUT_DIR = 'D:\\Users\\huan\\Documents\\GitHub\\lingjie\\.work\\dsh-persona-preset';
const APP_ASAR = 'C:\\Users\\huan\\AppData\\Local\\Programs\\DeepSeek Harness\\resources\\app.asar';

const jsTag = {
  tag: 'tag:yaml.org,2002:js',
  identify: (v) => v !== null && typeof v === 'object' && Object.keys(v).length === 1 && '__js' in v,
  resolve: (str) => ({ __js: str }),
};
const exprs = [];
const sentinelize = (node) => {
  if (Array.isArray(node)) return node.map(sentinelize);
  if (node === null || typeof node !== 'object') return node;
  if (Object.keys(node).length === 1 && '__js' in node) {
    const marker = `__DSH_JS_${exprs.length}__`;
    exprs.push([marker, node.__js]);
    return marker;
  }
  const out = {};
  for (const [k, v] of Object.entries(node)) out[k] = sentinelize(v);
  return out;
};

// ── 1. the legacy persona identity row (its prefix is the whole point) ──────
const meta = YAML.parse(readFileSync(join(LEGACY, 'preset.yml'), 'utf8'));
const legacyRows = YAML.parse(readFileSync(join(LEGACY, 'agent.cordis.yml'), 'utf8'), { customTags: [jsTag] });
const personaRow = legacyRows.find((r) => r.id === 'persona');
if (personaRow === undefined) throw new Error('legacy preset has no `persona` row');

// ── 2. the shipped 0.2.0 `standard` plugin list ─────────────────────────────
const asar = readFileSync(APP_ASAR, 'latin1');
const marker = '- insert:\n    - id: preset-standard\n';
const at = asar.indexOf(marker);
if (at === -1) throw new Error('shipped standard preset declaration not found in app.asar');
// The declaration runs from the insert marker to the last row of the preset
// (`tool-plugin-manager`); the following bytes are the package's LICENSE text.
const tail = asar.slice(at, at + 200000);
const lastRow = '- id: tool-plugin-manager\n            name: \'@deepseek-ai/dsh-plugin-manager/tools\'\n            disabled: true\n';
const lastAt = tail.indexOf(lastRow);
if (lastAt === -1) throw new Error('failed to find the end of the shipped standard declaration');
const block = tail.slice(0, lastAt + lastRow.length);
const standardDecl = YAML.parse(block, { customTags: [jsTag] });
const standardConfig = standardDecl?.[0]?.insert?.[0]?.config;
if (standardConfig?.id !== 'standard') throw new Error('failed to parse the shipped standard declaration');
const plugins = standardConfig.plugins;

// Keep the shipped order and row shapes; replace only the identity row.
const idx = plugins.findIndex((r) => r.id === 'persona');
if (idx === -1) throw new Error('shipped standard preset has no persona row');
plugins[idx] = { ...plugins[idx], config: personaRow.config };

const declaration = [
  {
    insert: [
      {
        id: 'preset-persona',
        name: '@deepseek-ai/dsh-agent-preset',
        config: {
          id: 'persona',
          ...(meta.name === undefined ? {} : { name: meta.name }),
          ...(meta.description === undefined ? {} : { description: meta.description }),
          ...(meta.order === undefined ? {} : { order: meta.order }),
          plugins,
        },
      },
    ],
  },
];

let patchYaml = YAML.stringify(sentinelize(declaration), { lineWidth: 0 });
for (const [m, expr] of exprs) patchYaml = patchYaml.split(`"${m}"`).join(m).split(m).join(`!!js ${expr}`);

// ── 3. write, keeping the previous attempt for comparison ───────────────────
mkdirSync(OUT_DIR, { recursive: true });
const target = join(OUT_DIR, 'cordis.patch.yml');
if (existsSync(target)) copyFileSync(target, join(OUT_DIR, 'cordis.patch.attempt1.yml.bak'));
writeFileSync(target, patchYaml, 'utf8');

// ── 4. report the parity diff against the shipped preset ────────────────────
const sig = (row) => `${row.id}|${row.name}|${row.disabled === undefined ? '' : 'disabled'}`;
const stdSig = standardConfig.plugins.map(sig);
const newSig = plugins.map(sig);
const diffs = [];
for (let i = 0; i < Math.max(stdSig.length, newSig.length); i++) {
  if (stdSig[i] !== newSig[i]) diffs.push(`row ${i + 1}: standard=${stdSig[i] ?? '-'} mine=${newSig[i] ?? '-'}`);
}
const count = (list) => {
  let n = 0;
  const walk = (rows) => {
    for (const r of rows) {
      n++;
      if (Array.isArray(r.config)) walk(r.config);
    }
  };
  walk(list);
  return n;
};

console.log(`shipped standard rows : ${count(standardConfig.plugins)}`);
console.log(`new persona rows      : ${count(plugins)}`);
console.log(`row-shape diffs       : ${diffs.length === 0 ? 'none' : '\n  ' + diffs.join('\n  ')}`);
console.log(`persona prefix kept   : ${/尊敬的女王大人/.test(plugins[idx].config.prefix ?? '')}`);
console.log(`!!js exprs kept       : ${(patchYaml.match(/!!js /g) ?? []).length}`);
console.log(`out                   : ${target}`);
