"""G3.11j: compiled block processing of the validated synthetic midpoint.
No allocation per sample inside the kernel; no fastmath, no physical fit."""
import argparse,json,time
from pathlib import Path
import numpy as np
from numba import njit
from scipy.linalg import cho_solve
from coupled_modal_midpoint import synthetic
from split_radiation import relative

@njit(cache=True)
def kernel(forces,m,k,d,A,R,M,K,B,S,om2,den,diag,U,V,G,h,gamma,q,v,x,a,
           u,z,free,bf,rhs,y,small,sol,vm,mid,am,ledger):
    n=len(m);p=A.shape[0];jcount=B.shape[0]
    for sample in range(forces.shape[0]):
        for i in range(p):
            u[i]=0.;z[i]=0.
            for j in range(n):
                u[i]+=A[i,j]*v[j];z[i]+=A[i,j]*q[j]
        for j in range(jcount):
            for i in range(p):
                free[j,i]=(a[j,i]-.5*h*om2[j,0]*x[j,i])/den[j,0]
        for i in range(p):
            t=0.
            for j in range(p):
                t+=2*M[i,j]*u[j]/h-K[i,j]*z[j]
            for j in range(jcount):
                for l in range(p):t-=B[j,i,l]*free[j,l]
            bf[i]=t
        for i in range(n):
            t=2*m[i]*v[i]/h-k[i]*q[i]+forces[sample,i]
            for j in range(p):t+=A[j,i]*bf[j]
            rhs[i]=t;y[i]=t/diag[i]
        for i in range(p):
            t=0.
            for j in range(n):t+=U[j,i]*y[j]
            small[i]=t
        for i in range(p):
            t=0.
            for j in range(p):t+=G[i,j]*small[j]
            sol[i]=t
        w=0.;ds=0.
        for i in range(n):
            t=y[i]
            for j in range(p):t-=V[i,j]*sol[j]
            vm[i]=t;q[i]+=h*t;v[i]=2*t-v[i]
            w+=t*forces[sample,i];ds+=d[i]*t*t
        for i in range(p):
            t=0.
            for j in range(n):t+=A[i,j]*vm[j]
            mid[i]=t
        da=0.
        for i in range(p):
            for j in range(p):da+=mid[i]*R[i,j]*mid[j]
        for j in range(jcount):
            for l in range(p):
                t=free[j,l]
                for i in range(p):t+=S[j,i,l]*mid[i]
                am[j,l]=t;x[j,l]+=h*t;a[j,l]=2*t-a[j,l]
                da+=2*gamma*t*t
        ledger[sample,0]=h*w;ledger[sample,1]=h*ds;ledger[sample,2]=h*da

class CompiledBlock:
    def __init__(self,model):
        if model.solver!='lowrank':raise ValueError('lowrank reference required')
        self.model=model
        n=len(model.m);p=model.A.shape[0];j=len(model.B)
        self.G=np.ascontiguousarray(cho_solve(model.fac,np.eye(p)))
        self.work=[np.zeros(p),np.zeros(p),np.zeros((j,p)),np.zeros(p),np.zeros(n),np.zeros(n),
                   np.zeros(p),np.zeros(p),np.zeros(n),np.zeros(p),np.zeros((j,p))]
        self.args=[np.ascontiguousarray(getattr(model,k),dtype=np.float64) for k in
            ('m','k','d','A','R','M','K','B','S','om2','den','diag','U','V')]+[self.G,model.h,model.gamma]
    def process(self,F,ledger):
        F=np.asarray(F)
        if F.dtype!=np.float64 or not F.flags.c_contiguous or F.ndim!=2 or F.shape[1]!=len(self.model.m) or not np.isfinite(F).all():raise ValueError('invalid force block')
        if ledger.shape!=(len(F),3) or ledger.dtype!=np.float64 or not ledger.flags.c_contiguous or not ledger.flags.writeable or np.shares_memory(F,ledger):raise ValueError('invalid ledger')
        m=self.model
        kernel(F,*self.args,m.q,m.v,m.x,m.a,*self.work,ledger)

def proof(n,rate):
    ref=synthetic(n,rate,'dense');a=synthetic(n,rate,'lowrank');fast=CompiledBlock(a)
    t=(np.arange(round(.12*rate))+.5)/rate;direction=np.cos(np.arange(n));direction/=np.linalg.norm(direction)
    F=np.ascontiguousarray((np.where(t<.025,np.sin(2*np.pi*130*t)*np.sin(np.pi*t/.025)**2,0.))[:,None]*direction)
    W=L=absolute=peak=err=state=power=0.;minimum=0.
    for start in range(0,len(F),64):
        block=F[start:start+64];log=np.empty((len(block),3));fast.process(block,log)
        other=np.asarray([ref.step(f) for f in block])
        power=max(power,relative(log,other))
        W+=log[:,0].sum();L+=log[:,1:].sum();absolute+=np.abs(log[:,0]).sum();minimum=min(minimum,float(log[:,1:].min()))
        E=a.energy();peak=max(peak,E);err=max(err,abs(W-L-E))
        state=max(state,relative(a.q,ref.q),relative(a.v,ref.v),relative(a.x,ref.x),relative(a.a,ref.a))
        if not np.isfinite([W,L,E,state,power]).all():raise ValueError('nonfinite compiled state')
    budget=err/max(absolute,peak,1e-30)
    return dict(structuralModes=n,sampleRate=rate,energyRelative=budget,stateRelative=state,ledgerRelative=power,minimumLoss=minimum,
        gate=bool(budget<=1e-9 and max(state,power)<=1e-8 and minimum>=-1e-14))

def timing(n,rate=48000):
    F=np.ascontiguousarray(np.tile(np.ones(n)/np.sqrt(n),(256,1)));log=np.empty((256,3))
    a=synthetic(n,rate,'lowrank');b=synthetic(n,rate,'lowrank');fast=CompiledBlock(b)
    fast.process(F,log)
    for f in F:a.step(f)
    results=[]
    for mode in ('python','compiled'):
        times=[]
        for _ in range(15):
            t=time.perf_counter_ns()
            if mode=='compiled':fast.process(F,log)
            else:
                for i,f in enumerate(F):log[i]=a.step(f)
            times.append((time.perf_counter_ns()-t)/len(F)/1000)
        results.append(dict(mode=mode,medianUs=float(np.median(times)),p95Us=float(np.percentile(times,95)),blockSize=len(F)))
    return dict(structuralModes=n,timings=results,speedup=results[0]['medianUs']/results[1]['medianUs'],
        fractionOf48kSampleBudget=results[1]['p95Us']/(1e6/rate))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[proof(n,r) for n in (32,64,128,256) for r in (44100,48000,96000)]
    times=[timing(n) for n in (32,64,128,256,512)]
    gate=all(v['gate'] for v in rows)
    summary=dict(gate=gate,diagnosticOnly=True,syntheticParameters=True,compiledBlock=True,fastmath=False,physicalFitAccepted=False,
        maximumEnergyError=max(v['energyRelative'] for v in rows),maximumStateError=max(v['stateRelative'] for v in rows),
        maximumLedgerError=max(v['ledgerRelative'] for v in rows),timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'compiled_midpoint.json').write_text(json.dumps(dict(summary=summary,cases=rows,benchmark=times),indent=2,allow_nan=False))
    print('G3_COMPILED_MIDPOINT_GATE '+json.dumps(summary),flush=True)
    print('G3_COMPILED_MIDPOINT_BENCHMARK '+json.dumps(times),flush=True)
    if not gate:raise ValueError('compiled kernel equivalence failed')
if __name__=='__main__':main()
