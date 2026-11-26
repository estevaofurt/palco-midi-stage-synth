"""G3.13e: experimental dry physical C4 -> retarded pressure WAV.
No feedback, no cabinet, no fitted envelope or calibrated audibility.
Common gain for all audition files; preserve raw pressure separately."""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from scipy.io.wavfile import write
from scipy.signal import butter,sosfilt
from wire_physical_midpoint import load
from compiled_wire_midpoint import Compiled
from physical_pedal_repeat import PointSchur,Repeating,damper_ports
from variable_damper import PedalControl
from physical_unison_decay import detune
from physical_loss_sensitivity import crossings
from felt_law import params
from causal_pressure_observer import Observer,TRAIN,HIGH
from structural_passive_fit import read_reference
from new_baffle_grid import coordinate_audit
from acoustic_matrix_archive import read_npz
from split_radiation import relative

RATE=48000
PARTIALS=32
CASES=[(0.,1.,.3),(0.,1.,3.),(1.,.25,.3),(1.,.25,3.)]

def pressure_source(root,sha,reference):
    raw=(root/'causal_pressure_observer.json').read_bytes();d=json.loads(raw);s=d['summary']
    expected=dict(gate=True,structureRank=80,cases=4,causalDelayObserver=True,sameCoordinateSurface=True,
        acousticFeedbackIncluded=False,validatedBandHz=[30,500],calibratedParameters=False)
    if d['sourceFrozenSha256']!=sha or any(s.get(k)!=v for k,v in expected.items()):raise ValueError('pressure source')
    shapes=dict(stiffness=(80,),damping=(80,80),ports=(80,7),wirePorts=(10,80),
        physicalLift=(1386,80),regionalDamping=(3,80,80),microphoneXYZ=(2,3),pressureReference=(len(TRAIN+HIGH),2,80))
    for row in d['cases']:shapes[f"kernel_{row['rate']}_{row['degree']}"]=(2,row['taps'],80)
    z=read_npz(root,d['archive'],shapes,TRAIN+HIGH)
    audit=coordinate_audit(z,reference)
    return z,audit,hashlib.sha256(raw).hexdigest()

def render(z,wires,rows,groups,masses,felts,spread,factor,speed,seconds=40.):
    ww,_=detune(wires,rows,spread);ww=copy.deepcopy(ww)
    for j,w in enumerate(ww):w.port=j
    rate=RATE;n=PARTIALS
    a=Compiled(z['stiffness'],z['damping']*factor,np.zeros((80,len(ww))),z['wirePorts'],ww,rate,n)
    B,I=damper_ports(a,rows);target=PointSchur(a,B,I)
    bank=Repeating(target,groups,masses,felts);ctrl=PedalControl(len(masses),rate,transition_ms=5.)
    groups=np.asarray(groups);strength=2./np.bincount(groups)[groups]
    ctrl.sustain(1.);ctrl.note(2,True);bank.launch(2,speed)
    count=round(.030*rate);acc=np.empty((count,80))
    for t in range(count):
        if t==round(.020*rate):ctrl.note(2,False)
        bank.damp(strength*ctrl.advance()[groups]);old=a.v.copy();bank.step()
        acc[t]=(a.v-old)*rate
    if bank.captures!=1 or np.any(bank.active) or np.any(target.d):raise ValueError('unsettled startup')
    E0=a.energy();init=abs(bank.storage()+bank.loss+bank.feltloss+bank.captureloss-bank.injected)/bank.injected
    if init>1e-8:raise ValueError('attack energy')
    observer=Observer(z['kernel_48000_3'],rate)
    pieces=[observer.process(acc)];tail=round(seconds*rate);loss=error=0.
    for start in range(0,tail,4096):
        m=min(4096,tail-start);F=np.zeros((m,len(ww)));O=F.copy();L=np.zeros((m,2));acc=np.zeros((m,80))
        a.process(F,O,L,acc)
        if np.any(L[:,0]) or L[:,1].min()<-E0*1e-12:raise ValueError('tail work/loss')
        loss+=float(L[:,1].sum());error=max(error,abs(a.energy()+loss-E0)/E0)
        pieces.append(observer.process(acc))
    y=np.concatenate(pieces)
    if not np.isfinite(y).all() or np.max(abs(y))<=0 or error>1e-8:raise ValueError('render energy/signal')
    rms=np.sqrt(np.mean(y[count:].reshape(-1,2400,2)**2,axis=1))
    # Separate causal lowpass for in-band diagnostic, no normalization of individual notes.
    filtered=sosfilt(butter(4,500,fs=rate,output='sos'),y,axis=0)
    band=np.sqrt(np.mean(filtered[count:].reshape(-1,2400,2)**2,axis=1))
    return y,filtered,rms,band,dict(spreadCents=spread,structureFactor=factor,hammerSpeedMps=speed,
        injectedJ=bank.injected,mechanicalEnergyJ=E0,startupBalance=init,tailBalance=error,peakPressurePa=np.max(abs(y),axis=0).tolist(),
        fullPedal=True,startupSamples=count,samples=len(y),tailSeconds=seconds)

