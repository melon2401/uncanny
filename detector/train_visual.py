"""Fit a frozen-DINOv3 linear head; select on validation, evaluate test once.

The output is a research candidate, never an automatic replacement for the app.
No pickle models, no paid APIs, no user samples in training.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import numpy as np

try:
    from .training_data import DEFAULT, digest, validate
    from .trained_features import FEATURE_VERSION
    from .extract_training import key
except ImportError:
    from training_data import DEFAULT, digest, validate
    from trained_features import FEATURE_VERSION
    from extract_training import key


def wilson(successes, total):
    if not total:
        return None
    z = 1.959963984540054
    p = successes / total
    center = (p + z*z/(2*total))/(1+z*z/total)
    half = z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/(1+z*z/total)
    return [max(0, center-half), min(1, center+half)]


def metrics(labels, flags):
    y, flag = np.asarray(labels, dtype=int), np.asarray(flags, dtype=bool)
    ai, real = y == 1, y == 0
    tp, fp = int(flag[ai].sum()), int(flag[real].sum())
    n_ai, n_real = int(ai.sum()), int(real.sum())
    if not n_ai or not n_real:
        raise ValueError("Evaluation needs both labels")
    recall, fpr = tp/n_ai, fp/n_real
    return dict(ai_clips=n_ai, real_clips=n_real, ai_flagged=tp, ai_missed=n_ai-tp,
                real_false_flags=fp, ai_recall=recall, real_false_positive_rate=fpr,
                balanced_accuracy=(recall+1-fpr)/2,
                ai_recall_95ci=wilson(tp,n_ai), real_false_positive_rate_95ci=wilson(fp,n_real))


def validation_threshold(scores, labels):
    """Require zero observed false flags on validation; not a population guarantee."""
    scores, labels = np.asarray(scores), np.asarray(labels)
    if not np.isfinite(scores).all() or not np.any(labels == 0):
        raise ValueError("Finite validation scores and real examples required")
    return float(np.nextafter(scores[labels == 0].max(), np.inf))


def load_features(plan_path, splits):
    plan = validate(json.loads(plan_path.read_text()))
    rows = [r for r in plan["rows"] if r["split"] in splits]
    normal, augmented = [], []
    for row in rows:
        with np.load(plan_path.parent / "features" / (key(row)+".npz"), allow_pickle=False) as f:
            if (str(f["source_file"]) != row["file"] or str(f["video_sha256"]) != row["sha256"]
                    or str(f["feature_version"]) != FEATURE_VERSION):
                raise ValueError("Feature provenance mismatch")
            normal.append(f["feature"])
            augmented.append(f["augmented"])
    x, aug = np.asarray(normal), np.asarray(augmented)
    if not rows or x.shape != (len(rows), 1024) or aug.shape != x.shape or not np.isfinite(x).all() or not np.isfinite(aug).all():
        raise ValueError("Invalid cached features")
    return rows, x, aug, np.array([int(r["label"] == "ai") for r in rows])


def linear_scores(model, x):
    if model["feature_version"] != FEATURE_VERSION:
        raise ValueError("Unsupported feature pipeline")
    weights = np.asarray(model["coefficients"], dtype=float)
    if weights.shape != (1024,) or not np.isfinite(weights).all():
        raise ValueError("Invalid model weights")
    return np.asarray(x, dtype=float) @ weights + float(model["intercept"])


def train(plan_path):
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    out = plan_path.parent / "candidate.json"
    if out.exists():
        raise ValueError("Candidate already locked; use a new experiment directory to retrain")
    rows, x, aug, y = load_features(plan_path, {"train"})
    val_rows, val_x, _, val_y = load_features(plan_path, {"validation"})
    candidates = []
    for c in (.01, .1, 1., 10., 100.):
        clf = LogisticRegression(C=c, class_weight="balanced", solver="lbfgs", max_iter=2000, random_state=0)
        clf.fit(np.concatenate([x, aug]), np.tile(y, 2), sample_weight=np.full(2*len(y), .5))
        if int(clf.n_iter_[0]) >= 2000:
            raise ValueError("Optimizer did not converge")
        score = clf.decision_function(val_x)
        threshold = validation_threshold(score, val_y)
        stats = metrics(val_y, score >= threshold)
        auc = float(roc_auc_score(val_y, score))
        candidates.append((stats["ai_recall"], auc, -c, clf, threshold, stats))
    best = max(candidates, key=lambda r: r[:3])
    _, auc, neg_c, clf, threshold, stats = best
    model = dict(schema=1, name="Uncanny DINOv3 linear pilot v1", feature_version=FEATURE_VERSION,
                 dataset_plan_sha256=digest(plan_path), backbone="facebook/dinov3-vitl16-pretrain-lvd1689m",
                 backbone_revision="ea8dc2863c51be0a264bab82070e3e8836b02d51", backbone_frozen=True,
                 coefficients=clf.coef_[0].tolist(), intercept=float(clf.intercept_[0]),
                 threshold=threshold, selected_C=-neg_c, validation=stats, validation_auc=auc,
                 train_clips=len(rows), validation_clips=len(val_rows),
                 train_counts=dict(Counter(r["label"] for r in rows)),
                 selection="maximum validation recall with zero observed real false flags; AUC then smaller C tie-break",
                 augmentation="one additional short-edge-256 JPEG50 view per training clip; each view weight 0.5",
                 status="research_only_not_deployed",
                 candidates=[dict(C=-r[2], recall=r[0], auc=r[1], threshold=r[4]) for r in candidates])
    out.write_text(json.dumps(model, indent=2)+"\n")
    print(json.dumps({k:v for k,v in model.items() if k != "coefficients"},indent=2))


def evaluate(plan_path):
    out = plan_path.parent / "test-report.json"
    if out.exists():
        raise ValueError("Test already evaluated; do not repeatedly tune against this holdout")
    candidate = plan_path.parent / "candidate.json"
    model = json.loads(candidate.read_text())
    if model["dataset_plan_sha256"] != digest(plan_path):
        raise ValueError("Dataset plan changed after training")
    rows, x, _, y = load_features(plan_path, {"test"})
    score = linear_scores(model, x)
    flags = score >= model["threshold"]
    baseline, inconclusive = [], []
    for row in rows:
        result = json.loads((plan_path.parent / "baseline" / (key(row)+".json")).read_text())
        if result["file"] != row["file"] or result["video_sha256"] != row["sha256"]:
            raise ValueError("Baseline provenance mismatch")
        baseline.append(result["label"] == "AI-like visual signal")
        inconclusive.append(result["label"] == "Inconclusive")
    trained_stats, baseline_stats = metrics(y, flags), metrics(y, baseline)
    baseline_stats["inconclusive_clips"] = sum(inconclusive)
    baseline_stats["comparison_note"] = "AI-flag metrics: abstentions count as unflagged, not correct real verdicts"
    by_source = {}
    for source in sorted({r["source"] for r in rows}):
        ids = [i for i,r in enumerate(rows) if r["source"] == source]
        by_source[source] = dict(clips=len(ids), ai_flags=int(flags[ids].sum()),
                                 waverep_ai_flags=sum(baseline[i] for i in ids),
                                 unseen_generator=source == "Veo")
    meets_pilot = (trained_stats["ai_recall"] >= .8 and trained_stats["real_false_positive_rate"] <= .1
                   and trained_stats["ai_recall"] > baseline_stats["ai_recall"]
                   and trained_stats["real_false_positive_rate"] <= baseline_stats["real_false_positive_rate"])
    report = dict(schema=1, candidate_sha256=digest(candidate), plan_sha256=digest(plan_path),
                  candidate=trained_stats, waverep=baseline_stats, by_source=by_source,
                  meets_predeclared_pilot_target=meets_pilot, production_ready=False,
                  limitations=["Only 20 independent action groups and 20 real test clips; intervals are clip-level approximations.",
                               "Action-disjoint, but creator identities unavailable and near-duplicate scenes not ruled out.",
                               "Six frames across a full public clip, not a live six-second social-media capture.",
                               "Older controlled generators and stock real footage; not representative of all current social videos.",
                               "Threshold selected on only 20 validation real clips; zero validation false flags is not a guarantee."],
                  predictions=[dict(file=r["file"], label=r["label"], group=r["group"],
                                    score=float(s), ai_flag=bool(f)) for r,s,f in zip(rows,score,flags)])
    out.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k != "predictions"},indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["train", "evaluate"])
    p.add_argument("--plan", type=Path, default=DEFAULT)
    a = p.parse_args()
    (train if a.command == "train" else evaluate)(a.plan)
