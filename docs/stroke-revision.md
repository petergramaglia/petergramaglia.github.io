# Revision: a landscape drawn in color

The first implementation blended an engraved image into a photograph. Peter requested a different interaction: start loosely sketched, draw lines progressively while dragging, and end in a refined, saturated drawing. This supersedes the photo-endpoint sections of the original plan.

## Rendering contract

The browser never samples the source photograph. Three transparent stroke plates describe the scene: initial sketch, broad colored linework, and finer rock/cloud/figure marks. Each plate has a lossless grayscale timing map. Its value at each covered pixel is the point in the slider's journey at which the pen reaches that pixel. Timing increases along each stroke's path, with staggered starts, so individual tips travel as the slider moves.

The shader maps byte timing to `-0.1…1`, reveals a small feathered edge around each arrival time, and composites visible marks over ivory. Early marks exist before zero so the initial view is a loose sketch. Each colored stroke develops opacity and saturation relative to its own arrival, while the arrival schedule orders the painted regions. At full progress every mark is visible and fully colored. The canvas remains the artwork at the endpoint; no photo fade or HTML-photo handoff occurs.

At stroke overlaps the visible layer records the topmost stroke's timing; lower plates supply underlying marks. This is an intentionally layered drawing rather than a complete reconstruction of physical pen history. Forward motion and reversal are deterministic.

## Asset authoring

`prepare-strokes.py` uses the approved source images to guide colored brush paths and sample their colors; authored ridge geometry anchors the early pencil sketch and composition regions. Sky strokes are gently curved and staggered. Mountain strokes follow local photo-derived directions, while shorter gestures describe rock facets and the climber. Narrower strokes at strong boundaries and compact colored dabs preserve detail without turning sharp edges into large paper gaps. Paper seams remain visible at full progress. The subject may lose photographic detail by design.

The desktop stroke plates are 1440×810 and the portrait plates 900×1200. RGB and timing are extended into a small transparent gutter to avoid dark or premature edges during texture filtering. Timing maps are PNG data without gamma/profile conversion; colored plates are lossless RGBA WebP. `finished.webp` is an opaque, lossless composite of the decoded plates and supplies the no-JS/loading/error fallback.

Six samplers fit WebGL1's guaranteed minimum of eight fragment texture units. Timing maps use LUMINANCE textures, keeping GPU allocations smaller than six full RGBA textures. The two cached decoded atlas sets have a conservative RGBA-equivalent footprint of about 54 MB, plus about 9 MB for both decoded finished drawings; the active GPU set is about 17 MB, temporarily about 34 MB while swapping (drivers may expand internal formats). The drawing buffer retains the 2.5-million-pixel cap. Source photographs remain authoring inputs, not runtime requests.

## Interaction and verification

Keep direct drag, native keyboard range, reduced-motion behavior, bounded frame loop, modal focus, safe cropping, transactional swaps, and fallback handling. Rename the visible interaction to “Drag to draw” and “Sketch ↔ Color”; accessible value is percent drawn.

Validate the actual shader in a real browser at 0, 25, 50, 75, and 100 percent. Also inspect successive small increments and reversal to verify traveling strokes rather than a dissolve. Assert that canvas remains visible at full progress, no source-photo requests occur, and the GPU endpoint agrees with the finished static drawing within sampling tolerance. Re-run orientation, network-failure, context-loss, keyboard, focus, reduced-motion, and gesture tests.

An Astra high approach review approved this architecture with explicit requirements for full endpoint coverage, lossless/dilated timing, visible moving tips, bounded memory, and matching drawn fallbacks. Separate code/art reviews follow implementation.

## Pacing refinement: sketch first, painting last

Peter's next review identified that the complete sketch arrived in the first 15 percent. The revised timeline spends the first half developing scene structure: a few rough mountain gestures at the beginning, then progressively drawn peaks/ridges/skyline, cloud outlines, the climber, and rock facets. These are additions to the sketch itself, not colored hatch marks standing in for a detailed sketch.

The sketch plate now carries structural arrival times through approximately 60 percent. Broad colored paths begin around 46 percent and grow through the later slider range; their global opacity rises smoothly from 45 to 100 percent. Fine wisps arrive around 70–98.5 percent, with their opacity rising from 68 to 100 percent. Saturation remains zero through 62 percent and reaches its full strength only at 100 percent. The pencil sketch remains fully present through 72 percent, then recedes as the painting comes together.

`src/progression.js` owns the renderer's opacity/saturation bounds. Stroke arrival maps control path growth separately. The final fallback composites only the two color plates, matching the shader's fully faded sketch at the endpoint. New tests require substantial actual sketch-ink growth between 15, 30, and 45 percent, no premature pigment, and a meaningful saturation increase between 90 and 100 percent. Browser checkpoints now include 15, 30, 45, 60, and 90 percent in addition to the original five.

## Unshaded artwork and background brushwork

The full-screen navigation gradient previously switched from light to dark at 82 percent. It is removed, along with the progress-dependent text-color class. Navigation text instead sits on small, constant ivory surfaces, so the drawing's own colored marks determine light and shade throughout the slider range. Browser captures include 81, 82, and 83 percent to inspect continuity around the former threshold.

The sky, clouds, and distant terrain receive their own curved colored brush gestures and finer marks. A separate distant horizon distinguishes the right-hand background mountains from open sky. Shorter, tapered paths, varied spacing, and exposed paper give these regions visible texture. Background generation uses a separate random stream and replaces only the area above the nearer mountain silhouette, preserving the existing foreground and midground marks. The three-plate rendering contract and sketch/color progression remain unchanged.

## A consistent brush style guided by the source image

The next revision extends the approved background brush style through the mountains, foreground rocks, and climber. All colored marks share a tapered profile; their direction, length, and curvature vary with the forms in the photograph. Replace the broad contour bands and fine straight hatching with paths guided by the source's local structure and edges. Shorter marks describe rock facets and the figure; longer gestures describe mountain slopes. Strong boundaries should separate lit cliffs, shadows, snow, and the climber rather than blending them together.

Visual acceptance compares both finished compositions with their source photographs: the serrated skyline, distinct rear peak and nearer crag wall, steep gullies and illuminated edges, individual foreground rocks, and the climber's hood, arms, legs, and poles. The sky's approved brush treatment, warm/cool light, staged pencil underdrawing, and late pigment buildup remain. The existing texture layout and drawn fallback contract still apply.

## Regional sequence and minimal controls

This revision replaces the earlier global opacity/saturation ramps. Broad strokes establish important mountain features, the climber, and foreground rock groups first. Supporting terrain develops next while the distant mountains and clouds begin; those regions fill before blue-sky strokes sweep upward from the horizon. Sky completes last. Deterministic, geometry-based scheduling changes timing without changing the approved brush paths or palette. Fine strokes follow their local broad marks instead of sharing one scene-wide detail phase.

The shader uses progress minus arrival to mature each colored mark over a short interval. The pencil stays visible in areas waiting for paint, followed by a brief cleanup near completion. Timing leaves room for late marks to mature before the endpoint, and the finished fallback stays identical to the approved painting. Tests measure actual GPU progress in mountain, figure, foreground, distant-terrain, cloud, and sky regions.

The interface contains an unboxed italic serif name, About and Contact text links, and a thin slider with its number. The edition, field-study label, and visible sketch/color hint are removed. A narrow ivory halo follows the text glyphs for steady contrast without a scene overlay. Native keyboard controls, 44px interaction targets, focus indicators, and screen-reader instructions remain.
