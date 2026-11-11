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
and local runtime must be resolved before integration. No STALL score is implemented.

Completion gate for the next milestone: reproduce authors' reference scoring,
evaluate valid sequences from known real and AI videos, measure latency and false
flags, and document outcomes before considering a live model replacement.
No accuracy promise follows from collecting denser frames.
