"""Offline WaveRep G4 comparison on existing exports; never used for live verdicts.
Reference: grip-unina/WaveRep-SyntheticVideoDetection, commit
0fd6010759c14b572b7842a28fa9f85fe1ddd2fd. Nonprofit research use only;
see the upstream LICENSE.md. No upstream code is vendored here.
"""
import argparse
import base64
import hashlib
import io
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.models/waverep-deps'))
import numpy as np
import torch
import timm
from PIL import Image
from torchvision import transforms


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('samples',nargs='+',type=Path)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--device',choices=['cpu','mps'],default='cpu')
    a=p.parse_args()
    weights=ROOT/'.models/waverep-g4.ckpt'
    if hashlib.md5(weights.read_bytes()).hexdigest()!='8bf19e6f68a92bed600dd97fbed3f2cd':
        raise ValueError('Checkpoint differs from authors published checksum')
    model=timm.create_model('vit_base_patch14_reg4_dinov2.lvd142m',num_classes=1,pretrained=False,img_size=504)
    state=torch.load(weights,map_location='cpu',weights_only=True)
    if 'state_dict' in state:
        state={k[6:]:v for k,v in state['state_dict'].items() if k.startswith('model.')}
    model.load_state_dict(state,strict=True)
    model=model.eval().to(a.device)
    transform=transforms.Compose([transforms.CenterCrop((504,504)),transforms.ToTensor(),
                                  transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
    seen=set();rows=[]
    for path in a.samples:
        sample=json.loads(path.read_text());frames=sample.get('frames',[])
        if sample.get('label') not in ['ai','real'] or len(frames)<6:continue
        digest=hashlib.sha256(''.join(f['data'] for f in frames).encode()).hexdigest()
        if digest in seen:continue
        seen.add(digest)
        indices=np.linspace(0,len(frames)-1,6,dtype=int).tolist()
        logits=[];padded=0;start=time.monotonic()
        with torch.inference_mode():
            for i in indices:
                im=Image.open(io.BytesIO(base64.b64decode(frames[i]['data'].split(',')[1]))).convert('RGB')
                padded+=int(min(im.size)<504)
                logits.append(float(model(transform(im)[None].to(a.device))[0,-1].cpu()))
        mean=float(np.mean(logits))
        if not np.isfinite(logits).all():raise ValueError('Nonfinite result')
        row=dict(sample=path.stem,label=sample['label'],mean_logit=mean,
                 flagged_ai=mean>0,frame_logits=logits,indices=indices,padded_frames=padded,
                 seconds=round(time.monotonic()-start,2))
        rows.append(row);print(json.dumps(row),flush=True)
        a.output.write_text(json.dumps(rows,indent=2))


if __name__=='__main__':main()
