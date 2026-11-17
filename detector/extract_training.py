"""Cache verified DINOv3 features, then (separately) current-detector baselines."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import time
import numpy as np

try:
    from .training_data import DEFAULT, digest, validate
    from .trained_features import Embedder, FEATURE_VERSION, clip_feature, compressed_image, video_frames
except ImportError:
    from training_data import DEFAULT, digest, validate
    from trained_features import Embedder, FEATURE_VERSION, clip_feature, compressed_image, video_frames


def key(row):
    return hashlib.sha256(row["file"].encode()).hexdigest()[:24]


def extract(plan_path, device, baseline=False, splits=None):
    plan = validate(json.loads(plan_path.read_text()))
    cache = plan_path.parent / ("baseline" if baseline else "features")
    cache.mkdir(exist_ok=True)
    rows = [r for r in plan["rows"] if not splits or r["split"] in splits]
    embedder = None
    start = time.monotonic()
    for i, row in enumerate(rows, 1):
        out = cache / (key(row) + (".json" if baseline else ".npz"))
        if out.exists():
            continue
        video = plan_path.parent / "videos" / row["file"]
        if digest(video) != row["sha256"]:
            raise ValueError(f"Unverified video: {row['file']}")
        images, timestamps = video_frames(video)
        if baseline:
            try:
                from .waverep import analyze
            except ImportError:
                from waverep import analyze
            frames = []
            for image in images:
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=90)
                frames.append("data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode())
            result = analyze(frames)
            result.update(file=row["file"], video_sha256=row["sha256"])
            out.write_text(json.dumps(result, indent=2))
        else:
            if embedder is None:
                embedder = Embedder(device)
            normal = embedder(images)
            compressed = embedder([compressed_image(im) for im in images]) if row["split"] == "train" else normal
            # Atomic file replacement makes interrupted extraction safe to resume.
            tmp = out.with_suffix(".tmp")
            with tmp.open("wb") as handle:
                np.savez_compressed(handle, feature=clip_feature(normal), augmented=clip_feature(compressed),
                                    frames=normal, timestamps=timestamps, source_file=row["file"],
                                    video_sha256=row["sha256"], feature_version=FEATURE_VERSION)
            tmp.replace(out)
        if i % 10 == 0 or i == len(rows):
            print(f"{'Baseline' if baseline else 'Features'} {i}/{len(rows)}, elapsed {time.monotonic()-start:.0f}s", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan", type=Path, default=DEFAULT)
    p.add_argument("--device", choices=["cpu", "mps"], default="mps")
    p.add_argument("--baseline", action="store_true")
    p.add_argument("--splits", nargs="+", choices=["train", "validation", "test"])
    a = p.parse_args()
    extract(a.plan, a.device, a.baseline, a.splits)
