"""G3.13t: regional physical damping compromise, no output processing.
Keep the damper open before impact and use one fixed regional law for
each run. Measure the initial envelope and full 40s fundamental decay."""
import argparse,json
from pathlib import Path
import numpy as np
from wire_physical_midpoint import load
from compiled_wire_midpoint import Compiled
from physical_pedal_repeat import PointSchur,Repeating,damper_ports
from variable_damper import PedalControl
from physical_unison_decay import detune
from causal_pressure_observer import Observer
from felt_law import params
from structural_passive_fit import read_reference
from dry_pressure_render import pressure_source,common_gain
from mode_selective_loss import mode_loss
from attack_flutter import envelope_metrics,episodes,write_checked
from spectral_tail_audit import analyze
from sustain_brightness import attack_bands,attack_compare,fixed_thresholds,nominal_source
from distributed_felt_loss import measures

KEYS=[45,48,60,64]
SECONDS=40.
REGIONS=('plateAndRibs','rim','bridges')
VARIANTS=(('reduced',(.25,.25,.25)),('plate_restored',(1.,.25,.25)),
    ('rim_restored',(.25,1.,.25)),('bridges_restored',(.25,.25,1.)),
    ('balanced',(.5,.5,.5)),('nominal',(1.,1.,1.)))

def regional_matrix(G,factors):
    G=np.asarray(G,float);f=np.asarray(factors,float)
    if G.ndim!=3 or G.shape[0]!=3 or G.shape[1]!=G.shape[2] or f.shape!=(3,) or not np.isfinite(G).all() or not np.isfinite(f).all() or np.any(f<0):raise ValueError('regional inputs')
    for m in G:
        if np.linalg.norm(m-m.T)>1e-9*max(np.linalg.norm(m),1e-30) or np.linalg.eigvalsh((m+m.T)/2).min()<-1e-9*max(np.linalg.norm(m),1e-30):raise ValueError('nonpassive region')
    D=np.einsum('i,ijk->jk',f,G)
    return (D+D.T)/2

def render(z,wires,rows,groups,masses,felts,key,speed,cfg):
    rate=cfg['rate'];n=cfg['partials'];ww,_=detune(wires,rows,cfg['spread'])
    ww=mode_loss(ww,4.,cfg['extra'])
    for j,w in enumerate(ww):w.port=j
    a=Compiled(z['stiffness'],regional_matrix(z['regionalDamping'],cfg['regions']),np.zeros((80,len(ww))),z['wirePorts'],ww,rate,n)
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


def screening(row,base):
    out=[]
    for ch,(c,b) in enumerate(zip(row['comparison'],base['comparison'])):
        cur=row['pressureEnvelope']['fundamental'][ch]['rippleRmsDb']
        ref=base['pressureEnvelope']['fundamental'][ch]['rippleRmsDb']
        ratio=None if cur is None or ref is None or ref<=1e-12 else cur/ref
        out.append(dict(channel=ch+1,rippleDb=cur,rippleRatio=ratio,
            sustainChangeS=c['fundamentalCommonT60S']-b['fundamentalCommonT60S'],
            fundamentalPeakRatio=c['fundamentalPeakRelative'],
            upperEnergyRatio=c['lateUpperEnergyPa2S']/max(b['lateUpperEnergyPa2S'],1e-30),
            rippleGate=bool(ratio is not None and ratio<=.8),
            sustainGate=bool(c['fundamentalCommonT60S']>=b['fundamentalCommonT60S']-max(1.,.1*b['fundamentalCommonT60S']))))
    return dict(channels=out,candidateGate=bool(all(v['rippleGate'] and v['sustainGate'] and v['upperEnergyRatio']<=1.05 for v in out) and row['attackComparison']['gate']))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','pressure','nominal','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--key',type=int,choices=KEYS,required=True);a=p.parse_args()
    archive,wires,sha=load(a.source,a.scale);ref,rh=read_reference(a.reference,sha)
    z,coord,ph=pressure_source(a.pressure,sha,ref,archive,wires)
    nominal,nominalWav,nh=nominal_source(a.nominal,a.key,sha,ph,rh)
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']}
    pars=[params(k,rows[k]['count'],spec,felt) for k in KEYS];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    if np.linalg.norm(regional_matrix(z['regionalDamping'],[1.,1.,1.])-z['damping'])>1e-8*np.linalg.norm(z['damping']):raise ValueError('regional replay')
    a.out.mkdir(parents=True,exist_ok=True);renders=[]
    for speed in (.3,3.):
        base=None
        for name,factors in VARIANTS:
            cfg=dict(rate=48000,partials=32,spread=1. if a.key==60 else 0.,extra=2. if a.key==64 else 4.,preopen=True,regions=list(factors))
            y,row=render(z,wires,rows,groups,masses,felts,a.key,speed,cfg)
            row['variant']=name;row['spectrum']=analyze(y,48000,a.key);row['attackBands']=attack_bands(y)
            if base is None:base=row
            row['comparison']=measures(row,base)
            row['attackComparison']=attack_compare(row['attackBands'],base['attackBands'])
            row['nominalStrongReferenceThresholds']=fixed_thresholds(row['spectrum'],nominal)
            row['screening']=screening(row,base)
            renders.append((y,row))
            print('G3_REGIONAL_ATTACK_CASE '+json.dumps({k:v for k,v in row.items() if k!='spectrum'},allow_nan=False),flush=True)
    gain=common_gain([nominalWav]+[y for y,_ in renders]);results=[]
    for y,row in renders:
        name=f'k{a.key}_{"weak" if row["speed"]==.3 else "strong"}_{row["variant"]}'
        row['wav40']=write_checked(a.out/(name+'_40s.wav'),y,48000,False,gain)
        row['wav5']=write_checked(a.out/(name+'_5s.wav'),y[:240000],48000,False,gain)
        results.append(row)
    candidates=[dict(variant=name,passedBothAttacks=all(v['screening']['candidateGate'] for v in results if v['variant']==name)) for name,_ in VARIANTS[1:]]
    summary=dict(gate=True,key=a.key,cases=len(results),diagnosticOnly=True,selectedParameters=None,
        noOutputEQ=True,acousticFeedbackIncluded=False,above500HzDiagnosticOnly=True,referencePianoCompared=False,
        maximumBalance=max(max(v['attackBalance'],v['tailBalance']) for v in results),commonGain=gain,
        candidates=candidates,sourceFrozenSha256=sha,pressureManifestSha256=ph,referenceManifestSha256=rh,nominalManifestSha256=nh)
    (a.out/'regional_attack.json').write_text(json.dumps(dict(summary=summary,results=results),indent=2,allow_nan=False))
    print('G3_REGIONAL_ATTACK_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