def common_gain(ys):
    peak=max(float(np.max(abs(y))) for y in ys)
    if peak<=0 or not np.isfinite(peak):raise ValueError('peak')
    return .8/peak

def pcm(y,gain):
    x=y*gain
    if not np.isfinite(x).all() or np.max(abs(x))>1.:raise ValueError('clipping')
    return np.rint(x*32767).astype(np.int16)

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','pressure','joint','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();_,wires,sha=load(a.source,a.scale);ref,rh=read_reference(a.reference,sha)
    z,coord,ph=pressure_source(a.pressure,sha,ref)
    raw=(a.joint/'physical_joint_decay.json').read_bytes();d=json.loads(raw)
    if d['sourceFrozenSha256']!=sha or any(d['summary'].get(k)!=v for k,v in dict(gate=True,cases=42,fullAttackRecomputed=True,acousticLoadIncluded=False).items()):
        raise ValueError('joint source')
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']};keys=[45,48,60,64]
    pars=[params(k,rows[k]['count'],spec,felt) for k in keys];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    a.out.mkdir(parents=True,exist_ok=True);renders=[]
    for spread,factor,speed in CASES:
        y,b,rms,band,row=render(z,wires,rows,groups,masses,felts,spread,factor,speed)
        prior=next(x for x in d['cases'] if x['rate']==RATE and x['spreadCents']==spread and x['structureFactor']==factor and x['hammerSpeedMps']==speed)
        e=abs(row['mechanicalEnergyJ']/prior['mechanicalEnergyJ']-1.)
        if e>1e-7:raise ValueError('attack replay')
        row['attackReplayRelative']=e;renders.append((y,b,rms,band,row))
        print('G3_DRY_PRESSURE_RENDER_CASE '+json.dumps(row,allow_nan=False),flush=True)
    gain=common_gain([v for y,b,*_ in renders for v in (y,b)])
    ref=renders[1][2].max(axis=0);bref=renders[1][3].max(axis=0);cases=[]
    for y,b,rms,band,row in renders:
        name=('nominal' if row['spreadCents']==0. else 'unison1_damping25')+('_weak' if row['hammerSpeedMps']==.3 else '_strong')
        files={}
        for suffix,signal,raw in [('pressure_pa',y,True),('audition_40s',y,False),('audition_5s',y[:5*RATE],False),('lowpass500_5s',b[:5*RATE],False)]:
            path=a.out/(name+'_'+suffix+'.wav')
            write(path,RATE,signal.astype(np.float32) if raw else pcm(signal,gain))
            files[suffix]=dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        row.update(files=files,commonPressureThresholds=[crossings(rms[:,i],ref[i]) for i in range(2)],
            commonLowpassThresholds=[crossings(band[:,i],bref[i]) for i in range(2)])
        cases.append(row)
        print('G3_DRY_PRESSURE_RENDER_RESULT '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=True,cases=len(cases),diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,
        sampleRate=RATE,partials=PARTIALS,structureRank=80,wires=10,key=60,commonAuditionGain=gain,
        noEnvelope=True,acousticFeedbackIncluded=False,oneSidedIdealBaffle=True,validatedObserverBandHz=[30,500],
        fullBandDiagnosticOnly=True,lowpass500IsNotBrickwall=True,audibleSustainMeasured=False,
        maximumEnergyError=max(max(v['startupBalance'],v['tailBalance']) for v in cases),
        maximumAttackReplay=max(v['attackReplayRelative'] for v in cases),timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'dry_pressure_render.json').write_text(json.dumps(dict(summary=summary,cases=cases,coordinateReplay=coord,
        sourceFrozenSha256=sha,referenceManifestSha256=rh,pressureManifestSha256=ph,jointManifestSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_DRY_PRESSURE_RENDER_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
