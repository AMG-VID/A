import { readFileSync } from 'node:fs';
import { Script } from 'node:vm';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const scriptTags = [...html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)];
let checked = 0;

for (const match of scriptTags) {
  if (/\bsrc\s*=/.test(match[1])) continue;
  const source = match[2].trim();
  if (!source) continue;
  new Script(source, { filename: 'index.html:inline-script-' + (++checked) });
}

if (checked === 0) throw new Error('No inline scripts were found.');
console.log('Validated ' + checked + ' inline JavaScript block(s).');
