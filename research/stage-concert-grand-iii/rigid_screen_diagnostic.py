"""Isolated candidate lid screen with independent offset point sources."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build,properties
from cabinet_geometry import geometry as cabinet
from rigid_screen import geometry,solve_screen
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=cabinet(poly,l,read('cabinet_geometry_hypothesis.json'))
    local,o,A,n=geometry(poly,a.angle,g['rimTopZ_m'])
    _,center,_=properties(local);mid=o+center@A.T
    # Fixture sources are separated from the lid, not yet the aperture basis.
    sources=np.array([mid-.5*n,mid-.6*n+.25*A[:,0],mid+.7*n+.3*A[:,1]])
    observers=np.array([mid+1.5*n,mid-1.5*n,mid+2*A[:,0]+.5*n])
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'rigid_screen.json'
    freq=[30.,80.,150.];rows=[];outputs=[]
    for d,outer,inner in [(2,10,18),(4,12,22),(6,14,26),(8,18,34),(8,22,42)]:
        P=[];Z=[];reports=[]
        for f in freq:
            v,w,q=solve_screen(local,o,A,n,sources,observers,2*np.pi*f/343.,d,outer,inner)
            P.append(v);Z.append(w);reports.append(dict(frequencyHz=f,**q))
        row=dict(degree=d,outer=outer,inner=inner,gate=all(q['gate'] for q in reports),reports=reports)
        for key in ('rawReciprocity','weakResidual','reciprocity','powerRelative'):
            row[key]=max(q[key] for q in reports)
        rows.append(row);outputs.append((np.array(P),np.array(Z)))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_SCREEN_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    checks=[dict(pressure=relative(x[0],y[0]),impedance=relative(x[1],y[1])) for x,y in zip(outputs,outputs[1:])]
    gate=rows[-1]['gate'] and all(max(q.values())<=.05 for q in checks[-2:])
    summary=dict(gate=gate,angleDeg=a.angle,convergence=checks,isolatedScreenOnly=True,edgeDensityConverged=False,
        apertureCouplingReady=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_SCREEN_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
