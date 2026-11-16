"""Choose the earliest usable consecutive window without consulting model scores."""
import math
try:
    from .audit_motion import audit_sample
except ImportError:
    from audit_motion import audit_sample


def select_window(sample):
    if not isinstance(sample, dict):
        raise ValueError('Expected a motion sample')
    if sample.get('schema') == 2:
        audit = audit_sample(sample, require_label=False)
        return sample if audit['ready'] else None, audit, 0
    frames = sample.get('frames')
    if sample.get('schema') != 3 or sample.get('mode') != 'motion' or not isinstance(frames, list) or len(frames) != 32:
        return None, {'ready': False, 'issues': ['Expected 16-frame or 32-frame motion capture']}, None
    try:
        times = [float(f['time']) for f in frames]
        if not all(math.isfinite(t) for t in times) or any(b <= a or b-a > .5 for a,b in zip(times,times[1:])):
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        return None, {'ready': False, 'issues': ['Playback jumped, looped or stalled; capture again']}, None
    # First passing window, never the highest-scoring one. Retain all original
    # frames in the client/export and disclose the selected range in responses.
    reasons = []
    for start in range(17):
        window = {**sample, 'schema': 2, 'frames': frames[start:start+16]}
        audit = audit_sample(window, require_label=False)
        if audit['ready']:
            return window, audit, start
        reasons.extend(audit['issues'])
    return None, {'ready': False, 'issues': ['No usable continuous section found. Try a steadier part of the video.'],
                  'screening_details': list(dict.fromkeys(reasons))}, None
