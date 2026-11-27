"""Long-horizon homogeneous modal recurrence, independent matrix exponential reference."""
from pathlib import Path
import json,numpy as np
from scipy.linalg import expm
import replay as r
ROOT=Path(__file__).resolve().parent;FS=384000;GAMMA=2*np.pi*5
base=ROOT.parent/'G3_consolidacao_20261127';r.load_defs(base,'G3_Exterior_Acoplamento/coupled.py',['Cavity'])
z=np.load(base/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');lam=z['lam'];res=z['res'];c=r.Cavity(lam,res,np.zeros((len(lam),1)),FS)
order=np.argsort(lam);ids=np.unique(np.r_[np.flatnonzero(lam==0),order[np.linspace(0,len(lam)-1,24,dtype=int)]])
rows=[]
for i in ids:
    w=float(np.sqrt(lam[i]));A=np.array([[0,w],[-w,-GAMMA]]);T=np.array([[c.a[i],c.b[i]],[c.c[i],c.d[i]]]);one=expm(A/FS)
    err=lambda x,y:float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-300))
    for ms in (100,250,500,1000):
        N=ms*384;power=np.linalg.matrix_power(T,N);ref=expm(A*(ms/1000));rows.append(dict(index=int(i),frequency_hz=w/(2*np.pi),ms=ms,one_step=err(T,one),long_relative=err(power,ref),long_absolute=float(np.linalg.norm(power-ref))))
mx=max(x['long_relative'] for x in rows);out=dict(modes=len(ids),cases=len(rows),one_step_max=max(x['one_step'] for x in rows),long_relative_max=mx,long_absolute_max=max(x['long_absolute'] for x in rows),gate_1e_10=mx<1e-10,rows=rows,scope='homogeneous archived cavity transitions only, not coupled forced response, no recalibration')
(ROOT/'cavity-memory.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
