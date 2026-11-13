# Repeatable motion development evaluation

From the repository root, run:

```sh
HF_HUB_OFFLINE=1 /opt/anaconda3/bin/python3 detector/evaluate_motion.py /Users/avantika/Downloads/uncanny-motion-*.json --device mps --output captures/motion-development-report.json
```

This loads the model once per process, screens captures, removes repeated decoded
sequences and records every export's disposition. An unknown-label export and an
identical labeled export count once, using the label. Conflicting known labels on
an identical sequence prevent inference for that sequence. Labels are user supplied.

Scores are recomputed with the current model rather than trusting export results.
Reports contain anonymous sample IDs, no images or source URLs. Repeated source
URLs are counted as a warning: clips are not independent evidence merely because
the frames differ. Different URLs can also contain the same underlying video.

Pairwise ranking counts how often a real-labeled sample scores above an AI-labeled
sample (ties count one half). This is not classification accuracy, does not set a
threshold and is undefined when either class is missing. It describes only the
scored subset. Always read the excluded-by-label and status counts alongside it.

The cut-screening heuristic was developed on existing samples. Re-evaluating them
is a regression check, not fresh validation. Animation remains non-AI when that is
its provenance; excluding cuts does not establish robustness to animation.

Future promotion requires new source-separated evaluation, explicit supported
media types, false-positive/miss/abstention measurement and uncertainty reporting.

## Local development run, 2026-11-12

13 exports: 2 duplicates, 5 screened out, 6 scored (4 real, 2 AI).
All 8 real/AI pair comparisons in the scored subset were ordered correctly.
Real range: 0.13795–0.64918; AI range: 0.04806–0.08821.
This is selected development evidence, not 100% accuracy. Five of eleven unique
captures were not scored, so coverage limitations are substantial. No threshold
was fitted and the known animation failure was not relabeled or claimed solved.
