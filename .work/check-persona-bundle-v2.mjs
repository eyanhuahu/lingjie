// Independent check of the generated bundle (take 2): the plugin list must be
// row-for-row identical to the shipped 0.2.0 `standard` preset except for the
// `persona` identity row's config, and the patch must parse the way the Loader
// parses it. Run: node check-persona-bundle-v2.mjs
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const require = createRequire('D:/aideepseek/data/profiles/web/package.json');
const YAML = require('yaml');

const DIR = 'D:\\Users\\huan\\Documents\\GitHub\\lingjie\\.work\\dsh-persona-preset';
const APP_ASAR = 'C:\\Users\\huan\\AppData\\Local\\Programs\\DeepSeek Harness\\resources\\app.asar';

const exprs = [];
const jsTag = {
  tag: 'tag:yaml.org,2002:js',
  identify: (v) => v !== null && typeof v === 'object' && Object.keys(v).length === 1 && '__js' in v,
  resolve: (str) => {
    exprs.push(str);
    return { __js: str };
  },
};

let failures = 0;
const check = (ok, label, detail = '') => {
  console.log(`${ok ? '  PASS' : '  FAIL'}  ${label}${detail ? '  — ' + detail : ''}`);
  if (!ok) failures++;
};

const manifest = JSON.parse(readFileSync(join(DIR, 'package.json'), 'utf8'));
const patch = YAML.parse(readFileSync(join(DIR, 'cordis.patch.yml'), 'utf8'), { customTags: [jsTag] });

check(Array.isArray(patch), 'patch root is a list');
check(manifest.dsh?.bundle?.patch === './cordis.patch.yml', 'manifest declares dsh.bundle.patch');

const entry = patch?.find((e) => e?.insert !== undefined)?.insert?.[0];
check(entry?.name === '@deepseek-ai/dsh-agent-preset', 'inserts a dsh-agent-preset row', String(entry?.name));
const config = entry?.config;
check(config?.id === 'persona', 'declared preset id is "persona"', String(config?.id));
check(config?.name !== undefined && config?.order === 10, 'display metadata carried over from preset.yml');

const plugins = config?.plugins ?? [];
const ids = [];
const refs = [];
const bad = [];
const walk = (list) => {
  for (const row of list) {
    if (typeof row?.id === 'string') ids.push(row.id);
    if (typeof row?.name === 'string' && row.name !== 'cordis:group') refs.push(row.name);
    if (row?.name === 'cordis:group' && !Array.isArray(row.config)) bad.push(`${row.id}: group without a nested list`);
    if (row?.disabled !== undefined && typeof row.disabled === 'object' && !('__js' in row.disabled)) bad.push(`${row.id}: malformed disabled`);
    if (Array.isArray(row?.config)) walk(row.config);
  }
};
walk(plugins);

check(new Set(ids).size === ids.length, 'row ids are unique', `${ids.length} ids`);
check(bad.length === 0, 'no malformed rows', bad.join('; '));
check(ids.includes('persona') && ids.includes('tool-plugin-manager'), 'identity row and plugin-manager row present');
check(!ids.includes('workflow-worker-thread'), 'retired workflow-worker-thread row is gone');
check(exprs.length === 2, 'both platform !!js expressions survive', exprs.join(' | '));

const head = readFileSync(APP_ASAR, 'latin1');
const stdAt = head.indexOf('- insert:\n    - id: preset-standard\n');
const lastRow = "- id: tool-plugin-manager\n            name: '@deepseek-ai/dsh-plugin-manager/tools'\n            disabled: true\n";
const tail = head.slice(stdAt, stdAt + 200000);
const standard = YAML.parse(tail.slice(0, tail.indexOf(lastRow) + lastRow.length), { customTags: [jsTag] })[0].insert[0].config;

const sig = (row) => `${row.id}|${row.name}|${row.disabled === undefined ? '' : 'disabled'}`;
const mineSig = plugins.map(sig).filter((s) => !s.startsWith('persona|'));
const stdSig = standard.plugins.map(sig).filter((s) => !s.startsWith('persona|'));
check(mineSig.length === stdSig.length && mineSig.every((s, i) => s === stdSig[i]), 'plugin list matches shipped standard row-for-row', `${mineSig.length} non-persona rows`);

const hostPackages = new Set([...head.slice(0, 6 * 1024 * 1024).matchAll(/"name":\s*"(@deepseek-ai\/[^"]+)"/g)].map((m) => m[1]));
const unresolved = [...new Set(refs)].filter((n) => !hostPackages.has(n.split('/').slice(0, n.startsWith('@') ? 2 : 1).join('/')));
check(unresolved.length === 0, 'every plugin reference resolves in the installed host', unresolved.join(', '));

const personaRows = plugins.filter((r) => r.id === 'persona');
check(personaRows.length === 1 && /dsh-persona$/.test(personaRows[0].name), 'exactly one dsh-persona row');
const prefix = personaRows[0]?.config?.prefix ?? '';
check(prefix.includes('尊敬的女王大人') && prefix.includes('{{model}}') && /【收敛开关】/.test(prefix), 'persona text intact (称呼 / {{model}} / 收敛开关)');
check(/Your working directory is \{\{cwd\}\}\./.test(personaRows[0]?.config?.suffix ?? ''), 'suffix template kept');

console.log(`\n${failures === 0 ? 'ALL CHECKS PASSED' : failures + ' CHECK(S) FAILED'}`);
process.exitCode = failures === 0 ? 0 : 1;
