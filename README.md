# Peter Gramaglia — Resolve

An interactive field study: drag the landscape or use the tuning scale to draw it, from a loose sketch to a painting built from tapered colored brushstrokes. The homepage is a buildless static site hosted on GitHub Pages. Existing résumé URLs are retained.

## Preview

From this directory:

```sh
python3 scripts/preview.py
```

Open `http://localhost:4173` (`npm run preview` starts the same server). The preview disables browser caching for HTML, modules, and artwork. Reload after edits; an already open canvas retains its decoded drawing until reloaded. The published site requires no package installation or build step. Use an HTTP server rather than `file://` for ES modules and image requests.

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

Tests cover real WebGL initialization, keyboard and pointer input, cancellation, responsive swaps and cached returns, About focus, no-JS/module/graphics/image failures, reduced motion, and short/narrow layouts. A GPU regression checks that key terrain precedes clouds and that blue sky finishes last. Screenshots across the drawing stages and mobile/short layouts are saved under ignored `test-results/`. `@playwright/test` is a development dependency only; the deployed page uses no runtime libraries or third-party network services.

## Design and implementation

The [stroke revision](docs/stroke-revision.md) describes the current drawing behavior. The [initial implementation plan](docs/resolve-plan.md) records the earlier photo-reveal direction and its three independent GPT-6 Astra plan reviews. [Review notes](docs/review-notes.md) record code review findings and validation.

- `index.html`, `styles/site.css`: real HTML controls, biography, progressive finished-drawing fallback.
- `src/renderer.js`, `src/shaders.js`: WebGL compositing, transactional texture changes, bounded resource allocation and cleanup.
- `src/composition.js`: shared canvas/fallback cover crop, prioritizing the climber on extreme aspect ratios.
- `src/interaction.js`, `src/main.js`: direct manipulation, frame-independent damping, lifecycle, reduced motion.
- `src/about.js`: progressive native modal; biography remains ordinary HTML without JavaScript.
- `assets/`: three timed stroke layers per composition, finished-drawing fallbacks, source photographs, manifest, and favicon.
- `scripts/source_features.py`: separate photographic crest, cliff, boulder, and human contours, registered to source edges for the opening sketch and first colored strokes.

There are two aspect-specific drawing sets. The desktop composition uses Peter's approved AI-expanded panorama, with the left ridge corrected against a second reference photograph. The mobile drawing is based on the original portrait photograph. Generated edges are disclosed in About. Contour-like marks are an artistic drawing, not elevation data. No coordinates, EXIF, or camera/location metadata are retained in the published derivatives.

At every slider position, the artwork consists of drawn strokes on ivory. Each stroke has a per-pixel arrival time that increases along its path. Major peaks and ridges appear first, followed by the rough human silhouette and foreground boundaries. Color repeats that hierarchy: ridge strokes first, human and foreground edge strokes next, then surface fill and finer detail. Distant mountains and clouds develop afterward; blue sky finishes last. Opacity and pigment mature relative to each stroke's own arrival, so already painted regions stay complete while later regions remain sketched. At full progress the canvas remains a colored drawing. No source photograph is loaded at runtime. The static fallback is the finished drawing, composited from the same delivered stroke plates. Unboxed typography uses a narrow ivory glyph halo for contrast; the visible control contains only the slider and its number. No continuous animation runs after the control settles; reduced motion removes easing while preserving direct control.

### Regenerating assets

Generated files are checked in; this is optional authoring work, not a deployment step. Original full-resolution source files remain outside the repository.

```sh
python3 -m venv /tmp/resolve-assets-env
/tmp/resolve-assets-env/bin/pip install Pillow numpy scipy
/tmp/resolve-assets-env/bin/python scripts/prepare-strokes.py
```

The stroke generator samples the checked-in `assets/{desktop,mobile}/photo.webp` authoring inputs, writes lossless RGBA ink plates and PNG timing maps, and produces `/tmp/resolve-stages-preview.jpg` for art review. `prepare-assets.py` retains the original source-normalization helpers and ridge geometry used by the stroke generator; it belongs to the first iteration and is not a deployment step. Inspect stroke growth and all checkpoints whenever changing inputs or parameters; the geometry is specific to this landscape.

The generator also records content hashes for every delivered image in the manifest. Runtime image URLs use those revisions; the manifest is fetched without caching. If editing an asset outside the generator, run `python3 scripts/asset_revisions.py` afterward. The static checks reject outdated hashes. Finish asset generation before previewing or deploying a revision.

Structural features use anchors in each source photograph's native pixel coordinates. A narrow search follows coherent image edges between those anchors. Separate cliff crests terminate at their visible ends; foreground structure uses individual rock outlines, without full-width construction bands. Run the asset environment's Python on `scripts/source_features.py` to produce photo-registration overlays under `/tmp/resolve-source-features/`. Review those overlays as well as rendered stages when changing a feature: a strong image gradient alone does not establish that a path represents the intended landform.

## Limits

The portrait and desktop variants are different compositions, so rotating a device intentionally changes framing. Very short wide windows prioritize the climber and may crop the peak or sky. A screen reader receives a persistent scene description and a labeled native range input. Contact links to Peter's existing LinkedIn; the site does not invent an email address or current employment biography.
