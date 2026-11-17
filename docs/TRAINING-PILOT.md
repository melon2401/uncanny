# Frozen DINOv3 training pilot

Plan written on 2026-11-16, before test-set inference. This experiment trains a
small supervised classifier, rather than changing thresholds on user failures.
The feature extractor is frozen: this is **not** foundation-model training.

## Data and boundaries

- [DeepAction v1](https://huggingface.co/datasets/faridlab/deepaction_v1), by Matyas
  Bohacek and Hany Farid; revision `476932c3369424ca59dc1f8fb758cb3c13fe63fe`.
- Dataset AI videos: CC BY 4.0. Real footage: [Pexels License](https://www.pexels.com/license/).
  Videos stay in ignored `.models/training`, with no redistribution in the repo.
- Select `a.mp4` from each source/action pair. Group by action/prompt, deterministic
  SHA-256 ordering with seed text `uncanny-action-v1:`. 60 training, 20 validation,
  20 test actions. File hashes are checked before extraction.
- Exclude Veo entirely from training/validation. 360 training clips (60 real,
  300 AI), 120 validation clips (20 real, 100 AI), 140 test clips (20 real, 120 AI).
- Plan SHA-256: `138e81cb205f4997fff2aa6b86abca11295afa11dd5d516610ca9c957e1a48c4`.
- User exports are **external regression examples only**. They are already seen
  development examples, not an untouched test set and not training data here.
- Action separation does not establish creator separation. Original source
  creator IDs are unavailable; exact-file checks do not exclude all near-duplicates.

## Method locked before test

Six frames at 10–90% of each clip's duration, encoded like the extension's
1280-long-edge JPEG90 capture. DINOv3 ViT-L/16 consumes the complete frame resized
to 224×224 (bilinear, ImageNet normalization). Normalize each frame's CLS feature,
average six, normalize the resulting clip vector. No caption, filename, hashtag,
source name or platform label is an input feature.

Use approved, local `facebook/dinov3-vitl16-pretrain-lvd1689m` weights, revision
`ea8dc2863c51be0a264bab82070e3e8836b02d51`, subject to the DINOv3 license. Train a
class-balanced logistic regression head on the frozen 1024-dimensional features.
Each training clip gets one extra compressed view (short edge at most 256, JPEG50),
equally for real and AI, with half weight per view. No validation/test augmentation
is used to select a model.

Select regularization C from `[0.01, 0.1, 1, 10, 100]`. For each model, set the
threshold just above the highest real validation score (zero observed validation
false flags). Select highest validation AI recall, then highest AUC, then smaller C.
Do not refit after validation or alter the threshold using test results. Scores are
not calibrated probabilities of authenticity.

Evaluate the locked candidate once against the current WaveRep five-of-six display
policy on the same 140 clips. Report AI recall, real false-flag rate, balanced
accuracy of the binary flag decision, counts, clip-level Wilson intervals and
per-generator results. WaveRep abstentions are separately counted; being unflagged
is not the same as proving real. Shared actions mean clip-level intervals do not
capture all dependence.

**Predeclared pilot target:** at least 80% AI recall, at most 10% real false flags,
strictly higher AI recall than WaveRep and no higher real false-flag rate. Passing
this small controlled test does not qualify the model for production deployment.
It needs social-video validation, more real controls and the saved-failure review.

## Reproduce locally

The research environment needs NumPy, Pillow, scikit-learn, Torch, Transformers,
huggingface_hub, the approved local DINOv3 weights and PyAV. On the development Mac,
PyAV 16.0.1 is installed separately under `.models/training-deps`; all other research
dependencies already existed. Expect a 3.3 GB video download plus model/packages.

```sh
python detector/training_data.py plan
python detector/training_data.py download
python detector/extract_training.py --splits train validation --device mps
python detector/train_visual.py train
python detector/extract_training.py --splits test --device mps
python detector/extract_training.py --splits test --baseline
python detector/train_visual.py evaluate
```

Use `--device cpu` for DINOv3 on machines without MPS. The baseline adapter chooses
MPS when available. Downloads/features resume; candidate/test report refuse
overwrites. A new model after looking at test outcomes requires a new untouched
evaluation set, not another claim of independent validation on this one.

The cached feature matrices, trained head and full report are stored locally under
`.models/training/deepaction-v1/`. None of these steps changes the live extension.

## Social-video follow-up

[SLOP](https://huggingface.co/datasets/matybohacek/slop) is closer to the deployment
domain, but requires separate approval for research at an academic/nonprofit
institution. Existing DINOv3 approval does not provide access. Its terms prohibit
redistributing the videos/metadata. Do not treat it as unrestricted app training
data or quietly bundle it into a public release. No gated videos were downloaded.
