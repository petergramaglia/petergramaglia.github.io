# Peter Gramaglia — Resolve

An interactive field study: drag the landscape or use the tuning scale to move from an engraved drawing to a photograph. The homepage is a buildless static site hosted on GitHub Pages. Existing résumé URLs are retained.

## Preview

From this directory:

```sh
python3 -m http.server 4173 --bind 127.0.0.1
```

Open `http://127.0.0.1:4173`. The published site requires no package installation or build step. Use an HTTP server rather than `file://` for ES modules and image requests.

## Checks

Node 20 or newer:

```sh
npm ci
npm test
npm run test:browser
```

The browser suite uses an installed Google Chrome by default. For Playwright-managed Chromium:

```sh
npx playwright install chromium
PLAYWRIGHT_CHANNEL=chromium npm run test:browser
```

Tests cover real WebGL initialization, keyboard and pointer input, cancellation, responsive swaps and cached returns, About focus, no-JS/module/graphics/image failures, reduced motion, and short/narrow layouts. Screenshots at five resolve values and mobile/short layouts are saved under ignored `test-results/`. `@playwright/test` is a development dependency only; the deployed page uses no runtime libraries or third-party network services.

## Design and implementation

The detailed [implementation plan](docs/resolve-plan.md) includes the initial brief and revisions from three independent GPT-6 Astra plan reviewers. [Review notes](docs/review-notes.md) record code review findings and validation.

- `index.html`, `styles/site.css`: real HTML controls, biography, progressive photo fallback.
- `src/renderer.js`, `src/shaders.js`: WebGL compositing, transactional texture changes, bounded resource allocation and cleanup.
- `src/composition.js`: shared canvas/photo cover crop, prioritizing the climber on extreme aspect ratios.
- `src/interaction.js`, `src/main.js`: direct manipulation, frame-independent damping, lifecycle, reduced motion.
- `src/about.js`: progressive native modal; biography remains ordinary HTML without JavaScript.
- `assets/`: precomputed aligned photo/drawing/control textures, manifest, and favicon.

There are two aspect-specific image sets. The desktop composition uses Peter's approved AI-expanded panorama, with the left ridge corrected against a second reference photograph. Mobile uses the original portrait photograph. Generated edges are disclosed in About. Contour-like marks are an artistic drawing, not elevation data. No coordinates, EXIF, or camera/location metadata are retained in the published derivatives.

At full resolve, the exact optimized photo derivative is displayed as an HTML image. At other settings a shader combines the ink drawing, regional tone/shading, and photographic color. Navigation legibility shading is separate from both layers. On graphics failure the current complete photograph remains usable. No continuous animation runs after the control settles; reduced motion disables easing and displacement.

### Regenerating assets

Generated files are checked in; this is optional authoring work, not a deployment step. Source photographs remain outside the repository.

```sh
python3 -m venv /tmp/resolve-assets-env
/tmp/resolve-assets-env/bin/pip install Pillow numpy scipy
/tmp/resolve-assets-env/bin/python scripts/prepare-assets.py --help
```

Pass `--desktop` and `--mobile` with source-image paths as described by `--help`. The pipeline bakes orientation, normalizes color to sRGB, strips metadata, authors ridge/contour strokes, and produces small aligned control maps. Inspect output and checkpoint previews whenever changing image inputs or drawing parameters; these anchors are specific to this landscape.

## Limits

The portrait and desktop variants are different compositions, so rotating a device intentionally changes framing. Very short wide windows prioritize the climber and may crop the peak or sky. A screen reader receives a persistent scene description and a labeled native range input. Contact links to Peter's existing LinkedIn; the site does not invent an email address or current employment biography.
