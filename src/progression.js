import { clamp } from './math.js';

// Keep structure, color coverage, and pigment strength on separate timelines.
// The renderer uses these same bounds when generating its GLSL source.
export const STAGES = {
  sketchFade: [.72, 1],
  broadOpacity: [.45, 1],
  detailOpacity: [.68, 1],
  saturation: [.62, 1],
};
function ramp([start, end], value) {
  const t = clamp((value - start) / (end - start));
  return t * t * (3 - 2 * t);
}
export function progression(value) {
  return {
    sketch: 1 - ramp(STAGES.sketchFade, value),
    broad: ramp(STAGES.broadOpacity, value),
    detail: ramp(STAGES.detailOpacity, value),
    saturation: ramp(STAGES.saturation, value),
  };
}
