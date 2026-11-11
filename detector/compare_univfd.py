"""Offline UniversalFakeDetect reproduction, using authors' no-resize center crop."""
import base64
import hashlib
import io
import json
import statistics
import argparse
from pathlib import Path
from urllib.request import urlopen
import torch
from torchvision import transforms
from PIL import Image
from transformers import CLIPVisionModelWithProjection

ROOT = Path(__file__).resolve().parents[1]
CLIP_REV = '32bd64288804d66eefd0ccbe215aa642df71cc41'
HEAD_REV = '030495aea3300a8b54c0ec37ec7fe1dd7e63c619'
HEAD_SHA = '477100745713bcc957beb2b40859536859b6483fd6301b3b9293151b194c7847'

def compare(paths):
    head_path = ROOT / '.models/univfd-head.pth'
    if not head_path.exists():
        head_path.parent.mkdir(exist_ok=True)
        with urlopen(f'https://raw.githubusercontent.com/WisconsinAIVision/UniversalFakeDetect/{HEAD_REV}/pretrained_weights/fc_weights.pth', timeout=60) as r:
            head_path.write_bytes(r.read())
    if hashlib.sha256(head_path.read_bytes()).hexdigest() != HEAD_SHA:
        raise ValueError('Classifier checksum mismatch')
    head = torch.nn.Linear(768,1)
    head.load_state_dict(torch.load(head_path, map_location='cpu', weights_only=True))
    head.eval()
    model = CLIPVisionModelWithProjection.from_pretrained('openai/clip-vit-large-patch14', revision=CLIP_REV,
        cache_dir=ROOT/'.models/huggingface', use_safetensors=True, trust_remote_code=False).eval()
    transform = transforms.Compose([transforms.CenterCrop(224), transforms.ToTensor(),
        transforms.Normalize([.48145466,.4578275,.40821073],[.26862954,.26130258,.27577711])])
    rows = []
    for path in paths:
        sample=json.loads(Path(path).read_text())
        if len(sample['frames']) != 6: raise ValueError('Expected six frames')
        scores=[]
        for frame in sample['frames']:
            im=Image.open(io.BytesIO(base64.b64decode(frame['data'].split(',')[1]))).convert('RGB')
            with torch.inference_mode():
                feature=model(pixel_values=transform(im)[None]).image_embeds
                scores.append(float(head(feature).sigmoid().item())*100)
        rows.append(dict(file=Path(path).name,label=sample['label'],frames=scores,median=statistics.median(scores)))
    return dict(model='UniversalFakeDetect CLIP ViT-L/14',clip_revision=CLIP_REV,
                classifier_revision=HEAD_REV,experimental=True,results=rows)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('samples',nargs='+');parser.add_argument('--output',required=True)
    args=parser.parse_args();result=compare(args.samples)
    Path(args.output).write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
