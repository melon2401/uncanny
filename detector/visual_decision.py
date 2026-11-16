"""Conservative display policy for raw signed visual-model evidence."""
import math


def decision(logits, distinct):
    if len(logits)!=6 or not all(math.isfinite(x) for x in logits):
        raise ValueError('Expected six finite logits')
    mean=sum(logits)/6
    positive=sum(x>0 for x in logits)
    negative=sum(x<0 for x in logits)
    if distinct<3:
        label='Inconclusive';reason='Too few distinct frames.'
    elif mean>0 and positive>=5:
        label='AI-like visual signal';reason='At least five sampled frames support this signal. This is not proof.'
    elif mean<0 and negative>=5:
        label='No strong AI evidence';reason='The model can miss generated content; this does not prove the video is real.'
    else:
        label='Inconclusive';reason='Sampled frames disagree. Try another part of the video.'
    return dict(label=label,summary=label+' — '+reason,mean_logit=mean,
                frames=logits,units='logit',model='WaveRep G4',experimental=True,
                policy='five-of-six-sign-agreement-v1',positive_frames=positive)
