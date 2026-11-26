"""G3.11r: compiled contact solver with manufactured strong reciprocal cases.
Contact solve only: no integration, event engine or real-time audio claim."""
import argparse,json,time,math
from pathlib import Path
import numpy as np
from numba import njit
from felt_law import Felt,frozen_force,potential
from multi_hammer_contact import solve_contacts

@njit(cache=True)
def secant(a,b,k,p):
    if a==b:return k*max(0.,a)**p
    lo=min(a,b);hi=max(a,b)
    if hi<=0 or k==0:return 0.
    if lo<=0:diff=hi**(p+1)
    elif lo/hi>.5:diff=-hi**(p+1)*math.expm1((p+1)*math.log1p((lo-hi)/hi))
    else:diff=hi**(p+1)-lo**(p+1)
    return k*diff/((p+1)*(hi-lo))

@njit(cache=True)
def law(a,b,z,row):
    return secant(a,b,row[0],row[2])+secant(a-z,b-z,row[1],row[2])

@njit(cache=True)
def solve_kernel(d0,dfree,z,G,params,F,disp,reverse,max_sweeps):
    n=len(F)
    for j in range(n):F[j]=0.;disp[j]=dfree[j]
    for sweep in range(1,max_sweeps+1):
        for q in range(n):
            j=n-1-q if reverse else q
            free=disp[j]+G[j,j]*F[j]
            hi=law(d0[j],free,z[j],params[j])
            if hi<=0:new=0.
            else:
                lo=0.
                for _ in range(64):
                    mid=(lo+hi)/2
                    if mid-law(d0[j],free-G[j,j]*mid,z[j],params[j])>0:hi=mid
                    else:lo=mid
                    if hi-lo<=1e-14*max(1.,hi):break
                new=(lo+hi)/2
            delta=new-F[j];F[j]=new
            for i in range(n):disp[i]-=G[i,j]*delta
        err=0.;peak=1.
        # Independent direct residual; reset accumulated displacement each sweep.
        for i in range(n):
            x=dfree[i]
            for j in range(n):x-=G[i,j]*F[j]
            disp[i]=x
            e=abs(F[i]-law(d0[i],x,z[i],params[i]))
            err=max(err,e);peak=max(peak,F[i])
        if err<=1e-11*peak:return sweep,err,True
    return max_sweeps,err,False

class ContactSolver:
    def __init__(self,G,felts):
        G=np.asarray(G,dtype=float);n=len(felts)
        if not n or G.shape!=(n,n) or not np.isfinite(G).all() or np.linalg.norm(G-G.T)>1e-12*max(np.linalg.norm(G),1e-30) or np.linalg.eigvalsh((G+G.T)/2).min()<=0:raise ValueError('invalid SPD compliance')
        self.G=np.ascontiguousarray((G+G.T)/2);self.params=np.ascontiguousarray([[f.ke,f.km,f.p] for f in felts]);self.F=np.zeros(n);self.disp=np.zeros(n)
    def solve(self,d0,dfree,z,reverse=False,max_sweeps=400):
        n=len(self.F)
        for v in (d0,dfree,z):
            if not isinstance(v,np.ndarray) or v.shape!=(n,) or v.dtype!=np.float64 or not v.flags.c_contiguous or not np.isfinite(v).all() or np.shares_memory(v,self.F) or np.shares_memory(v,self.disp):raise ValueError('invalid contact input')
        if np.any(z<0) or max_sweeps<1:raise ValueError('invalid contact state')
        s,e,ok=solve_kernel(d0,dfree,z,self.G,self.params,self.F,self.disp,reverse,max_sweeps)
        if not ok or not np.isfinite(self.F).all() or not np.isfinite(e):raise ValueError('contact solve did not converge')
        return self.F,s,e

def fixture(n,kind,seed=31):
    rng=np.random.default_rng(seed);f=[Felt(1.5e8,.5e8,3000.,3.,2.5)]*n
    signs=np.where(np.arange(n)%2==0,1.,-1.)
    if kind=='weak':G=2e-5*np.eye(n)+2e-15*np.outer(signs,signs)
    elif kind=='positive':G=2e-5*(.75*np.eye(n)+.25*np.ones((n,n)))
    elif kind=='signed':G=2e-5*(.75*np.eye(n)+.25*np.outer(signs,signs))
    else:raise ValueError('fixture kind')
    d0=np.ascontiguousarray(rng.uniform(-.0005,.002,n));d1=np.ascontiguousarray(rng.uniform(-.0006,.003,n));z=np.ascontiguousarray(rng.uniform(0,.0004,n))
    d0[::7]=-0.0007;d1[::7]=-0.0005
    expected=np.array([frozen_force(a,b,c,v) for a,b,c,v in zip(d0,d1,z,f)])
    dfree=np.ascontiguousarray(d1+G@expected)
    return G,f,d0,dfree,z,d1,expected

