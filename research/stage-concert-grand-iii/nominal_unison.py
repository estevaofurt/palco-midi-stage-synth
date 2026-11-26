"""G3.13u: preserve the listener-approved nominal attack; tune unisons
with fixed tension profiles across the four coupled groups. No EQ."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.io.wavfile import read
from wire_physical_midpoint import load
from compiled_wire_midpoint import Compiled
from physical_pedal_repeat import PointSchur,Repeating,damper_ports
from variable_damper import PedalControl
from causal_pressure_observer import Observer
from felt_law import params
from structural_passive_fit import read_reference
from dry_pressure_render import pressure_source,common_gain
from mode_selective_loss import mode_loss
from attack_flutter import envelope_metrics,episodes,write_checked
from spectral_tail_audit import analyze
from sustain_brightness import attack_bands,attack_compare,fixed_thresholds,nominal_source
from distributed_felt_loss import measures
from middle_tail import analyze as middle_analyze
from split_radiation import relative
from unison_profiles import KEYS,PROFILES,detune_profile

SECONDS=40.
def render(z,wires,rows,groups,masses,felts,key,speed,cfg):
    rate=cfg['rate'];n=cfg['partials'];ww=wires
    ww=mode_loss(ww,4.,cfg['extra'])
    for j,w in enumerate(ww):w.port=j
    a=Compiled(z['stiffness'],z['damping'],np.zeros((80,len(ww))),z['wirePorts'],ww,rate,n)
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
        a.process(F,O,L,acc);pieces.append(obs.process(acc));obs_wire.append(O) if start<2*rate else None
        loss+=float(L[:,1].sum());err=max(err,abs(a.energy()+loss-E0)/E0)
    if err>1e-8:raise ValueError('tail balance')
    y=np.concatenate(pieces);vel=np.concatenate(obs_wire);ids=np.flatnonzero(g==j)
    row=dict(key=key,speed=speed,config=cfg,attackBalance=balance,tailBalance=err,
        damperInitial=damper[0].tolist(),damperLossJ=target.loss,hammerContacts=episodes(force,rate),
        pressureEnvelope=envelope_metrics(y[:2*rate],rate,key),wireVelocityEnvelope=envelope_metrics(vel[:2*rate,ids].mean(axis=1),rate,key))
    # Store native pressure, resample only for comparable audition at 48k.
    return y,row


def approved_source(root,key,sha,ph,rh,speed):
    raw=(root/'attack_flutter.json').read_bytes();d=json.loads(raw);s=d['summary']
    expected=dict(gate=True,key=key,sourceFrozenSha256=sha,pressureManifestSha256=ph,referenceManifestSha256=rh,noOutputEQ=True,acousticFeedbackIncluded=False)
    if any(s.get(k)!=v for k,v in expected.items()):raise ValueError('approved source')
    row=next(v for v in d['results'] if v['variant']=='nominal_structure' and v['speed']==speed)
    item=row['native'];path=root/item['file']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('approved hash')
    rate,y=read(path)
    if rate!=48000 or y.dtype!=np.float32 or y.shape!=(96000,2):raise ValueError('approved pressure format')
    return y,hashlib.sha256(raw).hexdigest()

def screen(row,base):
    channels=[]
    for j,(c,b,m,mb) in enumerate(zip(row['comparison'],base['comparison'],row['middle'],base['middle'])):
        x=row['pressureEnvelope']['fundamental'][j]['rippleRmsDb'];r=base['pressureEnvelope']['fundamental'][j]['rippleRmsDb']
        change=c['fundamentalCommonT60S']-b['fundamentalCommonT60S']
        medium=m['middleEnergyAfter5s']/max(mb['middleEnergyAfter5s'],1e-30)
        upper=c['lateUpperEnergyPa2S']/max(b['lateUpperEnergyPa2S'],1e-30)
        channels.append(dict(channel=j+1,rippleDb=x,approvedRippleDb=r,sustainChangeS=change,mediumRatio=medium,upperRatio=upper,
            attackGate=bool(x is not None and r is not None and x<=max(1.10*r,r+.15)),
            tailGate=bool(medium<=1.05 and upper<=1.05 and c['upperDominanceWindowsCommon']<=b['upperDominanceWindowsCommon'] and m['middleWarningWindows']<=mb['middleWarningWindows'])))
    preserve=all(v['sustainChangeS']>=-1. for v in channels)
    attack=all(v['attackGate'] for v in channels) and row['attackComparison']['gate']
    tail=all(v['tailGate'] for v in channels)
    return dict(channels=channels,attackPreserved=bool(attack),tailPreserved=bool(tail),
        sustainPreserved=bool(preserve),longerBothChannels=all(v['sustainChangeS']>=2. for v in channels),
        candidateGate=bool(attack and tail and preserve))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','pressure','nominal','approved','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--key',type=int,choices=KEYS,required=True);a=p.parse_args()
    archive,wires,sha=load(a.source,a.scale);ref,rh=read_reference(a.reference,sha)
    z,coord,ph=pressure_source(a.pressure,sha,ref,archive,wires)
    nominal,nominalWav,nh=nominal_source(a.nominal,a.key,sha,ph,rh)
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']}
    pars=[params(k,rows[k]['count'],spec,felt) for k in KEYS];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    profiles=[(name,profile,*detune_profile(wires,rows,profile)) for name,profile in PROFILES]
    a.out.mkdir(parents=True,exist_ok=True);renders=[];replays=[]
    for speed in (.3,3.):
        approved,ah=approved_source(a.approved,a.key,sha,ph,rh,speed);base=None
        for name,profile,ww,records in profiles:
            cfg=dict(rate=48000,partials=32,spread=profile[2],extra=2. if a.key==64 else 4.,preopen=False,regions=[1.,1.,1.],unisonProfile=list(profile))
            y,row=render(z,ww,rows,groups,masses,felts,a.key,speed,cfg)
            row['variant']=name;row['tuning']=records
            if base is None:
                base=row;err=relative(y[:96000],approved.astype(float))
                if err>1e-6:raise ValueError('approved attack replay '+str(err))
                replays.append(dict(speed=speed,relative=err,manifestSha256=ah))
            row['spectrum']=analyze(y,48000,a.key);row['attackBands']=attack_bands(y)
            row['middle']=middle_analyze(y,48000,a.key,None if row is base else base['middle'])
            row['comparison']=measures(row,base);row['attackComparison']=attack_compare(row['attackBands'],base['attackBands'])
            row['nominalStrongReferenceThresholds']=fixed_thresholds(row['spectrum'],nominal)
            row['screening']=screen(row,base);renders.append((y,row))
            print('G3_NOMINAL_UNISON_CASE '+json.dumps({k:v for k,v in row.items() if k not in ('spectrum','middle')},allow_nan=False),flush=True)
    gain=common_gain([y for y,_ in renders]);results=[]
    for y,row in renders:
        label=f'k{a.key}_{"weak" if row["speed"]==.3 else "strong"}_{row["variant"]}'
        row['wav40']=write_checked(a.out/(label+'_40s.wav'),y,48000,False,gain)
        row['wav5']=write_checked(a.out/(label+'_5s.wav'),y[:240000],48000,False,gain)
        results.append(row)
    candidates=[]
    for name,profile in PROFILES[1:]:
        cases=[v for v in results if v['variant']==name]
        candidates.append(dict(profile=name,passedBothAttacks=all(v['screening']['candidateGate'] for v in cases),
            longerBothAttacks=all(v['screening']['longerBothChannels'] for v in cases)))
    summary=dict(gate=True,key=a.key,cases=len(results),diagnosticOnly=True,selectedParameters=None,
        approvedAttackReplays=replays,nominalStructure=True,noOutputEQ=True,acousticFeedbackIncluded=False,above500HzDiagnosticOnly=True,
        maximumBalance=max(max(v['attackBalance'],v['tailBalance']) for v in results),commonGain=gain,
        candidates=candidates,sourceFrozenSha256=sha,pressureManifestSha256=ph,referenceManifestSha256=rh,nominalManifestSha256=nh)
    (a.out/'nominal_unison.json').write_text(json.dumps(dict(summary=summary,results=results),indent=2,allow_nan=False))
    print('G3_NOMINAL_UNISON_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
