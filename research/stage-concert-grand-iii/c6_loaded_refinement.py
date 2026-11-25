"""C6 loaded impact refinement, same configuration and unchanged original gate."""
import argparse,json
from pathlib import Path
from moving_termination import basis
from loaded_target import LoadedTarget
from loaded_impact import compare_loaded
from termination_diagnostic import LOAD
from modal_impact import run
from voicing_candidate import candidate
ROOT=Path(__file__).parent
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    sc=json.loads(a.scale.read_text());assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    r=sc['rows'][63];s=candidate(84,json.loads((ROOT/'physical_sources.json').read_text()));c=json.loads((ROOT/'felt_hypothesis.json').read_text())
    w,P=basis(r,768,96000,LOAD['massKg'],LOAD['stiffnessNm'])
    rows=[run(r,s,c,w,P,sr,5.,target_factory=lambda w,P,sr:LoadedTarget(w,P,sr,LOAD)) for sr in (384000,768000,1536000,3072000)]
    pairs=[compare_loaded(x,y) for x,y in zip(rows,rows[1:])]
    summary=dict(original=pairs[0],refined=pairs[1:],loadStoredJ=[float(q['loadStoredJ']) for q in rows],contactMs=[q['contactDurationMs'] for q in rows],gate=pairs[-1]['gate'])
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'c6_loaded_refinement.json').write_text(json.dumps(dict(summary=summary,rows=rows),indent=2,allow_nan=False))
    print('G3_C6_LOADED_REFINEMENT '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
