"""Package tracked source only; models, tokens, private exports and envs are excluded."""
from pathlib import Path
import subprocess
import zipfile
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'dist/uncanny-0.4.0-beta.1.zip'
DEST.parent.mkdir(exist_ok=True)
files=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
with zipfile.ZipFile(DEST,'w',zipfile.ZIP_DEFLATED) as archive:
    for name in files:
        if not name:continue
        if name.startswith(('.models/','captures/','.venv/','.runtime/','.env','dist/')):
            raise ValueError('Private or generated file unexpectedly tracked: '+name)
        path=ROOT/name
        if path.is_file():archive.write(path,'uncanny/'+name)
print(DEST)
