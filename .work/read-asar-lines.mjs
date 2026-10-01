// Range-read specific lines from the Electron app.asar bundle (UTF-8 safe).
import fs from 'node:fs';

const file = process.argv[2];
const start = Number(process.argv[3]);
const end = Number(process.argv[4]);
const CHUNK = 4 * 1024 * 1024;
const fd = fs.openSync(file, 'r');
const size = fs.fstatSync(fd).size;
let pos = Math.max(0, start - CHUNK);
let carry = '';
let line = 0;
const out = [];
const decoder = new TextDecoder('utf-8');
while (pos < size && line < end) {
  const len = Math.min(CHUNK, size - pos);
  const buf = Buffer.allocUnsafe(len);
  fs.readSync(fd, buf, 0, len, pos);
  const text = carry + decoder.decode(buf, { stream: true });
  const lines = text.split('\n');
  carry = lines.pop();
  for (const l of lines) {
    line++;
    if (line >= start && line <= end) out.push(`${line}: ${l}`);
  }
  pos += len;
}
fs.closeSync(fd);
console.log(out.join('\n'));
