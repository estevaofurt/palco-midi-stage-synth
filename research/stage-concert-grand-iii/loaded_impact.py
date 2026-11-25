"""G3.03b: loaded impact and C8 band refinement. No piano bridge or audio."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from moving_termination import basis
from loaded_target import LoadedTarget
from termination_diagnostic import LOAD,simulate,compare as compare_pulse
from modal_target import basis as fixed_basis
from modal_impact import run,compare
from action_launch import launch
from voicing_candidate import candidate
ROOT=Path(__file__).parent
def compare_loaded(a,b):
    q=compare(a,b)
    for k in ('boundaryLossJ','netTargetWorkJ','loadStoredJ','stringStoredJ'):
        q['relative'][k]=float(abs(a[k]-b[k])/max(abs(b[k]),1e-12))
    q['gate']=bool(q['gate'] and max(q['relative'].values())<=.05)
    return q
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--key',type=int,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();scale=json.loads(raw);s=json.loads((ROOT/'physical_sources.json').read_text());f=json.loads((ROOT/'felt_hypothesis.json').read_text());c=json.loads((ROOT/'action_hypothesis.json').read_text())
    assert scale['version']=='G3-scale-hypothesis-02' and scale['summary']['gate'] and a.key in (60,84,108)
    r=scale['rows'][a.key-21];m=LOAD['massKg'];k=LOAD['stiffnessNm'];drag=LOAD['dampingNsm']
    w,P=basis(r,768,96000,m,k);w0,P0=basis(r,512,96000,m,k)
    freq=np.sqrt(w)/(2*np.pi);mask=freq<=72000
    same=len(w)==len(w0)
    ferr=float(np.max(abs(1200*np.log2(np.sqrt(w0/w))))) if same else None
    A=(P0.T/w0)@P0;B=(P.T/w)@P
    static=float(np.linalg.norm(A-B)/max(np.linalg.norm(B),1e-30))
    bgate=same and ferr<=.1 and static<=.01
    assert bgate,'96k basis'
    pulse=None
    if a.key==108:
        wp,Pp=basis(r,768,128000,m,k);fp=np.sqrt(wp)/(2*np.pi)
        pr=[]
        for cut,sr in ((24000,192000),(48000,192000),(48000,384000),(72000,384000),(96000,384000),(128000,384000),(128000,768000)):
            b=fp<=cut;z=simulate(wp[b],Pp[b],sr,drag,0);z['cutHz']=cut;pr.append(z)
        pulse=dict(rows=pr,originalBand=compare_pulse(pr[0],pr[1]),band72to96=compare_pulse(pr[3],pr[4]),band96to128=compare_pulse(pr[4],pr[5]),time=compare_pulse(pr[5],pr[6]))
        print('G3_REAR_PULSE_REFINEMENT '+json.dumps({x:y for x,y in pulse.items() if x!='rows'}),flush=True)
    wf,Pf=fixed_basis(r,768,96000,.005);cases=[]
    priors=[('original',s)]+([('graduated',candidate(a.key,s))] if a.key>72 else [])
    for name,prior in priors:
        for v in (24,76,127):
            q=launch(a.key,v,s,c);speed=q['impactSpeedMps']
            control=run(r,prior,f,wf,Pf,768000,speed)
            def loaded(w,P,sr):
                return run(r,prior,f,w,P,sr,speed,target_factory=lambda w,P,sr:LoadedTarget(w,P,sr,LOAD))
            low=loaded(w,P,384000);high=loaded(w,P,768000);band=loaded(w[mask],P[mask],384000)
            assert control['injectedJ']==low['injectedJ']==high['injectedJ']==band['injectedJ']
            tc=compare_loaded(low,high);bc=compare_loaded(band,low)
            cases.append(dict(prior=name,midi=v,control=control,loadedLow=low,loadedHigh=high,loadedBand72=band,time=tc,band=bc))
            E=high['injectedJ']
            print('G3_LOADED_IMPACT_CASE '+json.dumps(dict(key=a.key,prior=name,midi=v,contactMs=[control['contactDurationMs'],high['contactDurationMs']],
                fixedResidualFraction=control['targetJ']/E,loadedStringFraction=high['stringStoredJ']/E,loadStoredFraction=high['loadStoredJ']/E,
                loadLossFraction=high['boundaryLossJ']/E,netTargetFraction=high['netTargetFractionInput'],time=tc,band=bc)),flush=True)
    pgate=pulse is None or (pulse['band96to128']['gate'] and pulse['time']['gate'])
    summary=dict(key=a.key,impactSimulations=4*len(cases),pulseSimulations=0 if pulse is None else len(pulse['rows']),
        basisGate=bgate,basisFrequencyErrorCents=ferr,basisStaticError=static,timePassed=sum(q['time']['gate'] for q in cases),bandPassed=sum(q['band']['gate'] for q in cases),
        pulseRefinementGate=pgate,maxBalanceJ=max(q[z]['maxBalanceJ'] for q in cases for z in ('control','loadedLow','loadedHigh','loadedBand72')),
        gate=bgate and pgate and all(q['time']['gate'] and q['band']['gate'] for q in cases),selectedPrior=None,terminationReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'loaded_impact.json').write_text(json.dumps(dict(summary=summary,load=LOAD,cases=cases,pulseRefinement=pulse,scaleSha256=hashlib.sha256(raw).hexdigest(),
        scope='independent vertical strings and independent diagnostic loads; no shared bridge, no calibration or audio'),indent=2,allow_nan=False))
    print('G3_LOADED_IMPACT_GATE '+json.dumps(summary),flush=True)
    assert summary['gate'],'loaded impact or pulse refinement convergence'
if __name__=='__main__':main()
