import { clamp } from './math.js';

// A stroke matures relative to its own arrival. Regional atlas schedules carry
// the composition order; there is no scene-wide color or pigment wash.
export const STAGES = {
  sketchFade: [.965, 1],
  sketchReveal: [-.012, .012],
  strokeReveal: [-.003, .003],
  strokeOpacity: [-.006, .018],
  strokePigment: [-.006, .026],
};
function ramp([start, end], value) {
  const t = clamp((value - start) / (end - start));
  return t * t * (3 - 2 * t);
}
export function progression(value, arrival = .5) {
  const age = value - arrival;
  const reveal = value >= 1 ? 1 : ramp(STAGES.strokeReveal, age);
  const opacity = value >= 1 ? 1 : .55 + .45 * ramp(STAGES.strokeOpacity, age);
  return {
    sketch: 1 - ramp(STAGES.sketchFade, value),
    broad: reveal * opacity,
    detail: reveal * opacity,
    saturation: value >= 1 ? 1 : ramp(STAGES.strokePigment, age),
  };
}
