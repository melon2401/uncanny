"""Offline crop-sensitivity diagnostic. Does not change extension scoring."""
import argparse
import base64
import io
import json
import math
import statistics
from PIL import Image
try:
    from .server import load_model, preprocess
except ImportError:
    from server import load_model, preprocess


def inspect(sample):
    session = load_model()
    rows = []
    for frame in sample['frames']:
        im = Image.open(io.BytesIO(base64.b64decode(frame['data'].split(',')[1]))).convert('RGB')
        w, h = im.size
        # Fixed five regions, selected before inference. Never choose the most AI-looking crop.
        side = round(min(w, h) * .65)
        boxes = dict(full=(0, 0, w, h), top_left=(0, 0, side, side),
                     top_right=(w-side, 0, w, side), bottom_left=(0, h-side, side, h),
                     bottom_right=(w-side, h-side, w, h),
                     center=((w-side)//2, (h-side)//2, (w-side)//2+side, (h-side)//2+side))
        scores = {}
        for name, box in boxes.items():
            tensor, _ = preprocess(im.crop(box))
            logit = float(session.run(None, {'pixel_values': tensor})[0].item())
            scores[name] = round(100 / (1 + math.exp(-max(-80, min(80, logit)))), 2)
        rows.append(dict(time=frame['time'], scores=scores,
                         crop_median=statistics.median([v for k,v in scores.items() if k != 'full'])))
    return dict(experimental=True, label=sample['label'],
                warning='Crop sensitivity only; not a validated detector or a probability.',
                frames=rows,
                full_frame_median=statistics.median(r['scores']['full'] for r in rows),
                crop_median=statistics.median(r['crop_median'] for r in rows))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sample')
    args = parser.parse_args()
    with open(args.sample) as file:
        print(json.dumps(inspect(json.load(file)), indent=2))
