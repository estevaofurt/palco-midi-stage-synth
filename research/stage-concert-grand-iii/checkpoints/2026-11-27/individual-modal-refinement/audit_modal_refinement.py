"""Candidate coefficient generation in extended precision; never changes active integrator."""
from pathlib import Path
import json,numpy as np,mpmath as mp
from scipy.fft import dctn
import replay as r
ROOT=Path(__file__).resolve().parent;FS=384000;mp.mp.dps=60
root=ROOT.parent/'G3_consolidacao_20261127';r.load_defs(root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);z=np.load(root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');lam=z['lam'];res=z['res'];ch=z['ch'];c=r.Cavity(lam,res,np.zeros((len(lam),1)),FS)
assert np.finfo(np.longdouble).nmant>np.finfo(float).nmant
L=np.longdouble;gamma=L(r.GAMMA);dt=L(1)/FS;h=gamma/2;w=np.sqrt(lam.astype(L));g=np.sqrt(res.astype(L));nz=w>0;k=np.sqrt(np.maximum(w*w-h*h,0));e=np.exp(-h*dt);angle=k*dt;sn=np.divide(np.sin(angle),k,out=np.full_like(k,dt),where=k!=0);co=np.cos(angle)
a=e*(co+h*sn);b=e*w*sn;d=e*(co-h*sn);a[~nz]=1;d[~nz]=np.exp(-gamma*dt)
eq=np.divide(g,w,out=np.zeros_like(g),where=nz);one_minus_a=-np.expm1(-h*dt)+e*(2*np.sin(angle/2)**2-h*sn);one_minus_a[~nz]=0;g0=one_minus_a*eq;g1=b*eq;g1[~nz]=g[~nz]*(-np.expm1(-gamma*dt))/gamma
fac=np.divide(g,w*dt,out=np.zeros_like(g),where=nz);cx=-fac*one_minus_a;cv=fac*b;feed=fac*g0;mu=-np.expm1(-gamma*dt)/(gamma*dt);cv[~nz]=g[~nz]*mu;feed[~nz]=res[~nz]*(1-mu)/gamma
new=np.array([a,b,-b,d,g0,g1,cx,cv,feed],dtype=float);old=np.array([c.a,c.b,c.c,c.d,c.g0,c.g1,c.cx,c.cv,c.feed]);assert np.isfinite(new).all()
# Same original 24 samples; additional top-error samples selected from full coefficient array.
prior=json.loads((ROOT/'cavity-precision.json').read_text());ids=sorted({x['index'] for x in prior['rows']});extra=np.argsort(np.max(abs(new[:4]-old[:4]),axis=0))[-16:];ids=sorted(set(ids)|set(map(int,extra)))
mg=mp.mpf(float(r.GAMMA));mh=mg/2
def truth(l,t):
    ww=mp.sqrt(mp.mpf(float(l)))
    if ww==0:return mp.matrix([[1,0],[0,mp.exp(-mg*t)]])
    kk=mp.sqrt(ww*ww-mh*mh);s=mp.sin(kk*t)/kk;cc=mp.cos(kk*t);ee=mp.exp(-mh*t);return ee*mp.matrix([[cc+mh*s,ww*s],[-ww*s,cc-mh*s]])
def matrix(a):return mp.matrix([[mp.mpf(float(v)) for v in row] for row in a])
def err(x,y):return float(mp.norm(x-y)/mp.norm(y))
rows=[]
for i in ids:
    T=old[:4,i].reshape(2,2);U=new[:4,i].reshape(2,2);M=matrix(T);V=matrix(U)
    for ms in (100,250,500,1000):
        n=ms*384;ref=truth(lam[i],mp.mpf(ms)/1000);rows.append(dict(index=i,frequency_hz=float(w[i]/(2*np.pi)),ms=ms,old=err(M**n,ref),candidate=err(V**n,ref),candidate_float_power=err(matrix(np.linalg.matrix_power(U,n)),ref)))
# Full port-space discrete harmonic response. Separate high natural-frequency modes, no deletion in physical model.
grid=np.load(ROOT.parent/'G3_Acoplamento_369/grid-b64.npz');A,B=grid['A'],grid['B'];aa=dctn(A.reshape(30,30,-1),axes=(0,1),norm='ortho').reshape(900,-1);bb=dctn(B.reshape(30,30,-1),axes=(0,1),norm='ortho').reshape(900,-1);F=np.repeat(np.c_[aa,bb],2,axis=0);F[1::2,A.shape[1]:]*=-1

def modal(coef,f):
    a,b,c,d,g0,g1,cx,cv,feed=coef;zz=np.exp(2j*np.pi*f/FS);det=(zz-a)*(zz-d)-b*c;return cx*((zz-d)*g0+b*g1)/det+cv*(c*g0+(zz-a)*g1)/det+feed

def proj(y):
    v=np.bincount(ch,weights=y.real,minlength=1800)+1j*np.bincount(ch,weights=y.imag,minlength=1800);return F.T@(v[:,None]*F)
fr=[];freq=w/(2*np.pi)
for f in (55,110,220,440,880,1760,3520,7040,10000,15000,20000):
    y=modal(old,f);yn=modal(new,f);p=proj(y);norm=np.linalg.norm(p);fr.append(dict(frequency_hz=f,candidate_relative=float(np.linalg.norm(proj(yn-y))/norm),above_nyquist_relative=float(np.linalg.norm(proj(y*(freq>FS/2)))/norm),above_20khz_relative=float(np.linalg.norm(proj(y*(freq>20000)))/norm)))
summary={k:max(x[k] for x in rows) for k in ('old','candidate','candidate_float_power')};out=dict(precision_bits=int(np.finfo(L).nmant+1),modes=len(lam),modal_samples=len(ids),cases=len(rows),summary=summary,gate_1e_10=summary['candidate_float_power']<1e-10,above_nyquist_count=int(np.sum(freq>FS/2)),above_20khz_count=int(np.sum(freq>20000)),max_frequency_hz=float(max(freq)),max_coefficient_absolute_difference=float(np.max(abs(new-old))),rows=rows,port_response=fr,scope='Candidate extended-precision generation rounded once to binary64. Homogeneous power diagnostic and 369-port cavity-only discrete harmonic response; not full coupled simulation, no modal deletion or production modification.')
(ROOT/'modal-refinement.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
