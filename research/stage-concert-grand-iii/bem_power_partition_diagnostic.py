"""Compare boundary-work and integration errors for P1 on one fixed mesh."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from bem_linear import COL,targets,fit as collocate,far_gram
from bem_oversampled import TRAIN,fit as oversample
from bem_power_partition import integrate,partition
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    surf,ports,center=envelope(poly,g['rimTopZ_m'],a.angle,3,field);geo=geometry_audit(surf,ports,center);assert geo['gate']
    t,labels,gr=triangulate(surf,1);assert abs(gr['volume']-geo['volume'])<1e-10
    velocity=lambda x,owner:velocities(surf,ports,x,labels[owner])
    freq=[30.,80.,150.];rows=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_power_partition.json'
    for f in freq:
        k=2*np.pi*f/343.
        for method,L,fit in [('collocation',COL,collocate),('oversampled',TRAIN,oversample)]:
            x,n,w,owner=targets(t,L);q,fitrep=fit(t,velocity(x,owner),k,6)
            # Independent far-field refinement, hold final Gram fixed when
            # comparing the surface work quadrature.
            scale=1.204*343*k*k/(4*np.pi)
            F0=scale*far_gram(t,q,k,order=20,surface_order=5)
            F=scale*far_gram(t,q,k,order=28,surface_order=8)
            farChange=relative(F0,F);cases=[];previous=None
            for outer,inner in [(3,6),(5,8),(7,10)]:
                P,C,r=integrate(t,q,velocity,k,outer,inner)
                row=dict(**r,**partition(P,C,F),farConvergence=farChange)
                if previous is not None:
                    row['workConvergence']=dict(prescribed=relative(previous[0],P),computed=relative(previous[1],C))
                previous=(P,C);cases.append(row)
                print('G3_BEM_POWER_CASE '+json.dumps(dict(frequencyHz=f,method=method,**row)),flush=True)
            final=cases[-1]
            # Diagnostic reliability is distinct from physical solver readiness.
            reliable=final['partitionClosure']<=1e-10 and farChange<=.01 and max(final['workConvergence'].values())<=.01
            rows.append(dict(frequencyHz=f,method=method,fit=fitrep,cases=cases,diagnosticReliable=bool(reliable)))
            path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
    reliable=all(r['diagnosticReliable'] for r in rows)
    summary=dict(gate=reliable,diagnosticOnly=True,angleDeg=a.angle,elements=len(t),
        sameMesh=True,noSolverPromotion=True,physicalGatesUnchanged=True,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_BEM_POWER_GATE '+json.dumps(summary),flush=True);assert reliable
if __name__=='__main__':main()
