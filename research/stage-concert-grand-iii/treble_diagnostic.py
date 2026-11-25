"""G3.02e: band and physical-prior discrimination, no audio or parameter adoption."""
import argparse,json,math,copy
from pathlib import Path
import numpy as np
from modal_target import basis
from modal_impact import run,compare
from felt_law import params,force
ROOT=Path(__file__).parent
# Hall/Askenfelt via Chaigne/Askenfelt, as reproduced in Euphonics 12.2.
# Source parameters describe a power law, not a calibrated G3 memory model.
ANCHORS=[(36,4e8,2.3),(60,4.5e9,2.5),(96,1e12,3.)]
DREF=.0005
def alternative(k,s):
    if not 36<=k<=96:raise ValueError('no extrapolation outside measured anchors')
    for (a,K0,p0),(b,K1,p1) in zip(ANCHORS,ANCHORS[1:]):
        if a<=k<=b:
            t=(k-a)/(b-a);p=p0+(p1-p0)*t
            # Interpolate force at common compression, rather than dimensioned K.
            F=math.exp((1-t)*math.log(K0*DREF**p0)+t*math.log(K1*DREF**p1))
            K=F/DREF**p;break
    # Existing parameter provider evaluates polynomial in key index; replace only
    # local stiffness/power law with literature hypothesis, keep hammer mass.
    z=copy.deepcopy(s);h=z['hammer'];h.update(exponentCoefficients=[p,0.,0.],log10KIntercept=math.log10(K),log10KSlope=0.)
    return z
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--key',type=int,required=True);a=p.parse_args()
    scale=json.loads(a.scale.read_text());s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'felt_hypothesis.json').read_text());k=a.key
    assert scale['version']=='G3-scale-hypothesis-02' and scale['summary']['gate'] and k in (60,72,84,96,108)
    r=scale['rows'][k-21]
    w,P=basis(r,768,96000,.005);rows=[];checks=[]
    # Fixed physical model, vary only mechanical bandwidth and time.
    for speed in (.5,1.,2.):
        rr=[]
        for cut,sr in ((24000,192000),(48000,384000),(72000,384000),(96000,384000),(96000,768000)):
            keep=np.sqrt(w)/(2*np.pi)<=cut
            q=run(r,s,c,w[keep],P[keep],sr,speed,trace=True);q.update(cutHz=cut,prior='CD2012');rr.append(q)
        rows.extend(rr)
        time=compare(rr[3],rr[4]);band=compare(rr[2],rr[3])
        ck=dict(speed=speed,time=time,band72to96=band,band48to72=compare(rr[1],rr[2]),band24to48=compare(rr[0],rr[1]))
        checks.append(ck)
        print('G3_TREBLE_BAND '+json.dumps(dict(key=k,speed=speed,cuts=[q['cutHz'] for q in rr],rates=[q['sampleRateHz'] for q in rr],modes=[q['modesPerString'] for q in rr],transfer=[q['totalTransferFractionInput'] for q in rr],contactPeriods=[q['contactPeriods'] for q in rr],fundamentalForceRatio=[q['forceFundamentalOverDC'][0] for q in rr],**{x:y for x,y in ck.items() if x!='speed'})),flush=True)
    comparison=[]
    if k<=96:
        alt=alternative(k,s);m0,f0=params(k,r['count'],s,c);m1,f1=params(k,r['count'],alt,c)
        assert m0['massKg']==m1['massKg']
        for speed in (.5,1.,2.):
            old=next(q for q in rows if q['speedMps']==speed and q['cutHz']==96000 and q['sampleRateHz']==768000)
            new=run(r,alt,c,w,P,768000,speed,trace=True);new.update(cutHz=96000,prior='Hall-Askenfelt interpolated force')
            rows.append(new)
            entry=dict(key=k,speed=speed,massKg=m0['massKg'],power=[f0.p,f1.p],instantForceAt05mmN=[r['count']*force(DREF,0.,f0),r['count']*force(DREF,0.,f1)],
                transfer=[old['totalTransferFractionInput'],new['totalTransferFractionInput']],contactPeriods=[old['contactPeriods'],new['contactPeriods']],
                fundamentalForceRatio=[old['forceFundamentalOverDC'][0],new['forceFundamentalOverDC'][0]])
            comparison.append(entry);print('G3_TREBLE_PRIOR '+json.dumps(entry),flush=True)
    summary=dict(key=k,simulations=len(rows),timePassed=sum(x['time']['gate'] for x in checks),bandPassed=sum(x['band72to96']['gate'] for x in checks),
        maxEnergyBalanceJ=max(q['maxBalanceJ'] for q in rows),maxSpectrumResidualJ=max(q['forceSpectrumResidualJ'] for q in rows),
        baselineGate=all(x['time']['gate'] and x['band72to96']['gate'] for x in checks),selectedPrior=None)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'treble.json').write_text(json.dumps(dict(summary=summary,rows=rows,checks=checks,comparison=comparison,scope='diagnostic lossless fixed ends; mechanical band beyond audio; no candidate adopted'),indent=2,allow_nan=False))
    print('G3_TREBLE_SUMMARY '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
