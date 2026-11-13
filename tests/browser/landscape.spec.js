import { test, expect } from '@playwright/test';
const ready = async (page) => {
  await page.goto('/');
  await expect(page.locator('#field')).toHaveAttribute('data-renderer', 'ready');
};
const resolve = async (page, value) => {
  await page.locator('#resolve').fill(String(value));
  await expect(page.locator('#resolve')).toHaveAttribute('aria-valuetext', `${Math.round(value / 10)} percent drawn`);
};

test('preview revalidates old documents and loads versioned drawing assets', async ({ page, request }) => {
  const conditional = await request.get('/assets/desktop/time1.png', {
    headers: { 'If-Modified-Since': 'Thu, 31 Dec 2099 23:59:59 GMT', 'If-None-Match': 'old-drawing' },
  });
  expect(conditional.status()).toBe(200);
  expect(conditional.headers()['cache-control']).toBe('no-store');
  const manifest = await (await request.get('/assets/manifest.json')).json();
  const loaded = new Map();
  page.on('response', (response) => {
    const url = new URL(response.url());
    if (url.pathname.startsWith('/assets/desktop/')) loaded.set(url.pathname.split('/').at(-1), url.searchParams.get('v'));
  });
  await ready(page);
  for (const [file, revision] of Object.entries(manifest.desktop.revisions)) expect(loaded.get(file), file).toBe(revision);
  const document = await page.reload();
  expect(document.headers()['cache-control']).toBe('no-store');
  await expect(page.locator('#field')).toHaveAttribute('data-renderer', 'ready');
});

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
  await page.route('**/time2.png?*', (route) => route.abort());
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
  for (const p of [0, 150, 200, 250, 300, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 990, 1000]) {
    await resolve(page, p);
    await page.locator('#resolve').blur();
    await page.screenshot({ path: testInfo.outputPath(`desktop-${p}.png`) });
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('#field')).toHaveAttribute('data-variant', 'mobile');
  await resolve(page, 0); await page.locator('#resolve').blur();
  await page.screenshot({ path: testInfo.outputPath('mobile-drawing.png') });
  for (const p of [200, 400, 600]) {
    await resolve(page, p); await page.locator('#resolve').blur();
    await page.screenshot({ path: testInfo.outputPath(`mobile-${p}.png`) });
  }
  await resolve(page, 1000); await page.locator('#resolve').blur();
  await page.screenshot({ path: testInfo.outputPath('mobile-finished.png') });
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
  await page.route('**/mobile/time2.png?*', (route) => route.abort());
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
  for (const amount of [140, 170, 200, 230, 260, 290, 320, 290, 260, 230, 550, 560, 570, 580, 590, 580, 570]) {
    await resolve(page, amount); await page.locator('#resolve').blur();
    await page.screenshot({ path: testInfo.outputPath(`stroke-${amount}-${Date.now()}.png`) });
  }
});

test('mountain framework precedes the figure and foreground, then detail and color', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  for (const [width, height, regions] of [
    [1440, 810, { mountain: [0, .32, 1, .67], figure: [.455, .715, .54, .86], foreground: [0, .86, 1, .99], clouds: [.55, .1, 1, .3] }],
    [900, 1200, { mountain: [0, .30, 1, .625], figure: [.40, .67, .58, .80], foreground: [0, .82, 1, .99], clouds: [.5, .1, 1, .28] }],
  ]) {
    await page.setViewportSize({ width, height }); await ready(page);
    const stages = await page.evaluate((regions) => {
      const input = document.querySelector('#resolve'), canvas = document.querySelector('canvas');
      const gl = canvas.getContext('webgl');
      return Object.fromEntries([200, 400, 450, 600].map((value) => {
        input.value = String(value); input.dispatchEvent(new Event('input', { bubbles: true }));
        const pixels = new Uint8Array(canvas.width * canvas.height * 4);
        gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
        let chroma = 0;
        for (let i = 0; i < pixels.length; i += 16) {
          chroma += Math.max(0, Math.max(pixels[i], pixels[i + 1], pixels[i + 2]) - Math.min(pixels[i], pixels[i + 1], pixels[i + 2]) - 15);
        }
        const ink = Object.fromEntries(Object.entries(regions).map(([name, [x0, y0, x1, y1]]) => {
          let mass = 0;
          for (let y = Math.floor(y0 * canvas.height); y < y1 * canvas.height; y += 2) {
            for (let x = Math.floor(x0 * canvas.width); x < x1 * canvas.width; x += 2) {
              const i = ((canvas.height - y - 1) * canvas.width + x) * 4;
              mass += Math.max(0, 238 - (pixels[i] * .2126 + pixels[i + 1] * .7152 + pixels[i + 2] * .0722));
            }
          }
          return [name, mass];
        }));
        return [value, { ...ink, chroma }];
      }));
    }, regions);
    expect(stages[200].mountain).toBeGreaterThan(100);
    expect(stages[200].figure).toBe(0);
    expect(stages[200].foreground).toBe(0);
    expect(stages[400].figure).toBeGreaterThan(100);
    expect(stages[400].foreground).toBeGreaterThan(100);
    expect(stages[400].clouds).toBe(0);
    expect(stages[450].mountain).toBeGreaterThan(stages[400].mountain);
    expect(stages[200].chroma + stages[400].chroma + stages[450].chroma).toBe(0);
    expect(stages[600].chroma).toBeGreaterThan(0);
  }
});

