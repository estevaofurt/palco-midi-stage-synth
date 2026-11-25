"""G3.02f: discriminate flexible shaft at unchanged CD2012 felt.
No parameter adoption; same geometry, mass, initial kinetic energy, impact speed.
"""
import argparse,json,math,hashlib
from pathlib import Path
import numpy as np
from modal_target import basis
from modal_impact import run,compare
ROOT=Path(__file__).parent
SHAFT=dict(headMassFraction=.8,relativeModeHz=260.,status='engineering_hypothesis_not_measured_Yamaha')
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--key',type=int,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();scale=json.loads(raw);s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'felt_hypothesis.json').read_text())
    assert scale['version']=='G3-scale-hypothesis-02' and scale['summary']['gate'] and a.key in (60,72,84,96,108)
    r=scale['rows'][a.key-21];w,P=basis(r,768,96000,.005);cases=[]
    for speed in (.5,1.,2.):
        old=run(r,s,c,w,P,768000,speed,trace=True)
        lo=run(r,s,c,w,P,384000,speed,trace=True,shaft=SHAFT)
        hi=run(r,s,c,w,P,768000,speed,trace=True,shaft=SHAFT)
        assert old['injectedJ']==lo['injectedJ']==hi['injectedJ']
        ck=compare(lo,hi)
        # Include flex energy and COM recoil separately; head recoil may differ.
        ck['relative']['shaftEnergyJ']=abs(lo['shaftEnergyJ']-hi['shaftEnergyJ'])/max(hi['shaftEnergyJ'],1e-12)
        ck['relative']['centerOfMassReboundMps']=abs(lo['centerOfMassReboundMps']-hi['centerOfMassReboundMps'])/max(abs(hi['centerOfMassReboundMps']),1e-12)
        ck['gate']=ck['gate'] and max(ck['relative'].values())<=.05
        cases.append(dict(rigid=old,flexLow=lo,flexHigh=hi,convergence=ck))
        print('G3_SHAFT_CASE '+json.dumps(dict(key=a.key,speed=speed,transfer=[old['totalTransferFractionInput'],hi['totalTransferFractionInput']],
            fundamental=[old['fundamentalFractionInput'],hi['fundamentalFractionInput']],
            contactMs=[old['contactDurationMs'],hi['contactDurationMs']],forceFundamentalRatio=[old['forceFundamentalOverDC'][0],hi['forceFundamentalOverDC'][0]],
            flexFraction=hi['shaftEnergyJ']/hi['injectedJ'],headRebound=hi['reboundMps'],comRebound=hi['centerOfMassReboundMps'],convergence=ck)),flush=True)
    summary=dict(key=a.key,simulations=3*len(cases),timePassed=sum(x['convergence']['gate'] for x in cases),
        maxBalanceJ=max(x[q]['maxBalanceJ'] for x in cases for q in ('rigid','flexLow','flexHigh')),
        gate=all(x['convergence']['gate'] for x in cases),selectedShaft=None,impactReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'shaft.json').write_text(json.dumps(dict(summary=summary,shaft=SHAFT,cases=cases,scaleSha256=hashlib.sha256(raw).hexdigest(),
        scope='free two-mass transverse flexure proxy; not real pivoted shank, action, calibrated felt or audio'),indent=2,allow_nan=False))
    print('G3_SHAFT_GATE '+json.dumps(summary),flush=True)
    assert summary['gate'],'shaft time convergence'
if __name__=='__main__':main()
