# Uncanny — conversation and project handoff

Updated 2026-11-12. This is a curated transfer of decisions and context from the
Codex conversation, not a verbatim transcript. Read current source, Git status and
experiment reports before acting; older status paragraphs may be superseded.

## User intent and working style

The owner is Avantika, GitHub melon2401, public repository melon2401/uncanny.
Build a useful AI-content detector for YouTube Shorts, Instagram Reels and TikTok.
Laptop extension first; phone app/share-to-analyze is a later ambition, not done.
The user initially wanted to type and learn, then explicitly authorized direct
implementation, project-file access and GitHub publication. Explain work in simple
language, act on clear requests and avoid repeatedly asking permission for routine
work. They want faster, measurable progress, not endless data collection or promises.

Budget: free/local only. Hive was explored and abandoned because of cost; do not
restart paid-service setup. AI use in the detector is accepted. The user asked
whether non-AI detection could be equally effective, then explicitly agreed to
continue using AI. Privacy, uncertainty and evidence remain important.

The public repo should show honest incremental work: meaningful commits, no fake
history, fabricated results or backdated development. Verify local-vs-remote state
before promising code is on GitHub. Do not expose credentials, captures or weights.

## Product and design decisions

Name: Uncanny. Tagline: Look twice. Burnt orange and cobalt blue over a dark theme.
Mascot: illustrated half-human/half-robot woman, robot neck on the robotic side,
three-quarter-length denim jorts, no skirt/tights/neck scarf; high-top shoes using
cobalt, orange and black. The mascot has a scanning animation. Preserve existing
assets rather than regenerating them without a reason. The user requested 12ui for
substantial design work; its skill is available in the Codex environment but may
need separate installation/authentication in another tool.

User repeatedly objected to cramped text, squeezed tagline, awkward scrolling,
and a popup so wide it obscured the video. Existing fixed-width layout and one
Analyze action are deliberate. Capture and scoring should not require separate
scroll-and-click steps. Advanced frame details belong in expandable sections.

Detection must examine frames/motion, not simply infer from hashtags or platform
AI labels. Do not restore simulated scores. Avoid presenting signals as calibrated
probabilities. An inconclusive result must remain possible.

## Locations and runtime

