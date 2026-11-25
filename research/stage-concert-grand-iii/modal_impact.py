"""G3.02d: independent fixed-end string modes driven by a moving felt hammer.
No bridge, damping of strings, unison detuning, action or radiated audio.
"""
import argparse,json,math,hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from modal_target import basis,Target
from flexible_hammer import Hammer
from felt_law import params,energy,relax,frozen_force
ROOT=Path(__file__).parent
def run(r,s,c,w2,P,sr,speed,stagger=False,trace=False,shaft=None,target_factory=None):
    hm,f=params(r['key'],r['count'],s,c);m=hm['massKg'];N=r['count'];h=1/sr
    if target_factory is not None and trace:raise ValueError('lossless force-spectrum identity is not valid with loaded targets')
    targets=[(Target(w2,P,sr) if target_factory is None else target_factory(w2,P,sr)) for _ in range(N)]
    gaps=np.arange(N)*30e-6 if stagger else np.zeros(N)
    z=np.zeros(N);hammer=Hammer(m,sr,speed,shaft);E0=hammer.energy();gh=hammer.H
    loss=impulse=peak=maxbal=maxinc=maxrelax=maxport=maxforce=targetWork=0.;prev=E0
    forceHistory=[];ncontact=0;started=False;separated=False;maxCompression=0.;perImpulse=np.zeros(N)
    # Distinct contacts share the hammer displacement, not the state of felt or target.
    for i in range(round(.04*sr)):
        d0=hammer.position()-np.array([t.position() for t in targets])-gaps
        for j in range(N):
            z[j],l,e=relax(float(d0[j]),float(z[j]),h/2,f);loss+=l;maxrelax=max(maxrelax,abs(e))
        xf=hammer.free();free=xf-np.array([t.free() for t in targets])-gaps
        def per(total):
            result=[]
            for j,t in enumerate(targets):
                D=float(free[j]-gh*total);a=float(d0[j]);b=float(z[j])
                hi=frozen_force(a,D,b,f)
                if hi<=0:result.append(0.);continue
                fun=lambda F:F-frozen_force(a,D-t.H*F,b,f)
                result.append(brentq(fun,0.,hi,xtol=1e-12) if fun(hi)>0 else hi)
            return np.array(result)
        hi=float(sum(per(0.)))
        if hi>0:
            fun=lambda total:total-float(sum(per(total)))
            total=brentq(fun,0.,hi,xtol=1e-12) if fun(hi)>0 else hi
            F=per(total)
        else:F=np.zeros(N)
        if trace:forceHistory.append(F.copy())
        total=float(sum(F));e=hammer.energy();work=hammer.step(-total);maxport=max(maxport,abs(hammer.energy()-e-work))
        for t,Fj in zip(targets,F):
            e=t.energy();oldLoss=getattr(t,'loss',0.);work=t.step(float(Fj));targetWork+=work
            maxport=max(maxport,abs(t.energy()-e-work+getattr(t,'loss',0.)-oldLoss))
        d1=hammer.position()-np.array([t.position() for t in targets])-gaps
        for j in range(N):
            maxforce=max(maxforce,abs(F[j]-frozen_force(float(d0[j]),float(d1[j]),float(z[j]),f)))
            z[j],l,e=relax(float(d1[j]),float(z[j]),h/2,f);loss+=l;maxrelax=max(maxrelax,abs(e))
        assert np.all(F>=0) and np.all(z>=0)
        Eh=hammer.energy();Ef=sum(energy(float(d),float(q),f) for d,q in zip(d1,z));Es=sum(t.energy() for t in targets)
        boundaryLoss=sum(getattr(t,'loss',0.) for t in targets)
        E=Eh+Ef+Es;maxbal=max(maxbal,abs(E+loss+boundaryLoss-E0));maxinc=max(maxinc,E-prev);prev=E
        perImpulse+=h*F;impulse+=h*total;peak=max(peak,total);maxCompression=max(maxCompression,float(max(d1)))
        if total>0:ncontact+=1;started=True
        # Same first-separation criterion as the prior fixture, not a catcher model.
        if started and max(d1)<=0 and hammer.v<0 and hammer.velocity()<0 and all(hammer.velocity()-float(t.P@t.v)<=0 for t in targets):
            separated=True;break
    assert started and separated,(r['key'],sr,speed,hammer.velocity(),float(max(d1)))
    ie=abs(m*(speed-hammer.v)-impulse)
    assert maxbal<=max(1e-10,E0*1e-7) and maxinc<=1e-11 and maxrelax<=1e-11 and maxport<=1e-11 and maxforce<=1e-7*max(1.,peak)
    assert ie<=1e-10 and abs(float(sum(perImpulse))-impulse)<=1e-10 and loss>=0
    if not stagger:assert max(perImpulse)-min(perImpulse)<=1e-10
    modal=sum(.5*(t.v*t.v+w2*t.q*t.q) for t in targets)
    assert abs(float(sum(modal))-Es)<=1e-10
    assert abs(targetWork-Es-boundaryLoss)<=max(1e-10,E0*1e-7)
    audit=dict(boundaryLossJ=boundaryLoss,netTargetWorkJ=targetWork,netTargetFractionInput=targetWork/E0)
    if target_factory is not None:
        loadStored=sum(t.load_energy() for t in targets)
        assert 0<=loadStored<=Es+1e-12
        audit.update(loadStoredJ=loadStored,stringStoredJ=max(0.,Es-loadStored),modalEnergyScope='coupled string and diagnostic load')
    if trace:
        # Integral of piecewise constant contact force at each modal frequency.
        freq=np.sqrt(w2)/(2*np.pi);time=(np.arange(len(forceHistory))+.5)*h
        coeff=(np.exp(-2j*np.pi*freq[:,None]*time[None,:])@np.asarray(forceHistory))*h*np.sinc(freq*h)[:,None]
        predicted=.5*P*P*np.sum(abs(coeff)**2,axis=1)
        err=float(np.max(abs(predicted-modal)));assert err<=max(1e-12,E0*1e-9)
        audit=dict(forceSpectrumEnergyJ=predicted.tolist(),forceSpectrumResidualJ=err,
            forceFundamentalOverDC=(np.abs(coeff[0])/np.maximum(perImpulse,1e-30)).tolist(),
            contactPeriods=ncontact*h*r['nominalHz'])
    return dict(**audit,key=r['key'],sampleRateHz=sr,speedMps=speed,stagger=stagger,modesPerString=len(P),contactDurationMs=1000*ncontact/sr,
        injectedJ=E0,hammerReboundJ=Eh,targetJ=Es,storedFeltJ=Ef,lossJ=loss,maxBalanceJ=maxbal,maxIncreaseJ=maxinc,
        maxRelaxResidualJ=maxrelax,maxPortResidualJ=maxport,maxForceResidualN=maxforce,impulseErrorNs=ie,
        peakForceN=peak,impulseNs=impulse,maxCompressionM=maxCompression,reboundMps=-hammer.velocity(),centerOfMassReboundMps=-hammer.v,shaftEnergyJ=hammer.flex_energy(),shaft=shaft,perImpulseNs=perImpulse.tolist(),
        modalFrequenciesHz=(np.sqrt(w2)/(2*np.pi)).tolist(),modalEnergyJ=modal.tolist(),fundamentalFractionInput=float(modal[0]/E0),
        totalTransferFractionInput=Es/E0)
