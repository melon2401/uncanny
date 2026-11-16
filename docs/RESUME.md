# Portfolio description

**Uncanny — local-first AI-video analysis browser extension**

Built a Chrome Manifest V3 extension and Python inference services that sample
Shorts/Reels/TikTok video frames, run pretrained visual and temporal models locally,
and present evidence with disagreement-based abstention. Implemented Apple GPU
inference, capture-quality screening, source-aware evaluation and privacy-preserving
sample export. Packaged an experimental macOS beta with 60 automated tests.

Possible resume bullets (adapt to your actual contribution):

- Developed a Chrome extension with local Python/PyTorch inference for AI-generated
  video signals, including frame capture, evidence inspection and failure recovery.
- Integrated pretrained WaveRep and DINOv3/STALL models; reduced observed warm STALL
  inference from roughly 43 seconds on CPU to 3–4 seconds with Apple GPU batching.
- Built repeatable evaluation with duplicate detection, abstention accounting and
  documented false positives/misses; added 60 automated tests and local-only processing.

Do not claim you trained the pretrained models, achieved production accuracy, have
active users you have not measured, or published to the Chrome Web Store. Describe
AI-assisted implementation candidly if asked; understand the architecture and tradeoffs.
