"""G3.11m: compiled reciprocal string-board-air Schur block.
Synthetic coefficients only. Preallocate state/work, no fastmath."""
import argparse,json,time
from pathlib import Path
import numpy as np
from numba import njit
from scipy.linalg import cho_solve
from string_board_schur import StringBoard
from contiguous_midpoint import stress_model
from split_radiation import relative

@njit(cache=True)
def string_kernel(forces,Fs,ms,ks,ds_s,J,kc,dc,c,hs,qs,vs,rs,m,k,d,A,R,M,K,B,S,om2,den,diag,U,V,G,h,gamma,q,v,x,a,
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
        for j in range(len(ms)):
            rel=qs[j]
            for i in range(p):rel-=J[j,i]*z[i]
            spring=kc[j]*rel
            rs[j]=2*ms[j]*vs[j]/h-ks[j]*qs[j]+Fs[sample,j]-spring
            g=spring+c[j]*rs[j]/hs[j]
            for i in range(p):bf[i]+=J[j,i]*g
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
        coupling_loss=0.
        for j in range(len(ms)):
            gm=0.
            for i in range(p):gm+=J[j,i]*mid[i]
            sm=(rs[j]+c[j]*gm)/hs[j]
            qs[j]+=h*sm;vs[j]=2*sm-vs[j]
            w+=sm*Fs[sample,j];ds+=ds_s[j]*sm*sm
            rv=sm-gm;coupling_loss+=dc[j]*rv*rv
        da=0.
        for i in range(p):
            for j in range(p):da+=mid[i]*R[i,j]*mid[j]
        for j in range(jcount):
            for l in range(p):
                t=free[j,l]
                for i in range(p):t+=S[j,i,l]*mid[i]
                am[j,l]=t;x[j,l]+=h*t;a[j,l]=2*t-a[j,l]
                da+=2*gamma*t*t
        ledger[sample,0]=h*w;ledger[sample,1]=h*ds;ledger[sample,2]=h*coupling_loss;ledger[sample,3]=h*da


class StringBlock:
    def __init__(self,model):
        if model.solver!='schur':raise ValueError('Schur model required')
        self.model=model;b=model.b
        n=len(b.m);p=b.A.shape[0];j=len(b.B)
        self.rs=np.zeros(len(model.ms))
        self.work=[np.zeros(p),np.zeros(p),np.zeros((j,p)),np.zeros(p),np.zeros(n),np.zeros(n),
                   np.zeros(p),np.zeros(p),np.zeros(n),np.zeros(p),np.zeros((j,p))]
        self.string_args=[np.ascontiguousarray(getattr(model,k),dtype=np.float64) for k in ('ms','ks','ds','G','kc','dc','c','hs')]
        self.args=[np.ascontiguousarray(getattr(b,k),dtype=np.float64) for k in ('m','k','d','A','R','M','K','B','S','om2','den','diag')]
        self.args[3]=np.ascontiguousarray(b.A.T,dtype=np.float64)
        self.args += [np.ascontiguousarray(model.U),np.ascontiguousarray(model.V),np.ascontiguousarray(cho_solve(model.fac,np.eye(p))),b.h,b.gamma]
    def process(self,Fb,Fs,ledger):
        a=self.model;b=a.b
        for F,n in ((Fb,len(b.m)),(Fs,len(a.ms))):
            if not isinstance(F,np.ndarray) or F.ndim!=2 or F.shape[1]!=n or F.dtype!=np.float64 or not F.flags.c_contiguous or not np.isfinite(F).all():raise ValueError('invalid force block')
        if len(Fb)!=len(Fs) or ledger.shape!=(len(Fb),4) or ledger.dtype!=np.float64 or not ledger.flags.c_contiguous or not ledger.flags.writeable or any(np.shares_memory(ledger,v) for v in (Fb,Fs,a.q,a.v,b.q,b.v,b.x,b.a)):raise ValueError('invalid ledger')
        if any(np.shares_memory(F,v) for F in (Fb,Fs) for v in (a.q,a.v,b.q,b.v,b.x,b.a)):raise ValueError('force aliases state')
        string_kernel(Fb,Fs,*self.string_args,a.q,a.v,self.rs,*self.args,b.q,b.v,b.x,b.a,*self.work,ledger)

def fixture(voices,partials,n,atoms,rate,solver='schur'):
    b=stress_model(n,atoms,rate);f=(110*2**(np.arange(voices)/24))[:,None]*np.arange(1,partials+1)
    f=f.ravel();m=np.linspace(.02,.04,len(f));k=m*(2*np.pi*f)**2;d=.5*m
    rng=np.random.default_rng(932);G=np.repeat(rng.normal(size=(voices,4)),partials,axis=0)/np.sqrt(4*partials)
    kc=.025*k;dc=.02*np.sqrt(m*kc)
    return StringBoard(b,m,k,d,G,kc,dc,solver)

def state_error(a,b):
    return max(*(relative(getattr(a,k),getattr(b,k)) for k in ('q','v')),
        *(relative(getattr(a.b,k),getattr(b.b,k)) for k in ('q','v','x','a')))

def proof(voices,partials,n,atoms,rate,seconds=.05,block=64):
    a=fixture(voices,partials,n,atoms,rate);ref=fixture(voices,partials,n,atoms,rate,'dense')
    fast=StringBlock(a);W=L=absolute=peak=err=state=power=0.;minimum=0.
    t=(np.arange(round(seconds*rate))+.5)/rate;direction=np.cos(np.arange(voices*partials));direction/=np.linalg.norm(direction)
    Fs=np.ascontiguousarray(np.where(t<.015,np.sin(2*np.pi*130*t)*np.sin(np.pi*t/.015)**2,0.)[:,None]*direction)
    Fb=np.zeros((len(Fs),n))
    for start in range(0,len(Fs),block):
        x=Fb[start:start+block];y=Fs[start:start+block];log=np.empty((len(x),4));fast.process(x,y,log)
        other=np.asarray([ref.step(b,s) for b,s in zip(x,y)]);power=max(power,relative(log,other))
        W+=log[:,0].sum();L+=log[:,1:].sum();absolute+=np.abs(log[:,0]).sum();minimum=min(minimum,float(log[:,1:].min()))
        E=a.energy();peak=max(peak,E);err=max(err,abs(W-L-E));state=max(state,state_error(a,ref))
        if not np.isfinite([W,L,E,state,power]).all():raise ValueError('nonfinite state')
    budget=err/max(absolute,peak,1e-30)
    return dict(voices=voices,partials=partials,boardModes=n,atoms=atoms,sampleRate=rate,energyRelative=budget,stateRelative=state,
        ledgerRelative=power,minimumLoss=minimum,gate=bool(budget<=1e-9 and max(state,power)<=1e-8 and minimum>=-1e-14))

def timing(voices,partials,n,atoms,rate,block,blocks=200):
    a=fixture(voices,partials,n,atoms,rate);fast=StringBlock(a)
    Fb=np.zeros((block,n));s=voices*partials
    Fs=np.ascontiguousarray(np.sin(2*np.pi*130*(np.arange(block)+.5)/rate)[:,None]*np.cos(np.arange(s))/np.sqrt(s))
    log=np.empty((block,4));fast.process(Fb,Fs,log)
    times=[];W=a.energy();loss=0.;work=0.;abswork=0.;peak=W;err=0.;minimum=0.
    for _ in range(blocks):
        t=time.perf_counter_ns();fast.process(Fb,Fs,log);times.append((time.perf_counter_ns()-t)/1e3)
        work+=log[:,0].sum();loss+=log[:,1:].sum();abswork+=np.abs(log[:,0]).sum()
        E=a.energy();peak=max(peak,E);err=max(err,abs(W+work-loss-E));minimum=min(minimum,float(log[:,1:].min()))
        if not np.isfinite([E,err,work,loss]).all():raise ValueError('nonfinite stress')
    budget=1e6*block/rate;energy=err/max(abswork,peak,1e-30)
    return dict(voices=voices,partials=partials,stringDOFs=s,boardModes=n,atoms=atoms,sampleRate=rate,blockSize=block,blocks=blocks,
        medianUsPerSample=float(np.median(times)/block),p99BlockUs=float(np.percentile(times,99)),maxBlockUs=max(times),
        p99BudgetFraction=float(np.percentile(times,99)/budget),overruns=sum(v>budget for v in times),
        energyRelative=energy,minimumLoss=minimum,gate=bool(energy<=1e-9 and minimum>=-1e-14))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[proof(v,j,64,k,r) for v in (32,64) for j in (4,8) for k in (5,39) for r in (48000,96000)]
    times=[timing(v,j,n,k,r,64) for v in (32,64) for j in (4,8,16) for n in (128,256) for k in (5,39) for r in (48000,96000)]
    gate=all(v['gate'] for v in rows+times)
    summary=dict(gate=gate,diagnosticOnly=True,syntheticParameters=True,physicalFitAccepted=False,fastmath=False,maximumSyntheticVoices=64,
        maximumBenchmarkStringDOFs=1024,maximumReferenceStringDOFs=512,maximumEnergyError=max(v['energyRelative'] for v in rows+times),
        maximumStateError=max(v['stateRelative'] for v in rows),maximumLedgerError=max(v['ledgerRelative'] for v in rows),
        benchmarkConfigurations=len(times),timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'compiled_string_board.json').write_text(json.dumps(dict(summary=summary,cases=rows,benchmark=times),indent=2,allow_nan=False))
    print('G3_COMPILED_STRINGS_GATE '+json.dumps(summary),flush=True)
    for row in times:print('G3_COMPILED_STRINGS_BENCH '+json.dumps(row),flush=True)
    if not gate:raise ValueError('compiled string diagnostic failed')
if __name__=='__main__':main()
