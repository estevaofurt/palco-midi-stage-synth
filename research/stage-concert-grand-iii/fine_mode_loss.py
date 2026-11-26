"""G3.13p: fine search between the listener-supported extra2 and
the excessive extra6. Preserve one fixed physical law for all wires.
No output EQ or selected final parameters."""
import argparse,json
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
from sustain_brightness import attack_bands,attack_compare,fixed_thresholds,nominal_source
from middle_tail import analyze as middle_analyze
from mode_selective_loss import mode_loss

EXTRA=(0.,2.,3.,4.,5.)
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
    return y,dict(extraModalLossPerS=extra,widthM=width,wireStiffnessLossScale=lossScale,key=key,control=control,spreadCents=spread,structureFactor=factor,hammerSpeedMps=speed,
        keyReleaseS=None if control=='held_no_pedal' else .020,pedal=1. if control=='release_pedal' else 0.,
        finalDamperLevels=target.d.tolist(),injectedJ=bank.injected,startupBalance=init,tailBalance=err,spectrum=analyze(y,RATE,key))

def compare(row,base):
    out=[]
    for c,b,m,mb in zip(row['comparison'],base['comparison'],row['middle'],base['middle']):
        out.append(dict(channel=c['channel'],fundamentalCommonT60S=c['fundamentalCommonT60S'],
            fundamentalPeakRelative=c['fundamentalPeakRelative'],
            mediumEnergyRatioAfter5s=m['middleEnergyAfter5s']/max(mb['middleEnergyAfter5s'],1e-30),
            upperEnergyRatioAfter1s=c['lateUpperEnergyPa2S']/max(b['lateUpperEnergyPa2S'],1e-30),
            mediumWarningWindows=m['middleWarningWindows'],baselineMediumWarningWindows=mb['middleWarningWindows'],
            upperWarningWindows=c['upperDominanceWindowsCommon'],baselineUpperWarningWindows=b['upperDominanceWindowsCommon'],
            fundamentalPreserved=bool(c['fundamentalCommonT60S']>=b['fundamentalCommonT60S']-max(1.,.1*b['fundamentalCommonT60S'])
                and .95<=c['fundamentalPeakRelative']<=1.05)))
    gate=all(v['fundamentalPreserved'] and v['mediumEnergyRatioAfter5s']<=.75 and v['upperEnergyRatioAfter1s']<=.75
        and v['mediumWarningWindows']<=v['baselineMediumWarningWindows'] and v['upperWarningWindows']<=v['baselineUpperWarningWindows'] for v in out)
    return dict(channels=out,attackGate=row['attackComparison']['gate'],candidateGate=bool(gate and row['attackComparison']['gate']))

