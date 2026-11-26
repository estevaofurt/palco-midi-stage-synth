"""G3.13i: spectral-tail diagnostics across controls, notes and dynamics.
No retuning, no output filtering, no claim of audible sustain.
One-second Hann windows measure absolute RMS and spectral composition."""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from scipy.io.wavfile import read
from dry_pressure_render import RATE,PARTIALS,pressure_source,export_wav,common_gain,CASES
from wire_physical_midpoint import load
from structural_passive_fit import read_reference
from compiled_wire_midpoint import Compiled
from physical_pedal_repeat import PointSchur,Repeating,damper_ports
from variable_damper import PedalControl
from physical_unison_decay import detune
from causal_pressure_observer import Observer
from felt_law import params

KEYS=[45,48,60,64]
def db(r):
    return float(20*np.log10(max(float(r),1e-30)))
def analyze(y,rate,key):
    y=np.asarray(y,float)
    if y.ndim!=2 or y.shape[1]!=2 or len(y)<rate*10 or not np.isfinite(y).all():raise ValueError('pressure signal')
    f0=440*2**((key-69)/12);f=np.fft.rfftfreq(rate,1/rate);w=np.hanning(rate)
    masks=[abs(f-j*f0)<=max(5.,.008*j*f0) for j in range(1,13)]
    narrow=abs(f-1838)<=5.;reports=[]
    for ch in range(2):
        segments=[]
        for t in range(len(y)//rate):
            x=y[t*rate:(t+1)*rate,ch];p=np.abs(np.fft.rfft(w*x))**2
            p[1:-1]*=2.;p/=rate*np.sum(w*w)
            total=float(p.sum());h=[float(p[m].sum()) for m in masks]
            dominant=int(np.argmax(p));peakHz=float(f[dominant])
            line=float(p[abs(f-peakHz)<=5.].sum())
            segments.append(dict(timeS=t,rmsPa=float(np.sqrt(np.mean(x*x))),spectralRmsPa=float(np.sqrt(total)),
                fundamentalRmsPa=float(np.sqrt(h[0])),fundamentalFraction=h[0]/max(total,1e-300),
                harmonicFractions=[v/max(total,1e-300) for v in h],
                harmonicRmsPa=[float(np.sqrt(v)) for v in h],fraction1838=float(p[narrow].sum()/max(total,1e-300)),
                dominantHz=peakHz,dominantLineFraction=line/max(total,1e-300)))
        ref=max(v['spectralRmsPa'] for v in segments);ref0=max(v['fundamentalRmsPa'] for v in segments)
        if min(ref,ref0)<=0:raise ValueError('no fundamental')
        for v in segments:
            v['totalDbOwnPeak']=db(v['spectralRmsPa']/ref)
            v['fundamentalDbOwnPeak']=db(v['fundamentalRmsPa']/ref0)
            v['upperLineDominates']=bool(v['timeS']>=1 and v['dominantHz']>=2*f0 and v['dominantLineFraction']>=.8 and v['totalDbOwnPeak']>=-80)
        flags=[v for v in segments if v['upperLineDominates']]
        def last(field,limit):
            x=[v['timeS']+1 for v in segments if v[field]>=limit]
            return dict(lastWindowEndS=max(x,default=0),rightCensored=bool(x and max(x)==len(segments)))
        reports.append(dict(channel=ch+1,peakSpectralRmsPa=ref,peakFundamentalRmsPa=ref0,
            upperDominanceFirstS=flags[0]['timeS'] if flags else None,
            upperDominantFrequenciesHz=sorted(set(v['dominantHz'] for v in flags)),
            upperDominanceWindows=len(flags),fundamentalThresholds={str(k):last('fundamentalDbOwnPeak',k) for k in (-20,-40,-60,-80)},
            totalThresholds={str(k):last('totalDbOwnPeak',k) for k in (-20,-40,-60,-80)},windows=segments))
    return dict(key=key,nominalFundamentalHz=f0,channels=reports,
        upperDominanceDetected=any(v['upperDominanceWindows'] for v in reports))

def publish_row(row):
    compact=dict(row)
    compact['spectrum']=dict(row['spectrum'],channels=[{**{k:v for k,v in c.items() if k!='windows'},
        'selectedWindows':[{k:v[k] for k in ('timeS','dominantHz','dominantLineFraction','fundamentalFraction','fraction1838','totalDbOwnPeak','fundamentalDbOwnPeak')} for v in c['windows'] if v['timeS'] in (0,3,5,7,10,15,20,30,38)]} for c in row['spectrum']['channels']])
    print('G3_SPECTRAL_TAIL_CASE '+json.dumps(compact,allow_nan=False),flush=True)

def existing(root,out):
    raw=(root/'dry_pressure_render.json').read_bytes();d=json.loads(raw);s=d['summary']
    if any(s.get(k)!=v for k,v in dict(gate=True,cases=4,wavFiles=16,wavRoundTripExact=True,acousticFeedbackIncluded=False).items()):raise ValueError('unapproved render source')
    results=[]
    for row in d['cases']:
        item=row['files']['pressure_pa'];p=root/item['file']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('pressure hash')
        rate,y=read(p)
        if rate!=RATE or y.shape!=(1921440,2) or y.dtype!=np.float32:raise ValueError('pressure format')
        v=dict(key=60,control='release_pedal',spreadCents=row['spreadCents'],structureFactor=row['structureFactor'],
            hammerSpeedMps=row['hammerSpeedMps'],spectrum=analyze(y,rate,60),sourceFile=item['file'])
        results.append(v);publish_row(v)
    report=dict(gate=True,diagnosticOnly=True,cases=len(results),upperDominanceCases=sum(v['spectrum']['upperDominanceDetected'] for v in results),
        sourceManifestSha256=hashlib.sha256(raw).hexdigest(),results=results)
    out.mkdir(parents=True,exist_ok=True);(out/'existing_spectral_tails.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G3_SPECTRAL_TAIL_GATE '+json.dumps({k:v for k,v in report.items() if k!='results'}),flush=True)

def render_control(z,wires,rows,groups,masses,felts,key,control,spread,factor,speed):
    ww,_=detune(wires,rows,spread);ww=copy.deepcopy(ww)
    for j,w in enumerate(ww):w.port=j
    a=Compiled(z['stiffness'],z['damping']*factor,np.zeros((80,len(ww))),z['wirePorts'],ww,RATE,PARTIALS)
    B,I=damper_ports(a,rows);target=PointSchur(a,B,I)
    bank=Repeating(target,groups,masses,felts);ctrl=PedalControl(len(masses),RATE,transition_ms=5.)
    groups=np.asarray(groups);strength=2./np.bincount(groups)[groups];j=KEYS.index(key)
    if control not in ('release_pedal','held_no_pedal','release_no_pedal'):raise ValueError('control')
    ctrl.sustain(1. if control=='release_pedal' else 0.);ctrl.note(j,True);bank.launch(j,speed)
    count=round(.030*RATE);acc=np.empty((count,80))
    for t in range(count):
        if t==round(.020*RATE) and control!='held_no_pedal':ctrl.note(j,False)
        bank.damp(strength*ctrl.advance()[groups]);old=a.v.copy();bank.step();acc[t]=(a.v-old)*RATE
    if bank.captures!=1 or np.any(bank.active):raise ValueError('hammer capture')
    if not np.array_equal(target.d,strength*ctrl.advance()[groups]):raise ValueError('unsettled dampers')
    E0=a.energy();init=abs(bank.storage()+bank.loss+bank.feltloss+bank.captureloss-bank.injected)/bank.injected
    if init>1e-8:raise ValueError('attack energy')
    obs=Observer(z['kernel_48000_3'],RATE);pieces=[obs.process(acc)];loss=err=0.;F0=np.zeros(len(ww))
    # Fixed, settled dampers. Never bypass the damper path if any remain closed.
    for start in range(0,40*RATE,4096):
        n=min(4096,40*RATE-start);acc=np.empty((n,80))
        if np.any(target.d):
            for i in range(n):
                old=a.v.copy();_,work,l=target.step(F0);acc[i]=(a.v-old)*RATE
                if work!=0. or l<-E0*1e-12:raise ValueError('damper tail work/loss')
                loss+=l
        else:
            F=np.zeros((n,len(ww)));O=F.copy();L=np.zeros((n,2))
            a.process(F,O,L,acc)
            if np.any(L[:,0]) or L[:,1].min()<-E0*1e-12:raise ValueError('tail work/loss')
            loss+=float(L[:,1].sum())
        err=max(err,abs(a.energy()+loss-E0)/E0);pieces.append(obs.process(acc))
    y=np.concatenate(pieces)
    if not np.isfinite(y).all() or err>1e-8:raise ValueError('tail energy')
    return y,dict(key=key,control=control,spreadCents=spread,structureFactor=factor,hammerSpeedMps=speed,
        keyReleaseS=None if control=='held_no_pedal' else .020,pedal=1. if control=='release_pedal' else 0.,
        finalDamperLevels=target.d.tolist(),injectedJ=bank.injected,startupBalance=init,tailBalance=err,spectrum=analyze(y,RATE,key))

def new_cases(group):
    if group in ('held_no_pedal','release_no_pedal'):
        return [(60,group,*c) for c in CASES]
    key=int(group)
    if key not in (45,48,64):raise ValueError('group')
    return [(key,'release_pedal',0.,factor,speed) for factor in (1.,.25) for speed in (.3,3.)]

def controls(a):
    archive,wires,sha=load(a.source,a.scale);ref,rh=read_reference(a.reference,sha)
    z,coord,ph=pressure_source(a.pressure,sha,ref,archive,wires)
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']}
    pars=[params(k,rows[k]['count'],spec,felt) for k in KEYS];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    a.out.mkdir(parents=True,exist_ok=True);renders=[]
    for c in new_cases(a.group):
        y,row=render_control(z,wires,rows,groups,masses,felts,*c);publish_row(row);renders.append((y,row))
    gain=common_gain([y for y,_ in renders]);results=[]
    for i,(y,row) in enumerate(renders):
        row['wav']=export_wav(a.out/f'k{row["key"]}_{a.group}_{i}_40s.wav',y,gain)
        results.append(row)
    report=dict(gate=True,diagnosticOnly=True,group=a.group,cases=len(results),upperDominanceCases=sum(v['spectrum']['upperDominanceDetected'] for v in results),
        sourceFrozenSha256=sha,pressureManifestSha256=ph,referenceManifestSha256=rh,commonGainWithinGroup=gain,
        noAcousticFeedback=True,validatedObserverBandHz=[30,500],fullBandDiagnosticOnly=True,results=results)
    (a.out/'spectral_tails.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G3_SPECTRAL_TAIL_GATE '+json.dumps({k:v for k,v in report.items() if k!='results'}),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--existing',type=Path)
    p.add_argument('--group')
    for k in ('scale','source','reference','pressure'):p.add_argument('--'+k,type=Path)
    a=p.parse_args()
    if a.existing:existing(a.existing,a.out)
    else:controls(a)
if __name__=='__main__':main()
