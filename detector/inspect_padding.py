import json,base64,io,time
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from torchvision import transforms
from detector.waverep import load_model
from detector.visual_decision import decision
model,device=load_model()
t=transforms.Compose([transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
rows=[]
for report in ['waverep-motion-results.json','waverep-still-results.json']:
 for old in json.loads((Path('captures')/report).read_text()):
  s=json.loads((Path('captures')/(old['sample']+'.json')).read_text());scores=[]
  with torch.inference_mode():
   for i in old['indices']:
    im=Image.open(io.BytesIO(base64.b64decode(s['frames'][i]['data'].split(',')[1]))).convert('RGB')
    if min(im.size)<504:
     w,h=im.size;scale=504/min(w,h);im=im.resize((round(w*scale),round(h*scale)),Image.Resampling.BICUBIC)
    im=transforms.CenterCrop(504)(im)
    scores.append(float(model(t(im)[None].to(device))[0,-1].cpu()))
  row={'sample':old['sample'],'label':old['label'],'before':decision(old['frame_logits'],6)['label'],'after':decision(scores,6)['label'],'scores':scores}
  rows.append(row);print(json.dumps(row),flush=True)
  Path('captures/padding-ablation.json').write_text(json.dumps(rows,indent=2))
