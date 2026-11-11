# STALL follow-up: eight new motion captures

Eight distinct user-labeled captures from eight distinct exported source URLs passed preflight. One exact duplicate export was excluded. Different URLs do not prove independent underlying footage. Labels were supplied by the user, not independently authenticated. The initial two-video pilot was excluded from this batch.

| Label | Real-reference score | Spatial | Temporal | Seconds |
| --- | ---: | ---: | ---: | ---: |
| ai | 0.1018 | 0.0199 | 0.1837 | 10.98 |
| ai | 0.0481 | 0.0381 | 0.0580 | 3.28 |
| ai | 0.0882 | 0.0026 | 0.1738 | 3.15 |
| ai | 0.0639 | 0.0628 | 0.0650 | 3.08 |
| real | 0.6492 | 0.5747 | 0.7236 | 3.03 |
| real | 0.1380 | 0.1425 | 0.1334 | 4.16 |
| real | 0.5203 | 0.4577 | 0.5829 | 4.03 |
| real | 0.0353 | 0.0330 | 0.0376 | 3.36 |

Higher means more similar to the real-video calibration, not a probability. Three real captures rank above all four AI captures; the fourth real capture ranks below all four AI captures. Consequently no single threshold separates this batch perfectly. Both spatial and temporal components are low for that real capture, so simply selecting one component does not resolve the failure.

No classification threshold was selected and no classification accuracy is reported. Warm MPS processing was 3.03–4.16 seconds per clip; first-run processing was 10.98 seconds. Model, transforms and scoring remained unchanged from the initial MPS pilot.

Decision: do not replace live scoring with this experimental model yet. Investigate the low-scoring real capture and verify feature extraction compatibility before further threshold work. These samples are now development evidence, not an untouched final evaluation set. Captures and full reports remain in ignored local storage.
