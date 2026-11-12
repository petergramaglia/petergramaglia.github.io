import test from 'node:test';
import assert from 'node:assert/strict';
import { progression } from '../src/progression.js';

test('first half leaves room for structural sketch refinement before color', () => {
  for (const p of [0, .15, .3, .45]) {
    const phase = progression(p);
    assert.equal(phase.sketch, 1);
    assert.equal(phase.broad, 0);
    assert.equal(phase.detail, 0);
    assert.equal(phase.saturation, 0);
  }
  assert.ok(progression(.55).broad < .1);
  assert.equal(progression(.6).saturation, 0);
});
test('colored wisps and saturation remain incomplete until the endpoint', () => {
  const middle = progression(.75), late = progression(.9), end = progression(1);
  assert.ok(middle.broad < .6 && middle.saturation < .3);
  assert.ok(late.broad > middle.broad && late.broad < 1);
  assert.ok(late.detail < .8 && late.saturation < .9);
  assert.ok(progression(.98).saturation < 1);
  assert.deepEqual(end, { sketch: 0, broad: 1, detail: 1, saturation: 1 });
});
