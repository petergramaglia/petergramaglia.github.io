import { test, expect } from '@playwright/test';
const ready = async (page) => {
  await page.goto('/');
  await expect(page.locator('#field')).toHaveAttribute('data-renderer', 'ready');
};
const resolve = async (page, value) => {
  await page.locator('#resolve').fill(String(value));
  await expect(page.locator('#resolve')).toHaveAttribute('aria-valuetext', `${Math.round(value / 10)} percent drawn`);
};

test('GPU render, keyboard endpoints, and drag back from finished drawing', async ({ page }) => {
  const errors = []; page.on('pageerror', (error) => errors.push(error.message));
  await ready(page);
  const range = page.getByRole('slider', { name: 'Draw landscape' });
  await range.focus(); await range.press('End');
  await expect(page.locator('#field')).toHaveClass(/is-complete/);
  await page.mouse.move(1000, 350); await page.mouse.down(); await page.mouse.move(400, 350, { steps: 15 }); await page.mouse.up();
  await expect(page.locator('#field')).not.toHaveClass(/is-complete/);
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
  await expect(page.locator('#field')).toHaveClass(/is-complete/);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.locator('#managed-photo')).toHaveJSProperty('naturalWidth', 900);
  await page.getByRole('link', { name: 'About', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
});

test('reduced motion applies immediately and updates at runtime', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' }); await ready(page);
  await resolve(page, 1000); await expect(page.locator('#field')).toHaveClass(/is-complete/);
  await resolve(page, 0); await expect(page.locator('#field')).not.toHaveClass(/is-complete/);
  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await resolve(page, 1000);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await expect(page.locator('#field')).toHaveClass(/is-complete/);
});

test('missing map fails to finished drawing while About remains usable', async ({ page }) => {
  await page.route('**/time2.png', (route) => route.abort());
  await page.goto('/'); await expect(page.locator('#field')).toHaveAttribute('data-renderer', 'fallback');
  await expect(page.locator('#tuner')).toBeHidden();
  expect(await page.locator('#initial-photo img').evaluate((img) => img.complete && img.naturalWidth > 0)).toBe(true);
  await page.getByRole('link', { name: 'About', exact: true }).click(); await expect(page.getByRole('dialog')).toBeVisible();
});

test('context loss reveals managed drawing and disables tuner', async ({ page }) => {
  await ready(page);
  await page.locator('canvas').evaluate((canvas) => canvas.getContext('webgl').getExtension('WEBGL_lose_context').loseContext());
  await expect(page.locator('#field')).toHaveAttribute('data-renderer', 'fallback');
  await expect(page.locator('#managed-photo')).toBeVisible();
  await expect(page.locator('#tuner')).toBeHidden();
});

test('no JavaScript exposes biography and drawing', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage(); await page.goto('http://127.0.0.1:4173/');
  await page.getByRole('link', { name: 'About', exact: true }).click();
  await expect(page.locator('#about')).toBeVisible();
  await expect(page.locator('#tuner')).toBeHidden();
  expect(await page.locator('#initial-photo img').evaluate((img) => img.complete && img.naturalWidth > 0)).toBe(true);
  await context.close();
});

