"""Exact original assembly regression plus independent dense expansion checks."""
from pathlib import Path
import json,numpy as np
from scipy.linalg import cholesky,solve
from assembly_rank import KEYS,SPREAD
from compact_mechanics import assemble_compact,CompactSolve,midpoint
from regional_compact import assemble_regional
from dynamic_dampers import Dampers
ROOT=Path(__file__).resolve().parent;FS=384000;OLD={45:64,48:128,60:64,64:64};RANKS={33:64,**OLD,55:64,72:64};SP={k:SPREAD.get(k,0.) for k in RANKS};SHIFT={k:5.5 if k==48 else 0. for k in RANKS}
scale=json.loads((ROOT/'scale_geometry.json').read_text());base=np.load(ROOT.parent/'G3_consolidacao_20261127/G3_Base_Estrutural/integrated_80.npz')
a=assemble_compact(base,scale,list(OLD),OLD);b=assemble_regional(base,scale,list(OLD),OLD,{k:SP[k] for k in OLD},{k:SHIFT[k] for k in OLD})
for x,y in zip(a[:3],b[:3]):
    for k in ('board','g','ids','d','c','v','a'):assert np.array_equal(getattr(x,k),getattr(y,k)),k
assert np.array_equal(a[3],b[3]);M,K,D,P,w=assemble_regional(base,scale,list(RANKS),RANKS,SP,SHIFT);dam=Dampers(D,w,scale);n=M.n
# Independent dense assembly from modal coefficients and rank-one damper vectors.
md=np.eye(n);kd=np.zeros((n,n));dd=kd.copy();kd[:80,:80]=base['nominal']+.025*(base['treble_low']+base['treble_high']);dd[:80,:80]=base['damping'];off=80;db=[]
for key,f,g,_ in w:
    k=key['key'];r=RANKS[k];sl=slice(off,off+r);o=np.outer(g,g)
    for X,scalar,diag,cross in [(md,'m0',np.ones(r),'m'),(kd,'k0',f['w2'][:r],'k'),(dd,'d0',f['gamma'][:r],'d')]:
        X[:80,:80]+=f[scalar]*o;X[sl,sl]=np.diag(diag);X[sl,:80]=np.outer(f[cross][:r],g);X[:80,sl]=X[sl,:80].T
    vec=np.zeros(n);vec[:80]=.18*g;vec[sl]=f['damper'][:r];db.append(vec);off+=r
rng=np.random.default_rng(271127);R=rng.normal(size=(n,3));Z=np.zeros((80,80));tests=[]
for held,pedal in [([],0),([48,60,64],0),([48],.5),([48,60,64],1)]:
    f=dam.fractions(held,pedal);d=dam.operator(f);dense=dd+np.asarray(db).T@((f*dam.maximum)[:,None]*np.asarray(db));h=1/FS
    for X in (md,kd,dense):cholesky((X+X.T)/2,lower=True)
    J=2*md/h+dense+h*kd/2;y=solve(J,R,assume_a='pos');x=CompactSolve(midpoint(M,K,d,h,Z)).solve(R)
    err=lambda a,b:float(np.linalg.norm(a-b)/np.linalg.norm(b))
    rec=dict(held=held,pedal=pedal,mass_action=err(M@R,md@R),stiffness_action=err(K@R,kd@R),damping_action=err(d@R,dense@R),solve=err(x,y),residual=err(J@x,R));assert max(rec[k] for k in ('mass_action','stiffness_action','damping_action','solve','residual'))<1e-10;tests.append(rec)
out=dict(original_bitwise=True,ranks=RANKS,spread=SP,shift=SHIFT,notes=len(RANKS),wires=len(w),coordinates=n,tests=tests,scope='algebraic assembly only; new unison offsets nominal zero, no calibration; not acoustic convergence')
(ROOT/'regional-check.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
