# Field study review and validation

The original photo-reveal implementation below is historical. The current stroke-drawing revision is recorded at the end of this document and in `stroke-revision.md`.

## Plan review

Three GPT-6 Astra reviewers, each at high reasoning effort, independently reviewed `resolve-plan.md` before implementation:

- Design and interaction: approved; incorporated per-variant framing, a visible drag hint, and keeping controls below the climber.
- Rendering and assets: initially requested a concrete ink/map contract, atomic fallback behavior, resource limits, and exact-photo endpoint. The revised contract was approved before implementation started.
- Accessibility and reliability: approved; incorporated fail-open About, native range semantics, gesture interruption, reduced-motion changes, and nested-path checking.

## Independent code review

A separate team of three GPT-6 Astra reviewers, each at high reasoning effort, inspected the implementation:

- Rendering/correctness: approved after adding subject-and-peak-aware shared crops and a bounded decoded-image cache. A further revision relaxed crop margins to retain both subjects when possible. Both changes have regression tests.
- Accessibility/UX: approved after increasing navigation contrast. The reviewer measured refreshed desktop About backgrounds at approximately 6.7–7.8:1 against white text. A persistent scene description and gesture-cancellation coverage were also added.
- Integration/security/performance: approved, including the read-only CI workflow. Independently checked derivative dimensions and metadata, nested-path resource requests, local-only runtime requests, cache ownership, syntax, and diff formatting.

No reviewer found remaining blocking issues at handoff. Agent review does not replace real-device testing.

## Executed validation

- 8 Node tests: temporal interpolation, pixel budgets, cover registration, subject/peak retention, local references, unique IDs, generated assets, and legacy resume preservation.
- 13 browser tests in installed Google Chrome on macOS: real WebGL shader initialization; keyboard endpoints and reverse dragging; About focus containment/Escape; rapid orientation switching; runtime reduced motion; missing-image fallback; graphics-context loss; no JavaScript; module failure; WebGL denial; failed variant swap; narrow/short/ultrawide layouts; cached orientation return under network failure; pointer and second-contact cancellation. One test captures the five desktop resolve states and mobile states for visual review.
- Inspected actual browser screenshots and offline asset checkpoints; refined foreground line density and ridge weight.
- Independent HTTP checks successfully fetched 18 resources below a nested path.
- Binary asset inspection verified aligned dimensions and absence of EXIF/XMP/ICC/text metadata in the published photo, drawing, and control derivatives.

The in-app browser connector was unavailable due to a connection/runtime error. Browser validation instead used the repository's isolated headless Chrome test runner. No Safari, Firefox, physical touchscreen, or assistive-technology session was run. Pointer tests exercise browser events, not real device gestures. GitHub Actions runs the committed suite in Chromium on Linux when the PR opens; its result is separate from local checks.

## Implementation notes

The approved panorama's added edges are AI-generated and disclosed in About. Original user source images remain outside the repository; derivatives and the code-based drawing generator are committed. The line treatment is illustrative, not topography. Resume URLs are preserved, but the homepage does not promote an old student-era resume as current work.

The final photo is deliberately handed to the HTML image at full resolve. A separate navigation gradient remains for legibility. Extremely short windows may crop the summit when keeping both summit and climber is geometrically impossible; the climber takes priority and the tuner moves to the right.

## Current revision: stroke growth into a colored drawing

Peter requested that the slider build an increasingly refined and saturated drawing instead of fading into a photograph. `stroke-revision.md` documents the replacement rendering contract. The source photos now serve only as authoring inputs; every runtime state and fallback is drawn.

- Astra high approach review approved the per-stroke timing design, requiring full endpoint coverage, lossless timing with filtered-edge gutters, visible moving tips, memory bounds, and a matching drawn fallback.
- Separate Astra high rendering and integration reviewers approved the six-texture renderer, persistent canvas endpoint, cache/disposal behavior, asset metadata/dimensions, and regenerated-manifest synchronization. Their requested lossless atlas encoding and memory-accounting corrections were implemented.
- Astra high visual review inspected actual browser images at the five main checkpoints and successive forward/reverse positions. It confirmed lengthening/retracting marks, directional hatching, and recognizable blue/gold light. The result reads as a dense colored engraving; sky and figure are intentionally softer.
- Astra high accessibility review approved updated drawing semantics and screenshot contrast. A small additional bottom-gradient increase gives Contact more contrast over pale paper gaps.

Validation: 8 Node tests and 16 local Chrome browser tests pass. Added assertions cover zero runtime source-photo requests, a visible drawn canvas at the endpoint, and agreement between the GPU composition and the precomposited drawing fallback. Forward/reverse screenshot sequences supplement those checks. All previous interaction and failure-path tests now use the drawing assets. The 14 new published drawing assets are lossless, metadata-free, and aligned at 1440×810 or 900×1200; they total approximately 6.98 MiB across both variants. Only the active variant loads initially.

