"""G3.12j: compiled dry physical-wire midpoint.
Fixed Schur solve, preallocated buffers, no fastmath. Reference unchanged.
No acoustic load, hammer, or whole-engine real-time claim."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from numba import njit
from scipy.linalg import cho_solve
from wire_physical_midpoint import CoupledWire,load,proof
from split_radiation import relative

@njit(cache=True)
def kernel(h,k,D,A,P,ports,hammer,m0,k0,d0,mi,ki,di,ks,ds,C,invHi,J,
           q,v,x,u,rv,rq,rm,ri,rb,vm,um,forces,obs,ledger):
    n=len(q);nw=len(x);ns=x.shape[1];np_=P.shape[1];a=2/h
    for t in range(len(forces)):
        F=forces[t]
        for w in range(nw):
            vv=0.;qq=0.
            for j in range(n):
                vv+=A[w,j]*v[j];qq+=A[w,j]*q[j]
            rv[w]=vv;rq[w]=qq
            b=a*m0[w]*vv-k0[w]*qq
            for i in range(ns):
                R=a*u[w,i]-ks[w,i]*x[w,i]+a*mi[w,i]*vv-ki[w,i]*qq+hammer[w,i]*F[ports[w]]
                ri[w,i]=R
                b+=a*mi[w,i]*u[w,i]-ki[w,i]*x[w,i]-C[w,i]*R*invHi[w,i]
            rm[w]=b
        for j in range(n):
            b=a*v[j]-k[j]*q[j]
            for w in range(nw):b+=A[w,j]*rm[w]
            for i in range(np_):b+=P[j,i]*F[i]
            rb[j]=b
        for j in range(n):
            s=0.
            for i in range(n):s+=J[j,i]*rb[i]
            vm[j]=s
        loss=0.
        for j in range(n):
            d=0.
            for i in range(n):d+=D[j,i]*vm[i]
            loss+=vm[j]*d
        for i in range(np_):
            y=0.
            for j in range(n):y+=P[j,i]*vm[j]
            obs[t,i]=y
        for w in range(nw):
            vv=0.
            for j in range(n):vv+=A[w,j]*vm[j]
            loss+=d0[w]*vv*vv
            for i in range(ns):
                s=(ri[w,i]-C[w,i]*vv)*invHi[w,i]
                um[w,i]=s
                loss+=ds[w,i]*s*s+2*di[w,i]*vv*s
                obs[t,ports[w]]+=hammer[w,i]*s
        work=0.
        for i in range(np_):work+=F[i]*obs[t,i]
        ledger[t,0]=h*work;ledger[t,1]=h*loss
        for j in range(n):
            q[j]+=h*vm[j];v[j]=2*vm[j]-v[j]
        for w in range(nw):
            for i in range(ns):
                x[w,i]+=h*um[w,i];u[w,i]=2*um[w,i]-u[w,i]

class Compiled(CoupledWire):
    def __init__(self,*args):
        super().__init__(*args)
        n=self.n;h=self.h
        self.J=np.ascontiguousarray(cho_solve(self.fac,np.eye(n)))
        H=2/h*self.Mb+self.Db+h*self.Kb/2-self.A.T@(np.sum(self.C*self.C/self.Hi,axis=1)[:,None]*self.A)
        self.inverseResidual=relative(H@self.J,np.eye(n))
        if self.inverseResidual>1e-8:raise ValueError('Schur inverse residual')
        self.ports=np.array([w.port for w in self.wires],np.int64)
        self.hammer=np.ascontiguousarray(np.stack([w.p[:self.partials] for w in self.wires]))
        self.invHi=np.ascontiguousarray(1/self.Hi)
        self.rv=np.zeros(self.nw);self.rq=self.rv.copy();self.rm=self.rv.copy()
        self.ri=np.zeros_like(self.x);self.um=np.zeros_like(self.x)
        self.rb=np.zeros(n);self.vm=np.zeros(n)
        self.one=np.zeros((1,self.P.shape[1]));self.ob=np.zeros_like(self.one);self.le=np.zeros((1,2))
    def process(self,forces,obs,ledger):
        p=self.P.shape[1];n=len(forces)
        for a,shape in ((forces,(n,p)),(obs,(n,p)),(ledger,(n,2))):
            if not isinstance(a,np.ndarray) or a.shape!=shape or a.dtype!=np.float64 or not a.flags.c_contiguous:raise ValueError('contiguous float64 buffers required')
        if not np.isfinite(forces).all() or not obs.flags.writeable or not ledger.flags.writeable:raise ValueError('invalid buffer')
        for i,a in enumerate((forces,obs,ledger)):
            for b in (forces,obs,ledger)[i+1:]:
                if np.shares_memory(a,b):raise ValueError('alias')
            for b in (self.q,self.v,self.x,self.u,self.J,self.P,self.A,self.ri,self.um,self.rb,self.vm):
                if np.shares_memory(a,b):raise ValueError('state alias')
        kernel(self.h,self.k,self.D,self.A,self.P,self.ports,self.hammer,self.m0,self.k0,self.d0,
            self.mi,self.ki,self.di,self.ks,self.ds,self.C,self.invHi,self.J,self.q,self.v,self.x,self.u,
            self.rv,self.rq,self.rm,self.ri,self.rb,self.vm,self.um,forces,obs,ledger)
    def step(self,F):
        self.one[0]=F;self.process(self.one,self.ob,self.le)
        return self.ob[0].copy(),float(self.le[0,0]),float(self.le[0,1])

def block_proof(make,rate,n):
    a=make(rate,n);b=make(rate,n);ref=CoupledWire(a.k,a.D,a.P-a.A.T@np.array([[w.P[0] if w.port==j else 0. for j in range(a.P.shape[1])] for w in a.wires]),a.A,a.wires,rate,n)
    count=513;p=a.P.shape[1];F=np.random.default_rng(42).normal(size=(count,p));F[300:]=0
    O=np.zeros_like(F);L=np.zeros((count,2));a.process(F,O,L)
    O2=np.zeros_like(F);L2=np.zeros_like(L)
    for start in range(0,count,37):b.process(F[start:start+37],O2[start:start+37],L2[start:start+37])
    R=[];W=[]
    for f in F:
        o,w,l=ref.step(f);R.append(o);W.append([w,l])
    state=max(relative(getattr(a,x),getattr(ref,x)) for x in ('q','v','x','u'))
    bitwise=bool(np.array_equal(O,O2) and np.array_equal(L,L2) and all(np.array_equal(getattr(a,x),getattr(b,x)) for x in ('q','v','x','u')))
    silent=make(rate,n);Z=np.zeros((17,p));Y=Z.copy();Q=np.zeros((17,2));silent.process(Z,Y,Q)
    silence=bool(not np.any(Y) and not np.any(Q) and silent.energy()==0)
    obs=relative(O,np.asarray(R));ledger=relative(L,np.asarray(W))
    balance=abs(a.energy()+L[:,1].sum()-L[:,0].sum())/max(abs(L[:,0]).sum(),L[:,1].sum(),a.energy(),1e-30)
    gate=bool(bitwise and silence and max(state,obs,ledger,balance)<=1e-8 and L[:,1].min()>=-1e-18)
    return dict(gate=gate,rate=rate,partials=n,stateRelative=state,observerRelative=obs,ledgerRelative=ledger,
        energyRelative=float(balance),partitionBitwise=bitwise,silentExact=silence,inverseResidual=a.inverseResidual)

def benchmark(make,rate,n,block):
    a=make(rate,n);p=a.P.shape[1];F=np.random.default_rng(13).normal(size=(block,p));O=np.zeros_like(F);L=np.zeros((block,2))
    # Warm up JIT using a separate model; exclude compilation.
    warm=make(rate,n);warm.process(F,O,L)
    times=[];work=loss=peak=error=0.
    for i in range(200):
        start=time.perf_counter_ns();a.process(F,O,L);times.append((time.perf_counter_ns()-start)/1000)
        work+=L[:,0].sum();loss+=L[:,1].sum();E=a.energy();peak=max(peak,E,abs(work),loss)
        error=max(error,abs(E+loss-work))
    return dict(rate=rate,partials=n,block=block,medianUsPerSample=float(np.median(times)/block),
        p99BudgetFraction=float(np.percentile(times,99)/(block*1e6/rate)),overruns=int(np.count_nonzero(np.asarray(times)>block*1e6/rate)),
        energyRelative=float(error/max(peak,1e-30)))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','midpoint','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();z,wires,sha=load(a.source,a.scale)
    raw=(a.midpoint/'frozen_wire_midpoint.json').read_bytes();f=json.loads(raw)
    d=json.loads((a.midpoint/'wire_midpoint.json').read_text());s=d['summary']
    if d['frozenSha256']!=hashlib.sha256(raw).hexdigest() or f['sourceFrozenSha256']!=sha or any(s.get(k)!=v for k,v in dict(gate=True,interiorReductionGate=True,selectedPartials=16,structureRank=80,wires=10,acousticLoadIncluded=False,hammerContactIncluded=False,timeDomainReady=False).items()):raise ValueError('invalid midpoint provenance')
    if max(s['trainingMaximum'],s['validationMaximum'])>.05:raise ValueError('invalid interior gate')
    k,D,P,A=(z[x] for x in ('stiffness','damping','ports','wirePorts'))
    make=lambda r,n:Compiled(k,D,P,A,wires,r,n)
    proofs=[block_proof(make,r,n) for r in (48000,96000) for n in (16,32,64,128)]
    dense=[dict(rate=r,**proof(make(r,16))) for r in (48000,96000)]
    bench=[benchmark(make,r,n,b) for r in (48000,96000) for n in (16,32,64,128) for b in (64,128)]
    gate=all(v['gate'] for v in proofs+dense) and all(v['energyRelative']<=1e-8 for v in bench)
    summary=dict(gate=gate,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,structureRank=80,wires=10,
        maximumEnergyError=max(v['energyRelative'] for v in proofs+dense+bench),maximumStateError=max(v['stateRelative'] for v in proofs),
        configurations=len(bench),zeroOverrunConfigurations=sum(v['overruns']==0 for v in bench),
        acousticLoadIncluded=False,hammerContactIncluded=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'compiled_wire_midpoint.json').write_text(json.dumps(dict(summary=summary,proofs=proofs,dense=dense,benchmark=bench,
        sourceFrozenSha256=sha,midpointFrozenSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_COMPILED_WIRE_GATE '+json.dumps(summary),flush=True)
    for v in bench:print('G3_COMPILED_WIRE_BENCH '+json.dumps(v),flush=True)
    if not gate:raise ValueError('compiled physical wire proof failed')
if __name__=='__main__':main()
