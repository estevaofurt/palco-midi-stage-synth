"""Synthetic scaling benchmark, NOT the calibrated 88-key physical engine."""
import argparse,json
from pathlib import Path
from compiled_variable_damper import benchmark

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[]
    for v in (32,64,88,96,128,192,256):
        for j in (4,8,16):
            for r in (48000,96000):
                q=benchmark(v,j,128,r,block=128,blocks=200)
                q['headroomGate']=bool(q['gate'] and q['overruns']==0 and q['p99BudgetFraction']<=.70)
                rows.append(q);print('G3_POLYPHONY_SCALE '+json.dumps(q),flush=True)
    a.out.mkdir(parents=True,exist_ok=True)
    summary=dict(gate=all(v['gate'] for v in rows),syntheticParameters=True,physicalPolyphonyValidated=False,
        configurations=len(rows),zeroOverrunConfigurations=sum(v['overruns']==0 for v in rows),
        headroomConfigurations=sum(v['headroomGate'] for v in rows))
    (a.out/'polyphony_scale.json').write_text(json.dumps(dict(summary=summary,cases=rows),indent=2,allow_nan=False))
    print('G3_POLYPHONY_SCALE_GATE '+json.dumps(summary),flush=True)
    if not summary['gate']:raise ValueError('scaling energy proof failed')
if __name__=='__main__':main()
