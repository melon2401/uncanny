"""Explicit, external Hive comparison. Uploads only the JPEGs in supplied exports."""
import argparse
import base64
import hashlib
import json
import math
import os
import statistics
import uuid
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

ENDPOINT = 'https://api.thehive.ai/api/v2/task/sync'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def parse_score(payload):
    try:
        statuses = payload['status']
        if len(statuses) != 1 or str(statuses[0]['status']['code']) != '0':
            raise ValueError('Hive task did not succeed')
        output = statuses[0]['response']['output']
        if len(output) != 1:
            raise ValueError('Expected one image output')
        values = [c['score'] for c in output[0]['classes'] if c['class'] == 'ai_generated']
        if len(values) != 1:
            raise ValueError('Missing AI-generated class; check project API key')
        score = values[0]
        if isinstance(score, bool) or not isinstance(score, (float, int)) or not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError('Invalid Hive score')
        return score * 100
    except (KeyError, TypeError, IndexError) as error:
        raise ValueError('Unexpected Hive response format') from error


def upload(jpeg, key):
    boundary = 'uncanny-' + uuid.uuid4().hex
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="media"; filename="frame.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()
            + jpeg + f'\r\n--{boundary}--\r\n'.encode())
    req = Request(ENDPOINT, body, {'Authorization': 'Token '+key,
                                  'Content-Type': 'multipart/form-data; boundary='+boundary})
    try:
        with build_opener(NoRedirect).open(req, timeout=60) as response:
            return parse_score(json.load(response))
    except HTTPError as error:
        raise RuntimeError(f'Hive returned HTTP {error.code}. Check API access, quota and project type.') from None
    except URLError:
        raise RuntimeError('Hive connection failed. No automatic retry was attempted.') from None


def compare(paths, output, key):
    # Validate all frames before sending any requests.
    batches = []
    for path in paths:
        sample = json.loads(Path(path).read_text())
        if sample.get('schema') != 1 or len(sample.get('frames', [])) != 6:
            raise ValueError('Expected six-frame sample exports')
        images = []
        for frame in sample['frames']:
            prefix = 'data:image/jpeg;base64,'
            if not frame['data'].startswith(prefix):
                raise ValueError('Expected JPEG data')
            image = base64.b64decode(frame['data'][len(prefix):], validate=True)
            if not image.startswith(b'\xff\xd8') or len(image) > 1_000_000:
                raise ValueError('Invalid or oversized JPEG')
            images.append(image)
        batches.append((path, sample, images))
    cache_path = Path(output).with_suffix('.cache.json')
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    rows = []
    for path, sample, images in batches:
        scores = []
        for image in images:
            # Scope cache to this project key without storing the secret itself.
            fingerprint = hashlib.sha256(key.encode()+b'\0'+image).hexdigest()
            if fingerprint not in cache:
                cache[fingerprint] = upload(image, key)
                temporary = cache_path.with_suffix('.tmp')
                temporary.write_text(json.dumps(cache))
                temporary.replace(cache_path)
            scores.append(cache[fingerprint])
        rows.append(dict(file=Path(path).name, known_label=sample.get('label','unknown'),
                         frames=scores, median=statistics.median(scores),
                         frames_at_or_above_90=sum(s >= 90 for s in scores)))
    result = dict(provider='Hive', endpoint=ENDPOINT, results=rows,
                  note='Six JPEG requests per new sample. No motion/audio analysis; scores are not calibrated video probabilities.')
    Path(output).write_text(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('samples', nargs='+')
    parser.add_argument('--output', required=True)
    parser.add_argument('--allow-upload', action='store_true', help='Explicitly send frames to Hive; API charges may apply')
    args = parser.parse_args()
    if not args.allow_upload:
        parser.error('External upload requires --allow-upload')
    key = os.environ.get('HIVE_API_KEY', '').strip()
    if not key:
        parser.error('Set HIVE_API_KEY locally. Do not put it in source code or chat.')
    print(json.dumps(compare(args.samples, args.output, key), indent=2))
