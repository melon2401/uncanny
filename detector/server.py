"""Loopback-only, in-memory still-frame detector."""
import base64
import hashlib
import io
import json
import math
import re
import statistics
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.request import urlopen
import numpy as np
import onnxruntime as ort
from PIL import Image, ImageOps

MODEL = Path(__file__).resolve().parents[1] / '.models/v1.onnx'
URL = 'https://huggingface.co/buildborderless/CommunityForensics-DeepfakeDet-ViT/resolve/ac6ee457bea904a373065754107451793b56db00/onnx/model.onnx'
SHA = 'a42c7d740fbb345ba9a26d469b22f301d73089ce3c6da993877ed2b6965a8ba1'


def load_model():
    if not MODEL.exists():
        MODEL.parent.mkdir(exist_ok=True)
        with urlopen(URL, timeout=90) as response:
            data = response.read(87442081)
        if hashlib.sha256(data).hexdigest() != SHA:
            raise ValueError('Downloaded model failed verification.')
        MODEL.write_bytes(data)
    if hashlib.sha256(MODEL.read_bytes()).hexdigest() != SHA:
        raise ValueError('Model checksum mismatch.')
    session = ort.InferenceSession(str(MODEL), providers=['CPUExecutionProvider'])
    if session.get_outputs()[0].shape[-1] != 1:
        raise ValueError('Expected a single synthetic-image logit.')
    return session


PIPELINE = 'commfor-original-preprocess-v1'


def preprocess(im, pipeline=PIPELINE):
    im = im.convert('RGB')
    if pipeline == 'legacy':
        rgb = ImageOps.fit(im, (440, 440), method=Image.Resampling.BICUBIC).crop((28, 28, 412, 412))
        mean, std = [.48145466,.4578275,.40821073], [.26862954,.26130258,.27577711]
    elif pipeline == PIPELINE:
        # Match authors' torchvision Resize(440), CenterCrop(384), ImageNet Normalize.
        w, h = im.size
        size = (440, int(440 * h / w)) if w <= h else (int(440 * w / h), 440)
        resized = im.resize(size, Image.Resampling.BILINEAR)
        left, top = round((size[0] - 384) / 2), round((size[1] - 384) / 2)
        rgb = resized.crop((left, top, left + 384, top + 384))
        mean, std = [.485,.456,.406], [.229,.224,.225]
    else:
        raise ValueError('Unknown pipeline')
    arr = np.asarray(rgb, dtype=np.float32) / 255
    arr = (arr - np.array(mean, np.float32)) / np.array(std, np.float32)
    return arr.transpose(2, 0, 1)[None], hashlib.sha256(rgb.tobytes()).digest()


def analyze(session, frames, pipeline=PIPELINE):
    if not isinstance(frames, list) or len(frames) != 6:
        raise ValueError('Expected six frames.')
    scores, unique = [], set()
    for frame in frames:
        prefix = 'data:image/jpeg;base64,'
        if not isinstance(frame, str) or not frame.startswith(prefix):
            raise ValueError('Expected JPEG frames.')
        with Image.open(io.BytesIO(base64.b64decode(frame[len(prefix):], validate=True)), formats=['JPEG']) as im:
            if max(im.size) > 720:
                raise ValueError('Frame exceeds 720 pixels.')
            arr, fingerprint = preprocess(im, pipeline)
            unique.add(fingerprint)
        logit = float(session.run(None, {'pixel_values': arr})[0].item())
        if not math.isfinite(logit):
            raise RuntimeError('Nonfinite detector output.')
        scores.append(100 / (1 + math.exp(-max(-80, min(80, logit)))))
    label = 'Inconclusive'
    if len(unique) >= 3:
        if sum(s >= 80 for s in scores) >= 5 and min(scores) > 20:
            label = 'Strong synthetic signal'
        elif sum(s <= 20 for s in scores) >= 5 and max(scores) < 80:
            label = 'Weak synthetic signal'
    reason = ('repeated_frames' if len(unique) < 3 else
              'conflicting_frames' if min(scores) <= 20 and max(scores) >= 80 else
              'threshold_not_met' if label == 'Inconclusive' else 'consistent_frames')
    return dict(pipeline=pipeline, model_sha256=SHA, reason=reason, raw_frames=scores, signal=round(statistics.median(scores)), label=label, frames=[round(s) for s in scores])


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(20)

    def do_POST(self):
        if self.path != '/v1/score':
            return self.send_error(404)
        origin = self.headers.get('Origin')
        if (self.headers.get('Host') != '127.0.0.1:8767' or
                (origin and not re.fullmatch('chrome-extension://[a-p]{32}', origin)) or
                self.headers.get('X-Uncanny-Client') != 'popup'):
            return self.send_error(403)
        if self.headers.get_content_type() != 'application/json':
            return self.send_error(415)
        try:
            size = int(self.headers.get('Content-Length', 0))
            if not 0 < size <= 6_000_000:
                return self.send_error(413)
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError()
            result = analyze(self.server.model, payload.get('frames'))
        except (ValueError, OSError, Image.DecompressionBombError):
            return self.send_error(400, 'Invalid frame request')
        data = json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)


if __name__ == '__main__':
    model = load_model()
    with HTTPServer(('127.0.0.1', 8767), Handler) as server:
        server.model = model
        print('Uncanny detector ready on 127.0.0.1:8767', flush=True)
        server.serve_forever()
