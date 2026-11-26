"""G3.11k: contiguous modal layout and sustained block diagnostic.
All loads synthetic; no audio callback or physical fit approval."""
import argparse,json,time
from pathlib import Path
import numpy as np
from numba import njit
from scipy.linalg import cho_solve
from compiled_modal_midpoint import CompiledBlock
from coupled_modal_midpoint import CoupledModal
from split_radiation import relative

@njit(cache=True)
def kernel_contiguous(forces,m,k,d,A,R,M,K,B,S,om2,den,diag,U,V,G,h,gamma,q,v,x,a,
           u,z,free,bf,rhs,y,small,sol,vm,mid,am,ledger):
    n=len(m);p=A.shape[1];jcount=B.shape[0]
    for sample in range(forces.shape[0]):
        for i in range(p):
            u[i]=0.;z[i]=0.
        for j in range(n):
            for i in range(p):
                u[i]+=A[j,i]*v[j];z[i]+=A[j,i]*q[j]
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
            for j in range(p):t+=A[i,j]*bf[j]
            rhs[i]=t;y[i]=t/diag[i]
        for i in range(p):small[i]=0.
        for j in range(n):
            for i in range(p):small[i]+=U[j,i]*y[j]
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
        for i in range(p):mid[i]=0.
        for j in range(n):
            for i in range(p):mid[i]+=A[j,i]*vm[j]
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

class ContiguousBlock:
    def __init__(self,model):
        if model.solver!='lowrank':raise ValueError('lowrank reference required')
        self.model=model
        n=len(model.m);p=model.A.shape[0];j=len(model.B)
        self.G=np.ascontiguousarray(cho_solve(model.fac,np.eye(p)))
        self.work=[np.zeros(p),np.zeros(p),np.zeros((j,p)),np.zeros(p),np.zeros(n),np.zeros(n),
                   np.zeros(p),np.zeros(p),np.zeros(n),np.zeros(p),np.zeros((j,p))]
        self.args=[np.ascontiguousarray(getattr(model,k),dtype=np.float64) for k in
            ('m','k','d','A','R','M','K','B','S','om2','den','diag','U','V')]+[self.G,model.h,model.gamma]
        self.args[3]=np.ascontiguousarray(model.A.T,dtype=np.float64)
    def process(self,F,ledger):
        F=np.asarray(F)
        if F.dtype!=np.float64 or not F.flags.c_contiguous or F.ndim!=2 or F.shape[1]!=len(self.model.m) or not np.isfinite(F).all():raise ValueError('invalid force block')
        if ledger.shape!=(len(F),3) or ledger.dtype!=np.float64 or not ledger.flags.c_contiguous or not ledger.flags.writeable or np.shares_memory(F,ledger):raise ValueError('invalid ledger')
        m=self.model
        kernel_contiguous(F,*self.args,m.q,m.v,m.x,m.a,*self.work,ledger)


def stress_model(n,atoms,rate,solver='lowrank'):
    rng=np.random.default_rng(731)
    m=np.linspace(.7,1.3,n);k=m*(2*np.pi*np.geomspace(35,2400,n))**2;d=6*m
    A=rng.normal(size=(4,n))/np.sqrt(n);centers=np.linspace(20,800,atoms)
    factors=rng.normal(size=(atoms,4,4))
    weights=(factors@factors.transpose(0,2,1))*(100/atoms)
    C=np.concatenate([np.stack([.5*np.eye(4),.004*np.eye(4),100*np.eye(4)]),weights])
    return CoupledModal(m,k,d,A,C,centers,7.,rate,solver)

