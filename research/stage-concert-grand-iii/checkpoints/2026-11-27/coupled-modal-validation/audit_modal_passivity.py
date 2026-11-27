"""All-mode one-step passivity and work balance in normalized energy coordinates.
For nonzero modes, third coordinate is equilibrium shift e=(g/w)*force;
for zero-frequency modes it is equilibrium velocity e=(g/gamma)*force.
The energy identity is checked in extended precision on the actual binary64 coefficients.
"""
from pathlib import Path
import json,numpy as np
from refined_cavity import coefficients
import replay as r
ROOT=Path(__file__).resolve().parent;root=ROOT.parent/'G3_consolidacao_20261127';r.load_defs(root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);z=np.load(root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');lam=z['lam'];res=z['res'];L=np.longdouble;assert np.finfo(L).nmant>np.finfo(float).nmant
old=r.Cavity(lam,res,np.zeros((len(lam),1)),384000);new=coefficients(lam,res,384000);rows={};gamma=L(r.GAMMA);dt=L(1)/384000
for name,C in [('historic',np.array([old.a,old.b,old.c,old.d,old.g0,old.g1,old.cx,old.cv,old.feed])),('refined',new)]:
    a,b,c,d,g0,g1,cx,cv,feed=C.astype(L);w=np.sqrt(lam.astype(L));g=np.sqrt(res.astype(L));nz=w>0;active=g>0;eq=np.divide(g,w,out=np.zeros_like(g),where=nz);eq[~nz]=g[~nz]/gamma
    n=len(w);T=np.zeros((n,2,3),dtype=L);T[:,0,0]=a;T[:,0,1]=b;T[:,1,0]=c;T[:,1,1]=d;T[:,0,2]=np.divide(g0,eq,out=np.zeros_like(g0),where=active);T[:,1,2]=np.divide(g1,eq,out=np.zeros_like(g1),where=active)
    # Twice the physical dissipated energy as a quadratic form in (x,v,e).
    W=np.zeros((n,3,3),dtype=L);W[:,0,2]=W[:,2,0]=np.divide(dt*cx,eq,out=np.zeros_like(cx),where=active);W[:,1,2]=W[:,2,1]=np.divide(dt*cv,eq,out=np.zeros_like(cv),where=active);W[:,2,2]=np.divide(2*dt*feed,eq*eq,out=np.zeros_like(feed),where=active)
    S=W-np.einsum('nki,nkj->nij',T,T);S[:,0,0]+=1;S[:,1,1]+=1
    A=T[:,:,:2];Q=np.eye(2,dtype=L)-np.einsum('nki,nkj->nij',A,A);J=np.zeros_like(T);J[:,0,0]=1;J[:,1,1]=1;J[nz&active,0,2]=-1;J[~nz&active,1,2]=-1
    expected=np.einsum('nki,nkl,nlj->nij',J,Q,J)
    # Zero-mode loss includes the constant equilibrium velocity and cross term.
    ix=~nz&active;mu1=-np.expm1(-gamma*dt);mu2=-np.expm1(-2*gamma*dt)
    expected[ix]=0;expected[ix,1,1]=mu2;expected[ix,1,2]=expected[ix,2,1]=2*mu1-mu2;expected[ix,2,2]=2*gamma*dt-4*mu1+mu2
    qev=np.linalg.eigvalsh(Q.astype(float));sev=np.linalg.eigvalsh(S.astype(float));err=float(np.max(abs(S-expected)));minimum=float(sev.min());rows[name]=dict(all_modes=n,zero_frequency=int((~nz).sum()),zero_residue=int((~active).sum()),minimum_homogeneous_dissipation=float(qev.min()),minimum_work_minus_energy_quadratic_eigenvalue=minimum,max_absolute_loss_identity_error=err,minimum_feedthrough=float(feed.min()),gate=bool(minimum>=-1e-12 and qev.min()>=-1e-12 and err<1e-12 and feed.min()>=0))
(ROOT/'modal-passivity.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2));assert rows['refined']['gate']
