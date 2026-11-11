"""Offline motion adapter. Requires approved, locally downloaded original DINOv3 weights."""
import argparse
import base64
import hashlib
import io
import json
import sys
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from torchvision import transforms
try:
    from .stall_score import score_embeddings, validate_motion
except ImportError:
    from stall_score import score_embeddings, validate_motion

CALIB_SHA='beede546ca4385242c2a26075b8087ab51bee709549fc4ddc79d0eef5acce240'

def compare(sample_path, repo, weights, calibration):
    sample=json.loads(Path(sample_path).read_text())
    validate_motion(sample)
    if not Path(weights).is_file() or not Path(repo,'dinov3/hub/backbones.py').is_file():
        raise ValueError('DINOv3 source and approved original ViT-L/16 checkpoint are required')
    if hashlib.sha256(Path(calibration).read_bytes()).hexdigest()!=CALIB_SHA:
        raise ValueError('Calibration checksum mismatch')
    sys.path.insert(0,str(Path(repo).resolve()))
    from dinov3.hub.backbones import dinov3_vitl16
    model=dinov3_vitl16(weights=str(Path(weights).resolve())).eval()
    transform=transforms.Compose([transforms.ToTensor(),
        transforms.Resize((224,224),antialias=True),
        transforms.Normalize((.485,.456,.406),(.229,.224,.225))])
    embeddings=[]
    with torch.inference_mode():
        for frame in sample['frames']:
            im=Image.open(io.BytesIO(base64.b64decode(frame['data'].split(',')[1]))).convert('RGB')
            embeddings.append(model(transform(im)[None]).cpu().numpy()[0])
    with np.load(calibration,allow_pickle=False) as params:
        result=score_embeddings(np.stack(embeddings),params)
    result.update(model='STALL with original DINOv3 ViT-L/16',known_label=sample.get('label','unknown'))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('sample');p.add_argument('--dino-repo',required=True);p.add_argument('--weights',required=True)
    p.add_argument('--calibration',default='.models/stall/params.npz');p.add_argument('--output',required=True)
    a=p.parse_args();r=compare(a.sample,a.dino_repo,a.weights,a.calibration)
    Path(a.output).write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
