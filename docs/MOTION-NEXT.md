# Motion milestone

Implemented: optional Motion test capture, 16 direct-pixel JPEG frames, target
125 ms spacing, actual playback timestamps, normal playback speed only.
Video changes, loops, backward jumps, >500 ms gaps and stalled playback abort.
Screenshot fallback is refused because its capture-rate limit cannot support this
cadence. Normal six-frame image analysis remains unchanged.

This is approximate sampling: browser scheduling and extension RPC overhead add
delay. Do not interpret it as exact 8 FPS or native consecutive frames. A temporal
adapter must validate timestamps, resample if justified, or reject unsuitable clips.
Cuts within the same video are not yet detected or rejected.

Export: schema 2, mode motion, targetIntervalMs 125, 16 timestamped frames.
Files use uncanny-motion-*.json. They do not enter existing schema-1 benchmarks or
get submitted to the still-image scoring endpoint. Exports are local and voluntary.

Next named experiment: [STALL](https://github.com/OmerBenHayun/STALL), which uses
DINOv3 embeddings with spatial and temporal statistics and published real-video
calibration. Its paper-style setup is 8 FPS / two seconds. Score direction is
higher = more real, not more AI. Its weights/access requirements, sampling mismatch
and local runtime must be resolved before integration. Offline STALL scoring is implemented below; it is not enabled in the extension.

Completion gate for the next milestone: reproduce authors' reference scoring,
evaluate valid sequences from known real and AI videos, measure latency and false
flags, and document outcomes before considering a live model replacement.
No accuracy promise follows from collecting denser frames.

## Implemented STALL adapter (2026-11-11)

- `detector/stall_score.py`: spatial/temporal whitening, Gaussian likelihood,
  max-spatial/min-temporal aggregation, calibration percentiles and correct
  higher-is-real score direction.
- `detector/compare_stall.py`: offline motion-export adapter using the original
  DINOv3 ViT-L/16 backbone and original transform.
- Timing validation rejects loops, old six-frame exports, screenshot capture
  and captures too far from 8 FPS. This is a conservative engineering gate,
  not a guarantee of paper-identical sampling.
- Fully static embeddings abstain instead of producing a misleading high score.
- License/attribution in `detector/licenses/STALL.txt` (CC-BY-NC-4.0).
  This experimental module is not covered by the repository's MIT license.

Verified against pinned upstream scoring code at
f6dbb617a08d522f42ac02341028da8c58e669d1, with published VATEX calibration:
three synthetic embedding sequences matched spatial percentile, temporal percentile
and final score within 1e-12 (one sequence included equal adjacent embeddings).
The unused cv2 import was stubbed during this math-only comparison; neither
image embedding nor video decoding was exercised. This proves scoring parity
on those inputs, not end-to-end detection quality.

## Approved Hugging Face path

DINOv3 access was approved and the official Hugging Face weights downloaded locally
at revision `ea8dc2863c51be0a264bab82070e3e8836b02d51` into ignored
`.models/dinov3-hf`. The adapter now accepts `--hf-model .models/dinov3-hf`
instead of `--dino-repo` / `--weights`. Loading is local-only. It retains STALL's
224x224 tensor resize and ImageNet normalization, and uses the model's normalized
CLS output (`pooler_output`), not patch averaging or unit-length normalization.

Local smoke check: one previously captured frame produced a finite (1,1024)
feature vector; pooler output equaled the normalized sequence's CLS token.
Repeating that embedding sixteen times correctly abstained as static footage.
CPU model load plus one-frame processing took 2.71 seconds in this single run;
this is not a full-clip latency benchmark. Python tests: 27 passed.

This does not establish numerical parity with Meta's original implementation,
calibration compatibility in practice, or accuracy. No valid motion exports were
available for evaluation. No STALL score is exposed in the live extension yet.

Example (from repository root, using the Python environment with torch):

```sh
HF_HUB_OFFLINE=1 /opt/anaconda3/bin/python3 detector/compare_stall.py captures/MOTION.json --hf-model .models/dinov3-hf --output captures/stall-result.json
```

## Motion export preflight

Run `.venv/bin/python detector/audit_motion.py <export.json> [more exports...]`
before embedding extraction. It checks capture cadence, known labels, readable
JPEGs, consistent dimensions, repeated decoded pixels and duplicate sequences
within the batch. Output contains filenames and diagnostics, not imagery or source
URLs. Store reports under ignored `captures/`.

Repeated pixels conservatively mark a capture for inspection, not as synthetic.
Passing checks does not verify labels, detect scene cuts, establish independent
source videos, or prove model accuracy. No network or model weights are needed.
The original six-frame exports cannot substitute for dense motion sequences.

## Pending: original-backbone parity (2026-11-11)

Not yet run. The original Meta ViT-L/16 checkpoint is not on disk; only the
source code (`.models/dinov3-source`, commit 6876159) is. Download it through
Meta's form at https://ai.meta.com/resources/models-and-libraries/dinov3-downloads/
and keep the original filename, because the loader reads the `-8aa4cbdd.pth`
hash from it. Then score the same captures with both backends and compare:

```sh
HF_HUB_OFFLINE=1 /opt/anaconda3/bin/python3 detector/compare_stall.py captures/<motion>.json \
  --dino-repo .models/dinov3-source --weights .models/dinov3_vitl16_pretrain_lvd1689m-8aa4cbdd.pth \
  --device mps --batch-size 4 --output captures/<motion>-original.json
```

This compares final scores only, not embeddings. See `STALL-CUTS-2026-11-11.md`
for why scene cuts should be excluded before interpreting either backend.

## Opt-in extension experiment (2026-11-12)

`Start-Motion-Experiment.command` starts a separate loopback service on port 8768,
using a cached DINOv3 model and MPS when available. The existing still-image service
on 8767 is unchanged. The extension's expandable Motion test now captures and
requests an experimental signal automatically. No AI/real threshold is applied.

Requests stay in memory, undergo timing/image/duplicate/cut checks, and do not need
a ground-truth label. Captures with screening issues return inconclusive before
inference. Screening is heuristic, not a reliable animation or scene-cut detector.
The low-scoring animation remains a non-AI failure case; screening does not solve
animation generalization. The interface warns that animation and edits may mislead.

If the service is unavailable, captured frames remain exportable. Closing or clearing
the popup aborts its request; already-started model computation can finish locally.
Use Reload in chrome://extensions after updating installed extension files.

## Longer capture and disclosed section selection (2026-11-16)

New motion captures use schema 3 with 32 timestamped frames (about four seconds).
The service scans consecutive 16-frame windows in chronological order and uses
the first that passes existing timing, image and heuristic cut checks. Model
scores never influence selection. Legacy schema-2 captures remain supported.

The response includes zero-based start/end frame indices, playback time range and
total captured frame count. The popup marks analyzed versus unanalysed frames and
states that the result describes only that section, not the whole video. Exports
retain all 32 frames plus the returned window metadata. The evaluation command now
uses the same selection path; duplicate accounting is based on the selected section.

If none passes, no inference occurs. The cut heuristic can miss transitions and
this does not establish robustness to animation, mixed content or all edited video.
Selecting a section improves the opportunity to obtain usable input; it is not an
accuracy improvement demonstrated on a fresh dataset.

Validation: 40 Python tests, 14 extension tests and JS syntax checks passed.
A controlled saved-frame fixture exercised actual popup/capture/scoring JavaScript
against the running MPS HTTP service: 32 frames captured, 16 marked analyzed,
result 0.13795, identical to the source section's prior result. The fixture repeats
frames with synthetic timestamps and is a workflow test, not new video evidence.

To use: launch Start-Uncanny.command, reload the unpacked extension, play a video,
expand Motion test and click Check motion. Keep the popup open through capture and
analysis. No file export is required. The six-frame still-image mode remains separate.
