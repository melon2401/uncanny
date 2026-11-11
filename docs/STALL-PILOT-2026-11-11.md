# First local STALL motion pilot

Two user-labeled browser captures passed the motion preflight: 16 distinct direct
video frames each, spans 2.0222 and 2.0283 seconds. The capture cadence is approximate,
not the exact fixed-rate decoding used by the upstream evaluation.

Official DINOv3 ViT-L/16 Hugging Face revision:
`ea8dc2863c51be0a264bab82070e3e8836b02d51`.
Original STALL calibration and scoring with the experimental Hugging Face feature
backend; original-backbone numerical parity has not been established.

| User label | Spatial percentile | Temporal percentile | Real-reference score | Runtime |
| --- | ---: | ---: | ---: | ---: |
| Real | 0.0920 | 0.1362 | 0.1141 | 46.07 s |
| AI | 0.0205 | 0.0128 | 0.0166 | 42.70 s |

Higher scores resemble the real-video reference calibration more. These are not
probabilities or calibrated verdicts. Both components ranked the real sample above
the AI sample, but the real sample also has low reference percentiles. This is a
correct ranking for one pair, not proof of useful separation across videos.
Do not choose a threshold from this pair or report an accuracy percentage.

Runtime includes model loading and processing all sixteen frames on CPU, using
four-thread environment settings. No full-clip GPU benchmark has been run.
The experimental detector has not replaced the extension's existing detector.

Raw exports and results remain under ignored `captures/`; no images, source URLs,
model weights or credentials are included in this report.

Next evaluation: validate feature compatibility, benchmark an accelerated local
path, and evaluate a more varied set of independently labeled motion sequences
before selecting thresholds. Reserve fresh videos for confirmation after selection.
