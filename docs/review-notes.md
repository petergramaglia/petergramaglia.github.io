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
