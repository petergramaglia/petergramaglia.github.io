import test from 'node:test';
import assert from 'node:assert/strict';
import { follow, bufferSize, clamp } from '../src/math.js';
import { coverCrop, variantFor } from '../src/composition.js';

test('damping is independent of frame rate over one second', () => {
  const simulate = (fps) => { let value = 0; for (let i = 0; i < fps; i++) value = follow(value, 1, 1 / fps); return value; };
  assert.ok(Math.abs(simulate(30) - simulate(144)) < 1e-10);
  assert.ok(simulate(60) > .999);
});
test('cover registration keeps UVs within source at extreme viewport ratios', () => {
  for (const [w, h] of [[320, 960], [2560, 720], [800, 600], [1200, 1600]]) {
    for (const [sw, sh] of [[1672, 941], [1200, 1600]]) {
      const { scale, offset } = coverCrop(w, h, sw, sh, [.5, .64]);
      assert.ok(scale.every((v) => v > 0 && v <= 1));
      scale.forEach((v, i) => assert.ok(offset[i] >= 0 && offset[i] + v <= 1.000000001));
      assert.ok(Math.abs((scale[0] * sw) / (scale[1] * sh) - w / h) < 1e-10);
    }
  }
});
test('buffer budgets bound both total pixels and device dimensions', () => {
  for (const size of [[3840, 2160], [12000, 1000], [320, 900]]) {
    const [w, h] = bufferSize(...size, 3, 2_500_000, 4096);
    assert.ok(w * h <= 2_500_000 && w <= 4096 && h <= 4096);
    assert.ok(w > 0 && h > 0);
  }
});
test('portrait selection and resolve bounds', () => {
  assert.equal(variantFor(390, 844), 'mobile');
  assert.equal(variantFor(844, 390), 'desktop');
  assert.equal(clamp(-10), 0); assert.equal(clamp(10), 1);
});
test('wide cover crop retains the climber in a safe vertical region', () => {
  const subject = [.455, .677, .537, .853];
  const crop = coverCrop(2560, 720, 1672, 941, [.5, .64], subject);
  assert.ok((subject[3] - crop.offset[1]) / crop.scale[1] <= .90001);
  assert.ok((subject[1] - crop.offset[1]) / crop.scale[1] >= .1);
});
test('wide view retains peak and full climber when both fit by relaxing margins', () => {
  const subject = [.455, .677, .537, .853], peak = [.472, .365];
  const crop = coverCrop(2560, 720, 1672, 941, [.5, .64], subject, peak);
  assert.ok(crop.offset[1] <= peak[1]);
  assert.ok(crop.offset[1] + crop.scale[1] >= subject[3]);
  const extreme = coverCrop(1920, 400, 1672, 941, [.5, .64], subject, peak);
  assert.ok(extreme.offset[1] <= subject[1]);
  assert.ok(extreme.offset[1] + extreme.scale[1] >= subject[3]);
});