- Canonical repo: /Users/avantika/Documents/ChatGPT/ai detection social media/uncanny-animation
- Installed unpacked extension mirror: /Users/avantika/Desktop/uncanny/apps/extension
  (verify Chrome's loaded directory before syncing; editing repo alone may not update it).
- Extension: apps/extension, plain JS Chrome Manifest V3.
- Live backend: detector/server.py, loopback port 8767; Start-Uncanny.command launches it.
- .venv/bin/python: live detector/testing environment.
- /opt/anaconda3/bin/python3: torch/transformers research environment.
- Ignored .models/: approved local weights, reference code and calibration.
- Ignored captures/: exports, labels and local result reports. Downloads also holds exports.
- Hugging Face login was saved locally; never request/paste tokens in chat.

Keep the whole local folder when switching assistants. A GitHub clone alone lacks
ignored models, captures and virtual environments. Neither CLAUDE.md nor this file
transfers the chat automatically; it transfers the relevant summarized context.

## What works versus what is experimental

Live: six-frame direct-pixel capture (with screenshot fallback where applicable),
local still-image scoring, per-frame inspection, labeled sample export, UI mascot.
The live model has substantial errors; no general accuracy claim is justified.

Experimental: optional Motion test captures 16 direct-pixel frames at approximately
125 ms spacing. These exports are separate from normal six-frame scoring. STALL
uses DINOv3 frame embeddings and spatial/temporal reference statistics. It is an
offline evaluation path, not the live extension's replacement detector.

Motion adapter: detector/compare_stall.py. HF model revision:
ea8dc2863c51be0a264bab82070e3e8836b02d51. Local .models/dinov3-hf.
Use normalized CLS output, original STALL tensor resize to 224 square and ImageNet
normalization. Higher real_reference_score means more like real-video calibration,
not more AI and not an authenticity probability. Fully static embeddings abstain.
STALL-derived files have CC-BY-NC-4.0 licensing, separate from repo MIT.

Mac GPU (--device mps --batch-size 4) reduced observed warm latency to roughly
3–4 seconds for a clip versus 43–46 seconds on CPU. Initial GPU execution took
about 10 seconds. Component and final scores matched CPU for the pilot pair.
MPS was unavailable inside the macOS execution sandbox but available outside it;
do not conclude the Mac lacks GPU support from a sandbox-only check.

## Evidence and outstanding uncertainty

Read docs/BENCHMARK-2026-11-11.md: multiple still-image models were compared;
none earned promotion. Old image exports cannot replace dense motion samples.

Read docs/STALL-PILOT-2026-11-11.md and STALL-FOLLOWUP-2026-11-11.md:
- Pilot real score 0.1141 vs AI 0.0166: correct ranking for one pair only.
- Eight new distinct captures: four AI, four real; duplicate export excluded.
- Three real clips ranked above all four AI clips, but one real-labeled animation
  scored 0.0353, below every AI clip. No reliable threshold selected.
- Source URLs were distinct, but labels and provenance were not independently verified.

Newer docs/STALL-CUTS-2026-11-11.md records hard cuts in several development
captures, including the low-scoring animated explainer. audit_motion.py now includes
an experimental cut heuristic. Thresholds were chosen on these same examples;
cut-free subset results are exploratory, not held-out confirmation.

Important scope distinction: a camera-footage-only experiment can narrow its
supported domain, but HUMAN-MADE ANIMATION IS STILL NON-AI for the user's product.
Record media type separately from AI provenance. Do not relabel animation as AI,
discard hard cases silently, or claim broad detection based only on camera clips.
Cuts, animation and calibration mismatch are hypotheses, not proven explanations.

Math-only scoring parity was tested on synthetic embeddings. HF/original-backbone
feature parity remains unresolved in the documented state. Original source is in
.models/dinov3-source; original Meta .pth weights are not documented as downloaded.
A temporary /private/tmp/uncanny-parity.py maps HF tensors into original source for
a same-weights feature check. Its execution outcome was never confirmed in this
chat; inspect/reproduce before citing. Such a check would not independently verify
that an original Meta checkpoint matches HF weights. Do not bypass license gates.

## Next work, in order (proposed, not completed)

1. Inspect Git status/current docs and reconcile any work completed in another chat.
2. Resolve HF-versus-original feature compatibility with reproducible checks and
   explicit tolerances. Preserve weights, transforms and inference settings.
3. Examine failure cases and cut screening without changing labels or tuning a
   threshold merely to make these known examples pass. Separate camera footage,
   animation, edited clips, filters and mixed content in evaluation metadata.
4. Design an evaluation with source-group separation and fresh confirmation clips.
   Existing samples that informed model/threshold choices are development data.
   Report false flags, misses, abstentions and latency; not just overall accuracy.
5. Only after evidence supports it, integrate a persistent local motion model into
   the backend and the single-action flow, with clear supported-domain limitations,
   cancellation, progress/error handling and no fake confidence percentages.
6. Verify capture on Shorts/Reels/TikTok, video changes, pauses, loops, overlays,
   zoom and protected players. Preserve the comfortable compact UI.
7. Later: packaging/privacy docs, optional provenance evidence, mobile workflow,
   potentially audio. These are future ideas, not implemented commitments.

No new capture request is necessary just to start the compatibility investigation.
Do not spend user money or upload frames to external inference services.

## Validation and handoff checklist

Use commands in root CLAUDE.md. Current test counts may differ from historical
reports; rerun relevant checks rather than repeating stale counts. Run git diff
--check. Keep report artifacts anonymized; raw media and source URLs stay ignored.
Check installed-extension synchronization and GitHub push state separately from
local commits. Explain what was implemented, tested and still uncertain.

## Parity result confirmed on 2026-11-12

The temporary script still existed on this Mac and was copied into
`detector/verify_dinov3_parity.py`. Its same-weights CPU comparison completed with
exit code 0 on frame 8 of the low-scoring animation: maximum absolute difference
3.159046e-6, mean absolute difference 6.310843e-7, cosine similarity 0.99999988.
The assertion at atol=rtol=1e-3 passed. This supersedes the unconfirmed execution
status above. It is one-frame implementation agreement, not independent original
checkpoint verification, sequence-level validation, or detection accuracy.

The preserved version takes a sample path rather than hardcoding a private capture
filename. From repository root:

```sh
HF_HUB_OFFLINE=1 /opt/anaconda3/bin/python3 detector/verify_dinov3_parity.py captures/YOUR_SAMPLE.json --frame 8
```

If another assistant cannot see the Mac's files, give it this project folder or
transfer the tracked script. Different execution environments do not share /tmp.
