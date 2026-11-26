"""G3.11o: compiled variable damper, fixed normalized board map,
per-sample four-dimensional SPD solve. Synthetic diagnostic only."""
import argparse,json,time
from pathlib import Path
import numpy as np
from numba import njit
from scipy.linalg import solve_triangular
from compiled_string_board import fixture,state_error
from variable_damper import VariableDamper,PedalControl
from split_radiation import relative

@njit(cache=True)
def variable_kernel(forces,Fs,levels,mapping,extra,base,H0,Jt,H,Lc,ms,ks,ds_s,J,kc,dc,c,hs,qs,vs,rs,m,k,d,A,R,M,K,B,S,om2,den,diag,U,V,G,h,gamma,q,v,x,a,
           u,z,free,bf,rhs,y,small,sol,vm,mid,am,ledger):
    n=len(m);p=A.shape[1];jcount=B.shape[0]
    for sample in range(forces.shape[0]):
        for i in range(p):
            for j in range(p):H[i,j]=H0[i,j]
        for j in range(len(ms)):
            hs[j]=base[j]+extra[j]*levels[sample,mapping[j]]+c[j]
            eff=c[j]*(hs[j]-c[j])/hs[j]
            for i in range(p):
                for l in range(i+1):H[i,l]+=eff*Jt[j,i]*Jt[j,l]
        for i in range(p):
            for j in range(i):H[j,i]=H[i,j]
        # Cholesky of I + L^T Hphysical L, always SPD.
        for i in range(p):
            for j in range(i+1):
                t=H[i,j]+(1. if i==j else 0.)
                for l in range(j):t-=Lc[i,l]*Lc[j,l]
                Lc[i,j]=np.sqrt(t) if i==j else t/Lc[j,j]
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
            for j in range(p):t+=H[i,j]*small[j]
            for j in range(i):t-=Lc[i,j]*sol[j]
            sol[i]=t/Lc[i,i]
        for i in range(p-1,-1,-1):
            t=sol[i]
            for j in range(i+1,p):t-=Lc[j,i]*sol[j]
            sol[i]=t/Lc[i,i]
        w=0.;ds=0.;damper=0.
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
            damper+=extra[j]*levels[sample,mapping[j]]*sm*sm
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
        ledger[sample,0]=h*w;ledger[sample,1]=h*(ds+damper);ledger[sample,2]=h*coupling_loss;ledger[sample,3]=h*da;ledger[sample,4]=h*damper



class VariableBlock:
    def __init__(self,model,mapping,extra):
        if model.solver!='schur':raise ValueError('Schur model required')
        self.model=model;b=model.b;n=len(b.m);p=b.A.shape[0];j=len(b.B)
        self.mapping=np.asarray(mapping);self.extra=np.asarray(extra,dtype=float).copy()
        if self.mapping.shape!=model.ms.shape or self.mapping.dtype.kind not in 'iu' or np.any(self.mapping<0) or self.extra.shape!=model.ms.shape or not np.isfinite(self.extra).all() or np.any(self.extra<0):raise ValueError('invalid damping map')
        self.mapping=np.ascontiguousarray(self.mapping,dtype=np.int64)
        self.voices=int(self.mapping.max())+1
        # L L^T=A D^-1 A^T. The normalized map has identity Gram.
        # Reject deficient maps rather than regularize physical equations.
        L=np.linalg.cholesky((b.A/b.diag)@b.A.T)
        U=np.ascontiguousarray(solve_triangular(L,b.A,lower=True).T)
        V=np.ascontiguousarray(U/b.diag[:,None])
        if relative(U.T@V,np.eye(p))>1e-9:raise ValueError('ill-conditioned board map')
        H=b.R+2*b.M/b.h+b.h*b.K/2+np.einsum('jik,jlk->il',b.S,b.B)
        H0=np.ascontiguousarray(L.T@H@L)
        self.pre=[self.mapping,self.extra,model.base.copy(),H0,np.ascontiguousarray(model.G@L),np.zeros((p,p)),np.zeros((p,p))]
        self.string_args=[np.ascontiguousarray(getattr(model,k),dtype=np.float64).copy() for k in ('ms','ks','ds','G','kc','dc','c','hs')]
        self.rs=np.zeros(len(model.ms))
        self.args=[np.ascontiguousarray(getattr(b,k),dtype=np.float64) for k in ('m','k','d','A','R','M','K','B','S','om2','den','diag')]
        self.args[3]=np.ascontiguousarray(b.A.T)
        self.args += [U,V,np.zeros((p,p)),b.h,b.gamma]
        self.work=[np.zeros(p),np.zeros(p),np.zeros((j,p)),np.zeros(p),np.zeros(n),np.zeros(n),np.zeros(p),np.zeros(p),np.zeros(n),np.zeros(p),np.zeros((j,p))]
    def process(self,Fb,Fs,levels,ledger):
        a=self.model;b=a.b
        for F,n in ((Fb,len(b.m)),(Fs,len(a.ms)),(levels,self.voices)):
            if not isinstance(F,np.ndarray) or F.ndim!=2 or F.shape!=(len(Fb),n) or F.dtype!=np.float64 or not F.flags.c_contiguous or not np.isfinite(F).all():raise ValueError('invalid input')
        if np.any((levels<0)|(levels>1)):raise ValueError('invalid damper level')
        if ledger.shape!=(len(Fb),5) or ledger.dtype!=np.float64 or not ledger.flags.c_contiguous or not ledger.flags.writeable:raise ValueError('invalid ledger')
        states=(a.q,a.v,b.q,b.v,b.x,b.a)
        if any(np.shares_memory(v,w) for v in (Fb,Fs,levels,ledger) for w in states) or any(np.shares_memory(ledger,v) for v in (Fb,Fs,levels)):raise ValueError('alias')
        variable_kernel(Fb,Fs,levels,*self.pre,*self.string_args,a.q,a.v,self.rs,*self.args,b.q,b.v,b.x,b.a,*self.work,ledger)
        if len(Fb):a.ds[:]=self.string_args[2]+self.extra*levels[-1,self.mapping]
        # model.step must not be used after this wrapper: its factor is frozen.
        
