# STALL low-score investigation: scene cuts

Follow-up to `STALL-FOLLOWUP-2026-11-11.md`, using the same ten development
captures (pilot pair plus follow-up batch). No model was rerun; this is an
image-level inspection of the exported frames.

## Finding

The lowest-scoring real capture (0.0353) contains two hard cuts inside its
two-second window, and its content is a 2D animated explainer with motion-graphic
transitions, not camera footage. Contact-sheet inspection confirmed cuts in five
of the ten captures:

| Label | Real-reference score | Cuts after frame | Notes |
| --- | ---: | --- | --- |
| ai | 0.0166 | 2, 8 | |
| real | 0.0353 | 6, 14 | animated explainer |
| ai | 0.0639 | 0, 11 | first frame is a white transition |
| ai | 0.1018 | 13 | |
| real | 0.1141 | 3 | |
| ai | 0.0481 | none | |
| ai | 0.0882 | none | |
| real | 0.1380 | none | caption text changes, no cut |
| real | 0.5203 | none | |
| real | 0.6492 | none | |

STALL's temporal term takes the minimum likelihood over adjacent-frame changes,
so one cut can dominate it. Its spatial and temporal calibration come from
continuous natural-camera video (VATEX); animation is outside that reference.

Among the five cut-free captures, all three real ones rank above both AI ones.
This is a hypothesis from development data chosen after looking at the results.
It is not evidence that STALL works on cut-free clips, and no threshold or accuracy
is reported. It does mean the "real" label needs a narrower definition for this
test: camera-recorded footage, not just "not made with generative AI".

## Change

`detector/audit_motion.py` now flags adjacent frames whose mean pixel change is
above 40 and more than three times the clip's median change, and marks the
capture not ready. The thresholds were picked by inspecting these same captures,
so they are a screening heuristic, not a validated shot-boundary detector. Two new
unit tests cover a synthetic cut and gradual change.

## Next

Collect new motion captures of continuous camera footage, keeping cuts out at
capture time, and score them as a fresh set before choosing any threshold. Record
animation separately rather than labeling it real.
