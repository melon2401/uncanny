# Uncanny: notes for Claude

Chrome MV3 extension (`apps/extension`, plain JS, no build) that samples frames
from YouTube Shorts, Instagram Reels and TikTok, plus a loopback-only Python
detector (`detector/server.py`, port 8767). Development moved here from OpenAI
Codex on 2026-11-11; the repo docs are the only record of earlier decisions.

## Read first

- `README.md`, `docs/ROADMAP.md`: product scope and status.
- `detector/EVALUATION.md`, `docs/BENCHMARK-2026-11-11.md`: still-image
  detector results (no candidate promoted).
- `docs/MOTION-NEXT.md`, `docs/STALL-*.md`: current research on offline
  motion scoring with STALL + DINOv3. Not enabled in the extension.

## Commands

```sh
npm test && npm run check                                      # extension
.venv/bin/python -m unittest discover -s tests -p '*_test.py'  # detector
.venv/bin/python detector/server.py                            # live detector
.venv/bin/python detector/audit_motion.py captures/uncanny-motion-*.json
HF_HUB_OFFLINE=1 /opt/anaconda3/bin/python3 detector/compare_stall.py \
  captures/<motion>.json --hf-model .models/dinov3-hf --device mps --batch-size 4 \
  --output captures/<result>.json
```

`.venv` holds only the live detector deps (`detector/requirements.txt`).
STALL and the comparison scripts use the Anaconda Python with
`detector/requirements-research.txt`. MPS runs work only on the Mac itself,
not inside a Linux sandbox.

## Rules carried over from the project

- Never claim accuracy that has not been measured. Report false positives,
  false negatives and inconclusive results separately. Scores are signals,
  not probabilities.
- Keep development and held-out evidence separate. Once a set informs a
  decision, it is development data. Group by source video.
- Never commit `captures/` (imagery, URLs) or `.models/` (weights).
- No cloud upload of frames without explicit user consent. No hashtag or
  platform-label inference.
- STALL-derived files are CC-BY-NC-4.0 (`detector/licenses/STALL.txt`), not MIT.
- Small, single-purpose commits with a test or a written result.
