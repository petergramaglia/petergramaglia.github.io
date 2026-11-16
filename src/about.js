export function setupAbout(onChange) {
  const content = document.querySelector('#about');
  const opener = document.querySelector('.about-link');
  if (typeof HTMLDialogElement === 'undefined' || !HTMLDialogElement.prototype.showModal) return { open: false, dispose() {} };
  const dialog = document.createElement('dialog');
  dialog.className = 'about-dialog';
  dialog.setAttribute('aria-labelledby', 'about-title');
  document.body.append(dialog);
  dialog.append(content);
  const controller = new AbortController();
  const options = { signal: controller.signal };
  const changed = () => { document.body.classList.toggle('about-open', dialog.open); onChange(dialog.open); };
  opener.addEventListener('click', (event) => {
    event.preventDefault();
    dialog.showModal(); changed();
  }, options);
  content.querySelector('.close-about').addEventListener('click', (event) => { event.preventDefault(); dialog.close(); }, options);
  dialog.addEventListener('close', () => { changed(); opener.focus({ preventScroll: true }); }, options);
  dialog.addEventListener('keydown', (event) => {
    if (event.key !== 'Tab') return;
    const items = [...dialog.querySelectorAll('a[href], button, input, [tabindex="0"]')];
    const first = items[0], last = items.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }, options);
  // Only an actual backdrop click closes; a click in dialog padding remains inside.
  dialog.addEventListener('click', (event) => {
    const rect = dialog.getBoundingClientRect();
    if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
  }, options);
  if (location.hash === '#about') { dialog.showModal(); changed(); }
  return { get open() { return dialog.open; }, dispose() { controller.abort(); if (dialog.open) dialog.close(); document.body.append(content); dialog.remove(); document.body.classList.remove('about-open'); } };
}
