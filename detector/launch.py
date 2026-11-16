"""Start both local services, reuse healthy instances, stop only our own children."""
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def ready(port, service):
    try:
        with urlopen(f'http://127.0.0.1:{port}/health', timeout=1) as response:
            r = json.load(response)
        return r.get('app') == 'uncanny' and r.get('service') == service and r.get('ready') is True
    except Exception:
        return False


def main():
    children = []
    try:
        for python, script, port, service in [
            (Path('/opt/anaconda3/bin/python3'), 'visual_server.py', 8767, 'stills'),
            (Path('/opt/anaconda3/bin/python3'), 'motion_server.py', 8768, 'motion')]:
            if ready(port, service):
                print(f'{service}: already ready.', flush=True)
                continue
            if not python.exists():
                raise RuntimeError(f'Missing Python environment for {service}: {python}')
            child = subprocess.Popen([str(python), str(ROOT/'detector'/script)], cwd=ROOT,
                                     env={**os.environ, 'HF_HUB_OFFLINE': '1'})
            children.append(child)
            deadline = time.monotonic()+90
            while not ready(port, service):
                if child.poll() is not None:
                    raise RuntimeError(f'{service} failed to start. See the message above; the port may already be occupied.')
                if time.monotonic()>deadline:
                    raise RuntimeError(f'{service} did not become ready within 90 seconds.')
                time.sleep(.5)
            print(f'{service}: ready.', flush=True)
        print('Uncanny is ready. Open the extension on a playing video. Keep this window open; Ctrl+C stops services started here.', flush=True)
        if not children:
            return
        while all(p.poll() is None for p in children):
            time.sleep(1)
        raise RuntimeError('A detector stopped. Restart this launcher.')
    except KeyboardInterrupt:
        print('\nStopping Uncanny services started by this launcher.')
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill(); child.wait()


if __name__ == '__main__':
    main()
