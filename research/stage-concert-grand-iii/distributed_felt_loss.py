"""G3.13k: passive physical loss experiments. No output EQ.
Matched baseline, distributed contact and intrinsic stiffness damping.
Assess the raw pressure at identical gain before any parameter selection."""
import argparse,copy,json,hashlib
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
from spectral_tail_audit import analyze,publish_row,KEYS
from distributed_felt import contact,damping_levels,wire_loss

def render_control(z,wires,rows,groups,masses,felts,key,control,spread,factor,speed,width,lossScale):
    ww,_=detune(wires,rows,spread);ww=wire_loss(ww,lossScale)
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
    return y,dict(widthM=width,wireStiffnessLossScale=lossScale,key=key,control=control,spreadCents=spread,structureFactor=factor,hammerSpeedMps=speed,
        keyReleaseS=None if control=='held_no_pedal' else .020,pedal=1. if control=='release_pedal' else 0.,
        finalDamperLevels=target.d.tolist(),injectedJ=bank.injected,startupBalance=init,tailBalance=err,spectrum=analyze(y,RATE,key))

def configurations(group):
    key=int(group.split('-')[0]);control=group.split('-',1)[1]
    if key not in KEYS or control not in ('release_pedal','held_no_pedal','release_no_pedal'):raise ValueError('group')
    spread,factor=(1.,.25) if key==60 and control=='held_no_pedal' else (0.,1.)
    variants=[(0.,1.),(0.,4.),(0.,12.)] if control=='release_pedal' else [(0.,1.),(.005,1.),(.020,1.),(.020,4.)]
    return [(key,control,spread,factor,speed,width,scale) for speed in (.3,3.) for width,scale in variants]

def measures(row,ref):
    out=[]
    for c,b in zip(row['spectrum']['channels'],ref['spectrum']['channels']):
        def last(k):return c[k]['-60']['lastWindowEndS']
        # Compare with matched baseline peak rather than per-file normalization.
        base=b['peakSpectralRmsPa'];baseFund=b['peakFundamentalRmsPa']
        upper=[v['spectralRmsPa']*np.sqrt(v['upperBandFraction']) for v in c['windows']]
        late=[v for v in c['windows'] if v['timeS']>=1 and v['upperBandFraction']>=.7 and v['spectralRmsPa']>=base*1e-4]
        out.append(dict(channel=c['channel'],fundamentalT60OwnS=last('fundamentalThresholds'),
            totalT60OwnS=last('totalThresholds'),fundamentalPeakRelative=c['peakFundamentalRmsPa']/baseFund,
            fundamentalCommonT60S=max((v['timeS']+1 for v in c['windows'] if v['fundamentalRmsPa']>=baseFund*.001),default=0),
            upperDominanceWindowsCommon=len(late),upperLateRmsPa=max(upper[1:],default=0.),
            lateUpperEnergyPa2S=float(np.sum(np.square(upper[1:]))),
            totalLateEnergyPa2S=float(sum(v['spectralRmsPa']**2 for v in c['windows'][1:]))))
    return out

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','reference','pressure','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--group',required=True);a=p.parse_args()
    archive,wires,sha=load(a.source,a.scale);ref,rh=read_reference(a.reference,sha)
    z,coord,ph=pressure_source(a.pressure,sha,ref,archive,wires)
    root=Path(__file__).parent;spec=json.loads((root/'physical_sources.json').read_text());felt=json.loads((root/'felt_hypothesis.json').read_text())
    rows={x['key']:x for x in json.loads(a.scale.read_text())['rows']}
    pars=[params(k,rows[k]['count'],spec,felt) for k in KEYS];groups=[w.port for w in wires]
    masses=[h['massKg'] for h,_ in pars];felts=[pars[g][1] for g in groups]
    a.out.mkdir(parents=True,exist_ok=True);renders=[];baselines={}
    for cfg in configurations(a.group):
        y,row=render_control(z,wires,rows,groups,masses,felts,*cfg)
        speed=cfg[4]
        if cfg[-2:]==(0.,1.):baselines[speed]=row
        row['comparison']=measures(row,baselines[speed]);publish_row(row)
        print('G3_FELT_LOSS_CASE '+json.dumps({k:v for k,v in row.items() if k!='spectrum'},allow_nan=False),flush=True)
        renders.append((y,row))
    gain=common_gain([y for y,_ in renders]);results=[]
    for i,(y,row) in enumerate(renders):
        name=f'{a.group}_{i}_w{row["widthM"]}_loss{row["wireStiffnessLossScale"]}'
        row['wav']=export_wav(a.out/(name+'_40s.wav'),y,gain)
        row['pressure']=export_wav(a.out/(name+'_pressure.wav'),y,gain,True)
        results.append(row)
    summary=dict(gate=True,cases=len(results),group=a.group,diagnosticOnly=True,calibratedParameters=False,selectedParameters=None,
        commonGain=gain,noOutputEQ=True,acousticFeedbackIncluded=False,above500HzDiagnosticOnly=True,
        maximumBalance=max(max(v['startupBalance'],v['tailBalance']) for v in results),
        sourceFrozenSha256=sha,pressureManifestSha256=ph,referenceManifestSha256=rh)
    (a.out/'distributed_felt_loss.json').write_text(json.dumps(dict(summary=summary,results=results),indent=2,allow_nan=False))
    print('G3_FELT_LOSS_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
