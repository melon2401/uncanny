"""Audit approved SLOP metadata and select a small creator-separated pilot.

Run only after legitimate dataset access. This script downloads nothing, accepts
no credentials and keeps creator/video metadata in the ignored research folder.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"file_name", "split", "label", "platform", "creator_id", "handle",
            "sha256", "provenance", "size_bytes"}
QUOTAS = {"train":100, "validation":30, "test":50}


def rank(value):
    return hashlib.sha256(("uncanny-slop-v1:"+value).encode()).hexdigest()


def creator_balanced(rows):
    creators = defaultdict(list)
    for row in rows:
        creators[row["group"]].append(row)
    for values in creators.values():
        values.sort(key=lambda r:rank(r["file"]))
    # Round-robin creators, at most three clips per creator per cell.
    return [creators[c][i] for i in range(3) for c in sorted(creators,key=rank)
            if i < len(creators[c])]


def prepare(records):
    creators, handles, hashes, paths = {}, {}, {}, set()
    cells = defaultdict(list)
    excluded = Counter()
    for record in sorted(records,key=lambda r:r.get("file_name", "")):
        if not REQUIRED <= record.keys():
            raise ValueError("Missing required SLOP metadata fields")
        split, label, platform = (record[k].strip() for k in ("split","label","platform"))
        if split not in QUOTAS or label not in ("ai","real") or platform not in ("instagram","tiktok","x"):
            raise ValueError("Unknown split, label or platform")
        if platform == "x":
            excluded["outside_target_platforms"] += 1
            continue
        handle, creator = record["handle"].strip().lower(), record["creator_id"].strip()
        if not handle or not creator:
            excluded["unverifiable_creator"] += 1
            continue
        if record["provenance"] != "original":
            excluded["substitute_provenance"] += 1
            continue
        for mapping, identifier in ((creators,creator),(handles,platform+":"+handle)):
            if mapping.setdefault(identifier,(split,label)) != (split,label):
                raise ValueError("Creator crosses official splits or has conflicting labels")
        path = PurePosixPath(record["file_name"])
        if path.is_absolute() or ".." in path.parts or path.suffix != ".mp4":
            raise ValueError("Unsafe or unexpected video path")
        if path.parts[0] not in QUOTAS:
            path = PurePosixPath(split)/path
        if path.parts[:3] != (split,platform,label) or len(path.parts) != 4 or str(path) in paths:
            raise ValueError("Video path does not match metadata, or repeats")
        paths.add(str(path))
        sha = record["sha256"].lower()
        size = int(record["size_bytes"])
        if not re.fullmatch(r"[a-f0-9]{64}",sha) or size <= 0:
            raise ValueError("Missing content checksum or invalid file size")
        if sha in hashes:
            if hashes[sha] != (split,label):
                raise ValueError("Identical video crosses splits or has conflicting labels")
            excluded["duplicate_file"] += 1
            continue
        hashes[sha] = (split,label)
        cells[(split,platform,label)].append(dict(file=str(path),group=creator,split=split,
                                                 label=label,source=platform,sha256=sha,bytes=size))
    selected = []
    for split,quota in QUOTAS.items():
        for platform in ("instagram","tiktok"):
            real = creator_balanced(cells[(split,platform,"real")])
            ai = creator_balanced(cells[(split,platform,"ai")])
            count = min(quota,len(real),len(ai))
            if not count:
                raise ValueError(f"No balanced eligible videos for {split}/{platform}")
            selected.extend(real[:count]+ai[:count])
    summary = dict(selected_entries=len(selected), download_bytes=sum(r["bytes"] for r in selected),
                   exclusions=dict(excluded), counts=dict(Counter(f"{r['split']}/{r['source']}/{r['label']}" for r in selected)),
                   creator_groups={s:len({r["group"] for r in selected if r["split"]==s}) for s in QUOTAS})
    return dict(dataset="matybohacek/slop", selection="original-provenance-known-creators-v1",
                status="metadata_selection_only_requires_real_data_audit_before_training",
                summary=summary, rows=selected)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest",type=Path)
    p.add_argument("--output",type=Path,default=ROOT/".models/training/slop-v1/selection.json")
    a = p.parse_args()
    if a.output.exists():
        raise SystemExit("Selection already exists; inspect it instead of silently replacing it")
    with a.manifest.open(newline="") as handle:
        result = prepare(list(csv.DictReader(handle)))
    result["manifest_sha256"] = hashlib.sha256(a.manifest.read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result["summary"],indent=2))
