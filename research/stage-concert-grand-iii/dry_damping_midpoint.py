"""G3.11x: dry modal midpoint with full non-diagonal damping.
Passive block approximation screened against same-rank full damping.
Not an accepted physical model, no acoustic load or strings."""
import argparse,json,time,hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from numba import njit
from acoustic_matrix_archive import read_npz
from dry_structural_modal import mobility
from split_radiation import relative

def block_damping(D,b):
    n=len(D)
    if type(b)!=int or b<1:raise ValueError('invalid block')
    X=np.zeros_like(D)
    for i in range(0,n,b):X[i:i+b,i:i+b]=D[i:i+b,i:i+b]
    return X

@njit(cache=True)
def kernel(F,P,k,D,L,h,b,q,v,mid,rhs,obs,ledger):
    n=len(q)
    for t in range(len(F)):
        for i in range(n):
            r=2*v[i]/h-k[i]*q[i]
            for j in range(P.shape[1]):r+=P[i,j]*F[t,j]
            rhs[i]=r
        for start in range(0,n,b):
            end=min(n,start+b)
            for i in range(start,end):
                x=rhs[i]
                for j in range(start,i):x-=L[i,j]*mid[j]
                mid[i]=x/L[i,i]
            for i in range(end-1,start-1,-1):
                x=mid[i]
                for j in range(i+1,end):x-=L[j,i]*mid[j]
                mid[i]=x/L[i,i]
        work=0.;loss=0.
        for j in range(P.shape[1]):
            x=0.
            for i in range(n):x+=P[i,j]*mid[i]
            obs[t,j]=x;work+=x*F[t,j]
        for start in range(0,n,b):
            end=min(n,start+b)
            for i in range(start,end):
                x=0.
                for j in range(start,end):x+=D[i,j]*mid[j]
                loss+=mid[i]*x
        for i in range(n):q[i]+=h*mid[i];v[i]=2*mid[i]-v[i]
        ledger[t,0]=h*work;ledger[t,1]=h*loss

class DryBlock:
    def __init__(self,k,D,P,rate,b):
        k,D,P=[np.array(x,dtype=float,order='C',copy=True) for x in (k,D,P)]
        n=len(k)
        if k.shape!=(n,) or D.shape!=(n,n) or P.ndim!=2 or P.shape[0]!=n or not n or any(not np.isfinite(x).all() for x in (k,D,P)) or np.any(k<=0) or not np.isfinite(rate) or rate<=0:raise ValueError('invalid dry model')
        if relative(D,D.T)>1e-12 or np.linalg.eigvalsh(D).min()<-1e-10*max(np.linalg.norm(D),1e-30):raise ValueError('nonpassive damping')
        self.k=k;self.D=block_damping((D+D.T)/2,b);self.P=P;self.h=1/rate;self.b=min(n,b)
        self.L=np.ascontiguousarray(np.linalg.cholesky(np.diag(2/self.h+self.h*k/2)+self.D))
        self.q=np.zeros(n);self.v=np.zeros(n);self.mid=np.zeros(n);self.rhs=np.zeros(n)
    def energy(self):return .5*float(self.v@self.v+np.sum(self.k*self.q**2))
    def process(self,F,obs,ledger):
        if F.ndim!=2 or F.shape[1]!=self.P.shape[1] or obs.shape!=F.shape or ledger.shape!=(len(F),2):raise ValueError('invalid block shape')
        if any(x.dtype!=np.float64 or not x.flags.c_contiguous for x in (F,obs,ledger)) or not np.isfinite(F).all() or not obs.flags.writeable or not ledger.flags.writeable:raise ValueError('invalid block buffers')
        if any(np.shares_memory(x,y) for x,y in ((F,obs),(F,ledger),(obs,ledger))) or any(np.shares_memory(x,y) for x in (F,obs,ledger) for y in (self.q,self.v,self.mid,self.rhs)):raise ValueError('aliased block')
        kernel(F,self.P,self.k,self.D,self.L,self.h,self.b,self.q,self.v,self.mid,self.rhs,obs,ledger)

def proof(k,D,P,rate,b,seconds=.05):
    a=DryBlock(k,D,P,rate,b);h=a.h;n=len(k)
    fac=cho_factor(np.diag(2/h+h*k/2)+a.D);q=np.zeros(n);v=np.zeros(n)
    t=(np.arange(round(rate*seconds))+.5)/rate
    F=np.ascontiguousarray(np.where(t<.015,np.sin(2*np.pi*130*t)*np.sin(np.pi*t/.015)**2,0.)[:,None]*np.cos(np.arange(P.shape[1])))
    W=loss=absolute=peak=err=0.;minimum=0.;state=0.;ledger_error=0.;obs_error=0.
    for i in range(0,len(F),64):
        f=F[i:i+64];o=np.empty_like(f);l=np.empty((len(f),2));a.process(f,o,l)
        ro=[];rl=[]
        for x in f:
            mid=cho_solve(fac,2*v/h-k*q+P@x)
            out=P.T@mid;ro.append(out);rl.append([h*(out@x),h*(mid@a.D@mid)])
            q+=h*mid;v=2*mid-v
        obs_error=max(obs_error,relative(o,np.asarray(ro)));ledger_error=max(ledger_error,relative(l,np.asarray(rl)))
        state=max(state,relative(a.q,q),relative(a.v,v))
        W+=l[:,0].sum();loss+=l[:,1].sum();absolute+=np.abs(l[:,0]).sum();E=a.energy()
        peak=max(peak,E);err=max(err,abs(W-loss-E));minimum=min(minimum,float(l[:,1].min()))
    energy=err/max(absolute,peak,1e-30)
    return dict(modes=n,block=b,sampleRate=rate,energyRelative=energy,stateRelative=state,ledgerRelative=ledger_error,
        observerRelative=obs_error,minimumLoss=minimum,gate=bool(np.isfinite([energy,state,ledger_error,obs_error]).all() and energy<=1e-9 and max(state,ledger_error,obs_error)<=1e-8 and minimum>=-1e-14))

