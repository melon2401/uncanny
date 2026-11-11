"""Offline motion adapter. Requires approved, locally downloaded DINOv3 weights (original or Hugging Face)."""
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

def compare(sample_path, repo, weights, calibration, hf_model=None, device="cpu", batch_size=1):
    if device not in ('cpu', 'mps') or not 1 <= batch_size <= 16:
        raise ValueError('Use cpu or mps and batch size between 1 and 16')
    if device == 'mps' and not torch.backends.mps.is_available():
        raise ValueError('MPS acceleration is unavailable in this environment')
    sample=json.loads(Path(sample_path).read_text())
    validate_motion(sample)
    if hashlib.sha256(Path(calibration).read_bytes()).hexdigest()!=CALIB_SHA:
        raise ValueError('Calibration checksum mismatch')
    if hf_model:
        from transformers import AutoModel
        model=AutoModel.from_pretrained(hf_model,local_files_only=True).eval()
        c=model.config
        if (c.model_type,c.hidden_size,c.num_hidden_layers,c.patch_size)!=('dinov3_vit',1024,24,16):
            raise ValueError('Expected DINOv3 ViT-L/16')
        def embed(pixels):
            return model(pixel_values=pixels).pooler_output
    else:
        if not weights or not repo or not Path(weights).is_file() or not Path(repo,'dinov3/hub/backbones.py').is_file():
            raise ValueError('DINOv3 source and approved original ViT-L/16 checkpoint are required')
        sys.path.insert(0,str(Path(repo).resolve()))
        from dinov3.hub.backbones import dinov3_vitl16
        model=dinov3_vitl16(weights=str(Path(weights).resolve())).eval()
        embed=model
    model.to(device)
    transform=transforms.Compose([transforms.ToTensor(),
        transforms.Resize((224,224),antialias=True),
        transforms.Normalize((.485,.456,.406),(.229,.224,.225))])
    pixels=[]
    for frame in sample['frames']:
        im=Image.open(io.BytesIO(base64.b64decode(frame['data'].split(',')[1]))).convert('RGB')
        pixels.append(transform(im))
    embeddings=[]
    with torch.inference_mode():
        for start in range(0,len(pixels),batch_size):
            batch=torch.stack(pixels[start:start+batch_size]).to(device)
            embeddings.append(embed(batch).cpu().numpy())
    with np.load(calibration,allow_pickle=False) as params:
        result=score_embeddings(np.concatenate(embeddings),params)
    result.update(device=device,batch_size=batch_size,model='STALL with DINOv3 ViT-L/16',feature_backend='huggingface' if hf_model else 'original',known_label=sample.get('label','unknown'))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('sample');p.add_argument('--dino-repo');p.add_argument('--weights');p.add_argument('--hf-model')
    p.add_argument('--calibration',default='.models/stall/params.npz');p.add_argument('--output',required=True)
    p.add_argument('--device',choices=['cpu','mps'],default='cpu');p.add_argument('--batch-size',type=int,default=1)
    a=p.parse_args();r=compare(a.sample,a.dino_repo,a.weights,a.calibration,a.hf_model,a.device,a.batch_size)
    Path(a.output).write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
