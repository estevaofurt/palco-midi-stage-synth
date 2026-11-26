"""G3.12s: long dry mechanical decay, exact powers of the fixed midpoint.
Quadratic accumulators for physical loss and port velocity RMS; no sound calibration."""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky,cho_factor,cho_solve
from wire_physical_midpoint import CoupledWire,load
from physical_pedal_repeat import PointSchur,PointDense,Repeating,damper_ports
from felt_law import params
from variable_damper import PedalControl
from split_radiation import relative

def compose(T,G,U,H):
    # First T then U. Every accumulator is a quadratic form in the initial state.
    return U@T,G+np.stack([T.T@g@T for g in H])

def block_power(T,G,n):
    if type(n)!=int or n<1:raise ValueError('block length')
    A=np.eye(len(T));B=np.zeros_like(G);U=T.copy();H=G.copy()
    while n:
        if n&1:A,B=compose(A,B,U,H)
        n//=2
        if n:U,H=compose(U,H,U,H)
    return A,(B+B.transpose(0,2,1))/2

def propagator(M,K,D,Q,O,h,steps):
    # Energy coordinates: y=[L_K.T q,L_M.T v], E=||y||²/2.
    Lk=cholesky(K,lower=True);Lm=cholesky(M,lower=True)
    n=len(M);H=2*M/h+D+h*K/2
    s=1/np.sqrt(np.diag(M));fac=cho_factor(H*(s[:,None]*s[None,:]))
    W=s[:,None]*cho_solve(fac,s[:,None]*np.c_[-Lk,2*Lm/h])
    T=np.vstack([np.c_[np.eye(n),np.zeros((n,n))]+h*Lk.T@W,
                 np.c_[np.zeros((n,n)),-np.eye(n)]+2*Lm.T@W])
    G=[h*(W.T@D@W),h*(W.T@Q@W)]
    for o in O.T:
        y=o@W;G.append(h*np.outer(y,y))
    G=np.stack(G)
    step=float(np.linalg.norm(.5*(np.eye(2*n)-T.T@T)-G[0],ord='fro')/max(np.linalg.norm(G[0]),1e-30))
    A,B=block_power(T,G,steps)
    block=float(np.linalg.norm(.5*(np.eye(2*n)-A.T@A)-B[0],ord='fro')/max(np.linalg.norm(B[0]),1e-30))
    if max(step,block)>1e-7:raise ValueError(f'propagator energy identity {step} {block}')
    return A,B,Lk,Lm,dict(stepEnergyIdentity=step,blockEnergyIdentity=block)

def thresholds(values,dt):
    values=np.asarray(values);peak=float(values.max())
    if peak<=0:raise ValueError('zero observation')
    db=20*np.log10(np.maximum(values/peak,1e-30))
    out={}
    for limit in (-20,-40,-60):
        hits=np.flatnonzero(db>=limit)
        out[str(limit)]=dict(lastWindowEndS=float((hits[-1]+1)*dt) if len(hits) else 0.,
            rightCensored=bool(len(hits) and hits[-1]==len(db)-1))
    return db,out

def startup(k,D,A,wires,rows,groups,masses,felts,rate,n,pedal,speed):
    ww=copy.deepcopy(wires)
    for j,w in enumerate(ww):w.port=j
    a=CoupledWire(k,D,np.zeros((len(k),len(ww))),A,ww,rate,n)
    B,I=damper_ports(a,rows);target=PointSchur(a,B,I)
    bank=Repeating(target,groups,masses,felts)
    ctrl=PedalControl(len(masses),rate,transition_ms=5.)
    groups=np.asarray(groups);strength=2./np.bincount(groups)[groups]
    ctrl.sustain(pedal);ctrl.note(2,True);bank.launch(2,speed)
    for t in range(round(.030*rate)):
        if t==round(.020*rate):ctrl.note(2,False)
        bank.damp(strength*ctrl.advance()[groups]);bank.step()
    if bank.captures!=1 or np.any(bank.active):raise ValueError('hammer not captured')
    balance=abs(bank.storage()+bank.loss+bank.feltloss+bank.captureloss-bank.injected)/bank.injected
    if balance>1e-8:raise ValueError('startup energy')
    dense=PointDense(a,B,I);dense.set_levels(strength*ctrl.advance()[groups])
    if not np.array_equal(dense.d,target.d):raise ValueError('damper levels not settled')
    q,v=target.state();plate=np.r_[rows['_platePort'],np.zeros(a.nw*n)]
    # Mean velocity of C4 wires at hammer position and plate port velocity.
    ids=np.flatnonzero(groups==2)
    O=np.column_stack([dense.P[:,ids].mean(axis=1),plate])
    return dense,q,v,O,dict(injectedJ=bank.injected,mechanicalEnergyJ=target.energy(),
        startupBalance=balance,startupDamperLossJ=target.loss,initialFeltEnergyJ=bank.storage()-target.energy())

