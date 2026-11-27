"""Separate rounded-transition error from long-time scipy expm reference error, using 60 digits."""
from pathlib import Path
import json,numpy as np,mpmath as mp
from scipy.linalg import expm
import replay as r
ROOT=Path(__file__).resolve().parent;FS=384000;mp.mp.dps=60;gamma=mp.mpf(float(2*np.pi*5));root=ROOT.parent/'G3_consolidacao_20261127';r.load_defs(root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);z=np.load(root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');lam=z['lam'];c=r.Cavity(lam,z['res'],np.zeros((len(lam),1)),FS)
ids=sorted({x['index'] for x in json.loads((ROOT/'cavity-memory.json').read_text())['rows']});rows=[]
def truth(l,t):
    w=mp.sqrt(mp.mpf(float(l)));h=gamma/2
    if w==0:return mp.matrix([[1,0],[0,mp.exp(-gamma*t)]])
    k=mp.sqrt(w*w-h*h);s=mp.sin(k*t)/k;co=mp.cos(k*t);e=mp.exp(-h*t);return e*mp.matrix([[co+h*s,w*s],[-w*s,co-h*s]])
def matrix(a):return mp.matrix([[mp.mpf(float(v)) for v in row] for row in a])
def err(x,y):return float(mp.norm(x-y)/mp.norm(y))
for i in ids:
    w=float(np.sqrt(lam[i]));A=np.array([[0,w],[-w,-float(gamma)]]);T=np.array([[c.a[i],c.b[i]],[c.c[i],c.d[i]]]);M=matrix(T);one=err(M,truth(lam[i],mp.mpf(1)/FS))
    for ms in (100,250,500,1000):
        n=ms*384;ref=truth(lam[i],mp.mpf(ms)/1000);power=M**n;calc=matrix(np.linalg.matrix_power(T,n));scipy_ref=matrix(expm(A*(ms/1000)));rows.append(dict(index=i,frequency_hz=w/(2*np.pi),ms=ms,one_step_high_precision=one,rounded_transition_error=err(power,ref),float_matrix_power_error=err(calc,power),scipy_expm_error=err(scipy_ref,ref),combined_vs_high_precision=err(calc,ref)))
keys=('one_step_high_precision','rounded_transition_error','float_matrix_power_error','scipy_expm_error','combined_vs_high_precision');summary={k:max(x[k] for x in rows) for k in keys};out=dict(digits=60,modal_samples=len(ids),cases=len(rows),summary=summary,gate_1e_10=summary['combined_vs_high_precision']<1e-10,rows=rows,scope='homogeneous modal recurrence; error relative to decaying modal transition, not pressure or energy error in full instrument')
(ROOT/'cavity-precision.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
