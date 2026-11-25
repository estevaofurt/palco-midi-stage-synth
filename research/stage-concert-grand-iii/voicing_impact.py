"""Compare predeclared voicing hypothesis, no audio and no per-note optimization."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from modal_target import basis
from modal_impact import run,compare
from action_launch import launch
from voicing_candidate import candidate
ROOT=Path(__file__).parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--key',type=int,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();scale=json.loads(raw);s=json.loads((ROOT/'physical_sources.json').read_text());f=json.loads((ROOT/'felt_hypothesis.json').read_text());c=json.loads((ROOT/'action_hypothesis.json').read_text())
    assert scale['version']=='G3-scale-hypothesis-02' and scale['summary']['gate'] and a.key in (60,72,78,84,90,96,108)
    r=scale['rows'][a.key-21];alt=candidate(a.key,s);w,P=basis(r,768,96000,.005);mask=np.sqrt(w)/(2*np.pi)<=72000
    cases=[]
    for v in (24,76,127):
        q=launch(a.key,v,s,c);speed=q['impactSpeedMps']
        old=run(r,s,f,w,P,768000,speed,trace=True)
        low=run(r,alt,f,w,P,384000,speed,trace=True)
        high=run(r,alt,f,w,P,768000,speed,trace=True)
        band=run(r,alt,f,w[mask],P[mask],384000,speed,trace=True)
        assert old['injectedJ']==low['injectedJ']==high['injectedJ']==band['injectedJ']
        tc=compare(low,high);bc=compare(band,low)
        if a.key<=72:
            assert abs(old['targetJ']-high['targetJ'])<=1e-12 and abs(old['contactDurationMs']-high['contactDurationMs'])<=1e-12
        cases.append(dict(midi=v,launch=q,control=old,candidateLow=low,candidateHigh=high,candidateBand72=band,time=tc,band=bc))
        print('G3_VOICING_CASE '+json.dumps(dict(key=a.key,midi=v,speed=speed,transfer=[old['totalTransferFractionInput'],high['totalTransferFractionInput']],
            stringJ=[old['targetJ'],high['targetJ']],contactMs=[old['contactDurationMs'],high['contactDurationMs']],
            forceRatio=[old['forceFundamentalOverDC'][0],high['forceFundamentalOverDC'][0]],peakN=[old['peakForceN'],high['peakForceN']],
            compressionM=[old['maxCompressionM'],high['maxCompressionM']],time=tc,band=bc)),flush=True)
    summary=dict(key=a.key,simulations=12,timePassed=sum(x['time']['gate'] for x in cases),bandPassed=sum(x['band']['gate'] for x in cases),
        energyMonotone=all(x['candidateHigh']['targetJ']<y['candidateHigh']['targetJ'] for x,y in zip(cases,cases[1:])),
        maxBalanceJ=max(x[z]['maxBalanceJ'] for x in cases for z in ('control','candidateLow','candidateHigh','candidateBand72')),
        gate=all(x['time']['gate'] and x['band']['gate'] for x in cases),selected=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'voicing_impact.json').write_text(json.dumps(dict(summary=summary,cases=cases,scaleSha256=hashlib.sha256(raw).hexdigest(),scope='fixed ends, isolated vertical modal strings; no adoption or audio'),indent=2,allow_nan=False))
    print('G3_VOICING_GATE '+json.dumps(summary),flush=True)
    assert summary['gate'],'candidate convergence'
if __name__=='__main__':main()
