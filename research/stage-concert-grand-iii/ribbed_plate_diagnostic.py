"""Predeclared modal convergence, bare vs ribbed polygon, no bridge attached."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from ribbed_plate import assemble,response
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def compare(a,b):
    f=float(np.max(abs(a[0][:8]/b[0][:8]-1)))
    y=float(np.linalg.norm(a[1]-b[1])/max(np.linalg.norm(b[1]),1e-30))
    return dict(first8FrequencyRelative=f,mobilityRelative=y,gate=f<=.02 and y<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));material=read('board_interface_hypothesis.json')
    contour=contour_build(l,read('board_contour_hypothesis.json'),material);cfg=read('ribbed_plate_hypothesis.json')
    poly=np.array(contour['contourXY_m']);pts=np.array([l['bridgeAttachmentNodes'][s][len(l['bridgeAttachmentNodes'][s])//2]['footProjectionXYZ_m'][:2] for s in ('bass','treble')]+[contour['centroidXY_m']])
    freq=np.geomspace(30,150,24);cases=[];results=[]
    # Orders include independent quadrature check at identical final basis.
    for degree,order in [(6,24),(8,28),(10,32),(12,36),(12,44)]:
        m=assemble(poly,contour['ribs'],material['plate'],cfg['rib'],degree,order)
        assert abs(m['areaM2']-contour['summary']['areaM2'])<1e-10
        f,y=response(m,pts,freq,material['plate'],True);b,z=response(m,pts,freq,material['plate'],False)
        results.append((f,y));cases.append(dict(degree=degree,quadrature=order,rank=m['rank'],fullRank=m['fullRank'],condition=m['condition'],
            plateMassKg=m['plateMassKg'],ribMassKg=m['ribMassKg'],first8BareHz=b[:8].tolist(),first8RibbedHz=f[:8].tolist()))
    checks=[compare(x,y) for x,y in zip(results,results[1:])]
    summary=dict(contour=contour['summary'],cases=cases,convergence=checks,gate=checks[-2]['gate'] and checks[-1]['gate'] and all(q['rank']==q['fullRank'] for q in cases),boardReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'ribbed_plate.json').write_text(json.dumps(dict(summary=summary,config=cfg,pointsXY=pts.tolist(),frequenciesHz=freq.tolist(),
        mobilityReal=results[-1][1].real.tolist(),mobilityImag=results[-1][1].imag.tolist(),scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_RIBBED_PLATE_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'polygon plate convergence'
if __name__=='__main__':main()
