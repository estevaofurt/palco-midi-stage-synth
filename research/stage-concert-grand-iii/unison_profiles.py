"""Fixed per-group tuning profiles via physical tension, no oscillators."""
import numpy as np
from scipy.linalg import eigh
from physical_unison_decay import offsets,tension_multiplier,detune
from string_ports import element
from string_structure import Wire
KEYS=(45,48,60,64)
def profiles_for_key(key):
    """Keep the actual G3.13s reference: C4 spread was 1 cent ONLY for C4 runs."""
    if key not in KEYS:raise ValueError('key')
    s=1. if key==60 else 0.
    return (('approved',(0.,0.,s,0.)),('other_half',(.5,.5,s,.5)),
        ('other_one',(1.,1.,s,1.)),('other_two',(2.,2.,s,2.)),
        ('central_one_half',(1.,1.,1.5,1.)),('central_two',(1.,1.,2.,1.)))

def detune_profile(wires,rows,profile):
    if len(profile)!=len(KEYS) or not np.isfinite(profile).all() or min(profile)<0:raise ValueError('profile')
    # Use precisely the original C4 builder, including its zero-cent rebuild.
    central,central_records=detune(wires,rows,float(profile[2]))
    central_by_id={w.id:w for w in central if w.port==2}
    central_record_by_id={v['wireId']:v for v in central_records}
    result=[];records=[]
    for j,k in enumerate(KEYS):
        selected=[w for w in wires if w.port==j]
        if len(selected)!=rows[k]['count']:raise ValueError('wire group')
        for w,c in zip(selected,offsets(len(selected),float(profile[j]))):
            c=float(c);row=rows[k];N=len(w.w2)
            if j==2:
                x=central_by_id[w.id];m=central_record_by_id[w.id]['tensionMultiplier']
            elif c==0.:
                x=w;m=1.
            else:
                def frequency(multiplier):
                    rr=dict(row,tensionPerStringN=row['tensionPerStringN']*multiplier)
                    M,K,_=element(rr,N)
                    return np.sqrt(eigh(K[2:,2:],M[2:,2:],subset_by_index=[0,0],eigvals_only=True)[0])/(2*np.pi)
                m=tension_multiplier(frequency,c)
                x=Wire(dict(row,tensionPerStringN=row['tensionPerStringN']*m),N,w.rear,w.port,w.id)
            actual=float(1200*np.log2(np.sqrt(x.w2[0]/w.w2[0])))
            if abs(actual-c)>1e-6:raise ValueError('tuning tolerance')
            result.append(x);records.append(dict(wireId=w.id,key=k,targetCents=c,actualCents=actual,tensionMultiplier=m))
    if [w.id for w in result]!=[w.id for w in wires]:raise ValueError('wire order')
    return result,records
