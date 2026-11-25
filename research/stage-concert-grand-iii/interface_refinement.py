"""Rectangular interface basis refinement; unchanged physical parameters and gate."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from bridge_strings import centerline
from bridge_board_interface import assemble,mobility
from bridge_board_interface_diagnostic import compare
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    cfg=read('board_interface_hypothesis.json');bcfg=read('bridge_hypothesis.json')
    freq=np.geomspace(80,1000,24);rows=[];Y=[]
    for n,order in [(24,8),(32,12),(40,12),(48,12),(48,16)]:
        M,K,J,D,P,_,_=assemble(centers,l,cfg,bcfg,2,n,order)
        # Diagonal coordinate equilibration preserves conjugate port work.
        s=1/np.sqrt(np.diag(M));W=s[:,None]*s[None,:]
        y,recip,passmin=mobility(M*W,(K+J)*W,D*W,P*s[:,None],freq);Y.append(y)
        rows.append(dict(plateOrder=n,quadrature=order,dofs=len(M),reciprocity=recip,passivityMinRelative=passmin))
    pairs=[compare(x,y) for x,y in zip(Y,Y[1:])]
    summary=dict(cases=rows,comparisons=pairs,gate=pairs[-2]['gate'] and pairs[-1]['gate'],boardReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'interface_refinement.json').write_text(json.dumps(dict(summary=summary,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_INTERFACE_REFINEMENT '+json.dumps(summary),flush=True);assert summary['gate'],'rectangular interface refinement'
if __name__=='__main__':main()