test('capture drawing stages and mobile composition', async ({ page }, testInfo) => {
  await page.emulateMedia({ reducedMotion: 'reduce' }); await ready(page);
  for (const p of [0, 150, 250, 300, 450, 500, 600, 750, 810, 820, 830, 900, 1000]) {
    await resolve(page, p);
    await page.locator('#resolve').blur();
    await page.screenshot({ path: testInfo.outputPath(`desktop-${p}.png`) });
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('#field')).toHaveAttribute('data-variant', 'mobile');
  await resolve(page, 0); await page.screenshot({ path: testInfo.outputPath('mobile-drawing.png') });
  await resolve(page, 1000); await page.screenshot({ path: testInfo.outputPath('mobile-finished.png') });
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

test('failed orientation change retains a complete managed drawing', async ({ page }) => {
  await ready(page);
  await page.route('**/mobile/time2.png', (route) => route.abort());
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('#field')).toHaveAttribute('data-renderer', 'fallback');
  await expect(page.locator('#managed-photo')).toHaveJSProperty('naturalWidth', 1440);
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

test('all stages use strokes, and full progress stays on the drawn canvas', async ({ page }) => {
  const photos = [];
  page.on('request', (request) => { if (/\/photo\.webp(?:\?|$)/.test(request.url())) photos.push(request.url()); });
  await page.emulateMedia({ reducedMotion: 'reduce' }); await ready(page);
  for (const amount of [0, 170, 220, 310, 520, 740, 1000, 350, 0]) {
    await resolve(page, amount);
    await expect(page.locator('canvas')).toBeVisible();
    await expect(page.locator('canvas')).toHaveCSS('opacity', '1');
  }
  expect(photos).toEqual([]);
});

test('finished GPU stroke composition matches the static drawing fallback', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' }); await ready(page);
  const meanError = await page.evaluate(async () => {
    const range = document.querySelector('#resolve');
    range.value = '1000'; range.dispatchEvent(new Event('input', { bubbles: true }));
    const canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl');
    const pixels = new Uint8Array(canvas.width * canvas.height * 4);
    // Read in the same task as rendering; drawing buffers need not be preserved.
    gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    const reference = document.createElement('canvas'); reference.width = canvas.width; reference.height = canvas.height;
    const ctx = reference.getContext('2d');
    const image = document.querySelector('#managed-photo');
    const style = getComputedStyle(image).objectPosition.split(' ').map(parseFloat);
    const scale = Math.max(canvas.width / image.naturalWidth, canvas.height / image.naturalHeight);
    const w = image.naturalWidth * scale, h = image.naturalHeight * scale;
    ctx.drawImage(image, (canvas.width - w) * style[0] / 100, (canvas.height - h) * style[1] / 100, w, h);
    const expected = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
    let error = 0, count = 0;
    for (let y = 0; y < canvas.height; y += 5) {
      for (let x = 0; x < canvas.width; x += 5) {
        const actualIndex = ((canvas.height - y - 1) * canvas.width + x) * 4;
        const expectedIndex = (y * canvas.width + x) * 4;
        for (let c = 0; c < 3; c++) { error += Math.abs(pixels[actualIndex + c] - expected[expectedIndex + c]); count++; }
      }
    }
    return error / count;
  });
  // Compositing filtered translucent layers differs slightly from filtering
  // their precomposited fallback; large registration/color failures do not.
  expect(meanError).toBeLessThan(5);
});

test('capture visible stroke growth and reversal', async ({ page }, testInfo) => {
  await page.emulateMedia({ reducedMotion: 'reduce' }); await ready(page);
  for (const amount of [140, 170, 200, 230, 260, 290, 320, 290, 260, 230]) {
    await resolve(page, amount); await page.locator('#resolve').blur();
    await page.screenshot({ path: testInfo.outputPath(`stroke-${amount}-${Date.now()}.png`) });
  }
});

test('structural sketch keeps growing before color and pigment develops late', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' }); await ready(page);
  const stages = await page.evaluate(() => {
    const input = document.querySelector('#resolve'), canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl');
    return [150, 300, 450, 600, 900, 1000].map((value) => {
      input.value = String(value); input.dispatchEvent(new Event('input', { bubbles: true }));
      const pixels = new Uint8Array(canvas.width * canvas.height * 4);
      gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      let ink = 0, chroma = 0;
      for (let i = 0; i < pixels.length; i += 16) {
        const rgb = [pixels[i], pixels[i + 1], pixels[i + 2]];
        ink += Math.max(0, 238 - (rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722));
        // Ivory's own warm tint is not pigment.
        chroma += Math.max(0, Math.max(...rgb) - Math.min(...rgb) - 15);
      }
      return { value, ink, chroma };
    });
  });
  expect(stages[1].ink).toBeGreaterThan(stages[0].ink * 1.2);
  expect(stages[2].ink).toBeGreaterThan(stages[1].ink * 1.15);
  expect(stages[0].chroma + stages[1].chroma + stages[2].chroma).toBe(0);
  expect(stages[3].chroma).toBe(0);
  expect(stages[5].chroma).toBeGreaterThan(stages[4].chroma * 1.1);
});
