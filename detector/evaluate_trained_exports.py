"""External regression check of a locked pilot on already-seen user exports.

Local only. This cannot establish independent accuracy or select a new threshold.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import numpy as np
from PIL import Image

try:
    from .trained_features import Embedder, clip_feature
    from .training_data import DEFAULT, digest
    from .train_visual import linear_scores, metrics
except ImportError:
    from trained_features import Embedder, clip_feature
    from training_data import DEFAULT, digest
    from train_visual import linear_scores, metrics


def samples(folder):
    groups, content = {}, {}
    for path in sorted(folder.glob("*.json")):
        try:
            sample = json.loads(path.read_text())
        except (ValueError, OSError):
            continue
        if not isinstance(sample,dict) or sample.get("schema") not in (1,2,3) or sample.get("label") not in ("ai","real"):
            continue
        frames = sample.get("frames")
        expected = {1:6, 2:16, 3:32}[sample["schema"]]
        if not isinstance(frames,list) or len(frames) != expected or not all(isinstance(f,dict) and "data" in f for f in frames):
            continue
        # Apply the same six-frame visual probe to motion exports; this is not a
        # temporal-model test. Repeated captures still count as one source below.
        indices = np.linspace(0,len(frames)-1,6).round().astype(int).tolist()
        sample = {**sample, "frames":[frames[i] for i in indices], "selected_indices":indices}
        frames = sample["frames"]
        source = sample.get("source")
        if not isinstance(source,str) or not source:
            raise ValueError("Export missing source")
        parsed = urlsplit(source)
        # Preserve query strings for watch?v= URLs; only strip tracking for path-based reels/shorts.
        source = urlunsplit((parsed.scheme,parsed.netloc,parsed.path,
                            parsed.query if parsed.path == "/watch" else "", ""))
        group = hashlib.sha256(source.encode()).hexdigest()
        signature = hashlib.sha256("".join(f["data"] for f in frames).encode()).hexdigest()
        if signature in content:
            old_group, old_label = content[signature]
            if old_label != sample["label"]:
                raise ValueError("Duplicate frames have conflicting labels")
            continue
        content[signature] = (group,sample["label"])
        if group in groups and groups[group][0][1]["label"] != sample["label"]:
            raise ValueError("Same source has conflicting labels")
        groups.setdefault(group,[]).append((path,sample))
    return groups


def run(candidate, folder, device):
    try:
        from .waverep import analyze
    except ImportError:
        from waverep import analyze
    model = json.loads(candidate.read_text())
    groups = samples(folder)
    embedder = Embedder(device)
    details = []
    for i, (group, examples) in enumerate(groups.items(),1):
        scores, baseline_flags, captures = [], [], []
        for path, sample in examples:
            images = []
            for frame in sample["frames"]:
                data = frame["data"]
                if not data.startswith("data:image/jpeg;base64,"):
                    raise ValueError("Expected captured JPEG")
                with Image.open(io.BytesIO(base64.b64decode(data.split(",",1)[1],validate=True))) as im:
                    images.append(im.convert("RGB"))
            score = float(linear_scores(model,clip_feature(embedder(images))))
            baseline = analyze([f["data"] for f in sample["frames"]])
            scores.append(score)
            baseline_flags.append(baseline["label"] == "AI-like visual signal")
            captures.append(dict(file=path.name,score=score,ai_flag=score>=model["threshold"],
                                 waverep_label=baseline["label"], selected_indices=sample["selected_indices"]))
        flags = [s >= model["threshold"] for s in scores]
        # One result per known source. Any false alarm on a real source is a failure;
        # AI detection is credited only when all its captures are flagged.
        label = examples[0][1]["label"]
        aggregate = all if label == "ai" else any
        details.append(dict(source_id=group,label=label,ai_flag=aggregate(flags),
                            waverep_ai_flag=aggregate(baseline_flags),captures=captures))
        print(f"Regression source {i}/{len(groups)}",flush=True)
    labels = [int(d["label"] == "ai") for d in details]
    return dict(candidate_sha256=digest(candidate), evaluation="already_seen_user_labeled_regression_not_independent",
                candidate=metrics(labels,[d["ai_flag"] for d in details]),
                waverep=metrics(labels,[d["waverep_ai_flag"] for d in details]),details=details,
                captures_evaluated=sum(len(d["captures"]) for d in details),
                limitations="User labels not independently authenticated; source URLs grouped, unknown reuploads may remain.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate",type=Path,default=DEFAULT.parent / "candidate.json")
    p.add_argument("--folder",type=Path,default=Path("captures"))
    p.add_argument("--device",choices=["cpu","mps"],default="mps")
    p.add_argument("--output",type=Path,default=DEFAULT.parent / "regression-report.json")
    a = p.parse_args()
    result = run(a.candidate,a.folder,a.device)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k != "details"},indent=2))
