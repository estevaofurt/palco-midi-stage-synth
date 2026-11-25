"""Geometry and trace equivalence on the actual hypothetical cabinet.
No exterior solve or claim of high-order modal convergence.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from inclined_lid import build as inclined_build
from lid_exterior import ports
from lower_prism import build as lower_build
from nested_acoustic_ports import embedding
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    rows=[]
    for angle in (30,55):
        m,C0,r=inclined_build(poly,12,4,g['rimTopZ_m'],angle,field)
        hi,CH=ports(m,C0,r,36,canonical=True)
        for n in (21,28):
            lo,CL=ports(m,C0,r,n,canonical=True);E,e=embedding(hi,lo)
            row=dict(angleDeg=angle,domain='upper',modes=n,traceRelative=relative(CH@E,CL),
                maxCondition=max(x.basis.condition for x in hi),embedding=e)
            row['gate']=row['traceRelative']<=1e-8 and e['gate'];rows.append(row)
            print('G3_EXTENDED_FLUX_CASE '+json.dumps(row),flush=True)
    h=-g['rimBottomZ_m'];hi=lower_build(poly,18,h,field,36)
    for n in (21,28):
        lo=lower_build(poly,18,h,field,n);E,e=embedding([hi['mouth']],[lo['mouth']])
        row=dict(domain='lower',modes=n,traceRelative=relative(hi['B'][:,4:]@E,lo['B'][:,4:]),
            maxCondition=hi['mouth'].basis.condition,embedding=e)
        row['gate']=row['traceRelative']<=1e-8 and e['gate'];rows.append(row)
        print('G3_EXTENDED_FLUX_CASE '+json.dumps(row),flush=True)
    summary=dict(gate=all(r['gate'] for r in rows),maxModesPerPanel=36,maximumTotalModes=252,
        traceOnly=True,modalConvergenceReady=False,fullCabinetReady=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'extended_flux.json').write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_EXTENDED_FLUX_GATE '+json.dumps(summary),flush=True);assert summary['gate']
if __name__=='__main__':main()
