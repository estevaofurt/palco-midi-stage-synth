"""Independent convergence of the shared-edge interaction block B only."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry as cabinet
from inclined_lid import build
from lid_exterior import ports
from rigid_screen import geometry
from edge_screen import EdgeBasis
from shared_edge_quadrature import assemble
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=cabinet(poly,l,read('cabinet_geometry_hypothesis.json'))
    local,o,A,n=geometry(poly,a.angle,g['rimTopZ_m'])
    m,C0,rep=build(poly,12,4,g['rimTopZ_m'],a.angle,lambda x:np.ones((len(x),1)))
    panels,_=ports(m,C0,rep,3);basis=EdgeBasis(local,5)
    freq=[30.,80.,150.];ks=2*np.pi*np.array(freq)/m['c']
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'shared_edge.json'
    rows=[];outputs=[]
    for order in (8,12,16,22):
        B,r=assemble(basis,o,A,n,panels,ks,order,True)
        # Compare same geometry and graded tensor reference, no changed basis.
        T,_=assemble(basis,o,A,n,panels,ks,order,False)
        assert r['sharedPairs']==len(panels),r
        r.update(relativeTensor=relative(T,B),finite=bool(np.isfinite(B).all() and np.isfinite(T).all()))
        rows.append(r);outputs.append((B,T))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_SHARED_EDGE_CASE '+json.dumps(r),flush=True)
    checks=[dict(joint=relative(x[0],y[0]),tensor=relative(x[1],y[1])) for x,y in zip(outputs,outputs[1:])]
    gate=all(r['finite'] for r in rows) and checks[-1]['joint']<=.01
    summary=dict(gate=gate,angleDeg=a.angle,convergence=checks,sharedEdgeInteractionOnly=True,
        boundaryResidualValidated=False,apertureCouplingReady=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_SHARED_EDGE_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
