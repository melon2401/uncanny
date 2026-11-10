"""Offline second-model comparison. Does not alter extension scoring."""
import argparse
import base64
import io
import json
import statistics
from pathlib import Path
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

MODEL = 'Ateeqq/ai-vs-human-image-detector'
REVISION = '60e82406916921b823616bee33397baab38af3f0'


def compare(paths):
    cache = Path(__file__).resolve().parents[1] / '.models' / 'huggingface'
    processor = AutoImageProcessor.from_pretrained(MODEL, revision=REVISION, cache_dir=cache, trust_remote_code=False)
    model = AutoModelForImageClassification.from_pretrained(MODEL, revision=REVISION, cache_dir=cache, trust_remote_code=False, use_safetensors=True).eval()
    ai_index = model.config.label2id['ai']
    results = []
    for path in paths:
        sample = json.loads(Path(path).read_text())
        if sample.get('schema') != 1 or len(sample.get('frames', [])) != 6:
            raise ValueError('Expected a six-frame Uncanny export')
        scores = []
        for frame in sample['frames']:
            im = Image.open(io.BytesIO(base64.b64decode(frame['data'].split(',')[1]))).convert('RGB')
            with torch.inference_mode():
                logits = model(**processor(images=im, return_tensors='pt')).logits
                scores.append(float(logits.softmax(-1)[0, ai_index]) * 100)
        # Match the existing evidence rule for comparison, not a tuned new threshold.
        verdict = 'Inconclusive'
        if len({f['data'] for f in sample['frames']}) >= 3:
            if sum(s >= 80 for s in scores) >= 5 and min(scores) > 20:
                verdict = 'Strong synthetic signal'
            elif sum(s <= 20 for s in scores) >= 5 and max(scores) < 80:
                verdict = 'Weak synthetic signal'
        results.append(dict(file=Path(path).name, known_label=sample.get('label', 'unknown'),
                            signal=round(statistics.median(scores), 2),
                            frames=[round(s, 2) for s in scores], verdict=verdict))
    return dict(model=MODEL, revision=REVISION, experimental=True, results=results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('samples', nargs='+')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = compare(args.samples)
    Path(args.output).write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
