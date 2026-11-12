"""Check local motion exports before model evaluation; never uploads footage."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image
try:
    from .stall_score import validate_motion
except ImportError:
    from stall_score import validate_motion


def find_cuts(gray_frames, ratio=3.0, floor=40.0):
    """Flag adjacent pairs whose mean pixel change dwarfs the clip's typical motion.

    Heuristic chosen by visual inspection of ten development captures; it is a
    prompt to inspect, not a validated shot-boundary detector.
    """
    diffs = [float(np.abs(a - b).mean()) for a, b in zip(gray_frames, gray_frames[1:])]
    typical = float(np.median(diffs)) if diffs else 0.0
    return [i for i, d in enumerate(diffs) if d > floor and d > ratio * typical]


def audit_sample(sample):
    issues = []
    try:
        times = validate_motion(sample)
    except (ValueError, KeyError, TypeError) as error:
        return {'ready': False, 'issues': [str(error)]}
    label = sample.get('label', 'unknown')
    if label not in ('ai', 'real'):
        issues.append('A known AI or known real label is required for evaluation')
    hashes = []
    sizes = set()
    grays = []
    try:
        for frame in sample['frames']:
            prefix, encoded = frame['data'].split(',', 1)
            if prefix != 'data:image/jpeg;base64':
                raise ValueError('Expected JPEG data URL')
            with Image.open(io.BytesIO(base64.b64decode(encoded, validate=True))) as image:
                image = image.convert('RGB')
                sizes.add(image.size)
                hashes.append(hashlib.sha256(str(image.size).encode() + image.tobytes()).hexdigest())
                grays.append(np.asarray(image.convert('L'), dtype=np.float32))
    except (ValueError, KeyError, TypeError, OSError) as error:
        return {'ready': False, 'issues': ['Invalid frame image: ' + str(error)]}
    if len(sizes) != 1:
        issues.append('Frame dimensions changed within the capture')
    if len(set(hashes)) < len(hashes):
        issues.append('Repeated decoded frames: inspect for paused or frozen footage')
    cuts = find_cuts(grays) if len(sizes) == 1 else []
    if cuts:
        issues.append('Possible scene cut after frame(s) ' + ', '.join(map(str, cuts)) +
                      ': STALL assumes one continuous shot; inspect before scoring')
    return {'ready': not issues, 'label': label, 'issues': issues,
            'duration_seconds': round(float(times[-1] - times[0]), 4),
            'distinct_frames': len(set(hashes)), 'cut_after_frames': cuts,
            'sequence_hash': hashlib.sha256(''.join(hashes).encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('samples', nargs='+', type=Path)
    args = parser.parse_args()
    seen = set()
    results = []
    for path in args.samples:
        try:
            result = audit_sample(json.loads(path.read_text()))
        except (OSError, ValueError, TypeError, AttributeError) as error:
            result = {'ready': False, 'issues': [str(error)]}
        digest = result.pop('sequence_hash', None)
        if digest in seen:
            result['ready'] = False
            result['issues'].append('Duplicate sequence in this batch; do not count twice')
        if digest:
            seen.add(digest)
        results.append({'file': path.name, **result})
    print(json.dumps({'samples': results, 'ready_count': sum(r['ready'] for r in results),
                      'note': 'Capture checks only; readiness does not establish label correctness or detector accuracy.'}, indent=2))


if __name__ == '__main__':
    main()
