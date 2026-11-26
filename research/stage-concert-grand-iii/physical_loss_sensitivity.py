"""G3.12t: dry loss attribution and one-factor sensitivity.
Frozen attack states; no fitting, no pressure/audibility claims."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky,cho_factor,cho_solve
from physical_long_decay import startup,block_power
from wire_physical_midpoint import load
from duplex_diagnostic import LOSS
from felt_law import params

NAMES=('structure','stringMass','stringBendingTension','damper')

def partition(model):
    a=model.a;n=len(model.M);b=a.n
    S=np.zeros((n,n));S[:b,:b]=a.D
    M=model.M.copy();M[:b,:b]-=np.eye(b)
    K=model.K.copy();K[:b,:b]-=np.diag(a.k)
    Q=model.D-model.baseD
    G=np.stack([S,2*LOSS['mainSigma0PerS']*M,2*LOSS['mainSigma2S']*K,Q])
    G=(G+G.transpose(0,2,1))/2
    err=float(np.linalg.norm(G.sum(axis=0)-model.D)/max(np.linalg.norm(model.D),1e-30))
    mins=[float(np.linalg.eigvalsh(g).min()/max(np.linalg.norm(g),1e-30)) for g in G]
    if err>1e-8 or min(mins)<-1e-8:raise ValueError(f'loss partition {err} {mins}')
    return G,dict(reconstructionRelative=err,minimumEigenvalueRelative=mins)

def prepare(M,K,G,O,h,count):
    n=len(M);D=G.sum(axis=0)
    Lk=cholesky(K,lower=True);Lm=cholesky(M,lower=True)
    H=2*M/h+D+h*K/2;s=1/np.sqrt(np.diag(M));f=cho_factor(H*(s[:,None]*s[None,:]))
    W=s[:,None]*cho_solve(f,s[:,None]*np.c_[-Lk,2*Lm/h])
    T=np.vstack([np.c_[np.eye(n),np.zeros((n,n))]+h*Lk.T@W,
                 np.c_[np.zeros((n,n)),-np.eye(n)]+2*Lm.T@W])
    J=np.stack([h*W.T@g@W for g in G]+[h*np.outer(o@W,o@W) for o in O.T])
    def audit(T,J):
        expected=.5*(np.eye(len(T))-T.T@T);actual=J[:4].sum(axis=0)
        return float(np.linalg.norm(expected-actual)/max(np.linalg.norm(actual),1e-30))
    one=audit(T,J);U,V=block_power(T,J,count);blk=audit(U,V)
    if max(one,blk)>1e-7:raise ValueError(f'partition propagation {one} {blk}')
    return U,V,Lk,Lm,dict(stepIdentity=one,blockIdentity=blk)

def simulate(prepared,q,v,seconds=40.,dt=.05):
    T,G,Lk,Lm,audit=prepared;y=np.r_[Lk.T@q,Lm.T@v]
    initial=.5*float(y@y);E=initial;loss=np.zeros(4);err=rise=0.;rms=[];snapshots=[]
    if initial<=0:raise ValueError('empty initial state')
    for j in range(round(seconds/dt)):
        g=np.einsum('i,kij,j->k',y,G,y);y=T@y;new=.5*float(y@y)
        if not np.isfinite(g).all() or min(g)<-initial*1e-10:raise ValueError('invalid partition accumulator')
        loss+=g[:4];err=max(err,abs(new+loss.sum()-initial)/initial);rise=max(rise,(new-E)/initial);E=new
        rms.append(np.sqrt(np.maximum(g[4:],0)/dt))
        if j+1 in {round(t/dt) for t in (1.,5.,10.,15.,20.,30.,35.,40.)}:
            snapshots.append(dict(timeS=(j+1)*dt,energyFraction=E/initial,lossFractions=dict(zip(NAMES,(loss/initial).tolist()))))
    gate=bool(max(err,rise)<=1e-8 and min(loss)>=-initial*1e-10)
    return dict(gate=gate,initialEnergyJ=initial,finalEnergyFraction=E/initial,
        lossFractions=dict(zip(NAMES,(loss/initial).tolist())),balanceRelative=err,maximumRiseRelative=rise,
        snapshots=snapshots,**audit),np.asarray(rms)

def crossings(rms,reference,dt=.05):
    if reference<=0:raise ValueError('reference')
    db=20*np.log10(np.maximum(rms/reference,1e-30));out={}
    for limit in (-20,-40,-60,-80):
        ids=np.flatnonzero(db>=limit)
        out[str(limit)]=dict(lastWindowEndS=float((ids[-1]+1)*dt) if len(ids) else 0.,
            rightCensored=bool(len(ids) and ids[-1]==len(db)-1))
    return out

def configurations(pedal):
    base=[(1.,1.,1.,1.)]
    if pedal==1.:
        for j in range(3):
            for f in (.25,4.):
                x=[1.]*4;x[j]=f;base.append(tuple(x))
    return base

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','source','pedal','out'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();z,wires,sha=load(a.source,a.scale)
    raw=(a.pedal/'physical_pedal_repeat.json').read_bytes();d=json.loads(raw);s=d['summary']
    if d['sourceFrozenSha256']!=sha or any(s.get(k)!=v for k,v in dict(gate=True,pedalTrendGate=True,wires=10,structureRank=80,acousticLoadIncluded=False).items()):raise ValueError('unapproved pedal source')
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={r['key']:r for r in json.loads(a.scale.read_text())['rows']};keys=[45,48,60,64]
    pars=[params(k,rows[k]['count'],spec,felt) for k in keys];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    k,D,A=(z[x] for x in ('stiffness','damping','wirePorts'));rows['_platePort']=z['ports'][:,6]
    cases=[];rate=48000
    for n in (16,32):
        ref=None
        for pedal in (1.,.5,0.):
            states=[startup(k,D,A,wires,rows,groups,masses,felts,rate,n,pedal,speed) for speed in (.3,3.)]
            model,q,v,O,_=states[0];G,audit=partition(model)
            for factors in configurations(pedal):
                prepared=prepare(model.M,model.K,G*np.asarray(factors)[:,None,None],O,1/rate,2400)
                # Compare dynamics from identical attack states within each pedal/rank.
                pending=[]
                for speed,(m,q,v,o,init) in zip((.3,3.),states):
                    if not np.array_equal(m.D,model.D) or not np.array_equal(o,O):raise ValueError('inconsistent attack model')
                    result,rms=simulate(prepared,q,v)
                    pending.append((speed,result,rms,init))
                if ref is None:
                    ref=pending[1][2].max(axis=0)
                    if min(ref)<=0:raise ValueError('reference peak')
                for speed,result,rms,init in pending:
                    row=dict(rate=rate,partials=n,pedal=pedal,hammerSpeedMps=speed,factors=dict(zip(NAMES,factors)),
                        partition=audit,**result,referencePeakRmsMps=ref.tolist(),
                        commonReferenceThresholds={name:crossings(rms[:,i],ref[i]) for i,name in enumerate(('wire','plate'))},
                        ownPeakThresholds={name:crossings(rms[:,i],rms[:,i].max()) for i,name in enumerate(('wire','plate'))})
                    cases.append(row)
                    print('G3_LOSS_SENSITIVITY_CASE '+json.dumps({k:v for k,v in row.items() if k!='snapshots'},allow_nan=False),flush=True)
    summary=dict(gate=all(v['gate'] for v in cases),cases=len(cases),diagnosticOnly=True,physicalHypothesis=True,
        frozenAttackStates=True,calibratedParameters=False,selectedParameters=None,acousticLoadIncluded=False,audibleSustainMeasured=False,
        maximumBalanceError=max(v['balanceRelative'] for v in cases),maximumPartitionError=max(v['partition']['reconstructionRelative'] for v in cases),
        maximumBlockIdentity=max(v['blockIdentity'] for v in cases),timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'physical_loss_sensitivity.json').write_text(json.dumps(dict(summary=summary,cases=cases,sourceFrozenSha256=sha,
        pedalManifestSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_LOSS_SENSITIVITY_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('loss sensitivity proof failed')
if __name__=='__main__':main()
