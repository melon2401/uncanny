"""Compare pipelines on saved samples; one independent result per source video."""
import argparse
import json
from collections import defaultdict
from pathlib import Path
try:
    from .server import analyze, load_model, PIPELINE
except ImportError:
    from server import analyze, load_model, PIPELINE

def evaluate(folder, sample_paths=None, source_groups=None):
    groups = defaultdict(list)
    for path in sorted(sample_paths if sample_paths is not None else Path(folder).glob('*.json')):
        data = json.loads(path.read_text())
        if data.get('schema') != 1 or data.get('label') not in ('ai', 'real', 'unknown'):
            continue
        if not data.get('source'):
            raise ValueError(f'{path.name}: missing video source')
        group = source_groups[str(path)] if source_groups is not None else data['source']
        groups[group].append(data)
    if not groups:
        raise ValueError('No samples found. Export a test sample first.')
    session = load_model()
    report = {}
    for pipeline in ('legacy', PIPELINE):
        counts = {label: dict(videos=0, strong=0, weak=0, inconclusive=0) for label in ('ai', 'real')}
        details = []
        for source, samples in groups.items():
            labels = {s['label'] for s in samples}
            if len(labels) != 1:
                raise ValueError(f'Conflicting ground-truth labels for {source}')
            results = [analyze(session, [f['data'] for f in s['frames']], pipeline) for s in samples]
            verdicts = {r['label'] for r in results}
            # Repeated captures never inflate sample size or outweigh contradictory evidence.
            verdict = verdicts.pop() if len(verdicts) == 1 else 'Inconclusive'
            key = {'Strong synthetic signal':'strong', 'Weak synthetic signal':'weak', 'Inconclusive':'inconclusive'}[verdict]
            label = samples[0]['label']
            if label != 'unknown':
                counts[label]['videos'] += 1
                counts[label][key] += 1
            details.append(dict(source=source, label=label, verdict=verdict, results=results))
        real, ai = counts['real'], counts['ai']
        report[pipeline] = dict(counts=counts,
            unknown_videos=sum(d['label'] == 'unknown' for d in details),
            false_positive_rate=real['strong']/real['videos'] if real['videos'] else None,
            ai_detection_rate=ai['strong']/ai['videos'] if ai['videos'] else None,
            ai_inconclusive_rate=ai['inconclusive']/ai['videos'] if ai['videos'] else None,
            details=details)
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder')
    args = parser.parse_args()
    print(json.dumps(evaluate(args.folder), indent=2))
