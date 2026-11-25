"""Refine the failed C8 fixture without changing physical parameters or tolerances."""
import argparse,json
from pathlib import Path
from hammer_impact import impact,compare
ROOT=Path(__file__).parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    scale=json.loads(a.scale.read_text());s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'felt_hypothesis.json').read_text())
    assert scale['version']=='G3-scale-hypothesis-02' and scale['summary']['gate']
    rows=[];checks=[]
    for scheme in ('midpoint','exact'):
        rs=[impact(scale['rows'][87],s,c,sr,2.,'elastic',propagator=scheme) for sr in (96000,192000,384000,768000,1536000)]
        rows.extend(rs)
        for x,y in zip(rs,rs[1:]):
            check=compare(x,y);checks.append(dict(scheme=scheme,rates=[x['sampleRateHz'],y['sampleRateHz']],**check,absoluteTargetDeltaJ=abs(x['targetJ']-y['targetJ']),targetDeltaFractionOfInput=abs(x['targetJ']-y['targetJ'])/y['injectedJ']))
        for x in rs:print('G3_C8_REFINEMENT '+json.dumps(x),flush=True)
    old=rows[0:2]
    assert abs(old[0]['targetJ']-2.02652927722436e-10)<1e-15 and abs(old[1]['targetJ']-1.0682605169071613e-10)<1e-15
    finest=compare(rows[4],rows[9])
    summary=dict(originalGate=checks[0]['gate'],finestMidpointGate=checks[3]['gate'],finestExactGate=checks[7]['gate'],crossSchemeFinest=finest,originalFailureReproduced=not checks[0]['gate'],scope='diagnostic only; no change to 96/192k requirement, no physical selection')
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'c8_refinement.json').write_text(json.dumps(dict(summary=summary,rows=rows,checks=checks),indent=2,allow_nan=False))
    print('G3_C8_REFINEMENT_SUMMARY '+json.dumps(summary),flush=True)
    for x in checks:print('G3_C8_CONVERGENCE '+json.dumps(x),flush=True)
if __name__=='__main__':main()
