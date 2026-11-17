"""Reproducible DeepAction pilot selection and verified, resumable downloads.

No user exports are used here. Dataset bytes live under ignored .models/training.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "faridlab/deepaction_v1"
REVISION = "476932c3369424ca59dc1f8fb758cb3c13fe63fe"
SOURCES = ("Pexels", "BDAnimateDiffLightning", "CogVideoX5B", "RunwayML",
           "StableDiffusion", "VideoPoet", "Veo")
DEFAULT = ROOT / ".models/training/deepaction-v1/plan.json"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def select(files):
    """Split by action/prompt before looking at any model outputs."""
    actions = {p.split("/")[1] for p in files if p.startswith("Pexels/") and p.endswith("/a.mp4")}
    if len(actions) != 100:
        raise ValueError("Expected the pinned dataset's 100 real action groups")
    actions = sorted(actions, key=lambda a: hashlib.sha256(("uncanny-action-v1:" + a).encode()).hexdigest())
    rows = []
    for i, action in enumerate(actions):
        split = "train" if i < 60 else "validation" if i < 80 else "test"
        for source in SOURCES:
            if source == "Veo" and split != "test":
                continue  # Entire generator excluded from training and selection.
            name = f"{source}/{action}/a.mp4"
            if name not in files:
                raise ValueError(f"Missing required file: {name}")
            rows.append(dict(file=name, group=action, source=source,
                             label="real" if source == "Pexels" else "ai", split=split,
                             **files[name]))
    return rows


def validate(plan):
    if plan["dataset"] != REPO or plan["revision"] != REVISION:
        raise ValueError("Unexpected dataset revision")
    groups, paths, hashes = {}, set(), {}
    for row in plan["rows"]:
        name = row["file"]
        if name in paths or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Duplicate/unsafe file path")
        paths.add(name)
        if groups.setdefault(row["group"], row["split"]) != row["split"]:
            raise ValueError("Action group crosses splits")
        if row["source"] == "Veo" and row["split"] != "test":
            raise ValueError("Held-out generator leaked")
        if row["label"] != ("real" if row["source"] == "Pexels" else "ai"):
            raise ValueError("Source label mismatch")
        sha = row.get("sha256")
        if not sha or len(sha) != 64:
            raise ValueError("Missing upstream content hash")
        previous = hashes.setdefault(sha, (row["split"], row["label"]))
        if previous != (row["split"], row["label"]):
            raise ValueError("Identical content crosses splits or labels")
    return plan


def make_plan(path):
    from huggingface_hub import HfApi
    info = HfApi().dataset_info(REPO, revision=REVISION, files_metadata=True)
    files = {f.rfilename: dict(bytes=f.size, sha256=f.lfs.sha256)
             for f in info.siblings if f.rfilename.endswith(".mp4") and f.lfs}
    plan = validate(dict(schema=1, dataset=REPO, revision=REVISION, rows=select(files),
                         licenses={"ai": "CC-BY-4.0", "real": "Pexels License"},
                         split_unit="action/prompt; creator identity unavailable",
                         held_out_generator="Veo"))
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(plan, indent=2) + "\n"
    if path.exists() and path.read_text() != serialized:
        raise ValueError("Refusing to overwrite an existing experiment plan")
    path.write_text(serialized)
    print(json.dumps(dict(plan=str(path), sha256=digest(path),
                          clips=dict(Counter(r["split"] for r in plan["rows"])),
                          download_bytes=sum(r["bytes"] for r in plan["rows"])), indent=2))


def download(path):
    from huggingface_hub import hf_hub_download
    plan = validate(json.loads(path.read_text()))
    def get(row):
        target = path.parent / "videos" / row["file"]
        if not target.exists() or digest(target) != row["sha256"]:
            target = Path(hf_hub_download(REPO, row["file"], repo_type="dataset",
                                         revision=REVISION, local_dir=path.parent / "videos"))
        if digest(target) != row["sha256"]:
            raise ValueError(f"Checksum mismatch: {row['file']}")
        return row["file"]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, _ in enumerate(pool.map(get, plan["rows"]), 1):
            if i % 20 == 0 or i == len(plan["rows"]):
                print(f"Verified {i}/{len(plan['rows'])} videos", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "download"])
    parser.add_argument("--plan", type=Path, default=DEFAULT)
    args = parser.parse_args()
    (make_plan if args.command == "plan" else download)(args.plan)