def probe(n,kind):
    G,f,d0,dfree,z,d1,expected=fixture(n,kind);a=ContactSolver(G,f)
    F,s,e=a.solve(d0,dfree,z);F=F.copy()
    reverse,sr,er=a.solve(d0,dfree,z,True);reverse=reverse.copy()
    ref,sp,ep=solve_contacts(d0,dfree,z,G,f,max_sweeps=400)
    scale=max(np.linalg.norm(expected),1e-30);err=float(np.linalg.norm(F-expected)/scale)
    order=float(np.linalg.norm(F-reverse)/scale);comparison=float(np.linalg.norm(F-ref)/scale)
    d=dfree-G@F
    work=float(F@(d-d0))
    delta=sum(potential(b,v.ke,v.p)-potential(a,v.ke,v.p)+potential(b-c,v.km,v.p)-potential(a-c,v.km,v.p) for a,b,c,v in zip(d0,d,z,f))
    energy=abs(work-delta)/max(float(np.sum(np.abs(F*(d-d0)))),1e-30)
    displacement=float(np.linalg.norm(d-d1)/max(np.linalg.norm(d1),1e-30))
    result=dict(contacts=n,kind=kind,manufacturedForceRelative=err,referenceForceRelative=comparison,orderRelative=order,
        displacementRelative=displacement,workRelative=energy,maximumSweeps=max(s,sr,sp),compiledSweeps=s,maximumResidual=max(e,er,ep),
        zeroForceCount=int(np.count_nonzero(F==0)),crossComplianceRelative=float(np.linalg.norm(G-np.diag(np.diag(G)))/np.linalg.norm(G)))
    result['gate']=bool(np.isfinite([err,order,comparison,energy,displacement]).all() and max(err,order,comparison,energy,displacement)<=1e-8 and np.all(F>=0) and np.array_equal(F[expected==0],np.zeros(np.count_nonzero(expected==0))))
    return result

def timing(n,kind,repeats=30):
    G,f,d0,dfree,z,_,_=fixture(n,kind);a=ContactSolver(G,f);a.solve(d0,dfree,z)
    ts=[[],[]]
    for i in range(repeats):
        for j in (i%2,1-i%2):
            t=time.perf_counter_ns()
            if j==0:solve_contacts(d0,dfree,z,G,f,max_sweeps=400)
            else:a.solve(d0,dfree,z)
            ts[j].append((time.perf_counter_ns()-t)/1e3)
    return dict(contacts=n,kind=kind,repeats=repeats,pythonMedianUs=float(np.median(ts[0])),compiledMedianUs=float(np.median(ts[1])),
        compiledP99Us=float(np.percentile(ts[1],99)),speedup=float(np.median(ts[0])/np.median(ts[1])))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[probe(n,k) for n in (2,8,16,32,64) for k in ('weak','positive','signed')]
    times=[timing(n,k) for n in (8,16,32,64) for k in ('weak','positive','signed')]
    gate=all(v['gate'] for v in rows)
    summary=dict(gate=gate,diagnosticOnly=True,manufacturedCases=True,maximumContacts=64,fastmath=False,
        maximumForceError=max(v['manufacturedForceRelative'] for v in rows),maximumReferenceError=max(v['referenceForceRelative'] for v in rows),
        maximumWorkError=max(v['workRelative'] for v in rows),maximumSweeps=max(v['maximumSweeps'] for v in rows),
        physicalFitAccepted=False,timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'compiled_contacts.json').write_text(json.dumps(dict(summary=summary,cases=rows,benchmark=times),indent=2,allow_nan=False))
    print('G3_COMPILED_CONTACT_GATE '+json.dumps(summary),flush=True)
    for row in rows:print('G3_COMPILED_CONTACT_CASE '+json.dumps(row),flush=True)
    for row in times:print('G3_COMPILED_CONTACT_BENCH '+json.dumps(row),flush=True)
    if not gate:raise ValueError('compiled contact diagnostic failed')
if __name__=='__main__':main()
