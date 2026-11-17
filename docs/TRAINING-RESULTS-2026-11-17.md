# First trained classifier: completed, not promoted

We trained an Uncanny-specific logistic classifier on frozen DINOv3 features.
It reduced false alarms on the controlled public test but missed substantially
more generated videos. It also underperformed the existing detector on the saved
user exports. **This candidate does not replace the live WaveRep model.**

The [protocol](TRAINING-PILOT.md) was fixed before test inference. Training used
360 DeepAction entries (359 unique files), with 120 separate validation entries.
No user exports were used for training or model selection. Official approved
DINOv3 weights were used; their SHA-256 matches the pinned Hugging Face checkpoint.

## Untouched public test: 140 clips

| Measure | Current WaveRep policy | Trained DINOv3 classifier |
| --- | ---: | ---: |
| AI clips flagged | 116 / 120 | 82 / 120 |
| AI clips missed/unflagged | 4 / 120 | 38 / 120 |
| Real clips falsely flagged | 7 / 20 | 2 / 20 |
| Veo clips flagged (generator excluded from training) | 20 / 20 | 6 / 20 |

WaveRep abstained on seven test clips; the table measures AI flags, so an abstention
is unflagged rather than a correct authenticity verdict. The trained classifier
uses one fixed validation-selected threshold and has no abstention class.

The candidate missed the predeclared target of at least 80% AI recall and higher
recall than WaveRep without increasing real false flags. With only 20 real test
clips, the new model's observed 10% false-flag rate has a wide approximate 95%
interval (2.8–30.1%). Clips also share action groups, so clip-level intervals do
not capture all dependence. This is a controlled pilot, not social-media accuracy.

## Already-seen user exports: 23 captures

| Measure | Current WaveRep policy | Trained DINOv3 classifier |
| --- | ---: | ---: |
| User-labeled AI sources flagged | 7 / 10 | 6 / 10 |
| User-labeled real sources falsely flagged | 1 / 13 | 1 / 13 |

The new model avoids the most recently reported real-video false positive, but
falsely flags a different real example. That is not an overall fix. These labels
are user supplied, sources were seen during development, and this is a regression
check rather than independent validation. All 23 exports were included, with six
uniformly selected frames for motion exports; no media was uploaded.

## What changes next

The small stock/action training set and global frozen features did not establish
the generalization we need. We are moving the next training experiment toward
actual platform footage, with real controls, edited content and creator-separated
evaluation. This is a data/model adaptation step, not another change to the UI's
thresholds. Neither more data nor a different model guarantees the target will pass.

The user is requesting free SLOP research access. `detector/prepare_slop.py` is ready
to audit its metadata after approval: preserve official splits, exclude missing
creator identities and substitute-account provenance, reject cross-split duplicate
files, balance real/AI within Instagram/TikTok, and cap clips per creator. Its tests
use synthetic fixtures; the real gated manifest has **not** been inspected yet.
The first selection is capped at 720 clips rather than downloading the full corpus.
Selection sizes and download bytes will be checked against the approved metadata.

SLOP remains research-only with restrictions on sharing its media and metadata.
Access does not itself authorize a commercial deployment or establish label
perfection. Its labels are based on account provenance; YouTube is not covered by
the proposed Instagram/TikTok subset. The next protocol must account for resolution
and bitrate differences between classes before testing another candidate.

## Reproducibility and artifacts

- [Aggregate machine-readable result](reports/dinov3-linear-v1.json): counts,
  per-generator breakdown, intervals, model/data hashes and environment versions.
- Local-only `.models/training/deepaction-v1/candidate.json`: locked trained head.
- Local-only `test-report.json` and `regression-report.json`: detailed predictions.
- Local-only `features/`: all 620 cached clip entries, reusable for explicitly
  declared development experiments; this test set is now consumed.
- 58 Python checks passed after adding training, pixel-parity, regression grouping
  and SLOP selection tests. Both existing local services passed readiness checks.

The extension remains on its existing model. No claim of improved live detection
or production accuracy is justified by this experiment.
