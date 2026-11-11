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

Unknown-labeled samples are replayed and listed separately as `unknown_videos`.
They never enter false-positive or AI-detection rates. Missing labeled classes
produce null rates rather than invented zeros. Inspect the report's details
before making any performance claim.

## Offline region sensitivity

Run ` .venv/bin/python detector/inspect_regions.py captures/<sample>.json `
to compare the existing full-image preprocessing with five fixed 65%-size square
crops. This is a diagnostic only; it does not alter live scores. Crop medians are
not calibrated or validated as a classification rule. A higher maximum crop score
is not evidence of better detection.

On the first user-confirmed AI export, legacy preprocessing abstained at 63 and
author preprocessing abstained at 42. The five-region median diagnostic fell to
16. This is one missed source video, not a population accuracy estimate. No
known-real exported videos were available for a false-positive comparison. The
regional variant was not promoted into the extension.

## Second model: pinned SigLIP candidate

Offline comparison only; not enabled in the extension:

```sh
python detector/compare_siglip.py captures/uncanny-sample-*.json --output captures/siglip-comparison.txt
```

Use a separate Python environment with `torch==2.11.0`,
`transformers==5.12.1`, and Pillow. These are the versions used for this run.
Weights are downloaded to ignored `.models/huggingface`. The script loads only
safetensors, pins the revision, disables remote code and never sends frames out.

Candidate: [Ateeqq/ai-vs-human-image-detector](https://huggingface.co/Ateeqq/ai-vs-human-image-detector/tree/60e82406916921b823616bee33397baab38af3f0)
(Apache-2.0; revision 60e82406916921b823616bee33397baab38af3f0).
Use the model's image processor and class mapping: AI is index 0.
The model card reports user concerns about overfitting.

Observed on the one user-confirmed AI video: all six frames scored
99.86–99.92, median 99.91. The fixed existing decision rule gives strong
synthetic signal. The current detector abstains at 42 on the same sample.

Real-image sanity controls (skimage bundled photos, resized to max edge 720 and
JPEG quality 90): astronaut 85.83, camera 0.02, chelsea 0.05, coffee 0.10,
rocket 0.81. The astronaut is a high-scoring real image: a false-positive concern.
Each control repeated the same photo six times, so the duplicate-frame guard
abstained; these are five still images, NOT five real videos. Controls are kept
in a separate subdirectory and excluded from the video evaluation folder.

Decision: do not replace the live detector yet. The promising AI-example result
does not establish generalization, and the real-photo false alarm needs further
investigation. Next comparison needs known-real videos and additional independently
verified AI sources, with held-out examples. No claimed production accuracy.

### First user-confirmed real video

On the second exported source video (user label: real), the current and legacy
pipelines both returned rounded frame signals [0, 0, 0, 0, 0, 0] and weak synthetic
signal. SigLIP returned [0.21, 2.63, 99.89, 99.90, 84.08, 99.79], median 91.94.
The existing five-of-six rule abstained, so this is not a final strong-signal
false positive, but four high frame scores and a high median on real video are
a material failure for using its numeric score as a reliable indicator.
Only two user-labeled source videos have been tested. Candidate remains offline;
do not promote it or combine models by taking the maximum.

## Third model: SDXL/Swin comparison

Offline, noncommercial evaluation only:
[Organika/sdxl-detector](https://huggingface.co/Organika/sdxl-detector/tree/b37fede8562cb72b89ec201c0987f96ba21b518a),
revision b37fede8562cb72b89ec201c0987f96ba21b518a. Model card: CC-BY-NC-3.0;
trained on Wikimedia/SDXL pairs, with acknowledged generator-dependent performance.
Weights remain outside Git and are not included in Uncanny's runtime.

Run the same harness with `--candidate sdxl`; the default remains `siglip`.
The processor and positive label are model-specific and loaded from the pinned
configuration. Both comparisons use the same six-frame decision rule.

| User-labeled source | Current median | SigLIP median | SDXL median |
| --- | ---: | ---: | ---: |
| Known AI | 42 | 99.91 | 99.59 |
| Known real | 0 | 91.94 | 99.99 |

SDXL returns strong synthetic signal on BOTH samples: a final false positive
on the real video. Reject this candidate for promotion. Two source videos are
insufficient for general accuracy estimates, but one clear counterexample is
enough to reject a claim that this candidate fixes both observed problems.
Live detector unchanged. No external frame uploads were performed.

## Hive comparison (requires account access)

`compare_hive.py` implements the documented V2 project API, not the V3 Playground.
No live Hive call has been made yet; parser tests use fabricated responses.
A V2 AI-generated image/video detection project key is required. A general Hive
login, Hive Detect subscription, or a V3 Playground key is not interchangeable.

The user authorized an external comparison of the two saved samples. The script
requires an explicit `--allow-upload` flag on future runs; no extension integration
has been added. Six individual JPEGs per sample go to api.thehive.ai. Labels, social
URLs and entire videos are not submitted. API charges may apply to 12 new requests.

Set HIVE_API_KEY in the executing terminal (never source control or chat), then:

```sh
.venv/bin/python detector/compare_hive.py captures/uncanny-sample-*.json --output captures/hive-report.txt --allow-upload
```

The adjacent cache saves successful frame scores for the same project key and image.
Timeouts are not retried automatically: a timed-out request may still have incurred
a charge. Inspect account usage before rerunning. Cache is local and not a guarantee
of request idempotency. Reuse a report path only for the same experiment/model version.

The parser reads only `ai_generated`, never substitutes `deepfake` or a generator
attribution class. Reports include individual scores, median, and count above 90;
they are not a claim of video accuracy or calibration. Malformed results fail closed.
Docs: https://docs.thehive.ai/reference/authentication and
https://docs.thehive.ai/reference/ai-generated-image-and-video-detection-1

## UniversalFakeDetect research baseline

Free local research comparison:
[original implementation](https://github.com/WisconsinAIVision/UniversalFakeDetect/tree/030495aea3300a8b54c0ec37ec7fe1dd7e63c619).
The comparison script loads the authors' linear classifier with `weights_only=True`
and verifies its SHA-256, using a pinned OpenAI CLIP ViT-L/14 vision backbone.
Preprocessing follows original evaluation: center-crop 224 without resizing,
then CLIP normalization. Projected image features are not L2-normalized before
the classifier. Only vision weights are used from the joint CLIP checkpoint;
unused text weights in the loader report are expected. Numerical parity with
the authors' bundled CLIP implementation has not yet been independently tested.

Run with the same Torch/Transformers environment used by the candidate comparisons:

```sh
python detector/compare_univfd.py captures/uncanny-sample-*.json --output captures/univfd-comparison.txt
```

The approximately 1.7 GB backbone download is cached outside Git. It has no
per-request fee and no image uploads. This older detector is an additional baseline,
not a promise of generalization to current generators.

Observed results (0–100 sigmoid signal): known-AI video median 0.0194,
known-real video median 0.00214, real astronaut control 0.00474.
This baseline misses the AI case. It is not promoted into the live extension.
Do not lower a threshold to fit these two videos; use independent labeled
development and held-out sources before calibration or fine-tuning.
