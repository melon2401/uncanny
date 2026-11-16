"""Local WaveRep G4 adapter; research/nonprofit use, see licenses/WaveRep.txt."""
import base64
import hashlib
import io
import sys
from functools import lru_cache
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.models/waverep-deps'))
import torch
import timm
from PIL import Image
from torchvision import transforms
try:
    from .visual_decision import decision
except ImportError:
    from visual_decision import decision


@lru_cache(maxsize=1)
def load_model():
    path=ROOT/'.models/waverep-g4.ckpt'
    if hashlib.md5(path.read_bytes()).hexdigest()!='8bf19e6f68a92bed600dd97fbed3f2cd':
        raise ValueError('WaveRep checkpoint checksum mismatch')
    model=timm.create_model('vit_base_patch14_reg4_dinov2.lvd142m',num_classes=1,pretrained=False,img_size=504)
    state=torch.load(path,map_location='cpu',weights_only=True)
    if 'state_dict' in state:
        state={k[6:]:v for k,v in state['state_dict'].items() if k.startswith('model.')}
    model.load_state_dict(state,strict=True)
    device='mps' if torch.backends.mps.is_available() else 'cpu'
    return model.eval().to(device),device


def analyze(frames):
    if not isinstance(frames,list) or len(frames)!=6:raise ValueError('Expected six frames')
    transform=transforms.Compose([transforms.CenterCrop((504,504)),transforms.ToTensor(),
                                  transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
    tensors=[];fingerprints=set();padded=0;dimensions=[]
    for frame in frames:
        if not isinstance(frame,str) or not frame.startswith('data:image/jpeg;base64,'):raise ValueError('Expected JPEG')
        with Image.open(io.BytesIO(base64.b64decode(frame.split(',')[1],validate=True)),formats=['JPEG']) as image:
            if max(image.size)>1280:raise ValueError('Frame too large')
            dimensions.append(list(image.size));padded+=int(min(image.size)<504)
            image=image.convert('RGB')
            fingerprints.add(hashlib.sha256(image.tobytes()).digest())
            tensors.append(transform(image))
    if len(fingerprints)<3:return decision([0.]*6,len(fingerprints))
    model,device=load_model();logits=[]
    with torch.inference_mode():
        for tensor in tensors:
            logits.append(float(model(tensor[None].to(device))[0,-1].cpu()))
    return {**decision(logits,len(fingerprints)),'device':device,'padded_frames':padded,'input_dimensions':dimensions,'capture_pipeline':'visual-1280-v1'}
