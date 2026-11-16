# Resolve: implementation and review plan

## Brief and delivery

Replace the personal site's homepage with one full-viewport interactive field study. The approved desktop landscape is `IMG_8746-desktop-expanded-v2.png`; mobile uses the original `IMG_8746.HEIC`, converted to JPEG. Desktop mountains terminate in the descending left ridge approved by Peter. Preserve existing resume URLs and assets. Deliver one PR against `master`; do not merge or deploy separately.

The experience must communicate taste through composition and direct manipulation, with minimal biography. No invented current employer, location, contact email, geographic labels, elevations, or personal claims. Use existing LinkedIn as Contact. About can name software/AI and mountain interests and describe previously documented work in the past tense. Include a discreet image credit explaining the expanded desktop edges.

## Proposed architecture

Buildless HTML, CSS, ES modules, WebGL (a full-screen quad, not a 3D world). No runtime dependencies, external fonts, server, analytics, or API keys. A normal HTML picture is the reliable underlying photograph. Canvas is an aria-hidden visual enhancement. HTML navigation, About content, and range input remain usable independently.

Files: `index.html`, `styles/site.css`, `src/main.js`, `src/renderer.js`, `src/interaction.js`, `src/composition.js`, `src/math.js`, `src/shaders.js`, `assets/{desktop,mobile}/`, `scripts/prepare-assets.py`, `tests/`, and README. Preserve legacy files.

## Art direction

- Full bleed landscape, no image margins. Ivory drawing ground, blue-black ink, restrained vermilion indicator.
- Quiet name upper left, About upper right. Tuning scale bottom center. Field-study label and Contact at lower corners.
- Native sans serif for name and text; native monospace for small scale labels. No fake telemetry or dashboard ornaments.
- About is a compact ivory dialog/panel over the artwork, with a close button, focus containment, Escape support, and return focus. With no JavaScript, readable About remains accessible via an anchor.
- UI contrast is designed deliberately, with local translucent surfaces/shading where needed; avoid relying on blend-mode alone.

## Source assets and derivative pipeline

Keep original user files untouched. Copy optimized photo derivatives into repo. Strip EXIF/location metadata during conversion. Target roughly <= 1 MB desktop photograph and <= 600 KB mobile; select actual encoder sizes after inspection. Do not upscale beyond available source detail.

Each aspect has aligned photo and field-map assets generated offline. Asset prep uses Pillow/NumPy (optional SciPy if genuinely necessary), not a browser/runtime image model. Record commands and input roles; source paths configurable, not hardcoded personal filesystem paths. Check in generated assets so the deployed site requires no Python build.

The field map is code-generated from luminance, multiscale smoothing, and manually selected skyline/ridge anchors. Use a compact RGB map: broad tonal field, terrain mask, and fine edge/detail field. Explicit sky/terrain silhouette keeps sky mostly blank and protects the corrected skyline. Region-based stroke spacing plus authored ridge curves provide an engraved surface. Approximate climber region suppresses distracting high-frequency line detail and delays photograph detail, with generous feathering to avoid a cutout. Do not claim a true height/depth map.

Major ridge anchors are normalized to source-image coordinates and reviewed visually at the opening state. No independent AI-regenerated drawing that can drift from the photograph. Shader samples every map and photograph using the exact same crop transform.

## Resolve behavior

Single normalized value p in [0,1]. Initial p approximately 0.12.

1. 0–0.20: sparse contour-like field on ivory, aligned recognizable skyline, small bounded irregularity.
2. 0.20–0.45: finer structure becomes clearer and offsets settle.
3. 0.45–0.70: photographic shading emerges; color begins.
4. 0.70–0.90: color and climber details resolve; line opacity drops.
5. 0.90–1.00: final transition to exact source photograph, zero displacement at endpoint.

These intervals overlap through smoothstep functions. No full-page blur, scroll hijacking, automatic reveal, continuous ambient animation, or obligatory sound. Ensure p=0, .25, .5, .75, 1 all make deliberate, coherent compositions.

