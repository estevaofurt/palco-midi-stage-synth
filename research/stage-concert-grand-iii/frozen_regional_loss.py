"""G3.14d.20: frozen same-basis acoustic bundle and regional energy replay.
Do not rebuild or combine independent structural coordinates. No tuning."""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from wire_physical_midpoint import load
from acoustic_matrix_archive import read_npz
from fixed_acoustic_projection import TRAIN,CHECK,NOVEL
from physical_acoustic_audition import PartitionedContact
from physical_attack_comparison import checked
from wire_acoustic_port import WireAcoustic
from physical_pedal_repeat import Repeating,damper_ports
from variable_damper import PedalControl
from unison_profiles import KEYS,profiles_for_key,detune_profile
from mode_selective_loss import mode_loss
from felt_law import params
from causal_pressure_observer import Observer,stream_proof
from split_radiation import relative

RATE=48000
FREQ=list(TRAIN)+list(CHECK)+list(NOVEL)
NAMES=('plateAndRibs','rim','bridges','struckWires','otherWires','dampers','acousticWork')

def contract(d,expected):
    if any(d.get(k)!=v for k,v in expected.items()):raise ValueError('bundle contract '+str(expected))

def checked_pressure(root,entry):
    name=entry['file'];path=root/name
    if name!='same_basis_pressure.npz' or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('pressure hash')
    with np.load(path,allow_pickle=False) as z:
        if set(z.files)!={'frequencies','kernel','support','microphones'} or not np.array_equal(z['frequencies'],FREQ):raise ValueError('pressure arrays')
        K=z['kernel'];support=z['support'];mic=z['microphones']
    if K.ndim!=3 or K.shape[0]!=2 or K.shape[2]!=80 or not 1<=K.shape[1]<=48000 or support.shape!=(2,2) or mic.shape!=(2,3):raise ValueError('pressure shape')
    if not all(np.isfinite(x).all() for x in (K,support,mic)) or support.dtype.kind not in 'iu' or np.any(support<0) or np.any(support[:,0]>support[:,1]) or support.max()+1!=K.shape[1]:raise ValueError('pressure support')
    if any(np.count_nonzero(K[i,:lo]) or np.count_nonzero(K[i,hi+1:]) for i,(lo,hi) in enumerate(support)):raise ValueError('noncausal pressure')
    if not stream_proof(K,RATE,support)['gate']:raise ValueError('pressure replay')
    return K

def bundle(root,sha,wires):
    raw=(root/'physical_cq.json').read_bytes();s=json.loads(raw)['summary']
    contract(s,dict(gate=True,screeningGate=True,rate=RATE,rank=64,weightsGenerated=True,sourceFrozenSha256=sha,independentCoordinatesMixed=False))
    fraw=(root/'local_cq_projection.json').read_bytes();f=json.loads(fraw)
    if hashlib.sha256(fraw).hexdigest()!=s['localProjectionFrozenSha256']:raise ValueError('projection hash')
    contract(f,dict(rank=64,method='impedance',sourceFrozenSha256=sha,wireIds=[w.id for w in wires]))
    shapes=dict(projection=(80,64),stiffness=(80,),damping=(80,80),ports=(80,7),wirePorts=(10,80),physicalLift=(1386,80))
    z=read_npz(root,s['archive'],dict(weights=(1024,64,64),**shapes),FREQ)
    g=read_npz(root,f['archive'],dict(**shapes,regionalDamping=(3,80,80),fieldMap=(80,80)),list(TRAIN))
    if any(not np.array_equal(z[k],g[k]) for k in shapes):raise ValueError('same-run matrix mismatch')
    G=g['regionalDamping'];U=z['projection'];W=z['weights']
    if relative(G.sum(axis=0),z['damping'])>1e-10 or min(np.linalg.eigvalsh(x).min()/max(np.linalg.norm(x),1e-30) for x in G)<-1e-10:raise ValueError('regional damping')
    if relative(U.T@U,np.eye(64))>1e-10 or relative(W,W.transpose(0,2,1))>1e-10:raise ValueError('acoustic operators')
    folder=root/'long';doc=json.loads((folder/'physical_long_decay.json').read_text());l=doc['summary']
    contract(l,dict(gate=True,sameBasis=True,cases=2,seconds=40,rate=RATE,sourceFrozenSha256=sha,cqManifestSha256=hashlib.sha256(raw).hexdigest()))
    if l['pressureBandMaximum']>.005 or any(x['firstFiveSecondsReplayRelative']>1e-6 for x in doc['cases']):raise ValueError('long replay gate')
    K=checked_pressure(folder,l['pressureArchive'])
    return z,G,K,doc

