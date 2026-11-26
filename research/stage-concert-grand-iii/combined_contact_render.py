"""G3.13r: compare distributed felt with selective damping under
held and released key conditions. Fixed contact tail only after hammer
and pedal transition; no EQ or calibrated timbre claim."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from wire_physical_midpoint import load
from compiled_wire_midpoint import Compiled
from physical_pedal_repeat import PointSchur,Repeating
from variable_damper import PedalControl
from physical_unison_decay import detune
from causal_pressure_observer import Observer
from felt_law import params
from dry_pressure_render import RATE,PARTIALS,pressure_source,export_wav,common_gain
from structural_passive_fit import read_reference
from spectral_tail_audit import analyze,KEYS
from distributed_felt import contact,damping_levels
from distributed_felt_loss import measures
from mode_selective_loss import mode_loss
from fixed_contact_midpoint import FixedContacts
from sustain_brightness import attack_bands,attack_compare
from middle_tail import analyze as middle_analyze

def render_control(z,wires,rows,groups,masses,felts,key,control,spread,factor,speed,width,lossScale,extra):
    ww,_=detune(wires,rows,spread);ww=mode_loss(ww,lossScale,extra)
    for j,w in enumerate(ww):w.port=j
    a=Compiled(z['stiffness'],z['damping']*factor,np.zeros((80,len(ww))),z['wirePorts'],ww,RATE,PARTIALS)
    B,I,weights=contact(a,rows,width);target=PointSchur(a,B,I)
    bank=Repeating(target,groups,masses,felts);ctrl=PedalControl(len(masses),RATE,transition_ms=5.)
    groups=np.asarray(groups);strength=2./np.bincount(groups)[groups];j=KEYS.index(key)
    if control not in ('release_pedal','held_no_pedal','release_no_pedal'):raise ValueError('control')
    ctrl.sustain(1. if control=='release_pedal' else 0.);ctrl.note(j,True);bank.launch(j,speed)
    count=round(.030*RATE);acc=np.empty((count,80))
    for t in range(count):
        if t==round(.020*RATE) and control!='held_no_pedal':ctrl.note(j,False)
        bank.damp(damping_levels(strength*ctrl.advance()[groups],weights));old=a.v.copy();bank.step();acc[t]=(a.v-old)*RATE
    if bank.captures!=1 or np.any(bank.active):raise ValueError('hammer capture')
    if not np.array_equal(target.d,damping_levels(strength*ctrl.advance()[groups],weights)):raise ValueError('unsettled dampers')
    E0=a.energy();init=abs(bank.storage()+bank.loss+bank.feltloss+bank.captureloss-bank.injected)/bank.injected
    if init>1e-8:raise ValueError('attack energy')
    obs=Observer(z['kernel_48000_3'],RATE);pieces=[obs.process(acc)];loss=err=0.;F0=np.zeros(len(ww))
    # Fixed, settled dampers. Never bypass the damper path if any remain closed.
    fixed=FixedContacts(target)
    for start in range(0,40*RATE,4096):
        n=min(4096,40*RATE-start);acc=np.empty((n,80))
        F=np.zeros((n,len(ww)));O=F.copy();L=np.zeros((n,2))
        fixed.process(F,O,L,acc)
        if np.any(L[:,0]) or L[:,1].min()<-E0*1e-12:raise ValueError('tail work/loss')
        loss+=float(L[:,1].sum())
        err=max(err,abs(a.energy()+loss-E0)/E0);pieces.append(obs.process(acc))
    y=np.concatenate(pieces)
    if not np.isfinite(y).all() or err>1e-8:raise ValueError('tail energy')
    return y,dict(extraModalLossPerS=extra,widthM=width,wireStiffnessLossScale=lossScale,key=key,control=control,spreadCents=spread,structureFactor=factor,hammerSpeedMps=speed,
        keyReleaseS=None if control=='held_no_pedal' else .020,pedal=1. if control=='release_pedal' else 0.,
        finalDamperLevels=target.d.tolist(),injectedJ=bank.injected,startupBalance=init,tailBalance=err,spectrum=analyze(y,RATE,key))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','pressure','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--control',choices=['held_no_pedal','release_no_pedal'],required=True)
    p.add_argument('--speed',type=float,choices=[.3,3.],required=True);a=p.parse_args()
    archive,wires,sha=load(a.source,a.scale);ref,rh=read_reference(a.reference,sha)
    z,coord,ph=pressure_source(a.pressure,sha,ref,archive,wires)
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']}
    pars=[params(k,rows[k]['count'],spec,felt) for k in KEYS];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    a.out.mkdir(parents=True,exist_ok=True);renders=[];base=None
    for width,extra in ((0.,2.),(.020,2.),(.020,4.)):
        y,row=render_control(z,wires,rows,groups,masses,felts,60,a.control,1.,.25,a.speed,width,4.,extra)
        if base is None:base=row
        row['attackBands']=attack_bands(y)
        row['attackComparison']=attack_compare(row['attackBands'],base['attackBands'])
        row['comparison']=measures(row,base)
        row['middle']=middle_analyze(y,RATE,60,None if row is base else base['middle'])
        row['relativeMediumAfter5s']=[v['middleEnergyAfter5s']/max(b['middleEnergyAfter5s'],1e-30) for v,b in zip(row['middle'],base['middle'])]
        # Release metric uses short 50ms windows rather than the coarse
        # one-second spectral diagnostic, retaining the original pressure.
        windows=y[:len(y)//2400*2400].reshape(-1,2400,2)
        rms=np.sqrt(np.mean(windows**2,axis=1))
        refpeak=rms.max(axis=0)
        if np.any(refpeak<=0):raise ValueError('zero signal')
        if row is base:common=refpeak
        row['releaseThresholds']=[{str(db):dict(lastWindowEndS=float((i[-1]+1)*.05) if len(i) else 0.,
            rightCensored=bool(len(i) and i[-1]==len(rms)-1)) for db in (-40,-60,-80)
            for i in [np.flatnonzero(rms[:,ch]>=common[ch]*10**(db/20))]} for ch in range(2)]
        renders.append((y,row))
        print('G3_COMBINED_CONTACT_CASE '+json.dumps({k:v for k,v in row.items() if k not in ('middle','spectrum')},allow_nan=False),flush=True)
    gain=common_gain([y for y,_ in renders]);results=[]
    for y,row in renders:
        label=f'k60_{a.control}_{"weak" if a.speed==.3 else "strong"}_felt{int(row["widthM"]*1000)}mm_extra{int(row["extraModalLossPerS"])}'
        row['wav']=export_wav(a.out/(label+'_40s.wav'),y,gain)
        row['wav5']=export_wav(a.out/(label+'_5s.wav'),y[:5*RATE],gain)
        results.append(row)
    summary=dict(gate=True,cases=len(results),control=a.control,speed=a.speed,compiledFixedContact=True,
        maximumBalance=max(max(v['startupBalance'],v['tailBalance']) for v in results),commonGain=gain,
        diagnosticOnly=True,calibratedParameters=False,noOutputEQ=True,acousticFeedbackIncluded=False,
        above500HzDiagnosticOnly=True,sourceFrozenSha256=sha,referenceManifestSha256=rh,pressureManifestSha256=ph)
    (a.out/'combined_contact.json').write_text(json.dumps(dict(summary=summary,results=results),indent=2,allow_nan=False))
    print('G3_COMBINED_CONTACT_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
