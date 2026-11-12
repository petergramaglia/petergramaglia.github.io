import { test, expect } from '@playwright/test';
const ready = async (page) => {
  await page.goto('/');
  await expect(page.locator('#field')).toHaveAttribute('data-renderer', 'ready');
};
const resolve = async (page, value) => {
  await page.locator('#resolve').fill(String(value));
  await expect(page.locator('#resolve')).toHaveAttribute('aria-valuetext', `${Math.round(value / 10)} percent resolved`);
};

test('GPU render, keyboard endpoints, and drag back from photograph', async ({ page }) => {
  const errors = []; page.on('pageerror', (error) => errors.push(error.message));
  await ready(page);
  const range = page.getByRole('slider', { name: 'Resolve landscape' });
  await range.focus(); await range.press('End');
  await expect(page.locator('#field')).toHaveClass(/is-photo/);
  await page.mouse.move(1000, 350); await page.mouse.down(); await page.mouse.move(400, 350, { steps: 15 }); await page.mouse.up();
  await expect(page.locator('#field')).not.toHaveClass(/is-photo/);
  await range.focus(); await range.press('Home');
  await expect(range).toHaveValue('0');
  expect(errors).toEqual([]);
});

test('About contains focus, closes with Escape, and returns focus', async ({ page }) => {
  await ready(page);
  await page.getByRole('link', { name: 'About', exact: true }).click();
  const dialog = page.getByRole('dialog'); await expect(dialog).toBeVisible();
  for (let i = 0; i < 7; i++) {
    await page.keyboard.press('Tab');
    expect(await page.evaluate(() => document.querySelector('dialog').contains(document.activeElement))).toBe(true);
  }
  await page.keyboard.press('Escape'); await expect(dialog).not.toBeVisible();
  await expect(page.getByRole('link', { name: 'About', exact: true })).toBeFocused();
});

test('portrait swaps remain registered during rapid resizing', async ({ page }) => {
  await ready(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.setViewportSize({ width: 1200, height: 700 });
  await page.setViewportSize({ width: 320, height: 740 });
  await expect(page.locator('#field')).toHaveAttribute('data-variant', 'mobile');
  await resolve(page, 1000);
  await expect(page.locator('#field')).toHaveClass(/is-photo/);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.locator('#managed-photo')).toHaveJSProperty('naturalWidth', 1200);
  await page.getByRole('link', { name: 'About', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
});

test('reduced motion applies immediately and updates at runtime', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' }); await ready(page);
  await resolve(page, 1000); await expect(page.locator('#field')).toHaveClass(/is-photo/);
  await resolve(page, 0); await expect(page.locator('#field')).not.toHaveClass(/is-photo/);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await resolve(page, 1000);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await expect(page.locator('#field')).toHaveClass(/is-photo/);
});

test('missing map fails to photograph while About remains usable', async ({ page }) => {
  await page.route('**/control.png', (route) => route.abort());
  await page.goto('/'); await expect(page.locator('#field')).toHaveAttribute('data-renderer', 'fallback');
  await expect(page.locator('#tuner')).toBeHidden();
  expect(await page.locator('#initial-photo img').evaluate((img) => img.complete && img.naturalWidth > 0)).toBe(true);
  await page.getByRole('link', { name: 'About', exact: true }).click(); await expect(page.getByRole('dialog')).toBeVisible();
});

test('context loss reveals managed photograph and disables tuner', async ({ page }) => {
  await ready(page);
  await page.locator('canvas').evaluate((canvas) => canvas.getContext('webgl').getExtension('WEBGL_lose_context').loseContext());
  await expect(page.locator('#field')).toHaveAttribute('data-renderer', 'fallback');
  await expect(page.locator('#managed-photo')).toBeVisible();
  await expect(page.locator('#tuner')).toBeHidden();
});

test('no JavaScript exposes biography and photo', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage(); await page.goto('http://127.0.0.1:4173/');
  await page.getByRole('link', { name: 'About', exact: true }).click();
  await expect(page.locator('#about')).toBeVisible();
  await expect(page.locator('#tuner')).toBeHidden();
  expect(await page.locator('#initial-photo img').evaluate((img) => img.complete && img.naturalWidth > 0)).toBe(true);
  await context.close();
});