def compare(a,b):
    keys=('peakForceN','impulseNs','reboundMps','lossJ','maxCompressionM','targetJ')
    diffs={k:abs(a[k]-b[k])/max(abs(b[k]),1e-12) for k in keys}
    duration=abs(a['contactDurationMs']-b['contactDurationMs'])
    return dict(relative=diffs,durationDeltaMs=duration,gate=max(diffs.values())<=.05 and duration<=.1)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--key',type=int,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();scale=json.loads(raw);s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'felt_hypothesis.json').read_text())
    assert scale['version']=='G3-scale-hypothesis-02' and scale['summary']['gate'] and a.key in (21,30,49,60,72,84,108)
    r=scale['rows'][a.key-21];width=.005
    # Refine basis separately from cutoff; high modes beyond 24 kHz are not evaluated.
    # For low strings, a conservative large Ritz basis avoids truncating below cutoff.
    basisN=512;w2,P=basis(r,basisN,24000,width);wr,Pr=basis(r,768,24000,width)
    same=len(w2)==len(wr)
    freqError=float(np.max(abs(1200*np.log2(np.sqrt(w2/wr))))) if same else None
    # Compare contact receptance via spectral weights, insensitive to eigenvector sign.
    portError=float(np.linalg.norm(P*P-Pr*Pr)/max(np.linalg.norm(Pr*Pr),1e-30)) if same else None
    bgate=same and freqError<=.1 and portError<=.01
    print('G3_MODAL_BASIS '+json.dumps(dict(key=a.key,modes=len(wr),frequencyErrorCents=freqError,portWeightRelative=portError,gate=bgate)),flush=True)
    assert bgate,'basis convergence'
    cases=[]
    for speed,stagger in [(v,False) for v in c['impactSpeedsMps']]+([(1.,True)] if r['count']>1 else []):
        runs=[]
        for cut,sr in ((12000,192000),(18000,192000),(24000,96000),(24000,192000)):
            keep=np.sqrt(wr)/(2*np.pi)<=cut
            result=run(r,s,c,wr[keep],Pr[keep],sr,speed,stagger)
            result['cutHz']=cut;runs.append(result)
        tc=compare(runs[2],runs[3]);bc=compare(runs[1],runs[3]);low=compare(runs[0],runs[1])
        cases.append(dict(runs=runs,time=tc,band18to24=bc,band12to18=low))
        print('G3_MODAL_IMPACT_CASE '+json.dumps(dict(key=a.key,speed=speed,stagger=stagger,time=tc,band18to24=bc,band12to18=low,
            transfers=[x['totalTransferFractionInput'] for x in runs],fundamental=[x['fundamentalFractionInput'] for x in runs],
            peak=[x['peakForceN'] for x in runs],duration=[x['contactDurationMs'] for x in runs],modes=[x['modesPerString'] for x in runs])),flush=True)
    summary=dict(key=a.key,cases=len(cases),simulations=4*len(cases),basisGate=bgate,
        timePassed=sum(x['time']['gate'] for x in cases),bandPassed=sum(x['band18to24']['gate'] for x in cases),
        maxBalanceJ=max(y['maxBalanceJ'] for x in cases for y in x['runs']),
        maxImpulseErrorNs=max(y['impulseErrorNs'] for x in cases for y in x['runs']),
        gate=bgate and all(x['time']['gate'] and x['band18to24']['gate'] for x in cases),impactReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'modal_impact.json').write_text(json.dumps(dict(summary=summary,cases=cases,scaleReportSha256=hashlib.sha256(raw).hexdigest(),
        scope='lossless independent fixed-end vertical strings; width 5mm provisional; no audio'),indent=2,allow_nan=False))
    print('G3_MODAL_IMPACT_GATE '+json.dumps(summary),flush=True)
    assert summary['gate'],'modal impact time or band convergence'
if __name__=='__main__':main()
