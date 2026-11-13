"""Experimental same-weights implementation comparison, not checkpoint provenance verification.
Run from the repository root with the research Python and a local motion export.
Requires approved HF weights and Meta source under ignored .models/.
"""
import sys,json,base64,io,argparse
import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoModel
from safetensors.torch import load_file
sys.path.insert(0,'.models/dinov3-source')
from dinov3.hub.backbones import dinov3_vitl16
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('sample',help='Local motion export JSON')
parser.add_argument('--frame',type=int,default=8)
args=parser.parse_args()
torch.set_num_threads(4)
m=dinov3_vitl16(pretrained=False).eval()
h=load_file('.models/dinov3-hf/model.safetensors');state={}
base={'cls_token':'embeddings.cls_token','storage_tokens':'embeddings.register_tokens','mask_token':'embeddings.mask_token','patch_embed.proj.weight':'embeddings.patch_embeddings.weight','patch_embed.proj.bias':'embeddings.patch_embeddings.bias','norm.weight':'norm.weight','norm.bias':'norm.bias'}
for key,value in m.state_dict().items():
 if key in base: state[key]=h[base[key]].reshape(value.shape)
 elif key=='rope_embed.periods' or key.endswith('bias_mask'):state[key]=value
 elif key.startswith('blocks.'):
  _,i,tail=key.split('.',2);pre='layer.'+i+'.'
  if tail=='attn.qkv.weight':v=torch.cat([h[pre+'attention.'+x+'_proj.weight'] for x in ['q','k','v']])
  elif tail=='attn.qkv.bias':v=torch.cat([h[pre+'attention.q_proj.bias'],torch.zeros_like(h[pre+'attention.q_proj.bias']),h[pre+'attention.v_proj.bias']])
  else:
   tail=tail.replace('attn.proj','attention.o_proj').replace('ls1.gamma','layer_scale1.lambda1').replace('ls2.gamma','layer_scale2.lambda1').replace('mlp.fc1','mlp.up_proj').replace('mlp.fc2','mlp.down_proj')
   v=h[pre+tail]
  state[key]=v
 else:raise ValueError(key)
m.load_state_dict(state,strict=True)
hf=AutoModel.from_pretrained('.models/dinov3-hf',local_files_only=True).eval()
t=transforms.Compose([transforms.ToTensor(),transforms.Resize((224,224),antialias=True),transforms.Normalize((.485,.456,.406),(.229,.224,.225))])
with open(args.sample) as handle:
 s=json.load(handle)
im=Image.open(io.BytesIO(base64.b64decode(s['frames'][args.frame]['data'].split(',')[1]))).convert('RGB');x=t(im)[None]
with torch.inference_mode():a=m(x);b=hf(pixel_values=x).pooler_output
print(json.dumps({'max_absolute_error':float((a-b).abs().max()),'mean_absolute_error':float((a-b).abs().mean()),'cosine_similarity':float(torch.nn.functional.cosine_similarity(a,b)[0])}))
torch.testing.assert_close(a,b,atol=1e-3,rtol=1e-3)
