"""Numerical interface proof on both complete centerlines."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky
from spatial_layout import build as layout_build
from bridge_strings import centerline
from bridge_board_interface import assemble,mobility
ROOT=Path(__file__).parent
def compare(a,b):
    scale=np.array([1.,.02,1.,.02,1.,1.])
    x=a*scale[:,None]*scale[None,:];y=b*scale[:,None]*scale[None,:]
    e=float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-30))
    return dict(relative=e,gate=e<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    layout=layout_build(sc,json.loads((ROOT/'layout_hypothesis.json').read_text()));centers={s:centerline(layout['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    cfg=json.loads((ROOT/'board_interface_hypothesis.json').read_text());bcfg=json.loads((ROOT/'bridge_hypothesis.json').read_text())
    freq=np.geomspace(80,1000,24);rows=[];Y=[]
    for sub,n,order,connected in [(1,12,4,True),(2,12,6,True),(2,18,6,True),(2,24,8,True),(2,24,8,False)]:
        M,K,J,D,P,maps,nb=assemble(centers,layout,cfg,bcfg,sub,n,order,connected)
        cholesky(M);cholesky(K+J) if connected else None
        y,recip,passmin=mobility(M,K+J,D,P,freq);Y.append(y)
        rows.append(dict(sub=sub,plateOrder=n,quadrature=order,connected=connected,dofs=len(M),reciprocity=recip,passivityMinRelative=passmin,
                         crossBridgeMaxMsN=float(np.max(abs(y[:,0,2]))),crossBoardMaxMsN=float(np.max(abs(y[:,0,4])))))
        if connected:assert rows[-1]['crossBridgeMaxMsN']>0 and rows[-1]['crossBoardMaxMsN']>0
        else:assert rows[-1]['crossBridgeMaxMsN']<1e-14 and rows[-1]['crossBoardMaxMsN']<1e-14
    mesh=compare(Y[0],Y[1]);plate1=compare(Y[1],Y[2]);plate2=compare(Y[2],Y[3])
    summary=dict(cases=rows,mesh=mesh,plate12to18=plate1,plate18to24=plate2,gate=mesh['gate'] and plate2['gate'],boardReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'bridge_board_interface.json').write_text(json.dumps(dict(summary=summary,config=cfg,scaleSha256=hashlib.sha256(raw).hexdigest(),frequenciesHz=freq.tolist(),
       mobilityReal=Y[3].real.tolist(),mobilityImag=Y[3].imag.tolist(),scope='reciprocal distributed relative spring; rectangular plate fixture, no strings, no radiation'),indent=2,allow_nan=False))
    print('G3_BRIDGE_BOARD_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'interface convergence'
if __name__=='__main__':main()
