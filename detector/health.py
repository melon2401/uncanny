"""Minimal loopback readiness response; no media or account details."""
import json
import re


def respond(handler, port, service):
    if handler.path != '/health':
        return handler.send_error(404)
    origin = handler.headers.get('Origin')
    if (handler.headers.get('Host') != f'127.0.0.1:{port}' or
            (origin and not re.fullmatch(r'chrome-extension://[a-p]{32}', origin))):
        return handler.send_error(403)
    data = json.dumps({'app': 'uncanny', 'service': service, 'ready': True}).encode()
    handler.send_response(200)
    handler.send_header('Content-Type', 'application/json')
    handler.send_header('Cache-Control', 'no-store')
    handler.end_headers()
    handler.wfile.write(data)
