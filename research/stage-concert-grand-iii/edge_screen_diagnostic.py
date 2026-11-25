"""Compare edge-aware basis refinement and quadrature; isolated lid only."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build,properties
from cabinet_geometry import geometry as cabinet
from rigid_screen import geometry
from edge_screen import EdgeBasis,operators,solve
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=cabinet(poly,l,read('cabinet_geometry_hypothesis.json'))
    local,o,A,n=geometry(poly,a.angle,g['rimTopZ_m']);_,center,_=properties(local);mid=o+center@A.T
    sources=np.array([mid-.5*n,mid-.6*n+.25*A[:,0],mid+.7*n+.3*A[:,1]])
    observers=np.array([mid+1.5*n,mid-1.5*n,mid+2*A[:,0]+.5*n])
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'edge_screen.json'
    freq=[30.,80.,150.];k=2*np.pi*np.array(freq)/343.;rows=[];outputs=[]
    b=EdgeBasis(local,7);cache={}
    for d,outer,inner in [(2,12,22),(4,12,22),(6,12,22),(6,18,34),(6,24,46)]:
        key=(outer,inner)
        if key not in cache:cache[key]=operators(b,k,outer,inner)
        P=[];Z=[];reports=[]
        for f,kl,W in zip(freq,k,cache[key]):
            v,z,q=solve(b,W,kl,o,A,n,sources,observers,d,max(outer,18))
            P.append(v);Z.append(z);reports.append(dict(frequencyHz=f,**q))
        row=dict(degree=d,outer=outer,inner=inner,gate=all(q['gate'] for q in reports),reports=reports)
        for name in ('rawReciprocity','weakResidual','reciprocity','powerRelative'):
            row[name]=max(q[name] for q in reports)
        rows.append(row);outputs.append((np.array(P),np.array(Z)))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_EDGE_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    checks=[dict(pressure=relative(x[0],y[0]),impedance=relative(x[1],y[1])) for x,y in zip(outputs,outputs[1:])]
    gate=rows[-1]['gate'] and all(max(q.values())<=.05 for q in checks[-3:])
    summary=dict(gate=gate,angleDeg=a.angle,convergence=checks,isolatedScreenOnly=True,
        cornerExponentValidated=False,apertureCouplingReady=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_EDGE_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
