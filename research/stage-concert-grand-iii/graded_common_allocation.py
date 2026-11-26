"""Find a single allocation passing both lid angles, from exhaustive evidence."""
import argparse,json,itertools
from pathlib import Path
from graded_reference_audit import configurations,choose,FREQ

def common(a,b):
    A={tuple(r['counts']):r for r in a};B={tuple(r['counts']):r for r in b}
    expected=set(itertools.chain.from_iterable(configurations(k) for k in range(8)))
    if len(a)!=128 or len(b)!=128 or set(A)!=expected or set(B)!=expected:raise ValueError('incomplete allocation evidence')
    rows=[]
    for k in sorted(expected):
        x,y=A[k],B[k]
        if set(x['maximum'])!=set(y['maximum']):raise ValueError('inconsistent metrics')
        m={n:max(v,y['maximum'][n]) for n,v in x['maximum'].items()}
        if bool(x['gate'] and y['gate'])!=all(v<=.05 for v in m.values()):raise ValueError('inconsistent approval')
        rows.append(dict(counts=list(k),totalModes=sum(k),maximum=m,gate=all(v<=.05 for v in m.values())))
    return choose(rows),rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--a',type=Path,required=True);p.add_argument('--b',type=Path,required=True);p.add_argument('--out',type=Path,required=True);v=p.parse_args()
    a,b=(json.loads(x.read_text()) for x in (v.a,v.b))
    assert a['scaleSha256']==b['scaleSha256']
    for d,angle in ((a,30),(b,55)):
        s=d['summary'];assert s['gate'] and s['angleDeg']==angle and s['diagnosticOnly'] and s['referenceModes']==385 and not s['radiationReady'] and d['frequenciesHz']==FREQ
    best,rows=common(a['cases'],b['cases']);v.out.mkdir(parents=True,exist_ok=True)
    summary=dict(gate=True,diagnosticOnly=True,angles=[30,55],commonSelection=best,retrospectiveSelection=True,modalConvergenceCertified=False,radiationReady=False)
    (v.out/'graded_common_allocation.json').write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=a['scaleSha256'],frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_GRADED_COMMON_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