test('capture five desktop states and mobile composition', async ({ page }, testInfo) => {
  await page.emulateMedia({ reducedMotion: 'reduce' }); await ready(page);
  for (const p of [0, 250, 500, 750, 1000]) {
    await resolve(page, p);
    await page.locator('#resolve').blur();
    await page.screenshot({ path: testInfo.outputPath(`desktop-${p}.png`) });
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('#field')).toHaveAttribute('data-variant', 'mobile');
  await resolve(page, 0); await page.screenshot({ path: testInfo.outputPath('mobile-drawing.png') });
  await resolve(page, 1000); await page.screenshot({ path: testInfo.outputPath('mobile-photo.png') });
});

test('WebGL denial and module failure preserve static content', async ({ browser }) => {
  const context = await browser.newContext();
  await context.addInitScript(() => {
    const get = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (kind, ...args) { return kind === 'webgl' ? null : get.call(this, kind, ...args); };
  });
  const page = await context.newPage(); await page.goto('http://127.0.0.1:4173/');
  await expect(page.locator('#field')).toHaveAttribute('data-renderer', 'fallback');
  await expect(page.locator('#tuner')).toBeHidden();
  await context.close();
  const other = await browser.newPage(); await other.route('**/src/main.js', (route) => route.abort());
  await other.goto('http://127.0.0.1:4173/');
  await other.getByRole('link', { name: 'About', exact: true }).click();
  await expect(other.locator('#about')).toBeVisible();
  await other.close();
});

test('failed orientation change retains a complete managed photo', async ({ page }) => {
  await ready(page);
  await page.route('**/mobile/control.png', (route) => route.abort());
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('#field')).toHaveAttribute('data-renderer', 'fallback');
  await expect(page.locator('#managed-photo')).toHaveJSProperty('naturalWidth', 1672);
  await expect(page.locator('#managed-photo')).toBeVisible();
  await expect(page.locator('#tuner')).toBeHidden();
});

test('short landscape and narrow views keep controls usable', async ({ page }, testInfo) => {
  await page.emulateMedia({ reducedMotion: 'reduce' }); await ready(page);
  for (const [width, height] of [[1200, 360], [320, 568], [2560, 720]]) {
    await page.setViewportSize({ width, height });
    await expect(page.locator('#field')).toHaveAttribute('data-variant', height > width ? 'mobile' : 'desktop');
    await resolve(page, 1000);
    const bounds = await page.locator('#resolve').boundingBox();
    expect(bounds.x).toBeGreaterThanOrEqual(0); expect(bounds.y).toBeGreaterThanOrEqual(0);
    expect(bounds.x + bounds.width).toBeLessThanOrEqual(width);
    expect(bounds.y + bounds.height).toBeLessThanOrEqual(height);
    await page.locator('#resolve').blur();
    await page.screenshot({ path: testInfo.outputPath(`layout-${width}.png`) });
  }
});

test('returning orientation reuses decoded assets even when network fails', async ({ page }) => {
  await ready(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('#field')).toHaveAttribute('data-variant', 'mobile');
  let requests = 0;
  await page.route('**/assets/desktop/*', (route) => { requests++; route.abort(); });
  await page.setViewportSize({ width: 1440, height: 900 });
  await expect(page.locator('#field')).toHaveAttribute('data-variant', 'desktop');
  await expect(page.locator('#field')).toHaveAttribute('data-renderer', 'ready');
  expect(requests).toBe(0);
});

test('pointer cancellation and second contact end artwork drag', async ({ page }) => {
  await ready(page);
  await page.mouse.move(900, 300); await page.mouse.down(); await page.mouse.move(800, 300);
  const afterMove = await page.locator('#resolve').inputValue();
  await page.locator('canvas').dispatchEvent('pointercancel', { pointerId: 1, isPrimary: true });
  await page.mouse.move(300, 300); await page.mouse.up();
  expect(await page.locator('#resolve').inputValue()).toBe(afterMove);
  await page.mouse.move(900, 300); await page.mouse.down();
  await page.locator('canvas').dispatchEvent('pointerdown', { pointerId: 9, isPrimary: false, pointerType: 'touch', button: 0, clientX: 950, clientY: 300 });
  await page.mouse.move(400, 300); await page.mouse.up();
  expect(await page.locator('#resolve').inputValue()).toBe(afterMove);
  await page.locator('canvas').dispatchEvent('pointerup', { pointerId: 9, isPrimary: false });
});