def incremental(row,reference):
    """Compare directly to extra2, using absolute Pa^2 seconds, not
    normalized playback files. Flag the C3 791 Hz region separately."""
    channels=[]
    for c,b,m,mb in zip(row['comparison'],reference['comparison'],row['middle'],reference['middle']):
        ratio=lambda x,y: float(x/max(y,1e-30))
        channels.append(dict(channel=c['channel'],
            mediumRatioAfter5s=ratio(m['middleEnergyAfter5s'],mb['middleEnergyAfter5s']),
            upperRatioAfter1s=ratio(c['lateUpperEnergyPa2S'],b['lateUpperEnergyPa2S']),
            targetRatiosAfter1s={k:ratio(v,mb['targetEnergyAfter1s'][k]) for k,v in m['targetEnergyAfter1s'].items()},
            fundamentalT60ChangeS=c['fundamentalCommonT60S']-b['fundamentalCommonT60S'],
            fundamentalPeakRatio=ratio(c['fundamentalPeakRelative'],b['fundamentalPeakRelative']),
            mediumWarningChange=m['middleWarningWindows']-mb['middleWarningWindows'],
            upperWarningChange=c['upperDominanceWindowsCommon']-b['upperDominanceWindowsCommon']))
    # Do not trade a worse medium tail for a quieter upper tail. The
    # 1% numerical/physical screening allowance is not audibility.
    passGate=all(v['mediumRatioAfter5s']<=1.01 and v['upperRatioAfter1s']<=.75
        and v['fundamentalT60ChangeS']>=-1. and .98<=v['fundamentalPeakRatio']<=1.02
        and v['mediumWarningChange']<=0 and v['upperWarningChange']<=0 for v in channels)
    return dict(channels=channels,incrementalGate=bool(passGate and row['screening']['candidateGate']))

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
    spread=1. if a.key==60 else 0.
    a.out.mkdir(parents=True,exist_ok=True);renders=[]
    for speed in (.3,3.):
        base=None;reference2=None
        for extra in EXTRA:
            y,row=render_control(z,wires,rows,groups,masses,felts,a.key,'release_pedal',spread,.25,speed,0.,4.,extra)
            row['attackBands']=attack_bands(y)
            if base is None:base=row
            row['middle']=middle_analyze(y,RATE,a.key,None if extra==0. else base['middle'])
            row['comparison']=measures(row,base)
            row['attackComparison']=attack_compare(row['attackBands'],base['attackBands'])
            row['nominalStrongReferenceThresholds']=fixed_thresholds(row['spectrum'],nominal)
            row['screening']=compare(row,base)
            if extra==2.:reference2=row
            if extra>=2.:row['incremental']=incremental(row,reference2)
            renders.append((y,row))
            print('G3_FINE_LOSS_CASE '+json.dumps({k:v for k,v in row.items() if k not in ('spectrum','middle')},allow_nan=False),flush=True)
    gain=common_gain([nominalWav]+[y for y,_ in renders]);listen=a.out/'listen';physical=a.out/'physical'
    listen.mkdir(exist_ok=True);physical.mkdir(exist_ok=True)
    refs=a.out/'references';refs.mkdir(exist_ok=True)
    original=export_wav(refs/f'REFERENCIA_ORIGINAL_k{a.key}_forte_40s.wav',nominalWav,gain)
    for y,row in renders:
        extra=row['extraModalLossPerS'];folder=refs if extra==0. else listen
        label='REFERENCIA_SEM_SELETIVA' if extra==0. else ('BASE_MELHORADA' if extra==2. else 'EXPERIMENTAL')
        name=f'{label}_k{a.key}_{"fraco" if row["hammerSpeedMps"]==.3 else "forte"}_extra{int(extra)}'
        row['files']=dict(auditionFolder=folder.name,audition40=export_wav(folder/(name+'_40s.wav'),y,gain),
            audition5=export_wav(folder/(name+'_5s.wav'),y[:5*RATE],gain),
            pressure=export_wav(physical/(name+'_pressure.wav'),y,gain,True))
    results=[row for _,row in renders]
    candidates=[]
    for x in EXTRA[1:]:
        match=[v for v in results if v['extraModalLossPerS']==x]
        candidates.append(dict(extraPerS=x,passedBothAttacks=all(v['screening']['candidateGate'] for v in match),
            incrementalPassBothAttacks=all(v['incremental']['incrementalGate'] for v in match),
            worstMediumRatioToExtra2=max(c['mediumRatioAfter5s'] for v in match for c in v['incremental']['channels']),
            worstUpperRatioToExtra2=max(c['upperRatioAfter1s'] for v in match for c in v['incremental']['channels']),
            worstAttackChangeDb=max(v['attackComparison']['maximumSignificantBandChangeDb'] for v in match)))
    summary=dict(gate=True,key=a.key,cases=len(results),diagnosticOnly=True,calibratedParameters=False,selectedParameters=None,
        noOutputEQ=True,acousticFeedbackIncluded=False,above500HzDiagnosticOnly=True,commonGain=gain,candidates=candidates,
        maximumBalance=max(max(v['startupBalance'],v['tailBalance']) for v in results),sourceFrozenSha256=sha,
        pressureManifestSha256=ph,referenceManifestSha256=rh,nominalManifestSha256=nh)
    (listen/'fine_mode_loss.json').write_text(json.dumps(dict(summary=summary,original=original,results=results),indent=2,allow_nan=False))
    print('G3_FINE_LOSS_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
