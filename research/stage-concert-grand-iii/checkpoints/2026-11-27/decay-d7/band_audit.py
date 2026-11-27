"""Finite-window spectral energy audit; not a note attack or audible error metric."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.fft import rfft,rfftfreq
FS=384000
BANDS=[0,300,1000,3000,8000,16000,24000,48000,96000,192001]

def rel(a,b):return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-300))
def sq(a):return np.sum(np.abs(a)**2,axis=0)
def window(a,b):
    den=sq(b);num=sq(a-b)
    return dict(combined=rel(a,b),per_mic=(np.sqrt(num/np.maximum(den,1e-300))).tolist(),reference_rms=np.sqrt(den/len(b)).tolist())
def spectrum(a,b):
    N=len(b);f=rfftfreq(N,1/FS);A=rfft(a,axis=0);B=rfft(b,axis=0);w=np.full(len(f),2.);w[0]=1
    if N%2==0:w[-1]=1
    E=np.abs(B)**2*w[:,None];D=np.abs(A-B)**2*w[:,None];Y=np.abs(A)**2*w[:,None];et=E.sum(axis=0);dt=D.sum(axis=0);rows=[]
    for lo,hi in zip(BANDS,BANDS[1:]):
        q=(f>=lo)&(f<hi);e=E[q].sum(axis=0);d=D[q].sum(axis=0);y=Y[q].sum(axis=0)
        rows.append(dict(lo=lo,hi=hi,bins=int(q.sum()),reference_fraction=(e/np.maximum(et,1e-300)).tolist(),error_fraction=(d/np.maximum(dt,1e-300)).tolist(),relative_error=np.sqrt(d/np.maximum(e,1e-300)).tolist(),relative_to_full_reference=np.sqrt(d/np.maximum(et,1e-300)).tolist(),level_delta_db=(10*np.log10(np.maximum(y,1e-300)/np.maximum(e,1e-300))).tolist()))
    assert np.allclose(et/N,sq(b),rtol=1e-12,atol=0);assert np.allclose(dt/N,sq(a-b),rtol=1e-12,atol=0)
    assert np.allclose(sum(np.array(r['reference_fraction']) for r in rows),1,rtol=1e-12);assert np.allclose(sum(np.array(r['error_fraction']) for r in rows),1,rtol=1e-12)
    return dict(resolution_hz=FS/N,rows=rows)
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('output',type=Path);a=p.parse_args();z=np.load(a.root/'new-reference.npz');r=z['pressure'];N=len(z['flow']);ne=106*8;rows=[]
    for mode in ('d6','targeted','d7'):
        v=np.load(a.root/('new-'+mode+'.npz'));x=v['pressure'];assert x.shape==r.shape
        row=dict(mode=mode,full=window(x,r),prefix=window(x[:N],r[:N]),after=window(x[N:],r[N:]),prefix_bands=spectrum(x[:N],r[:N]),full_bands=spectrum(x,r),prefix_reference_fraction=(sq(r[:N])/sq(r)).tolist(),reference_lower_last64_fraction=float(np.linalg.norm(z['flow'][N-512:,:][:,80:])**2/np.linalg.norm(z['flow'][:,80:])**2),lower_tail_error=rel(v['flow'][ne:,80:],z['flow'][ne:,80:]))
        if N>2560:row['continuation']=window(x[2560:N],r[2560:N])
        rows.append(row)
    a.output.write_text(json.dumps(dict(fine_steps=N,rows=rows),indent=2))
    for row in rows:
        print(row['mode'], 'full',row['full']['per_mic'],'prefix',row['prefix']['per_mic'],'fraction',row['prefix_reference_fraction'])
        for b in row['prefix_bands']['rows']:
            print(b['lo'],b['hi'], 'ref', np.round(np.array(b['reference_fraction'])*100,5),'err',np.round(np.array(b['relative_error'])*100,5),'contribution',np.round(np.array(b['relative_to_full_reference'])*100,5))
if __name__=='__main__':main()