Renderer uses one quad and one fragment shader, at most three small textures, linear filtering and clamp-to-edge. Precompute expensive image analysis offline. Deterministic noise in shader is only tiny drawing irregularity; do not let it turn terrain into generic waves. Major skyline and light/dark zones should stay recognizable.

## Input and state

- Drag horizontally on artwork changes target p relative to starting p and gesture distance. No jump to absolute pointer position.
- Native range input offers direct p control, keyboard arrows/Home/End, associated label and meaningful aria-valuetext (e.g. '50 percent resolved'). Native range remains the focusable, hit-testable control; visible ticks are decoration.
- Pointer capture, one active pointer, cancellation/lost-capture handling. Exclude navigation/dialog/form controls from drag handling. Use horizontal drag with `touch-action: pan-y pinch-zoom`; do not block pinch zoom globally.
- Frame-rate-independent easing: `1 - exp(-12 * dt)` toward target. Optional tiny velocity displacement, capped and zero at settled endpoints. No oscillating spring, mandatory snap or detents in v1.
- Stop requestAnimationFrame when settled; restart for input/resize. Pause when tab hidden and About open; reset timing on resume.
- Reduced motion removes easing and displacement, renders directly on input, still permits manual resolve. Listen for preference changes.

## Responsive composition

Choose portrait assets for portrait-oriented viewports, wide assets for landscape. Maintain source aspect metadata and compute cover UV transform. Use common focal coordinates and safe region to keep climber and central peak visible; center the photo horizontally and tune vertical alignment for shorter screens. Keep canvas and HTML fallback crop identical.

Controls respect safe-area insets and short-height layouts; no clipping at 320 px width, 200% zoom, mobile landscape, or tall phones. Dialog gets its own scrollable region. On viewport variant change, keep old complete asset set visible until new pair is ready; apply one atomic swap. Guard stale async loads with generation IDs. Resize uses ResizeObserver/window events and DPR capped initially at 1.5 (bounded by max pixel budget). Handle orientation changes without refetching already-loaded assets.

## Loading and failure behavior

HTML photograph and functioning links present before JS. Hide inert tuning UI until renderer ready. On success, show opening drawing and tuning control. Prefer minimal paint flash by initial ivory overlay with bounded timeout only if this remains robust with failed JS; otherwise accept photo-first progressive enhancement.

If WebGL unavailable, shader compile fails, assets fail, or context is lost: show static photo, hide tuning UI, keep About and Contact usable. No infinite spinner or blocking error. Log concise diagnostic to console for developer troubleshooting, no implementation details in product flow. Texture fetch CORS is same-origin. On recoverable context restore, reinitialize safely or remain on reliable static fallback.

## Verification

Use Node built-in tests for nontrivial math/crop invariants and frame-rate-independent interpolation. Add static checks for local asset references, image dimensions/pair alignment, duplicate IDs, valid module syntax, no missing required copy, and no token/source metadata leakage. Add real browser checks when supported: shader compiles; opening and all five checkpoints look coherent; range keyboard works; drag works/cancels; About focus/Escape; no-js/WebGL failure; reduced motion; tab sleep; portrait/landscape switch; 320px and wide desktop.

Use the installed browser skill for browser QA, read local preview guidance first. If infrastructure fails, report exact verification limitation; do not claim visual/browser approval based on static tests. Review rendered textures offline to catch image-processing problems even if browser unavailable.

## Review gates and implementation stages

Before code: three GPT-6 Astra reviewers (high reasoning), covering (1) visual/interaction fit, (2) rendering/assets/performance, (3) accessibility/reliability/testing. Each returns approve or requested changes. Integrate changes into this plan and request re-review until no blockers.

