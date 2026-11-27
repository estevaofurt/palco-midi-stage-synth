"""Parseval audit of fine causal pressure error. Fractions are norms, not radiated energy."""
from pathlib import Path
import json
import numpy as np
from scipy.fft import rfft,rfftfreq
ROOT=Path(__file__).parent

def main():
    a=json.loads((ROOT/'regional-audit.json').read_text());N=a['fine_steps'];f=rfftfreq(N,1/384000);w=np.full(len(f),2.);w[0]=1
    if N%2==0:w[-1]=1
    edges=[0,24000,48000,96000,192001];rows=[]
    with np.load(ROOT/'regional-pressure.npz') as z:
        for x in a['rows']:
            key=x['key'];s=x['speed'];r=x['rate'];rr=x['reference_rate'];p=x['rank'];pr=x['reference_rank']
            A=z[f'{key}-{p}-{r}-{s}-{round(.012*r)}_fine'][:N];B=z[f'{key}-{pr}-{rr}-{s}-{round(.012*rr)}_fine'][:N];E=abs(rfft(A-B,axis=0))**2*w[:,None];T=abs(rfft(B,axis=0))**2*w[:,None];assert np.allclose(E.sum(0)/N,np.sum((A-B)**2,axis=0),rtol=1e-12,atol=0);assert np.allclose(T.sum(0)/N,np.sum(B**2,axis=0),rtol=1e-12,atol=0)
            bands=[]
            for lo,hi in zip(edges,edges[1:]):
                q=(f>=lo)&(f<hi);e=E[q].sum(0);t=T[q].sum(0);bands.append(dict(lo=lo,hi=hi,error_fraction=(e/E.sum(0)).tolist(),reference_fraction=(t/T.sum(0)).tolist(),relative_to_full_reference=np.sqrt(e/T.sum(0)).tolist(),band_relative=np.sqrt(e/np.maximum(t,1e-300)).tolist()))
            rows.append(dict(key=key,speed=s,rank=p,rate=r,reference_rank=pr,reference_rate=rr,bands=bands))
    (ROOT/'band-diagnostic.json').write_text(json.dumps(rows,indent=2));
    for x in rows:print(x['key'],x['rate'],'error >96k fractions',x['bands'][-1]['error_fraction'],'error <24k relative to full',x['bands'][0]['relative_to_full_reference'])
if __name__=='__main__':main()
