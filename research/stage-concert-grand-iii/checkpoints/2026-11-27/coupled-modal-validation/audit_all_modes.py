"""Full-mode homogeneous evolution audit; verify worst cases against 60-digit analytic reference.
No coupled long-time trajectory is inferred from this diagnostic.
"""
from pathlib import Path
import json,numpy as np,mpmath as mp
from refined_cavity import coefficients
import replay as r
ROOT=Path(__file__).resolve().parent;root=ROOT.parent/'G3_consolidacao_20261127';r.load_defs(root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);z=np.load(root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');lam=z['lam'];res=z['res'];L=np.longdouble;assert np.finfo(L).nmant>np.finfo(float).nmant;FS=384000
c=r.Cavity(lam,res,np.zeros((len(lam),1)),FS);old=np.stack([c.a,c.b,c.c,c.d],axis=1).reshape(-1,2,2);new=coefficients(lam,res,FS)[:4].T.reshape(-1,2,2);w=np.sqrt(lam.astype(L));g=L(r.GAMMA);h=g/2;k=np.sqrt(np.maximum(w*w-h*h,0));nz=w>0

def ref(ms):
    t=L(ms)/1000;sn=np.divide(np.sin(k*t),k,out=np.full_like(k,t),where=k!=0);co=np.cos(k*t);e=np.exp(-h*t);T=np.stack([e*(co+h*sn),e*w*sn,-e*w*sn,e*(co-h*sn)],axis=1).reshape(-1,2,2);T[~nz]=np.diag([L(1),np.exp(-g*t)]);return T

def power(A,n,dtype):
    B=A.astype(dtype);P=np.broadcast_to(np.eye(2,dtype=dtype),B.shape).copy()
    while n:
        if n&1:P=P@B
        n//=2
        if n:B=B@B
    return P

def error(A,B):return np.sqrt(np.sum((A.astype(L)-B)**2,axis=(1,2))/np.sum(B**2,axis=(1,2)))
mp.mp.dps=60

def mp_truth(i,ms):
    ww=mp.sqrt(mp.mpf(float(lam[i])));gg=mp.mpf(float(r.GAMMA));t=mp.mpf(ms)/1000;hh=gg/2
    if ww==0:return mp.matrix([[1,0],[0,mp.exp(-gg*t)]])
    kk=mp.sqrt(ww*ww-hh*hh);ss=mp.sin(kk*t)/kk;co=mp.cos(kk*t);e=mp.exp(-hh*t);return e*mp.matrix([[co+hh*ss,ww*ss],[-ww*ss,co-hh*ss]])

def mat(A):return mp.matrix([[mp.mpf(float(v)) for v in row] for row in A])
rows=[];verify=[]
for ms in (100,250,500,1000):
    R=ref(ms);n=ms*384;results={};errs={};powers={}
    for name,A,dtype in [('historic_coefficients',old,L),('refined_coefficients',new,L),('refined_float_power',new,np.float64)]:
        P=power(A,n,dtype);E=error(P,R);errs[name]=E;powers[name]=P;i=int(np.argmax(E));results[name]=dict(maximum=float(E[i]),index=i,frequency_hz=float(w[i]/(2*np.pi)),above_gate=int(np.sum(E>=1e-10)),p99=float(np.quantile(E,.99)))
    indices=sorted({results[k]['index'] for k in results}|{int(np.argmax(w)),int(np.argmin(w))})
    for i in indices:
        truth=mp_truth(i,ms);H=mat(old[i])**n;C=mat(new[i])**n;F=mat(powers['refined_float_power'][i]);exact=[float(mp.norm(x-truth)/mp.norm(truth)) for x in [H,C,F]];approx=[float(errs[name][i]) for name in results];verify.append(dict(ms=ms,index=i,exact=exact,extended=approx,max_error_difference=max(abs(a-b) for a,b in zip(exact,approx))))
    rows.append(dict(ms=ms,results=results));print(ms,results,flush=True)
max_validation=max(x['max_error_difference'] for x in verify);gate=all(x['results']['refined_float_power']['maximum']<1e-10 for x in rows) and max_validation<1e-12
out=dict(modes=len(lam),duration_cases=len(rows),modal_comparisons=len(lam)*len(rows),arithmetic='vectorized matrix powers; longdouble analytic reference cross-checked at worst cases with mpmath 60 digits',rows=rows,validation=verify,max_reference_crosscheck_error=max_validation,gate=gate,scope='Homogeneous transition powers, no driven trajectory or pressure validation at long duration.')
(ROOT/'all-mode-memory.json').write_text(json.dumps(out,indent=2));print('gate',gate,'cross-check',max_validation,flush=True)
