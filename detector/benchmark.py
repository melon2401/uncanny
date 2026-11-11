"""Audit labeled samples before evaluating development or held-out videos."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
try:
    from .evaluate import evaluate
except ImportError:
    from evaluate import evaluate


def audit(manifest):
    manifest = Path(manifest).resolve()
    entries = json.loads(manifest.read_text())
    if not isinstance(entries, list) or not entries:
        raise ValueError('Manifest must contain sample entries')
    groups, sources, fingerprints = {}, {}, {}
    paths = {'development': [], 'heldout': []}
    counts = {split: {'ai': set(), 'real': set()} for split in paths}
    seen_paths = set()
    for entry in entries:
        split, group, label = entry['split'], entry['group'], entry['label']
        if split not in paths or label not in ('ai','real') or not group or not entry.get('evidence','').strip():
            raise ValueError('Every sample needs split, group, known label and label evidence')
        path = (manifest.parent / entry['file']).resolve()
        if path in seen_paths:
            raise ValueError('Duplicate sample path')
        seen_paths.add(path)
        sample = json.loads(path.read_text())
        if sample.get('schema') != 1 or sample.get('label') != label or len(sample.get('frames',[])) != 6:
            raise ValueError('Sample schema or ground-truth label does not match manifest')
        source = sample.get('source')
        if not source:
            raise ValueError('Missing source')
        # Shared source/group always stays in one split, including related reuploads.
        for mapping, key in [(groups, group), (sources, source)]:
            if key in mapping and mapping[key] != (split,label):
                raise ValueError('Source/group crosses splits or has conflicting labels')
            mapping[key] = (split,label)
        for frame in sample['frames']:
            data = frame['data']
            if not data.startswith('data:image/jpeg;base64,'):
                raise ValueError('Expected captured JPEG')
            digest = hashlib.sha256(base64.b64decode(data.split(',',1)[1],validate=True)).hexdigest()
            if digest in fingerprints and fingerprints[digest] != split:
                raise ValueError('Identical frame appears in both splits')
            fingerprints[digest] = split
        counts[split][label].add(group)
        paths[split].append(path)
    sizes = {s:{label:len(g) for label,g in labels.items()} for s,labels in counts.items()}
    warnings = []
    if not all(sizes['heldout'].values()):
        warnings.append('No balanced held-out set. No generalization claim is supported.')
    if any(v < 10 for labels in sizes.values() for v in labels.values()):
        warnings.append('Small sample counts: diagnostic only, not a dependable accuracy estimate.')
    return paths, dict(independent_groups=sizes, warnings=warnings)


def run(manifest, split):
    paths, result = audit(manifest)
    if not all(result['independent_groups'][split].values()):
        raise ValueError('Selected split must include both known AI and known real sources')
    # Inference is performed only on the explicitly selected split.
    result['split'] = split
    base = Path(manifest).resolve().parent
    source_groups = {str((base/e['file']).resolve()):e['group'] for e in json.loads(Path(manifest).read_text())}
    result['results'] = evaluate(None, sample_paths=paths[split], source_groups=source_groups)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest')
    parser.add_argument('--split', choices=['development','heldout'], default='development')
    parser.add_argument('--audit-only', action='store_true')
    parser.add_argument('--output')
    args=parser.parse_args()
    result = audit(args.manifest)[1] if args.audit_only else run(args.manifest,args.split)
    text=json.dumps(result,indent=2)
    if args.output: Path(args.output).write_text(text)
    print(text)