def input_blocks(voices,partials,n,rate,seconds):
    N=round(rate*seconds);t=(np.arange(N)+.5)/rate
    direction=np.cos(np.arange(voices*partials));direction/=np.linalg.norm(direction)
    Fs=np.ascontiguousarray(np.where(t<.015,np.sin(2*np.pi*130*t)*np.sin(np.pi*t/.015)**2,0.)[:,None]*direction)
    Fb=np.zeros((N,n));ctrl=PedalControl(voices,rate);levels=np.empty((N,voices))
    events={0:('on',0),round(.01*rate):('pedal',1.),round(.02*rate):('off',0),round(.035*rate):('pedal',.5),round(.05*rate):('pedal',0.)}
    for i in range(N):
        if i in events:
            k,v=events[i]
            if k=='pedal':ctrl.sustain(v)
            else:ctrl.note(v,k=='on')
        levels[i]=ctrl.advance()
    return Fb,Fs,levels

def proof(voices,partials,n,atoms,rate,seconds=.07,block=64):
    a=fixture(voices,partials,n,atoms,rate);b=fixture(voices,partials,n,atoms,rate,'dense')
    mapping=np.repeat(np.arange(voices),partials);extra=160*a.ms
    fast=VariableBlock(a,mapping,extra);ref=VariableDamper(b,mapping,extra)
    F,S,D=input_blocks(voices,partials,n,rate,seconds)
    W=loss=absolute=peak=err=state=power=0.;minimum=0.
    for start in range(0,len(F),block):
        f=F[start:start+block];s=S[start:start+block];d=D[start:start+block];log=np.empty((len(f),5))
        fast.process(f,s,d,log);other=[]
        for x,y,z in zip(f,s,d):
            w,dl=ref.step(x,y,z);other.append(np.r_[w,dl])
        power=max(power,relative(log,np.asarray(other)));state=max(state,state_error(a,b))
        W+=log[:,0].sum();loss+=log[:,1:4].sum();absolute+=np.abs(log[:,0]).sum();E=a.energy()
        peak=max(peak,E);err=max(err,abs(W-loss-E));minimum=min(minimum,float(log[:,1:].min()),float((log[:,1]-log[:,4]).min()))
        if not np.isfinite([W,loss,E,state,power]).all():raise ValueError('nonfinite response')
    energy=err/max(absolute,peak,1e-30)
    return dict(voices=voices,partials=partials,boardModes=n,atoms=atoms,sampleRate=rate,energyRelative=energy,stateRelative=state,ledgerRelative=power,minimumLoss=minimum,
        gate=bool(energy<=1e-9 and max(state,power)<=1e-8 and minimum>=-1e-14))

def benchmark(v,j,n,rate,block=64,blocks=200):
    a=fixture(v,j,n,39,rate);fast=VariableBlock(a,np.repeat(np.arange(v),j),160*a.ms)
    F=np.zeros((block,n));S=np.ones((block,v*j))/np.sqrt(v*j);D=np.empty((block,v));log=np.empty((block,5));times=[]
    D[:]=np.linspace(0,1,block)[:,None];fast.process(F,S,D,log)
    W0=a.energy();W=L=absolute=err=peak=0.
    for i in range(blocks):
        D[:]=np.linspace(0,1,block)[:,None] if i%2==0 else np.linspace(1,0,block)[:,None]
        t=time.perf_counter_ns();fast.process(F,S,D,log);times.append((time.perf_counter_ns()-t)/1e3)
        W+=log[:,0].sum();L+=log[:,1:4].sum();absolute+=np.abs(log[:,0]).sum();E=a.energy()
        peak=max(peak,E);err=max(err,abs(W0+W-L-E))
        if not np.isfinite([E,W,L]).all():raise ValueError('nonfinite benchmark')
    budget=1e6*block/rate;energy=err/max(absolute,peak,W0,1e-30)
    return dict(voices=v,partials=j,boardModes=n,sampleRate=rate,blockSize=block,medianUsPerSample=float(np.median(times)/block),p99BudgetFraction=float(np.percentile(times,99)/budget),
        overruns=sum(t>budget for t in times),energyRelative=energy,gate=bool(energy<=1e-9))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[proof(v,j,64,5,r) for v in (32,64) for j in (1,4) for r in (44100,48000,96000)]
    times=[benchmark(v,j,n,r) for v in (32,64) for j in (4,8,16) for n in (128,256) for r in (48000,96000)]
    gate=all(v['gate'] for v in rows+times)
    summary=dict(gate=gate,diagnosticOnly=True,syntheticParameters=True,physicalFitAccepted=False,maximumEnergyError=max(v['energyRelative'] for v in rows+times),
        maximumStateError=max(v['stateRelative'] for v in rows),maximumLedgerError=max(v['ledgerRelative'] for v in rows),benchmarkConfigurations=len(times),
        timeDomainReady=False,polyphonyValidated=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'compiled_variable_damper.json').write_text(json.dumps(dict(summary=summary,cases=rows,benchmark=times),indent=2,allow_nan=False))
    print('G3_COMPILED_DAMPER_GATE '+json.dumps(summary),flush=True)
    for row in times:print('G3_COMPILED_DAMPER_BENCH '+json.dumps(row),flush=True)
    if not gate:raise ValueError('variable compiled diagnostic failed')
if __name__=='__main__':main()
