import { LandscapeRenderer } from './renderer.js';
import { setupInteraction } from './interaction.js';
import { setupAbout } from './about.js';
import { variantFor } from './composition.js';
import { clamp, follow } from './math.js';

const field = document.querySelector('#field');
const canvas = document.querySelector('#landscape');
const tuner = document.querySelector('#tuner');
const range = document.querySelector('#resolve');
const number = document.querySelector('#resolve-number');
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const lifecycle = new AbortController();
let renderer, input, observer, manifest, requestedVariant;
let target = .03, current = .03, raf = 0, lastTime = 0, paused = false, failed = false;

function pause(value) {
  paused = value || document.hidden;
  input?.cancel();
  cancelAnimationFrame(raf); raf = 0; lastTime = 0;
  if (!paused) schedule();
}
const about = setupAbout((open) => pause(open));
function syncUI() {
  field.style.setProperty('--resolve', target);
  range.value = Math.round(target * 1000);
  range.setAttribute('aria-valuetext', `${Math.round(target * 100)} percent drawn`);
  number.textContent = String(Math.round(target * 100)).padStart(3, '0');
}
function paint() {
  if (failed) return;
  renderer?.draw(current);
  field.classList.toggle('is-complete', current === 1);
  syncUI();
}
function frame(time) {
  raf = 0;
  if (paused || failed || !renderer?.meta) return;
  const dt = lastTime ? Math.min((time - lastTime) / 1000, .05) : 1 / 60;
  lastTime = time;
  current = reduced.matches ? target : follow(current, target, dt);
  if (Math.abs(current - target) < .0001) current = target;
  paint();
  if (current !== target) raf = requestAnimationFrame(frame);
  else { lastTime = 0; renderer.draw(current); }
}
function schedule() {
  if (!raf && !paused && !failed && renderer?.meta) raf = requestAnimationFrame(frame);
}
function fail(error) {
  if (failed) return;
  failed = true;
  console.warn('Interactive landscape unavailable; using finished drawing.', error?.message || '');
  cancelAnimationFrame(raf); raf = 0;
  input?.dispose(); observer?.disconnect(); renderer?.dispose();
  tuner.hidden = true;
  field.classList.remove('is-ready', 'is-complete');
  field.dataset.renderer = 'fallback';
}
function resize() {
  if (!renderer || failed || !manifest) return;
  const width = field.clientWidth, height = field.clientHeight;
  renderer.resize(width, height);
  if (renderer.meta) paint();
  const variant = variantFor(width, height);
  if (variant === requestedVariant) return;
  requestedVariant = variant;
  renderer.setVariant(variant, manifest[variant], (photo) => {
    document.querySelector('#managed-photo').replaceWith(photo);
    field.classList.add('has-managed');
    // The decoded managed image now owns fallback. Remove the native picture
    // so its media source cannot trigger redundant orientation requests.
    document.querySelector('#initial-photo')?.remove();
    renderer.resize(field.clientWidth, field.clientHeight);
    paint();
    field.classList.add('is-ready');
    field.dataset.renderer = 'ready';
    field.dataset.variant = variant;
    tuner.hidden = false;
    schedule();
  }).catch(fail);
}

async function start() {
  try {
    // About is already usable even if graphics or asset loading fails.
    const response = await fetch(new URL('../assets/manifest.json', import.meta.url), { signal: AbortSignal.timeout(12_000) });
    if (!response.ok) throw new Error('Landscape manifest unavailable');
    manifest = await response.json();
    renderer = new LandscapeRenderer(canvas, fail);
    input = setupInteraction(canvas, range, () => target, (value) => {
      target = clamp(value);
      syncUI();
      if (reduced.matches) { current = target; paint(); } else schedule();
    });
    observer = new ResizeObserver(resize); observer.observe(field);
    resize();
  } catch (error) { fail(error); }
}
reduced.addEventListener('change', () => {
  if (reduced.matches) { current = target; cancelAnimationFrame(raf); raf = 0; lastTime = 0; paint(); }
  else schedule();
}, { signal: lifecycle.signal });
document.addEventListener('visibilitychange', () => pause(about.open), { signal: lifecycle.signal });
window.addEventListener('resize', resize, { signal: lifecycle.signal });
window.addEventListener('pagehide', (event) => {
  pause(true);
  if (!event.persisted) { lifecycle.abort(); observer?.disconnect(); input?.dispose(); renderer?.dispose(); }
}, { signal: lifecycle.signal });
window.addEventListener('pageshow', () => pause(about.open), { signal: lifecycle.signal });
start();
