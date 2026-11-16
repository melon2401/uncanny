# Research and dependencies

- [WaveRep](https://github.com/grip-unina/WaveRep-SyntheticVideoDetection), Corvi et al.,
  “Seeing What Matters: Generalizable AI-generated Video Detection with Forensic-Oriented
  Augmentation.” Main G4 checkpoint and original preprocessing. Research/nonprofit
  license: detector/licenses/WaveRep.txt. Original source revision and weight checksums
  are documented in docs/WAVEREP-2026-11-16.md. Weights are downloaded separately.
- [STALL](https://github.com/OmerBenHayun/STALL), Ben Hayun et al., spatial-temporal
  reference scoring, adapted in detector/stall_score.py. CC BY-NC 4.0:
  detector/licenses/STALL.txt. Calibration downloaded separately.
- [DINOv3](https://github.com/facebookresearch/dinov3), Meta, optional research
  backbone. Official approved Hugging Face weights; Meta's DINOv3 license applies.
- [timm](https://github.com/huggingface/pytorch-image-models), PyTorch, torchvision,
  NumPy and Pillow provide the inference/runtime components under their respective
  licenses. Installed separately, not vendored in the release.
- Legacy detector comparisons retain attribution in detector/EVALUATION.md.

The Uncanny author did not train the above foundation models. The application
integrates pretrained models, evaluates behavior and presents local evidence.
