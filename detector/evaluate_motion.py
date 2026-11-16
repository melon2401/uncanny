"""Repeatable local development evaluation; no thresholds or accuracy claims."""
import argparse
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
try:
    from .motion_window import select_window
except ImportError:
    from motion_window import select_window


def summarize(rows):
    scored = [r for r in rows if r['status'] == 'scored']
    real = [r['score'] for r in scored if r['label'] == 'real']
    ai = [r['score'] for r in scored if r['label'] == 'ai']
    pairs = len(real) * len(ai)
    wins = sum(r > a for r in real for a in ai)
    ties = sum(r == a for r in real for a in ai)
    return dict(status_counts=dict(Counter(r['status'] for r in rows)),
                scored_by_label=dict(Counter(r['label'] for r in scored)),
                excluded_by_label=dict(Counter(r['label'] for r in rows if r['status'] != 'scored')),
                real_range=[min(real), max(real)] if real else None,
                ai_range=[min(ai), max(ai)] if ai else None,
                correctly_ordered_pairs=wins, tied_pairs=ties, total_pairs=pairs,
                pairwise_ranking=(wins + .5 * ties) / pairs if pairs else None,
                note='Development ranking only, not classification accuracy. Screening exclusions are reported; labels are user supplied.')


def evaluate(paths, infer):
    rows, groups = [], defaultdict(list)
    for path in paths:
        try:
            sample = json.loads(Path(path).read_text())
            window, audit, start = select_window(sample)
            row = dict(id=f'sample-{len(rows)+1}', label=sample.get('label', 'unknown'),
                       status='excluded', issues=audit['issues'])
            rows.append(row)
            digest = audit.get('sequence_hash')
            if digest:
                groups[digest].append((row, window or sample, audit))
        except (ValueError, OSError, KeyError, TypeError, AttributeError):
            rows.append(dict(id=f'sample-{len(rows)+1}', label='unknown', status='excluded', issues=['Unreadable export']))
    sources = Counter()
    for entries in groups.values():
        labels = {r['label'] for r, _, _ in entries if r['label'] in ('ai', 'real')}
        if len(labels) > 1:
            for row, _, _ in entries:
                row.update(status='label_conflict', issues=['Identical sequence has conflicting labels'])
            continue
        chosen = next((e for e in entries if e[0]['label'] in labels), entries[0])
        for entry in entries:
            if entry is not chosen:
                entry[0].update(status='duplicate', issues=['Repeated sequence; counted once'])
        row, sample, audit = chosen
        if not audit['ready']:
            continue
        if row['label'] not in ('ai', 'real'):
            row['issues'] = ['Ground-truth label missing']
            continue
        source = sample.get('source')
        if source:
            sources[source] += 1
        start = time.monotonic()
        try:
            result = infer(sample)
            score = result.get('real_reference_score')
            if result.get('status') != 'experimental' or score is None:
                row.update(status='abstained', issues=[result.get('reason', 'No score')])
            elif not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError('Invalid score')
            else:
                row.update(status='scored', score=score, issues=[])
        except Exception:
            row.update(status='error', issues=['Inference failed; inspect local model setup'])
        row['seconds'] = round(time.monotonic()-start, 3)
    return dict(samples=rows, summary=summarize(rows),
                repeated_source_groups=sum(n > 1 for n in sources.values()),
                warning='Same-source clips are not independent. No source URLs or image data are included. No model threshold is fitted.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('samples', nargs='+', type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--device', choices=['cpu','mps'], default='cpu')
    a = p.parse_args()
    from compare_stall import compare
    root = Path(__file__).resolve().parents[1]
    report = evaluate(a.samples, lambda s: compare(s, None, None, str(root/'.models/stall/params.npz'),
                      str(root/'.models/dinov3-hf'), a.device, 4))
    a.output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report['summary'], indent=2))
