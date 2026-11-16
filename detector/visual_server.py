"""Local-only WaveRep image service; no media is written or uploaded."""
import json
import re
from http.server import BaseHTTPRequestHandler,HTTPServer
from PIL import Image
from waverep import analyze,load_model
from health import respond


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup();self.connection.settimeout(20)

    def do_GET(self):
        return respond(self,8767,'stills')

    def do_POST(self):
        if self.path!='/v1/score':return self.send_error(404)
        origin=self.headers.get('Origin')
        if (self.headers.get('Host')!='127.0.0.1:8767' or
            (origin and not re.fullmatch(r'chrome-extension://[a-p]{32}',origin)) or
            self.headers.get('X-Uncanny-Client')!='popup'):return self.send_error(403)
        if self.headers.get_content_type()!='application/json':return self.send_error(415)
        try:
            size=int(self.headers.get('Content-Length',0))
            if not 0<size<=6_000_000:return self.send_error(413)
            payload=json.loads(self.rfile.read(size))
            if not isinstance(payload,dict):raise ValueError()
            result=analyze(payload.get('frames'))
        except (ValueError,TypeError,OSError,Image.DecompressionBombError):
            return self.send_error(400,'Invalid frame request')
        except Exception:
            return self.send_error(503,'Visual model unavailable')
        data=json.dumps(result).encode()
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers()
        try:self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError):pass


if __name__=='__main__':
    _,device=load_model()
    with HTTPServer(('127.0.0.1',8767),Handler) as server:
        print(f'Uncanny visual detector ready (WaveRep, {device})',flush=True)
        server.serve_forever()