def proof(n,atoms,rate,block=64,seconds=.12):
    a=stress_model(n,atoms,rate);ref=stress_model(n,atoms,rate,'dense')
    fast=ContiguousBlock(a);W=L=absolute=peak=err=state=power=0.;minimum=0.
    t=(np.arange(round(seconds*rate))+.5)/rate;direction=np.cos(np.arange(n));direction/=np.linalg.norm(direction)
    F=np.ascontiguousarray(np.where(t<.025,np.sin(2*np.pi*130*t)*np.sin(np.pi*t/.025)**2,0.)[:,None]*direction)
    for start in range(0,len(F),block):
        ff=F[start:start+block];ledger=np.empty((len(ff),3));fast.process(ff,ledger)
        other=np.asarray([ref.step(f) for f in ff]);power=max(power,relative(ledger,other))
        W+=ledger[:,0].sum();L+=ledger[:,1:].sum();absolute+=np.abs(ledger[:,0]).sum()
        minimum=min(minimum,float(ledger[:,1:].min()))
        E=a.energy();peak=max(peak,E);err=max(err,abs(W-L-E))
        state=max(state,*(relative(getattr(a,k),getattr(ref,k)) for k in ('q','v','x','a')))
        if not np.isfinite([W,L,E,state,power]).all():raise ValueError('nonfinite state')
    budget=err/max(absolute,peak,1e-30)
    return dict(structuralModes=n,atoms=atoms,sampleRate=rate,blockSize=block,energyRelative=budget,
        stateRelative=state,ledgerRelative=power,minimumLoss=minimum,
        gate=bool(budget<=1e-9 and max(state,power)<=1e-8 and minimum>=-1e-14))

def timing(n,atoms,rate,block,blocks=200):
    # Warm both compiled variants before timing. Reuse buffers and alternate
    # measurement order. Deadline is a block budget, not an audio callback.
    F=np.ascontiguousarray(np.tile(np.cos(np.arange(n))/np.sqrt(n),(block,1)));ledger=np.empty((block,3))
    models=[stress_model(n,atoms,rate) for _ in range(2)]
    engines=[CompiledBlock(models[0]),ContiguousBlock(models[1])]
    for a in engines:a.process(F,ledger)
    times=[[],[]]
    for j in range(blocks):
        for i in (j%2,1-j%2):
            start=time.perf_counter_ns();engines[i].process(F,ledger)
            times[i].append((time.perf_counter_ns()-start)/1e3)
    budget=1e6*block/rate;rows=[]
    for mode,t in zip(('original','contiguous'),times):
        rows.append(dict(mode=mode,medianUsPerSample=float(np.median(t)/block),p95BlockUs=float(np.percentile(t,95)),
            p99BlockUs=float(np.percentile(t,99)),maxBlockUs=max(t),deadlineOverruns=sum(v>budget for v in t),
            p99BudgetFraction=float(np.percentile(t,99)/budget)))
    state=max(relative(getattr(models[0],k),getattr(models[1],k)) for k in ('q','v','x','a'))
    if not np.isfinite(state) or state>1e-8:raise ValueError('benchmark state mismatch')
    return dict(structuralModes=n,atoms=atoms,sampleRate=rate,blockSize=block,blocks=blocks,blockBudgetUs=budget,
        timings=rows,medianSpeedup=rows[0]['medianUsPerSample']/rows[1]['medianUsPerSample'],stateRelative=state)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[proof(n,j,r) for n in (64,256,512) for j in (5,39) for r in (48000,96000)]
    times=[timing(n,j,r,b) for n in (128,256,512,1024) for j in (5,39) for r in (48000,96000) for b in (32,64,128,256)]
    gate=all(v['gate'] for v in rows)
    summary=dict(gate=gate,diagnosticOnly=True,syntheticParameters=True,physicalFitAccepted=False,fastmath=False,
        maximumEnergyError=max(v['energyRelative'] for v in rows),maximumStateError=max(v['stateRelative'] for v in rows),
        maximumLedgerError=max(v['ledgerRelative'] for v in rows),benchmarkConfigurations=len(times),
        timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'contiguous_midpoint.json').write_text(json.dumps(dict(summary=summary,cases=rows,benchmark=times),indent=2,allow_nan=False))
    print('G3_CONTIGUOUS_GATE '+json.dumps(summary),flush=True)
    for row in times:print('G3_CONTIGUOUS_BENCH '+json.dumps(row),flush=True)
    if not gate:raise ValueError('contiguous kernel failed equivalence')
if __name__=='__main__':main()
