import test from 'node:test';
import assert from 'node:assert/strict';
import { progression } from '../src/progression.js';

test('strokes mature independently while later strokes remain undrawn', () => {
  for (const p of [0, .15, .3, .45]) {
    const phase = progression(p);
    assert.equal(phase.sketch, 1);
    assert.equal(phase.broad, 0);
    assert.equal(phase.detail, 0);
    assert.equal(phase.saturation, 0);
  }
  const painted = progression(.65, .55), waiting = progression(.65, .86);
  assert.equal(painted.broad, 1);
  assert.equal(painted.saturation, 1);
  assert.equal(waiting.broad, 0);
  assert.equal(waiting.saturation, 0);
  assert.equal(waiting.sketch, 1);
});
test('local stroke growth reverses and late strokes mature before the endpoint', () => {
  const early = progression(.85, .9), drawing = progression(.9, .9), done = progression(.94, .9);
  assert.equal(early.detail, 0);
  assert.ok(drawing.detail > 0 && drawing.detail < 1);
  assert.ok(drawing.saturation > 0 && drawing.saturation < 1);
  assert.equal(done.detail, 1);
  assert.equal(done.saturation, 1);
  assert.deepEqual(progression(.9, .9), drawing);
  assert.equal(progression(.995, .968).saturation, 1);
  const end = progression(1, .968);
  assert.deepEqual(end, { sketch: 0, broad: 1, detail: 1, saturation: 1 });
});