Safari, Firefox, physical touch hardware, and assistive technology remain untested. GitHub Actions validation is reported by the PR checks for the corresponding commit.

## Pacing refinement: developing the sketch before color

Peter found that the initial sketch completed too early. The sketch plate now starts with a few simplified mountain gestures and adds actual scene structure through the first half: refined skyline and spurs, traced cloud/mountain contours, the climber, and foreground rock facets. Approximately 705 desktop and 744 mobile connected contour paths supplement the authored geometry. The offline coverage audit grows from 1,944 to 72,311 sketch pixels on desktop and 1,368 to 70,458 on mobile between 0 and 60 percent.

Broad wisps begin after 45 percent; fine colored marks and saturation develop later. Separate opacity/pigment controls prevent the stroke schedule from making the picture look complete too soon. The last 10 percent still increases color strength and completes the fine wisps. The sketch fades out at the endpoint, and the fallback is regenerated from the two color plates to match.

Astra high rendering, accessibility, and visual reviewers approved the updated code and actual checkpoints. The visual reviewer specifically confirmed new scene features appearing after 15 percent, a detailed pencil drawing at 60 percent, restrained color at 75 percent, and meaningful completion between 90 and 100 percent.

Validation: 10 Node tests and 17 local Chrome browser tests pass. New tests use actual GPU output to verify substantial ink growth from 15 to 30 to 45 percent, no premature pigment, and more than 10 percent chroma growth from 90 to 100 percent. The existing endpoint/fallback comparison, interaction, failure, and responsive tests also pass. Browser verification limits remain as stated above.

## Background brushwork and removal of the vignette

Removed the full-screen navigation gradient and its abrupt 82-percent switch. Constant ivory surfaces immediately behind the text provide contrast throughout the drawing and fallback states. The sky, clouds, and distant mountains now use curved, tapered colored strokes with varied spacing and direction, replacing the smooth, closely spaced horizontal background ribbons. The foreground and midground treatment and the slow sketch-to-color progression remain intact.

Independent Astra high accessibility, rendering, and visual reviewers approved the change. Reviews included desktop/mobile compositions, 320px, short and ultrawide layouts, and actual browser captures at 81, 82, and 83 percent. Added spacing separates the ultrawide tuner from Contact. Asset comparison confirmed byte-identical sketch plates/timing, unchanged finished pixels at and below the near skyline in both compositions, unchanged color plates/timing below the four-pixel edge gutter, and no untimed covered pixels. The lossless endpoint remains an exact offline composite; the real GPU/fallback comparison also passes.

Final validation: 10 Node tests and 17 local Chrome browser tests pass. An earlier screenshot run entered fallback once; its targeted rerun and the final full run passed. Updated previews show the unshaded artwork and new background texture. Texture count, dimensions, resource bounds, interaction, and fallback contracts are unchanged. The browser/device coverage limits above still apply.

## Source-guided brushwork throughout the painting

Extended the approved background brush style through all colored terrain and figure marks. Removed interpolated contour ribbons, straight fine hatching, synthetic colored ridge outlines, and figure crosshatching. New curved paths follow a sharper photo-derived orientation field, stop at strong tone/color boundaries, and narrow near sharp edges. Short tapered dabs preserve the source color where a boundary cannot support a long gesture. Stroke size and coverage vary with mountain slopes, rock facets, and the figure.

Independent Astra high art and rendering reviewers approved both final compositions. Source comparisons confirmed distinct rear peak and jagged nearer cliff walls, steep fissures, golden light, separate rock facets and dark crevices, and a readable climber with poles. Iterations corrected excessive paper gaps around high-contrast details and the figure. Artifact audits verified byte-identical sketch assets, unchanged visible background away from the boundary gutter, valid timing throughout, unchanged dimensions, and an exact offline endpoint composite. The six-sampler renderer and progression controls are unchanged.

Validation: 10 Node tests and 17 local Chrome browser tests pass, including actual GPU/fallback agreement and sketch/pigment progression. Refreshed desktop/mobile previews show the complete brush treatment. Drawing assets total about 9.3 MiB across both variants; decoded/GPU memory bounds are unchanged. The previously stated browser and physical-device testing limits still apply.

## Regional painting sequence and minimal interface

Replaced the global color opacity/saturation ramps with arrival-relative stroke maturity. Geometry-based schedules establish important mountain features, the climber and foreground first; supporting terrain, distant mountains and clouds follow; blue sky finishes last. Larger gestures precede compact fill, with wider per-stroke staggering and sharper moving tips. Figure priority follows its silhouette and poles instead of a rectangular bounding box. Early pencil behavior is preserved.