def components(a,G,v,u,damper,group):
    rear=a.A@v
    wire=a.d0*rear**2+np.sum(a.ds*u*u+2*a.di*rear[:,None]*u,axis=1)
    return a.h*np.r_[[v@x@v for x in G],wire[group].sum(),wire[~group].sum(),damper]

def replay(z,G,K,wires,rows,speed,wet,seconds=5):
    groups=[w.port for w in wires];g=np.asarray(groups);key=60;j=KEYS.index(key)
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    pars=[params(k,rows[k]['count'],spec,felt) for k in KEYS]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[x][1] for x in groups]
    ww,_=detune_profile(copy.deepcopy(wires),rows,profiles_for_key(key)[0][1]);ww=mode_loss(ww,4.,4.)
    for i,w in enumerate(ww):w.port=i
    U=z['projection'];W=z['weights'] if wet else np.zeros((1,64,64))
    a=WireAcoustic(z['stiffness'],z['damping'],np.zeros((80,len(ww))),z['wirePorts'],ww,RATE,32,U,W)
    B,I=damper_ports(a,rows);target=PartitionedContact(a,B,I)
    bank=Repeating(target,groups,masses,felts);ctrl=PedalControl(len(masses),RATE,transition_ms=5.)
    strength=2./np.bincount(g)[g];ctrl.sustain(1.);ctrl.note(j,True);bank.launch(j,speed)
    F=np.zeros(len(ww));count=1440;total=round(seconds*RATE);acc=np.empty((total,80));loss=np.zeros(6);error=0.;snapshots=[]
    initial=None;air0=None;original=0.
    for t in range(total):
        v=a.v.copy();u=a.u.copy();damperBefore=target.loss
        if t<count:
            if t==960:ctrl.note(j,False)
            bank.damp(strength*ctrl.advance()[g]);bank.step()
            if t==count-1:
                if bank.captures!=1 or np.any(bank.active) or np.any(target.d):raise ValueError('unsettled attack')
                initial=a.energy();air0=target.air
        else:
            _,_,l=target.step(F);original+=l
            vm=(a.v+v)/2;um=(a.u+u)/2
            # damper increment is already in joules; convert to midpoint power
            dl=components(a,G,vm,um,(target.loss-damperBefore)/a.h,g==j)
            if min(dl)<-initial*1e-10:raise ValueError('negative loss')
            loss+=dl
            if (t+1)%RATE==0 or t==total-1:
                air=target.air-air0;E=a.energy()
                error=max(error,abs(loss.sum()-original)/initial,abs(E+loss.sum()+air-initial)/initial)
                if error>1e-8:raise ValueError('regional balance')
                snapshots.append(dict(timeS=(t+1)/RATE,remainingFraction=E/initial,
                    fractions=dict(zip(NAMES,(np.r_[loss,air]/initial).tolist()))))
        acc[t]=(a.v-v)*RATE
    obs=Observer(K,RATE);y=np.concatenate([obs.process(acc[i:i+4096]) for i in range(0,total,4096)])
    return y,dict(speed=speed,wet=wet,initialEnergyJ=initial,maximumPartitionError=error,snapshots=snapshots)

def main():
    p=argparse.ArgumentParser()
    for name in ('scale','source','bundle','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();_,wires,sha=load(a.source,a.scale);z,G,K,doc=bundle(a.bundle,sha,wires)
    rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']};cases=[]
    for row in doc['cases']:
        speed=row['speed'];wet=row['wet'];reference=checked(a.bundle/'long',row['native'],40)[:5*RATE]
        y,report=replay(z,G,K,wires,rows,speed,wet);err=relative(y,reference)
        if err>1e-6:raise ValueError('frozen bundle replay '+str(err))
        report['pressureReplayRelative']=err;cases.append(report)
        print('G3_FROZEN_REGIONAL_CASE '+json.dumps(report,allow_nan=False),flush=True)
    summary=dict(gate=True,diagnosticOnly=True,cases=len(cases),sameBasisBundle=True,rebuiltCoordinates=False,
        sourceFrozenSha256=sha,reference='mechanical energy at 30ms',acousticWorkSigned=True,
        acousticWorkNotIrreversibleLoss=True,selectedParameters=None,physicalFeedbackAccepted=False,audibleSustainMeasured=False,
        maximumPartitionError=max(v['maximumPartitionError'] for v in cases))
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'frozen_regional_loss.json').write_text(json.dumps(dict(summary=summary,cases=cases),indent=2,allow_nan=False))
    print('G3_FROZEN_REGIONAL_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
