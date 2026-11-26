"""G3.13s: isolate attack flutter with controlled physical variants.
Diagnostic envelopes only; audition WAVs are unfiltered physical pressure."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.io.wavfile import write,read
from scipy.signal import butter,sosfiltfilt,hilbert,resample_poly,savgol_filter
from wire_physical_midpoint import load
from compiled_wire_midpoint import Compiled
from physical_pedal_repeat import PointSchur,Repeating,damper_ports
from variable_damper import PedalControl
from physical_unison_decay import detune
from causal_pressure_observer import Observer
from felt_law import params
from structural_passive_fit import read_reference
from dry_pressure_render import pressure_source,common_gain,pcm
from mode_selective_loss import mode_loss
from split_radiation import relative

KEYS=[45,48,60,64]
SECONDS=2.
def variants(key):
    spread=1. if key==60 else 0.
    extra=2. if key==64 else 4.
    base=dict(rate=48000,partials=32,spread=spread,structure=.25,extra=extra,preopen=False)
    changes=[('baseline',{}),('pedal_preopened',dict(preopen=True)),
        ('rate96k',dict(rate=96000)),('partials64',dict(partials=64)),
        ('partials128',dict(partials=128)),('nominal_structure',dict(structure=1.)),
        ('no_selective_loss',dict(extra=0.))]
    if key==60:changes.append(('exact_unison',dict(spread=0.)))
    return [(name,dict(base,**change)) for name,change in changes]

def episodes(force,rate):
    f=np.asarray(force,float)
    result=[]
    for j in range(f.shape[1]):
        x=f[:,j];peak=float(x.max());active=x>max(1e-12,peak*1e-6)
        start=np.flatnonzero(active & ~np.r_[False,active[:-1]])
        end=np.flatnonzero(active & ~np.r_[active[1:],False])+1
        result.append(dict(wire=j,peakN=peak,impulseNs=float(x.sum()/rate),
            contacts=[dict(startMs=float(a*1000/rate),endMs=float(b*1000/rate)) for a,b in zip(start,end)]))
    return result

def envelope_metrics(signal,rate,key):
    """Measure local envelope deviations after removing slow trend.
    Analysis only. Restrict to 40–500ms to avoid onset and edge artifacts.
    Broad bands can include legitimate harmonic interference."""
    signal=np.asarray(signal,float)
    if signal.ndim==1:signal=signal[:,None]
    if len(signal)<rate or not np.isfinite(signal).all():raise ValueError('signal')
    f0=440*2**((key-69)/12)
    bands=[('fundamental',max(30.,.72*f0),1.28*f0),('low',30.,500.),('middle',500.,1500.),('high',1500.,8000.)]
    result={}
    for name,lo,hi in bands:
        x=sosfiltfilt(butter(3,[lo,hi],btype='bandpass',fs=rate,output='sos'),signal,axis=0)
        e=abs(hilbert(x,axis=0))
        # Average over 5ms to suppress carrier-scale ripple.
        hop=round(.005*rate);e=e[:len(e)//hop*hop].reshape(-1,hop,e.shape[1]).mean(axis=1)
        start=8;end=100;v=e[start:end];peak=e.max(axis=0)
        db=20*np.log10(np.maximum(e,np.maximum(peak*1e-5,1e-30))/np.maximum(peak,1e-30))
        trend=savgol_filter(db,21,2,axis=0)
        residual=(db-trend)[start:end]
        valid=v>=peak[None,:]*.01
        channels=[]
        for j in range(e.shape[1]):
            a=residual[valid[:,j],j]
            channels.append(dict(validWindows=len(a),peakEnvelope=float(peak[j]),
                rippleRmsDb=float(np.sqrt(np.mean(a*a))) if len(a) else None,
                rippleP90MinusP10Db=float(np.percentile(a,90)-np.percentile(a,10)) if len(a) else None,
                envelopeDbAtMs=[float(db[k,j]) for k in (8,12,20,40,60,99)]))
        result[name]=channels
    return result

def render(z,wires,rows,groups,masses,felts,key,speed,cfg):
    rate=cfg['rate'];n=cfg['partials'];ww,_=detune(wires,rows,cfg['spread'])
    ww=mode_loss(ww,4.,cfg['extra'])
    for j,w in enumerate(ww):w.port=j
    a=Compiled(z['stiffness'],z['damping']*cfg['structure'],np.zeros((80,len(ww))),z['wirePorts'],ww,rate,n)
    B,I=damper_ports(a,rows);target=PointSchur(a,B,I)
    bank=Repeating(target,groups,masses,felts);ctrl=PedalControl(len(masses),rate,transition_ms=5.)
    g=np.asarray(groups);strength=2./np.bincount(g)[g];j=KEYS.index(key)
    ctrl.sustain(1.)
    if cfg['preopen']:
        for _ in range(round(.005*rate)+2):ctrl.advance()
        if np.any(ctrl.level):raise ValueError('preopen')
    ctrl.note(j,True);bank.launch(j,speed)
    count=round(.030*rate);acc=np.empty((count,80));force=np.empty((count,len(ww)))
    wire=np.empty_like(force);damper=np.empty_like(force)
    for t in range(count):
        if t==round(.020*rate):ctrl.note(j,False)
        bank.damp(strength*ctrl.advance()[g]);old=a.v.copy()
        force[t]=bank.step()[0];acc[t]=(a.v-old)*rate
        wire[t]=target.velocity();damper[t]=target.d
    if bank.captures!=1 or np.any(bank.active) or np.any(target.d):raise ValueError('unsettled attack')
    E0=a.energy();balance=abs(bank.storage()+bank.loss+bank.feltloss+bank.captureloss-bank.injected)/bank.injected
    if balance>1e-8:raise ValueError('attack balance')
    obs=Observer(z[f'kernel_{rate}_3'],rate);pieces=[obs.process(acc)]
    obs_wire=[wire];loss=err=0.
    for start in range(count,round(SECONDS*rate),4096):
        size=min(4096,round(SECONDS*rate)-start);acc=np.empty((size,80));F=np.zeros((size,len(ww)));O=F.copy();L=np.zeros((size,2))
        a.process(F,O,L,acc);pieces.append(obs.process(acc));obs_wire.append(O)
        loss+=float(L[:,1].sum());err=max(err,abs(a.energy()+loss-E0)/E0)
    if err>1e-8:raise ValueError('tail balance')
    y=np.concatenate(pieces);vel=np.concatenate(obs_wire);ids=np.flatnonzero(g==j)
    row=dict(key=key,speed=speed,config=cfg,attackBalance=balance,tailBalance=err,
        damperInitial=damper[0].tolist(),damperLossJ=target.loss,hammerContacts=episodes(force,rate),
        pressureEnvelope=envelope_metrics(y,rate,key),wireVelocityEnvelope=envelope_metrics(vel[:,ids].mean(axis=1),rate,key))
    # Store native pressure, resample only for comparable audition at 48k.
    return y,row

def write_checked(path,y,rate,physical,gain):
    payload=y.astype(np.float32) if physical else pcm(y,gain)
    write(path,rate,payload);r,v=read(path)
    if r!=rate or v.dtype!=payload.dtype or not np.array_equal(v,payload) or not np.isfinite(v).all():raise ValueError('WAV replay')
    return dict(file=path.name,rate=rate,samples=len(v),sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','pressure','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--key',type=int,choices=KEYS,required=True);a=p.parse_args()
    archive,wires,sha=load(a.source,a.scale);ref,rh=read_reference(a.reference,sha)
    z,coord,ph=pressure_source(a.pressure,sha,ref,archive,wires)
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']}
    pars=[params(k,rows[k]['count'],spec,felt) for k in KEYS];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    a.out.mkdir(parents=True,exist_ok=True);renders=[]
    for speed in (.3,3.):
        baseline=None
        for name,cfg in variants(a.key):
            y,row=render(z,wires,rows,groups,masses,felts,a.key,speed,cfg)
            audio=resample_poly(y,1,2,axis=0) if cfg['rate']==96000 else y
            if baseline is None:baseline=audio
            row['variant']=name;row['pressureDifferenceToBaseline']={str(ms):relative(audio[:ms*48],baseline[:ms*48]) for ms in (30,100,500,1000)}
            renders.append((y,audio,row))
            print('G3_ATTACK_FLUTTER_CASE '+json.dumps(row,allow_nan=False),flush=True)
    gain=common_gain([audio for _,audio,_ in renders])
    for y,audio,row in renders:
        stem=f'k{a.key}_{"weak" if row["speed"]==.3 else "strong"}_{row["variant"]}'
        row['native']=write_checked(a.out/(stem+'_pressure.wav'),y,row['config']['rate'],True,gain)
        row['listen']=write_checked(a.out/(stem+'_listen.wav'),audio,48000,False,gain)
    results=[v for _,_,v in renders]
    summary=dict(gate=True,cases=len(results),key=a.key,diagnosticOnly=True,selectedParameters=None,
        noOutputEQ=True,acousticFeedbackIncluded=False,above500HzDiagnosticOnly=True,referencePianoCompared=False,
        maximumBalance=max(max(v['attackBalance'],v['tailBalance']) for v in results),commonGain=gain,
        sourceFrozenSha256=sha,pressureManifestSha256=ph,referenceManifestSha256=rh)
    (a.out/'attack_flutter.json').write_text(json.dumps(dict(summary=summary,results=results),indent=2,allow_nan=False))
    print('G3_ATTACK_FLUTTER_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
