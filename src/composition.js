import { clamp } from './math.js';
export function variantFor(width, height) { return height > width ? 'mobile' : 'desktop'; }
// object-position and shader offset share exactly the same cover transform.
export function coverCrop(width, height, sourceWidth, sourceHeight, focal = [.5, .55], subject, peak) {
  const scale = Math.max(width / sourceWidth, height / sourceHeight);
  const visible = [width / (sourceWidth * scale), height / (sourceHeight * scale)];
  const position = focal.map((v, axis) => {
    if (!subject || visible[axis] >= .9999) return clamp(v);
    const extent = visible[axis];
    // Keep both summit and person whenever their combined bounds fit. Relax
    // the preferred margins before sacrificing either part of the composition.
    if (peak) {
      const low = Math.min(subject[axis], peak[axis]);
      const high = Math.max(subject[axis + 2], peak[axis]);
      if (high - low <= extent) {
        const margin = Math.min(.02 * extent, (extent - (high - low)) * .49);
        const min = Math.max(0, high + margin - extent);
        const max = Math.min(1 - extent, low - margin);
        if (min <= max) return clamp((1 - extent) * v, min, max) / (1 - extent);
      }
    }
    const min = Math.max(0, subject[axis + 2] - extent * .9);
    const max = Math.min(1 - extent, subject[axis] - extent * .1);
    if (min > max) return clamp(v); // At extreme crops there may be no safe interval.
    const offset = clamp((1 - extent) * v, min, max);
    return offset / (1 - extent);
  });
  return { scale: visible, offset: visible.map((v, i) => (1 - v) * position[i]), position };
}
