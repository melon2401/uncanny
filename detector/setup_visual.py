"""Install the primary visual model. Uses no account, key or inference API."""
import hashlib
from pathlib import Path
import subprocess
import sys
import urllib.request
import venv
ROOT=Path(__file__).resolve().parents[1]
URL='https://www.grip.unina.it/download/prog/WaveRep_SynthVideoDet/weights_dinov2_G4.ckpt'
MD5='8bf19e6f68a92bed600dd97fbed3f2cd'


def main():
    if not (3,11)<=sys.version_info[:2]<=(3,12):
        raise SystemExit('Use Python 3.11 or 3.12 for this tested setup.')
    print('Uncanny uses WaveRep for local experimental analysis. Its model is licensed for nonprofit/informational use. Read detector/licenses/WaveRep.txt before continuing. Downloads include PyTorch and a 330 MB model.')
    if input('Accept these terms and install? [y/N] ').strip().lower()!='y':
        return
    env=ROOT/'.runtime'
    if not (env/'bin/python').exists():venv.EnvBuilder(with_pip=True).create(env)
    subprocess.run([str(env/'bin/python'),'-m','pip','install','-r',str(ROOT/'detector/requirements-visual.txt')],check=True)
    path=ROOT/'.models/waverep-g4.ckpt';path.parent.mkdir(exist_ok=True)
    if path.exists() and hashlib.md5(path.read_bytes()).hexdigest()==MD5:
        print('Verified existing model.');return
    temp=path.with_suffix('.download')
    try:
        with urllib.request.urlopen(URL,timeout=90) as response,temp.open('wb') as out:
            while chunk:=response.read(1024*1024):out.write(chunk)
        if hashlib.md5(temp.read_bytes()).hexdigest()!=MD5:raise ValueError('Model checksum mismatch')
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)
    print('Setup complete. Open Start-Uncanny.command next.')


if __name__=='__main__':main()