Implement sequentially: shell/assets -> render -> interaction/fallback -> tests and polish. Parallel agent coding is optional; primary owns integration. Post-implementation use a separate set of three GPT-6 Astra reviews for (1) rendering/correctness, (2) accessibility/UX, (3) security/performance/repo integration. Reviewers inspect actual diff and tests, identify concrete blockers with file references, and give explicit verdicts. Resolve findings and get re-review before PR completion.

PR includes behavior, art/asset provenance, test results, browser verification limits, screenshots if available, and remaining material risks. Do not merge. No new deployment target or hosting registration.

## Review resolution: concrete rendering contract (supersedes earlier tentative map packing)

Plan design and accessibility reviewers approved. Rendering reviewer requested these specifications before code:

1. Three aligned textures per variant: sRGB photograph; opaque ivory-and-ink drawing; RGB control map with R=terrain mask, G=feathered climber region, B=smoothed tonal field. Generate the drawing offline at 2x output resolution and downsample for antialiased ink. Manually authored normalized skyline and major ridge polylines are smoothed, rasterized, and used as boundaries for intervening contour strokes. Interpolate between neighboring ridge boundaries with small smoothed-luminance offsets, suppress detail in sky and reduce drawing density around climber without making a blank patch. Draw major boundaries with slightly more weight. This is an image-aligned engraved illustration, not elevation contours. GPU shader uses sampled drawing and tone/region map to reveal photographic shading and color at different times, plus bounded drawing-only displacement. Precomputed ink avoids WebGL derivative/line antialiasing ambiguity. Use WebGL1-compatible shader and LINEAR filtering. Review offline opening and five transition renders at asset stage before interaction work; revise if waves/noisy outlines dominate.

2. Each variant owns dimensions, focal point, peak/subject bounds and ridge anchors. EXIF-transpose then convert ICC to sRGB before stripping metadata. Desktop stays <=1672x941; portrait <=1200x1600. Control maps <=source dimensions, initially half resolution if visually adequate. Drawing same dimensions as photo. The live canvas crop and managed fallback image use one shared cover calculation and object-position. Before enhancement, native picture works independently; after enhancement, use a separate managed photo element committed in the same transaction as textures/crop/variant. Hide the initial picture only once a complete enhanced set is ready. If a swap fails, retain current complete set or static current managed photo. At extreme ratios, prioritize the person and accept cropping peripheral sky/rocks; do not distort.

3. Drawing buffer max 2,500,000 pixels, max DPR 1.5, and each axis clamped to device MAX_RENDERBUFFER_SIZE/MAX_VIEWPORT_DIMS. Validate image dimensions against MAX_TEXTURE_SIZE; unsupported image sizes cause static fallback. Cache at most desktop+mobile decoded asset sets (~38 MB max RGBA for all textures at stated limits, usually less), upload only active set. Use abortable fetch+decoded images with explicit release; decoded bitmap.close() on eviction/disposal; revoke any object URLs. Transaction upload deletes partial GPU resources on failure and deletes superseded textures on successful commit. Stale loads release acquired resources. Dispose aborts fetches and releases cache, active textures, program, quad buffer, observers, listeners, and pending RAF. Context loss invokes terminal safe fallback and invalidates async generation rather than guessing at restoration.

4. Use top-origin UV throughout: fullscreen quad computes v=0 at screen top, uploads HTML/bitmap pixels without vertical flip; avoid premultiplied-alpha image ambiguity through opaque assets. All photographic derivatives are sRGB with baked orientation and shared by canvas/managed HTML image. At settled p=1, expose the managed HTML photograph and hide canvas, eliminating a persistent shader color difference. Near endpoint shader returns unmodified photograph; verify handoff if browser works. Failures reveal the same managed image. No photographic filters applied at endpoint.

5. About enhancement is independent and fail-open. Range reports target value, renderer follows it. Reduced motion toggled mid-ease settles immediately. Pinch/second pointer cancels art drag; lifecycle and dialog events cancel active capture. Add nested-path static hosting check. Opening-state user hint remains visible until first successful input. Credit goes inside About.
