// Read-only: decompress every zstd frame of a DSH session log and report events
// near a given time, plus anything naming a preset.
import fs from 'node:fs';
import zlib from 'node:zlib';

const file = process.argv[2];
const sinceMs = Number(process.argv[3] ?? 0);
const ZSTD = Buffer.from([0x28, 0xb5, 0x2f, 0xfd]);

const buf = fs.readFileSync(file);
const frames = [];
let i = 0;
while (i < buf.length) {
  const next = buf.indexOf(ZSTD, i + 4);
  frames.push(buf.subarray(i, next === -1 ? buf.length : next));
  if (next === -1) break;
  i = next;
}
let text = '';
for (const f of frames) {
  try {
    text += zlib.zstdDecompressSync(f).toString('utf8');
  } catch {}
}
const lines = text.split('\n').filter((l) => l.trim().length > 0);
console.log(`frames=${frames.length} lines=${lines.length} bytes=${text.length}`);

const presetish = [];
const recent = [];
for (const line of lines) {
  let rec;
  try {
    rec = JSON.parse(line);
  } catch {
    continue;
  }
  const s = JSON.stringify(rec);
  if (/agent-preset|preset-persona|persona"|agentPreset/.test(s)) presetish.push(rec);
  const t = rec.time ?? rec.data?.time;
  if (typeof t === 'number' && t >= sinceMs) recent.push({ t, type: rec.type, s: s.slice(0, 300) });
}

console.log(`\n--- preset-ish records: ${presetish.length} ---`);
for (const r of presetish.slice(0, 12)) console.log(`${r.time ?? ''} ${r.type}: ${JSON.stringify(r.data ?? r).slice(0, 300)}`);

console.log(`\n--- records at/after ${new Date(sinceMs).toISOString()}: ${recent.length} ---`);
for (const r of recent.slice(0, 25)) console.log(`${new Date(r.t).toISOString()} ${r.type}: ${r.s}`);