def decay(model,q,v,O,rate,seconds=40.,dt=.05,prepared=None):
    count=round(dt*rate);duration=round(seconds/dt)
    if prepared is None:prepared=propagator(model.M,model.K,model.D,model.D-model.baseD,O,1/rate,count)
    T,G,Lk,Lm,audit=prepared
    y=np.r_[Lk.T@q,Lm.T@v];E0=.5*float(y@y);E=E0
    total=damper=error=0.;rise=0.;rms=[];energy=[]
    for j in range(duration):
        g=np.einsum('i,kij,j->k',y,G,y);next_y=T@y;En=.5*float(next_y@next_y)
        if not np.isfinite(g).all() or min(g)<-1e-10*E0:raise ValueError('invalid loss accumulator')
        total+=g[0];damper+=g[1];error=max(error,abs(En+total-E0)/E0);rise=max(rise,(En-E)/E0)
        rms.append(np.sqrt(np.maximum(g[2:],0)/dt));energy.append(En/E0)
        y=next_y;E=En
    rms=np.asarray(rms);trace=[];metrics={}
    for i,name in enumerate(('c4HammerPointVelocity','platePortVelocity')):
        db,limits=thresholds(rms[:,i],dt);metrics[name]=dict(peakRmsMps=float(rms[:,i].max()),thresholds=limits)
        trace.append(db.tolist())
    result=dict(gate=bool(max(error,rise)<=1e-8 and damper>=-1e-12 and damper<=total+1e-10*E0),
        initialEnergyJ=E0,finalEnergyJ=E,totalMechanicalLossJ=float(total),damperLossJ=float(damper),
        energyBalanceRelative=error,maximumEnergyIncreaseRelative=rise,**audit,metrics=metrics,
        energyFraction=energy,velocityDb=trace,windowSeconds=dt,tailSeconds=seconds)
    return result

def main():
    p=argparse.ArgumentParser()
    for name in ('scale','source','pedal','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();z,wires,sha=load(a.source,a.scale)
    raw=(a.pedal/'physical_pedal_repeat.json').read_bytes();d=json.loads(raw);s=d['summary']
    if d['sourceFrozenSha256']!=sha or any(s.get(k)!=v for k,v in dict(gate=True,pedalTrendGate=True,wires=10,structureRank=80,acousticLoadIncluded=False).items()):raise ValueError('unapproved pedal source')
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={r['key']:r for r in json.loads(a.scale.read_text())['rows']};keys=[45,48,60,64]
    pars=[params(k,rows[k]['count'],spec,felt) for k in keys];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    k,D,A=(z[x] for x in ('stiffness','damping','wirePorts'));rows['_platePort']=z['ports'][:,6]
    cases=[]
    for rate in (48000,96000):
        for n in (16,32):
            for pedal in (0.,.5,1.):
                prepared=None
                for speed in (.3,1.,3.):
                    model,q,v,O,init=startup(k,D,A,wires,rows,groups,masses,felts,rate,n,pedal,speed)
                    if prepared is None:prepared=propagator(model.M,model.K,model.D,model.D-model.baseD,O,1/rate,round(.05*rate))
                    row=dict(rate=rate,partials=n,pedal=pedal,hammerSpeedMps=speed,**init,**decay(model,q,v,O,rate,prepared=prepared))
                    cases.append(row)
                    print('G3_LONG_DECAY_CASE '+json.dumps({k:v for k,v in row.items() if k not in ('energyFraction','velocityDb')},allow_nan=False),flush=True)
    summary=dict(gate=all(v['gate'] for v in cases),diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,
        acousticLoadIncluded=False,audibleSustainMeasured=False,structureRank=80,wires=10,key=60,cases=len(cases),tailSeconds=40.,
        maximumEnergyError=max(v['energyBalanceRelative'] for v in cases),maximumStepEnergyIdentity=max(v['stepEnergyIdentity'] for v in cases),
        maximumBlockEnergyIdentity=max(v['blockEnergyIdentity'] for v in cases),timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'physical_long_decay.json').write_text(json.dumps(dict(summary=summary,cases=cases,sourceFrozenSha256=sha,
        pedalManifestSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_LONG_DECAY_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('long mechanical decay failed')
if __name__=='__main__':main()