Independent Astra high rendering, accessibility, and visual reviewers approved the final implementation. Actual-size and browser checkpoints show individual tapered marks accumulating within the regional sequence, rather than a uniform translucent wash. The offline audit confirmed byte-identical ink plates, pencil timing, and finished paintings in both variants, valid timing at every covered pixel, and full local pigment maturity before the endpoint. Only the four color timing maps changed. Runtime texture counts and memory bounds remain unchanged; drawing assets now total about 8.7 MiB.

Removed the edition, field-study label, and visible sketch/color hint. The interface now uses a plain dark italic serif name at 24–29px, unboxed About/Contact links, and a thin slider with its number. Narrow ivory glyph halos support small text on the artwork. Native keyboard controls, 44px targets, focus indicators, screen-reader instructions, and responsive placement remain. Review included mobile, 320px, short, and ultrawide layouts.

Validation: 10 Node tests and 18 local Chrome browser tests pass. New tests verify independent local stroke maturity and measure actual GPU progression in mountain, figure, foreground, distant, cloud, and sky regions. The 15/30/45-percent pencil-growth checks and endpoint/fallback comparison still pass. Updated captures include 55–99-percent regional checkpoints and colored-stroke growth/reversal. The final preview capture was rerun with the range unfocused for presentation; focus behavior is tested separately. Browser/device coverage limits remain as stated above.

## Mountain framework, human and foreground, then detail

Reordered the pencil stage to follow the requested drawing hierarchy. The opening through roughly 22 percent contains only the skyline, principal mountain ridge, and selected major spurs. The next stage establishes the human silhouette, poles, near-ground boundaries, and four sparse contours taken from large foreground rock edges. Dense mountain/rock contours and inner figure detail begin after roughly 42 percent; cloud sketching waits for the later background work. Pencil-only earliest-arrival preservation keeps later crossings from delaying established structural lines.

Independent Astra high visual and rendering reviews approved both desktop and mobile. The audit found no untimed covered pencil pixels and confirmed that all colored plates, colored timing maps, and finished paintings remain byte-identical. No renderer, interface, or later color-sequence changes were needed.

Validation: 10 Node tests and 18 local Chrome browser tests pass. The revised GPU regression checks mountain-only structure at 20 percent, rough human/foreground outlines and an empty cloud bank at 40 percent, then detail growth and pigment. It reproduced the previous premature cloud detail before the fix and passes with the revised assets in both compositions. Existing regional painting, reversal, fallback, and interaction checks still pass. Updated previews explicitly show the 20/40/60-percent hierarchy.

## Color follows the same construction hierarchy

The preceding revision changed pencil order; this revision applies that order to the actual colored strokes. Narrow distance bands prioritize existing paint along major ridges and peaks, followed by the human boundary, poles, and defining foreground edges. All other body/detail/fill strokes wait until roughly 67 percent or later. Classification considers most of the path and brush radius, preventing wide marks that merely touch an edge from exposing a surface early. Foreground priority excludes strokes crossing the human's interior.

Independent Astra high visual and rendering reviews approved desktop and mobile. Actual 55-percent images show colored ridge bands with unpainted mountain faces and figure; 65-percent images add colored human and foreground boundaries with open interiors; 75-percent images introduce body painting. Audits confirm byte-identical pencil assets, RGBA plates, and finished paintings, valid color timing, and preserved later background/sky paint. No renderer or UI changes were needed.

Validation: 10 Node tests and 18 local Chrome browser tests pass. The color-order regression measures pigment independently of pencil using its distance from the grayscale/ivory color axis, requiring ridge paint before figure/foreground pigment, limited outline coverage before surface fill, and sky completion last. Pencil hierarchy, GPU/fallback agreement, reversal, failure paths, and interaction checks remain passing. Refreshed previews show the colored-outline stages explicitly.

## Preview freshness and drawing revisions

The user's 65-percent screenshot showed the previous patch-based reveal while fresh HTTP requests returned the current contour timing maps. The old preview server supplied no cache policy and artwork URLs were unchanged between revisions. We could not inspect the existing user tab because the browser connector failed, so its exact retained state was not established.

Added a checkout-rooted preview server that sends no-store for every resource and ignores conditional validators, preventing stale 304 reuse after same-second rewrites. The manifest now records per-file content hashes; the renderer and initial finished-image fallbacks use revisioned URLs, and the manifest is fetched without caching. The generator updates revisions after writing the complete artwork; a standalone updater supports other authoring paths. Static checks reject stale hashes. Already open pages still require reloading to replace decoded canvas textures.

An independent Astra high integration review approved the fix and independently checked all fourteen asset hashes, conditional HTTP behavior, generator integration, and failure routes. Validation: 10 Node tests and 19 Chrome browser tests pass, including revisioned asset requests, reload behavior, old conditional requests, GPU color hierarchy, and fallback paths. A separate fresh browser capture at http://localhost:4173, 1440×790, shows colored ridge, human, and foreground outlines at 65 percent with open interiors. Drawing image bytes were unchanged by this delivery fix.