test('early pigment follows photographic cliff edges instead of old construction bands', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 810 });
  await page.emulateMedia({ reducedMotion: 'reduce' }); await ready(page);
  const stages = await page.evaluate(() => {
    const input = document.querySelector('#resolve'), canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl');
    // Landmarks inspected on the 1672×941 source photograph, independently
    // of the generated guides: real cliff tops/perimeters and two old guides
    // that crossed featureless interiors. Never sample UI text or controls.
    const landmarks = { cragTop: [743, 466], litCliffEdge: [353, 547],
      oldCrossFaceLine: [700, 510], oldForegroundBand: [350, 734] };
    return Object.fromEntries([550, 650].map((value) => {
      input.value = String(value); input.dispatchEvent(new Event('input', { bubbles: true }));
      const pixels = new Uint8Array(canvas.width * canvas.height * 4);
      gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      return [value, Object.fromEntries(Object.entries(landmarks).map(([name, [sx, sy]]) => {
        const cx = Math.round(sx / 1672 * canvas.width), cy = Math.round(sy / 941 * canvas.height);
        let pigment = 0;
        for (let y = cy - 5; y <= cy + 5; y++) for (let x = cx - 5; x <= cx + 5; x++) {
          const i = ((canvas.height - y - 1) * canvas.width + x) * 4;
          pigment += Math.max(0, Math.abs(3 * pixels[i] - 4 * pixels[i + 1] + pixels[i + 2]) - 5);
        }
        return [name, pigment];
      }))];
    }));
  });
  expect(stages[550].cragTop).toBeGreaterThan(50);
  expect(stages[550].litCliffEdge).toBeGreaterThan(50);
  expect(stages[650].oldCrossFaceLine).toBe(0);
  expect(stages[650].oldForegroundBand).toBe(0);
});

test('color follows ridges, human and foreground edges, then surface fill and sky', async ({ page }, testInfo) => {
  // Match the desktop artwork aspect ratio so source landmarks map directly
  // to GPU pixels, independently of the UI or responsive crop behavior.
  await page.setViewportSize({ width: 1440, height: 810 });
  await page.emulateMedia({ reducedMotion: 'reduce' }); await ready(page);
  const stages = await page.evaluate(() => {
    const input = document.querySelector('#resolve'), canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl');
    const regions = {
      mountain: [.20, .43, .35, .66], figure: [.46, .69, .53, .85],
      foreground: [.60, .80, .92, .97], distant: [.82, .44, .97, .58],
      clouds: [.55, .12, .98, .33], sky: [.10, .02, .55, .16],
    };
    const samples = [450, 550, 650, 700, 800, 850, 900, 950, 990, 1000].map((value) => {
      input.value = String(value); input.dispatchEvent(new Event('input', { bubbles: true }));
      const pixels = new Uint8Array(canvas.width * canvas.height * 4);
      gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      const colors = Object.fromEntries(Object.entries(regions).map(([name, [x0, y0, x1, y1]]) => {
        const result = [];
        for (let y = Math.floor(y0 * canvas.height); y < y1 * canvas.height; y += 4) {
          for (let x = Math.floor(x0 * canvas.width); x < x1 * canvas.width; x += 4) {
            const i = ((canvas.height - y - 1) * canvas.width + x) * 4;
            result.push([pixels[i], pixels[i + 1], pixels[i + 2]]);
          }
        }
        return [name, result];
      }));
      return { value, colors };
    });
    const start = samples[0].colors, end = samples.at(-1).colors;
    // Measure closeness to the approved finished painting, normalized against
    // the pencil stage. Exclude blue pixels from the cloud-bank rectangle.
    return Object.fromEntries(samples.map(({ value, colors }) => [value, Object.fromEntries(
      Object.keys(regions).map((name) => {
        let remaining = 0, total = 0, pigment = 0, finalPigment = 0;
        end[name].forEach((pixel, i) => {
          if (name === 'clouds' && pixel[2] - pixel[0] >= 45) return;
          // Pencil gray mixed with ivory lies on 3R−4G+B=0. Measure
          // pigment off that axis, allowing for byte-rounding noise.
          const color = colors[name][i];
          pigment += Math.max(0, Math.abs(3 * color[0] - 4 * color[1] + color[2]) - 5);
          finalPigment += Math.max(0, Math.abs(3 * pixel[0] - 4 * pixel[1] + pixel[2]) - 5);
          for (let c = 0; c < 3; c++) {
            remaining += Math.abs(colors[name][i][c] - pixel[c]);
            total += Math.abs(start[name][i][c] - pixel[c]);
          }
        });
        return [name, { completion: 1 - remaining / total, pigment: pigment / finalPigment }];
      })
    )]));
  });
  await testInfo.attach('regional-progression.json', { body: JSON.stringify(stages, null, 2), contentType: 'application/json' });
  // The first colored marks belong to mountain structure, not the figure
  // or foreground. Their limited coverage must not fill the mountain face.
  expect(stages[550].mountain.pigment).toBeGreaterThan(.005);
  expect(stages[550].mountain.pigment).toBeLessThan(.3);
  expect(stages[550].figure.pigment).toBe(0);
  expect(stages[550].foreground.pigment).toBe(0);
  // Human and foreground acquire colored edges while their interiors wait.
  for (const region of ['figure', 'foreground']) {
    expect(stages[650][region].pigment).toBeGreaterThan(.005);
    expect(stages[650][region].pigment).toBeLessThan(.55);
    expect(stages[900][region].completion).toBeGreaterThan(.9);
  }
  expect(stages[650].mountain.pigment).toBeLessThan(.4);
  expect(stages[800].mountain.pigment).toBeGreaterThan(stages[650].mountain.pigment + .3);
  expect(stages[700].clouds.pigment).toBe(0);
  expect(stages[850].sky.pigment).toBeLessThan(.1);
  expect(stages[900].distant.completion).toBeGreaterThan(.9);
  expect(stages[900].clouds.completion).toBeGreaterThan(.8);
  expect(stages[900].sky.completion).toBeLessThan(.6);
  expect(stages[990].sky.completion).toBeGreaterThan(.95);
});
