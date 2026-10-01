// One-shot migration: turn the legacy directory preset
//   $DSH_HOME/.agent-presets/persona/{preset.yml,agent.cordis.yml}
// (a DSH 0.1.x mechanism that 0.2.x no longer reads) into a 0.2.x
// configuration-only bundle: manifest + cordis.patch.yml holding one
// `@deepseek-ai/dsh-agent-preset` declaration row.
//
// The legacy directory is only read; everything written goes to OUT_DIR.
// Run: node migrate-persona-preset.mjs
import { createRequire } from 'node:module';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const require = createRequire('D:/aideepseek/data/profiles/web/package.json');
const YAML = require('yaml');

const LEGACY = 'D:\\aideepseek\\data\\.agent-presets\\persona';
const OUT_DIR = 'D:\\Users\\huan\\Documents\\GitHub\\lingjie\\.work\\dsh-persona-preset';
const APP_ASAR = 'C:\\Users\\huan\\AppData\\Local\\Programs\\DeepSeek Harness\\resources\\app.asar';

// `disabled: !!js <expr>` must survive as a Loader expression rather than text.
// yaml v2 has no clean re-emit path for a custom tag here, so every expression
// becomes a sentinel string that is substituted back after stringifying.
const exprs = [];
const jsTag = {
  tag: 'tag:yaml.org,2002:js',
  identify: (v) => v !== null && typeof v === 'object' && Object.keys(v).length === 1 && '__js' in v,
  resolve: (str) => ({ __js: str }),
};
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

const meta = YAML.parse(readFileSync(join(LEGACY, 'preset.yml'), 'utf8'));
const rows = YAML.parse(readFileSync(join(LEGACY, 'agent.cordis.yml'), 'utf8'), { customTags: [jsTag] });
if (!Array.isArray(rows)) throw new Error('legacy agent.cordis.yml is not a top-level list');
const topLevelCount = rows.length;

/** Depth-first walk over the entry list, descending into group `config` lists. */
const eachRow = (list, fn) => {
  for (let i = 0; i < list.length; i++) {
    fn(list[i], list, i);
    if (Array.isArray(list[i]?.config)) eachRow(list[i].config, fn);
  }
};
const findRow = (id) => {
  let hit;
  eachRow(rows, (row) => {
    if (row?.id === id && hit === undefined) hit = row;
  });
  return hit;
};

// Between 0.1.5 and 0.2.0 one package was replaced: `dsh-workflow-worker-thread`
// became `@deepseek-ai/dsh-workflow-ptc`, which the shipped preset leaves
// disabled because orchestration needs a PTC runtime.
const renames = [];
const renamed = findRow('workflow-worker-thread');
if (renamed !== undefined) {
  Object.assign(renamed, {
    id: 'workflow-ptc',
    name: '@deepseek-ai/dsh-workflow-ptc',
    disabled: { __js: 'true' },
    config: { provider: 'spawn' },
  });
  renames.push('workflow-worker-thread -> workflow-ptc');
}

// Rows the shipped 0.2.0 `standard` preset carries that the 0.1.5 list does not.
// `native` keeps this preset's promise: tools identical to standard.
const additions = [];
for (const row of [
  { id: 'tool-presentation', name: '@deepseek-ai/dsh-agent-tool-presentation', config: { mode: 'native' } },
  { id: 'tool-plugin-manager', name: '@deepseek-ai/dsh-plugin-manager/tools', disabled: { __js: 'true' } },
]) {
  if (findRow(row.id) !== undefined) continue;
  rows.push(row);
  additions.push(row.id);
}
const presentIdx = rows.findIndex((r) => r.id === 'present');
if (presentIdx !== -1) rows.push(rows.splice(presentIdx, 1)[0]);

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
          plugins: rows,
        },
      },
    ],
  },
];

let patchYaml = YAML.stringify(sentinelize(declaration), { lineWidth: 0 });
for (const [marker, expr] of exprs) {
  patchYaml = patchYaml.split(`"${marker}"`).join(marker).split(marker).join(`!!js ${expr}`);
}

const manifest = {
  name: '@local/dsh-preset-persona',
  version: '1.0.0',
  private: true,
  type: 'module',
  description: meta.description ?? 'Legacy persona preset migrated to a 0.2.x bundle.',
  dsh: { bundle: { patch: './cordis.patch.yml' } },
};

// Validate every referenced package against the installed 0.2.0 host manifest.
const head = readFileSync(APP_ASAR, 'latin1').slice(0, 6 * 1024 * 1024);
const hostPackages = new Set([...head.matchAll(/"name":\s*"(@deepseek-ai\/[^"]+)"/g)].map((m) => m[1]));
const refs = [];
eachRow(rows, (row) => {
  if (typeof row?.name === 'string' && row.name !== 'cordis:group') refs.push(row.name);
});
const uniqueRefs = [...new Set(refs)];
const unresolved = uniqueRefs.filter((n) => !hostPackages.has(n.split('/').slice(0, n.startsWith('@') ? 2 : 1).join('/')));

mkdirSync(OUT_DIR, { recursive: true });
writeFileSync(join(OUT_DIR, 'package.json'), JSON.stringify(manifest, null, 2) + '\n', 'utf8');
writeFileSync(join(OUT_DIR, 'cordis.patch.yml'), patchYaml, 'utf8');

const check = YAML.parse(patchYaml, { customTags: [jsTag] });
console.log(`legacy top-level rows : ${topLevelCount}`);
console.log(`renamed rows          : ${renames.join(', ') || '(none)'}`);
console.log(`added rows            : ${additions.join(', ') || '(none)'}`);
console.log(`patch root            : ${Array.isArray(check) ? 'list' : 'NOT A LIST'}`);
console.log(`declared id           : ${check?.[0]?.insert?.[0]?.config?.id}`);
console.log(`plugins read back     : ${check?.[0]?.insert?.[0]?.config?.plugins?.length}`);
console.log(`!!js exprs kept       : ${(patchYaml.match(/!!js /g) ?? []).length}`);
console.log(`plugin refs           : ${uniqueRefs.length}`);
console.log(`unresolved            : ${unresolved.length === 0 ? 'none' : unresolved.join(', ')}`);
console.log(`out                   : ${OUT_DIR}`);
