# First held-out video comparison — November 11, 2026

Nine newly supplied YouTube Shorts: four user-labeled AI, five user-labeled real.
All contain six distinct captured JPEGs with advancing playback timestamps.
The two previously inspected videos remain development data and are excluded here.
Labels are supplied by the user, not independently verified provenance. This small,
single-platform sample is a diagnostic, not a population accuracy estimate.

The split was assigned before scoring the new videos. Model weights, preprocessing
and the existing evidence rule were kept unchanged. Any future model selection using
this report consumes this set as development evidence; it is no longer unseen for
that decision. New independent clips would be needed for confirmation.

A positive flag requires at least five of six scores >=80 and no score <=20.
A weak signal requires at least five scores <=20 and none >=80.
Other results abstain. Abstention on AI is not counted as successful detection.
Weak signal does not prove real footage. Scores are not calibrated probabilities.

| Model | AI flagged / 4 | AI weak / 4 | AI inconclusive / 4 | Real falsely flagged / 5 | Real weak / 5 | Real inconclusive / 5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Community Forensics, legacy preprocessing | 1 | 0 | 3 | 0 | 2 | 3 |
| Community Forensics, current preprocessing | 0 | 1 | 3 | 0 | 1 | 4 |
| SigLIP candidate | 2 | 0 | 2 | 2 | 1 | 2 |
| SDXL/Swin candidate | 3 | 0 | 1 | 3 | 0 | 2 |
| UniversalFakeDetect baseline | 0 | 3 | 1 | 0 | 5 | 0 |

No candidate above is promoted into the live extension. Higher AI recall comes with
substantial false flags in this sample. The change to author preprocessing did not
improve this test set; earlier tensor-parity tests establish implementation fidelity,
not superior detection accuracy. Do not describe it as an accuracy improvement.

Raw reports, URLs, manifests and imagery remain in ignored local captures/.
No paid API was called. No images were uploaded.

## Decision

None of the tested models provides an acceptable replacement on this sample. Keep live deployment experimental. Next research should investigate video-specific models and temporal evidence using a development subset, then validate on new sources. Do not combine these scores with tuned weights using this nine-video set and call the result held-out accuracy.
