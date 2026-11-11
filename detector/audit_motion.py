"""Check local motion exports before model evaluation; never uploads footage."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path

from PIL import Image
try:
    from .stall_score import validate_motion
except ImportError:
    from stall_score import validate_motion


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
    try:
        for frame in sample['frames']:
            prefix, encoded = frame['data'].split(',', 1)
            if prefix != 'data:image/jpeg;base64':
                raise ValueError('Expected JPEG data URL')
            with Image.open(io.BytesIO(base64.b64decode(encoded, validate=True))) as image:
                image = image.convert('RGB')
                sizes.add(image.size)
                hashes.append(hashlib.sha256(str(image.size).encode() + image.tobytes()).hexdigest())
    except (ValueError, KeyError, TypeError, OSError) as error:
        return {'ready': False, 'issues': ['Invalid frame image: ' + str(error)]}
    if len(sizes) != 1:
        issues.append('Frame dimensions changed within the capture')
    if len(set(hashes)) < len(hashes):
        issues.append('Repeated decoded frames: inspect for paused or frozen footage')
    return {'ready': not issues, 'label': label, 'issues': issues,
            'duration_seconds': round(float(times[-1] - times[0]), 4),
            'distinct_frames': len(set(hashes)),
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
