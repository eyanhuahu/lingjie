// Read-only: report the header and the agent-preset identity of a v4 session log,
// plus how many preset/selected events it carries.
import fs from 'node:fs';
import zlib from 'node:zlib';

const file = process.argv[2];
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
const decoded = [];
for (const f of frames) {
  try {
    const t = zlib.zstdDecompressSync(f).toString('utf8');
    decoded.push(t);
    text += t;
  } catch {}
}
const lines = text.split('\n').filter((l) => l.trim().length > 0);
console.log(`file=${file}`);
console.log(`size=${buf.length} frames=${frames.length} decodedFrames=${decoded.length} lines=${lines.length}`);
console.log(`\n--- first 2 lines ---`);
for (const l of lines.slice(0, 2)) console.log(l.slice(0, 600));

const selected = [];
const personaish = [];
for (const l of lines) {
  if (l.includes('agent-preset/selected')) selected.push(l.slice(0, 400));
  if (/persona/.test(l) && /preset/i.test(l)) personaish.push(l.slice(0, 300));
}
console.log(`\nagent-preset/selected events: ${selected.length}`);
for (const s of selected.slice(0, 5)) console.log(s);
console.log(`\nlines mentioning persona+preset: ${personaish.length}`);
for (const s of personaish.slice(0, 3)) console.log(s);

console.log(`\n--- last 2 lines ---`);
for (const l of lines.slice(-2)) console.log(l.slice(0, 500));
