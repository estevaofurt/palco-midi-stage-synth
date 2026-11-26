"""G3.14d.21: frozen CQ harmonic sensitivity around C4.
No coordinate reconstruction, no audio, no parameter selection.
Discrete midpoint mechanics with BDF2 CQ at the acoustic port."""
import argparse,copy,json,hashlib
from pathlib import Path
import numpy as np
from wire_physical_midpoint import load,CoupledWire
from acoustic_matrix_archive import read_npz
from fixed_acoustic_projection import TRAIN,CHECK,NOVEL
from physical_cq_offline import transfer
from unison_profiles import profiles_for_key,detune_profile
from mode_selective_loss import mode_loss
from split_radiation import relative

RATE=48000
FREQ=list(TRAIN)+list(CHECK)+list(NOVEL)
PROFILES={'nominal':(1.,1.,1.),'plate_quarter':(.25,1.,1.),'rim_quarter':(1.,.25,1.),
          'bridge_three_quarters':(1.,1.,.75),'bridge_half':(1.,1.,.5),'bridge_quarter':(1.,1.,.25)}
NAMES=('plateAndRibs','rim','bridges','struckWires','otherWires','air')

def frozen(root,sha,wires):
    raw=(root/'physical_cq.json').read_bytes();s=json.loads(raw)['summary']
    expected=dict(gate=True,screeningGate=True,rate=RATE,rank=64,weightsGenerated=True,sourceFrozenSha256=sha,independentCoordinatesMixed=False)
    if any(s.get(k)!=v for k,v in expected.items()):raise ValueError('CQ provenance')
    fraw=(root/'local_cq_projection.json').read_bytes();f=json.loads(fraw)
    if hashlib.sha256(fraw).hexdigest()!=s['localProjectionFrozenSha256'] or f['sourceFrozenSha256']!=sha or f['wireIds']!=[w.id for w in wires]:raise ValueError('projection provenance')
    shapes=dict(projection=(80,64),stiffness=(80,),damping=(80,80),ports=(80,7),wirePorts=(10,80),physicalLift=(1386,80))
    z=read_npz(root,s['archive'],dict(weights=(1024,64,64),**shapes),FREQ)
    g=read_npz(root,f['archive'],dict(**shapes,regionalDamping=(3,80,80),fieldMap=(80,80)),list(TRAIN))
    if any(not np.array_equal(z[k],g[k]) for k in shapes):raise ValueError('matrix identity')
    G=g['regionalDamping']
    if relative(G.sum(axis=0),z['damping'])>1e-10 or min(np.linalg.eigvalsh(x).min()/max(np.linalg.norm(x),1e-30) for x in G)<-1e-10:raise ValueError('loss partition')
    return z,G,s['localProjectionFrozenSha256']

def solve(a,G,Z,f,force,group):
    # Discrete mechanical frequency uses midpoint bilinear map.
    s=2j*RATE*np.tan(np.pi*f/RATE)
    den=a.ks+s*a.ds+s*s
    c=a.ki+s*a.di+s*s*a.mi
    H=a.Kb+s*(a.Db+Z)+s*s*a.Mb-a.A.T@(np.sum(c*c/den,axis=1)[:,None]*a.A)
    rhs=a.P@force-a.A.T@np.sum(c*(a.F@force)/den,axis=1)
    q=np.linalg.solve(H,rhs);x=(a.F@force-c*(a.A@q)[:,None])/den
    v=s*q;u=s*x;rear=a.A@v
    velocity=a.P.T@v+np.einsum('wip,wi->p',a.F,u)
    wire=a.d0*abs(rear)**2+np.sum(a.ds*abs(u)**2+2*a.di*(rear.conj()[:,None]*u).real,axis=1)
    R=(Z+Z.conj().T)/2
    losses=np.r_[[float(np.vdot(v,g@v).real) for g in G],wire[group].sum(),wire[~group].sum(),float(np.vdot(v,R@v).real)]
    power=float(np.vdot(force,velocity).real)
    if power<=0 or not np.isfinite(losses).all():raise ValueError('nonpositive power')
    error=abs(losses.sum()-power)/power
    if error>1e-8 or losses.min()<-power*1e-8:raise ValueError('harmonic energy partition')
    return dict(frequencyHz=float(f),mobilityMagnitude=float(abs(np.vdot(force,velocity))),
        mobilityReal=power,boardVelocityNorm=float(np.linalg.norm(v)),powerRelativeError=error,
        lossFractions=dict(zip(NAMES,(losses/power).tolist())))

def main():
    p=argparse.ArgumentParser()
    for name in ('scale','source','cq','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();_,wires,sha=load(a.source,a.scale);z,G,ph=frozen(a.cq,sha,wires)
    rows={v['key']:v for v in json.loads(a.scale.read_text())['rows']}
    ww,_=detune_profile(copy.deepcopy(wires),rows,profiles_for_key(60)[0][1]);ww=mode_loss(ww,4.,4.)
    group=np.array([w.port==2 for w in ww]);force=np.array([0.,0.,1.,0.])
    fs=np.linspace(250.,273.,231);U=z['projection'];i,j=np.triu_indices(64)
    packed=transfer(z['weights'][:,i,j],fs,RATE)
    W=np.empty((len(fs),64,64),complex);W[:,i,j]=packed;W[:,j,i]=packed
    full=U@W@U.T;zero=np.zeros((80,80),complex)
    result=[]
    for name,factors in PROFILES.items():
        local=G*np.array(factors)[:,None,None]
        model=CoupledWire(z['stiffness'],local.sum(axis=0),np.zeros((80,4)),z['wirePorts'],ww,RATE,32)
        for wet in (False,True):
            rr=[solve(model,local,Z if wet else zero,f,force,group) for f,Z in zip(fs,full)]
            peak=max(rr,key=lambda v:v['mobilityMagnitude'])
            board=max(rr,key=lambda v:v['boardVelocityNorm'])
            summary=dict(profile=name,factors=list(factors),wet=wet,peakMobility=peak,peakBoardVelocity=board,
                nominalFrequency=rr[int(np.argmin(abs(fs-261.63)))],maximumPowerError=max(v['powerRelativeError'] for v in rr))
            result.append(dict(summary=summary,frequencyRows=rr))
            print('G3_CQ_BRIDGE_SENSITIVITY_CASE '+json.dumps(summary,allow_nan=False),flush=True)
    report=dict(gate=True,diagnosticOnly=True,cases=len(result),frequencies=len(fs),frequencyRangeHz=[250.,273.],
        sourceFrozenSha256=sha,projectionFrozenSha256=ph,independentCoordinatesMixed=False,
        selectedParameters=None,acousticFeedbackAccepted=False,audibleSustainMeasured=False,
        forcedHarmonicNotFreeDecay=True,maximumPowerError=max(v['summary']['maximumPowerError'] for v in result))
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'cq_bridge_sensitivity.json').write_text(json.dumps(dict(summary=report,cases=result),indent=2,allow_nan=False))
    print('G3_CQ_BRIDGE_SENSITIVITY_GATE '+json.dumps(report,allow_nan=False),flush=True)
if __name__=='__main__':main()
