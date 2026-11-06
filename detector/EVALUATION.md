# Evaluate the detector

The detector is experimental. No accuracy improvement on social-media videos has
been established. Scores are model signals, not calibrated probabilities.

## Reproduce a failure locally

1. Analyze a video and expand **View six captured frames**.
2. Choose **Known AI** or **Known real** only when you have independent evidence
   (e.g. you created the video). A hashtag alone is not ground truth.
3. Click **Save test sample**. This downloads the original six JPEGs, timestamps,
   capture method, video URL, label, model checksum and raw scores as JSON.
4. Place downloads into the ignored `captures/` directory in this repository.
   These files contain imagery and URLs; do not commit or publish them.

Run from the repository root:

```sh
.venv/bin/python detector/evaluate.py captures > captures/comparison-report.txt
.venv/bin/python -m unittest discover -s tests -p '*_test.py'
```

The evaluator rescans identical inputs with both pipelines. It reports AI detection,
real-video false positives and inconclusive outcomes separately. Multiple captures
from the same URL count as one video; contradictory captures cause abstention.
An inconclusive AI video counts as **not detected**, rather than a successful result.

Gather separate development and held-out folders. Keep an entire source video,
its reuploads and related generation sessions in the same split; the script only
groups exact source URLs, so cross-URL duplicates require manual review. Do not
select thresholds on held-out results. Include real, generated, edited, animated,
filtered, low-light and compressed videos. Report subgroup and total counts.
Small convenience samples are diagnostics, not evidence of production accuracy.

## Preprocessing investigation

The pinned converted model publishes CLIP normalization and bicubic interpolation.
The [original authors' dataloader](https://github.com/JeongsooP/Community-Forensics/blob/main/dataloader.py)
uses ImageNet normalization, torchvision Resize(440) (bilinear), CenterCrop(384).
Our new `commfor-original-preprocess-v1` reproduces the latter; `legacy` preserves
the previous implementation for comparison. The reference tensor check on a
deterministic 359×641 RGB input had maximum absolute difference 0 against torchvision.
Both paths still use the same pinned ONNX weights, whose conversion has not been
independently verified against the original checkpoint in this project.

Sanity checks only: one author-provided DALL-E image and the skimage astronaut
photograph both retain expected score direction. This is not a video benchmark.
The model still sees a center crop and does not analyze motion or audio.

Next decision: use exported failure cases to determine whether reference
preprocessing helps. If not, compare a different detector or multi-region sampling
on the same development set, then confirm on held-out videos. Do not average
unvalidated models or take maximum frame scores just to increase AI detections.

## Product references reviewed (2026-11-06)

- [Hive](https://hivemoderation.com/ai-generated-content-detection) offers
  image/video/audio detection APIs and an extension. It is a candidate external
  comparison, not evidence that it outperforms this model on our examples.
  Integration needs documented API access and explicit user consent to send media.
  No external detector has been connected, and no captured frames have been uploaded.
- [Get Cyber Safe](https://www.getcybersafe.gc.ca/en/resources/recognize-artificial-intelligence-ai-9-ways-spot-ai-content-online)
  discusses anatomy, lighting, movement and audio clues, and advises against relying
  on detectors alone. These can inform separate inspection guidance, but are not
  validated numerical scoring rules. Do not automatically equate smooth skin,
  unusual movement, missing blinks or a watermark with a measured AI probability.
- [AIBotOrNot](https://www.aibotornot.com/) did not expose enough implementation
  details in the retrieved page to substantiate its detector or accuracy.
