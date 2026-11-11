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

Blocked dependency: official DINOv3 weights returned HTTP 401 without approved
access. No weights gate was bypassed. Access via Meta/Hugging Face requires the
user's license acceptance. The current offline adapter expects the original
.pth checkpoint and original DINOv3 source; Hugging Face safetensors are NOT
directly interchangeable with that CLI. If only HF format is available, its
feature-extraction path still needs implementation and verification.

No STALL score is exposed in the live extension. End-to-end inference, runtime,
model-feature parity and real/AI validation remain outstanding.

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
