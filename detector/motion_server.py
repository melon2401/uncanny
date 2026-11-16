"""Opt-in local motion research service. Does not return AI/real classifications."""
import json
import re
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
try:
    from .motion_window import select_window
except ImportError:
    from motion_window import select_window

ROOT = Path(__file__).resolve().parents[1]


def analyze_motion(sample, infer):
    if not isinstance(sample, dict):
        raise ValueError('Expected a motion sample')
    window, audit, start = select_window(sample)
    if not audit['ready']:
        return {'status': 'inconclusive', 'issues': audit['issues']}
    result = infer(window)
    return {**result,
            'window': {'start_frame': start, 'end_frame': start+15, 'start_seconds': window['frames'][0]['time'], 'end_seconds': window['frames'][-1]['time'], 'captured_frames': len(sample['frames'])},
            'notice': 'Research signal only. Animation and edited footage may score poorly. No reliable AI/real verdict.'}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            from .health import respond
        except ImportError:
            from health import respond
        return respond(self, 8768, 'motion')

    def setup(self):
        super().setup()
        self.connection.settimeout(20)

    def do_POST(self):
        if self.path != '/v1/motion':
            return self.send_error(404)
        origin = self.headers.get('Origin')
        if (self.headers.get('Host') != '127.0.0.1:8768' or
                (origin and not re.fullmatch(r'chrome-extension://[a-p]{32}', origin)) or
                self.headers.get('X-Uncanny-Client') != 'popup'):
            return self.send_error(403)
        if self.headers.get_content_type() != 'application/json':
            return self.send_error(415)
        try:
            size = int(self.headers.get('Content-Length', 0))
            if not 0 < size <= 24_000_000:
                return self.send_error(413)
            sample = json.loads(self.rfile.read(size))
            result = analyze_motion(sample, self.server.infer)
        except (ValueError, KeyError, TypeError, AttributeError, OSError):
            return self.send_error(400, 'Invalid motion capture')
        except Exception:
            return self.send_error(503, 'Motion model unavailable')
        data = json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass


if __name__ == '__main__':
    import torch
    from compare_stall import compare, load_embedder
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    model = str(ROOT / '.models/dinov3-hf')
    calibration = str(ROOT / '.models/stall/params.npz')
    load_embedder(None, None, model, device)
    with HTTPServer(('127.0.0.1', 8768), Handler) as server:
        server.infer = lambda sample: compare(sample, None, None, calibration, model, device, 4)
        print(f'Experimental motion service ready on 127.0.0.1:8768 ({device}); no AI/real verdicts.', flush=True)
        server.serve_forever()
