"""Independent local-basis refinement and passive elastic rim fixture."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import eigh
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from spline_plate import assemble,rim_matrices
from ribbed_plate import response
from ribbed_plate_diagnostic import compare
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);cfg=read('ribbed_plate_hypothesis.json')
    poly=np.array(c['contourXY_m']);pts=np.array([l['bridgeAttachmentNodes'][s][len(l['bridgeAttachmentNodes'][s])//2]['footProjectionXYZ_m'][:2] for s in ('bass','treble')]+[c['centroidXY_m']])
    freq=np.geomspace(30,150,24);cases=[];results=[]
    for cells,order in [(6,14),(9,14),(12,14),(15,14),(15,18)]:
        m=assemble(poly,c['ribs'],mat['plate'],cfg['rib'],cells,order)
        assert abs(m['areaM2']-c['summary']['areaM2'])<1e-10
        f,y=response(m,pts,freq,mat['plate'],True);b,z=response(m,pts,freq,mat['plate'],False)
        results.append((f,y));cases.append(dict(cells=cells,quadrature=order,rank=m['rank'],fullRank=m['fullRank'],condition=m['condition'],
            plateMassKg=m['plateMassKg'],ribMassKg=m['ribMassKg'],first8BareHz=b[:8].tolist(),first8RibbedHz=f[:8].tolist()))
    checks=[compare(x,y) for x,y in zip(results,results[1:])]
    # Independent elastic edge demonstration, not a selected rim or convergence proof.
    m=assemble(poly,c['ribs'],mat['plate'],cfg['rib'],9,14,False)
    K=m['K']+m['Kr'];M=m['M']+m['Mr'];Z,R=rim_matrices(m,2e6,200.,14)
    modes=[]
    for factor in (.1,1.,10.):
        w=eigh(K+factor*(Z+R),M,eigvals_only=True);assert min(w)>0
        modes.append(dict(factor=factor,first8Hz=(np.sqrt(w[:8])/(2*np.pi)).tolist()))
    assert np.all(np.diff(np.array([x['first8Hz'] for x in modes]),axis=0)>=-1e-6)
    summary=dict(cases=cases,convergence=checks,rimFixture=dict(kzNperM2=2e6,ktN=200.,cases=modes,selected=None,ready=False),
        gate=checks[-2]['gate'] and checks[-1]['gate'] and all(x['rank']==x['fullRank'] for x in cases),boardReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'spline_plate.json').write_text(json.dumps(dict(summary=summary,scaleSha256=hashlib.sha256(raw).hexdigest(),scope='local spline Ritz and independent elastic edge fixture'),indent=2,allow_nan=False))
    print('G3_SPLINE_PLATE_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'local basis convergence'
if __name__=='__main__':main()
