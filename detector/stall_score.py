"""Adapted STALL scoring math, Omer Ben Hayun et al., CC-BY-NC-4.0.
Source revision f6dbb617a08d522f42ac02341028da8c58e669d1.
See licenses/STALL.txt. Added validation and abstention for no temporal information.
"""
import numpy as np

def score_embeddings(embeddings, params):
    x=np.asarray(embeddings,dtype=np.float32)
    if x.shape != (16, len(params['mu_spat'])) or not np.isfinite(x).all():
        raise ValueError('Expected sixteen finite DINOv3 embeddings')
    delta=np.diff(x,axis=0)
    norms=np.linalg.norm(delta,axis=-1,keepdims=True)
    if np.all(norms==0):
        return dict(status='inconclusive',reason='No temporal information')
    delta=delta/np.where(norms==0,1,norms)
    def ll(v,mu,w):
        z=(v-mu)@w
        return -.5*(z.shape[-1]*np.log(2*np.pi)+(z*z).sum(axis=-1))
    spatial=ll(x,params['mu_spat'],params['W_spat']).max()
    temporal=ll(delta,params['mu_temp'],params['W_temp'])
    temporal[norms[:,0]==0]=np.inf
    temporal=temporal.min()
    def percentile(v,calib,aggregation):
        ordered=np.sort(aggregation(calib,axis=1))
        return float(np.searchsorted(ordered,v,side='right')/len(ordered))
    a=percentile(spatial,params['calib_ll_spat'],np.max)
    b=percentile(temporal,params['calib_ll_temp'],np.min)
    return dict(status='experimental',spatial_percentile=a,temporal_percentile=b,
                real_reference_score=(a+b)/2,
                direction='higher resembles real-video calibration more; not an authenticity probability')


def validate_motion(sample):
    if sample.get('schema')!=2 or sample.get('mode')!='motion' or len(sample.get('frames',[]))!=16:
        raise ValueError('Expected a schema-2 motion export with sixteen frames')
    times=np.asarray([f['time'] for f in sample['frames']],dtype=float)
    gaps=np.diff(times)
    if not np.isfinite(times).all() or np.any(gaps<=0):
        raise ValueError('Frames must advance without loops')
    # Strict adapter gate; do not silently pretend irregular captures are fixed-rate video.
    if np.any(np.abs(gaps-.125)>.035) or abs(times[-1]-times[0]-1.875)>.2:
        raise ValueError('Capture timing is too irregular for the 8-FPS calibration')
    if any(f.get('method')!='Video pixels' for f in sample['frames']):
        raise ValueError('Motion scoring requires direct video pixels')
    return times
