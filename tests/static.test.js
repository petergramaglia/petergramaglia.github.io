import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, access } from 'node:fs/promises';
import { createHash } from 'node:crypto';
const root = new URL('../', import.meta.url);
test('homepage local references exist and identifiers are unique', async () => {
  const html = await readFile(new URL('index.html', root), 'utf8');
  const refs = [...html.matchAll(/(?:src|href|srcset)="([^"#]+)"/g)].map((m) => m[1]).filter((ref) => !/^(https?:|mailto:)/.test(ref));
  for (const ref of refs) await access(new URL(ref, root));
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1]);
  assert.equal(new Set(ids).size, ids.length);
  assert.match(html, /type="range"/);
  assert.match(html, /AI-expanded edges/);
});
test('all derivative assets and legacy resume remain available', async () => {
  const manifest = JSON.parse(await readFile(new URL('assets/manifest.json', root), 'utf8'));
  for (const variant of ['desktop', 'mobile']) {
    assert.ok(manifest[variant].width > 0 && manifest[variant].height > 0);
    assert.equal(manifest[variant].focal.length, 2);
    for (const filename of ['finished.webp', 'layer0.webp', 'time0.png', 'layer1.webp', 'time1.png', 'layer2.webp', 'time2.png']) {
      const bytes = await readFile(new URL(`assets/${variant}/${filename}`, root));
      assert.equal(manifest[variant].revisions[filename], createHash('sha256').update(bytes).digest('hex').slice(0, 20), `${variant}/${filename} needs a new revision`);
    }
  }
  await access(new URL('resume.html', root));
  await access(new URL('Gramaglia_Resume.pdf', root));
});