def screen(k,D,P,freq,valid):
    train=mobility(k,D,P,freq);validation=mobility(k,D,P,valid);rows=[]
    for b in (1,4,8,16,32,64,128,len(k)):
        if b>len(k) or any(v['block']==b for v in rows):continue
        d=block_damping(D,b)
        Y=mobility(k,d,P,freq)
        maximum=max(relative(x,y) for x,y in zip(Y,train))
        rows.append(dict(block=b,trainingMaximum=maximum,minimumEigenvalue=float(np.linalg.eigvalsh(d).min())))
    selected=min((r for r in rows if r['trainingMaximum']<=.05 and r['minimumEigenvalue']>=0),key=lambda r:r['block'])
    b=selected['block'];d=block_damping(D,b)
    v=mobility(k,d,P,valid);error=max(relative(x,y) for x,y in zip(v,validation))
    return dict(modes=len(k),selectedBlock=b,trainingMaximum=selected['trainingMaximum'],validationMaximum=error,
        sameRankOnly=True,selectionUsedValidation=False,approximationGate=bool(error<=.05),candidates=rows)

def timing(k,D,P,rate,b,blocks=200):
    a=DryBlock(k,D,P,rate,b);F=np.zeros((64,P.shape[1]));F[:,0]=1.
    O=np.empty_like(F);L=np.empty((64,2));a.process(F,O,L);times=[]
    E0=a.energy();W=loss=absolute=err=peak=0.
    for _ in range(blocks):
        t=time.perf_counter_ns();a.process(F,O,L);times.append((time.perf_counter_ns()-t)/1e3)
        W+=L[:,0].sum();loss+=L[:,1].sum();absolute+=np.abs(L[:,0]).sum();E=a.energy()
        peak=max(peak,E);err=max(err,abs(E0+W-loss-E))
    budget=64e6/rate;energy=err/max(E0,absolute,peak,1e-30)
    return dict(modes=len(k),block=b,sampleRate=rate,medianUsPerSample=float(np.median(times)/64),p99BudgetFraction=float(np.percentile(times,99)/budget),
        overruns=sum(x>budget for x in times),energyRelative=energy,gate=bool(np.isfinite(energy) and energy<=1e-9))

def require_grid(freq):
    freq=np.asarray(freq)
    if freq.shape!=(32,) or not np.isfinite(freq).all() or not np.allclose(freq,np.geomspace(30,500,32),rtol=1e-14,atol=0):raise ValueError('invalid source frequency grid')

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=(a.source/'dry_structural_modal.json').read_bytes();d=json.loads(raw);s=d['summary'];freq=np.asarray(d['frequencyHz'])
    expected=dict(gate=True,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,eigenGate=True,knotAlignedQuadrature=True,
        fullDampingPreserved=True,maximumModes=256,acousticFitAccepted=False,timeDomainReady=False,radiationReady=False)
    for k,v in expected.items():
        if s.get(k)!=v:raise ValueError('invalid source field '+k)
    require_grid(freq)
    data=read_npz(a.source,d['archive'],dict(modalHz=(256,),stiffness=(256,),damping=(256,256),ports=(256,4),fourFieldMap=(4,256),dryReference=(32,4,4)),freq)
    valid=np.sqrt(freq[:-1]*freq[1:]);rows=[];proofs=[];bench=[]
    for n in (64,128,256):
        k=data['stiffness'][:n];D=data['damping'][:n,:n];P=data['ports'][:n]
        row=screen(k,D,P,freq,valid);rows.append(row)
        for b in sorted(set([n,row['selectedBlock']])):
            for rate in (48000,96000):
                proofs.append(proof(k,D,P,rate,b));bench.append(timing(k,D,P,rate,b))
    gate=all(x['gate'] for x in proofs+bench)
    summary=dict(gate=gate,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,fullDampingSupported=True,
        maximumEnergyError=max(v['energyRelative'] for v in proofs+bench),maximumStateError=max(v['stateRelative'] for v in proofs),
        maximumLedgerError=max(v['ledgerRelative'] for v in proofs),sameRankApproximationOnly=True,
        acousticFitAccepted=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'dry_damping_midpoint.json').write_text(json.dumps(dict(summary=summary,sourceManifestSha256=hashlib.sha256(raw).hexdigest(),
        trainingHz=freq.tolist(),validationHz=valid.tolist(),screen=rows,proof=proofs,benchmark=bench),indent=2,allow_nan=False))
    print('G3_DRY_DAMPING_GATE '+json.dumps(summary),flush=True)
    for row in rows:print('G3_DRY_DAMPING_SCREEN '+json.dumps(row),flush=True)
    for row in bench:print('G3_DRY_DAMPING_BENCH '+json.dumps(row),flush=True)
    if not gate:raise ValueError('dry midpoint diagnostic failed')
if __name__=='__main__':main()
