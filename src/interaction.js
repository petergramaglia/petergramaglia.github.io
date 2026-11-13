import { clamp } from './math.js';
export function setupInteraction(canvas, range, getTarget, onInput) {
  const controller = new AbortController();
  const options = { signal: controller.signal };
  let active = null;
  const pointers = new Set();
  const cancel = () => {
    const previous = active; active = null;
    if (previous && canvas.hasPointerCapture(previous.id)) canvas.releasePointerCapture(previous.id);
  };
  canvas.addEventListener('pointerdown', (event) => {
    pointers.add(event.pointerId);
    if (pointers.size !== 1 || !event.isPrimary || event.button !== 0) { cancel(); return; }
    active = { id: event.pointerId, x: event.clientX, value: getTarget() };
    canvas.setPointerCapture(event.pointerId);
  }, options);
  canvas.addEventListener('pointermove', (event) => {
    if (!active || event.pointerId !== active.id) return;
    const value = clamp(active.value + (event.clientX - active.x) / Math.max(220, canvas.clientWidth * .65));
    onInput(value);
  }, options);
  const end = (event) => { pointers.delete(event.pointerId); if (active?.id === event.pointerId) cancel(); };
  window.addEventListener('pointerup', end, options);
  window.addEventListener('pointercancel', end, options);
  canvas.addEventListener('lostpointercapture', end, options);
  window.addEventListener('blur', () => { cancel(); pointers.clear(); }, options);
  range.addEventListener('input', () => onInput(Number(range.value) / 1000), options);
  return { cancel() { cancel(); pointers.clear(); }, dispose() { cancel(); controller.abort(); } };
}
