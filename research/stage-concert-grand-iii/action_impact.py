"""Connect launch convention to isolated modal impact, without audio or scheduling."""
import argparse,json
from pathlib import Path
from action_launch import launch
from modal_target import basis
from modal_impact import run,compare
ROOT=Path(__file__).parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--key',type=int,required=True);a=p.parse_args()
    scale=json.loads(a.scale.read_text());s=json.loads((ROOT/'physical_sources.json').read_text());f=json.loads((ROOT/'felt_hypothesis.json').read_text());c=json.loads((ROOT/'action_hypothesis.json').read_text())
    assert scale['version']=='G3-scale-hypothesis-02' and scale['summary']['gate'] and a.key in (60,72,84,96,108)
    r=scale['rows'][a.key-21];w,P=basis(r,768,96000,.005);cases=[]
    for v in (24,76,127):
        q=launch(a.key,v,s,c);speed=q['impactSpeedMps']
        lo=run(r,s,f,w,P,384000,speed,trace=True);hi=run(r,s,f,w,P,768000,speed,trace=True)
        assert abs(hi['injectedJ']-q['impactEnergyJ'])<1e-12
        ck=compare(lo,hi)
        cases.append(dict(launch=q,low=lo,high=hi,convergence=ck))
        print('G3_ACTION_IMPACT_CASE '+json.dumps(dict(key=a.key,midi=v,speed=speed,transfer=hi['totalTransferFractionInput'],stringJ=hi['targetJ'],contactMs=hi['contactDurationMs'],fundamental=hi['fundamentalFractionInput'],convergence=ck)),flush=True)
    summary=dict(key=a.key,simulations=6,timePassed=sum(x['convergence']['gate'] for x in cases),gate=all(x['convergence']['gate'] for x in cases),selectedCurve=None,actionReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'action_impact.json').write_text(json.dumps(dict(summary=summary,cases=cases,scope='rigid hammer, fixed ends, original felt; pre-contact analytic action separated from impact; no gravity during short impact, no audio'),indent=2,allow_nan=False))
    print('G3_ACTION_IMPACT_GATE '+json.dumps(summary),flush=True)
    assert summary['gate'],'action impact time convergence'
if __name__=='__main__':main()
