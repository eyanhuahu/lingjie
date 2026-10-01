// Independent check of the generated bundle: parse the patch the way the Loader
// will and confirm the declaration and every plugin reference.
// Run: node check-persona-bundle.mjs
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
check(manifest.private === true && typeof manifest.version === 'string', 'manifest has version and private');

const entry = patch?.find((e) => e?.insert !== undefined)?.insert?.[0];
check(entry?.name === '@deepseek-ai/dsh-agent-preset', 'inserts a dsh-agent-preset row', String(entry?.name));
const config = entry?.config;
check(config?.id === 'persona', 'declared preset id is "persona"', String(config?.id));
check(config?.name !== undefined && config?.description !== undefined && config?.order === 10, 'display metadata carried over from preset.yml');

const plugins = config?.plugins ?? [];
check(Array.isArray(plugins) && plugins.length > 0, 'declares a plugin list', `${plugins.length} top-level rows`);

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
check(ids.includes('persona'), 'the persona identity row is present');
check(ids.includes('tool-presentation'), 'presentation row present');
check(!ids.includes('workflow-worker-thread'), 'retired workflow-worker-thread row is gone');
check(exprs.length === 4, 'four !!js expressions survive as expressions', exprs.join(' | '));

const head = readFileSync(APP_ASAR, 'latin1').slice(0, 6 * 1024 * 1024);
const hostPackages = new Set([...head.matchAll(/"name":\s*"(@deepseek-ai\/[^"]+)"/g)].map((m) => m[1]));
const unresolved = [...new Set(refs)].filter((n) => !hostPackages.has(n.split('/').slice(0, n.startsWith('@') ? 2 : 1).join('/')));
check(unresolved.length === 0, 'every plugin reference resolves in the installed host', unresolved.join(', '));

const personaRows = plugins.filter((r) => r.id === 'persona');
check(personaRows.length === 1 && /dsh-persona$/.test(personaRows[0].name), 'exactly one dsh-persona row');
const prefix = personaRows[0]?.config?.prefix ?? '';
check(prefix.includes('尊敬的女王大人'), 'persona prefix kept');
check(prefix.includes('{{model}}'), '{{model}} placeholder kept');
check(/【收敛开关】/.test(prefix), 'convergence switch kept');

console.log(`\n${failures === 0 ? 'ALL CHECKS PASSED' : failures + ' CHECK(S) FAILED'}`);
process.exitCode = failures === 0 ? 0 : 1;
