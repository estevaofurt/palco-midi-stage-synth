"""Fixed-density comparison of conventional and edge-graded audit rules.
Test the low-frequency worst power case at 30 Hz; not a solver proof.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from bem_p1_static_moments import fit,operators,audit
from bem_oversampled import audit_targets
from bem_linear import far_gram
from bem_power_partition import integrate,partition,herm
from bem_edge_audit import edge_samples
from bem_mesh_guard import signature,require_same_mesh
from exterior_bem import samples
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
    t,labels,top=triangulate(surf,1);sig=signature(t,labels);assert abs(top['volume']-geo['volume'])<=1e-10
    velocity=lambda x,o:velocities(surf,ports,x,labels[o])
    f=30.;k=2*np.pi*f/343.;q,fr=fit(t,k,5,6,velocity);assert fr['weakResidual']<=1e-8
    qsig=hashlib.sha256(np.ascontiguousarray(q).tobytes()).hexdigest()
    x,n,w,o=audit_targets(t);Va=velocity(x,o)
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    _,_,baseline=audit(t,q,Va,k,far,8)
    F=1.204*343*k*k/(4*np.pi)*far_gram(t,q,k,order=28,surface_order=8)
    rows=[];mat=[];a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_edge_audit.json'
    # Inner integration fixed for comparisons; final case increases it
    # independently to distinguish source and target quadrature errors.
    for name,outer,inner,rule in [('tensor',6,6,samples),('edge',4,6,edge_samples),
        ('edge',6,6,edge_samples),('edge',8,6,edge_samples),('edge',8,8,edge_samples)]:
        require_same_mesh(sig,signature(t,labels))
        assert qsig==hashlib.sha256(np.ascontiguousarray(q).tobytes()).hexdigest()
        P,C,r=integrate(t,q,velocity,k,outer,inner,operator=operators,sample_rule=rule)
        row=dict(rule=name,frequencyHz=f,elements=len(t),meshSha256=sig,densitySha256=qsig,
            **r,**partition(P,C,F))
        row['targetPoints']=len(t)*outer**2*(3 if name=='edge' else 1)
        rows.append(row);mat.append((P,C))
        path.write_text(json.dumps(dict(cases=rows,degreeFourAudit=baseline,complete=False),indent=2,allow_nan=False))
        print('G3_EDGE_AUDIT_CASE '+json.dumps(row),flush=True)
    def changes(i,j):
        return dict(prescribedWork=relative(herm(mat[i][0]),herm(mat[j][0])),
            computedWork=relative(herm(mat[i][1]),herm(mat[j][1])),
            residual=abs(rows[i]['heldoutResidual']-rows[j]['heldoutResidual'])/max(rows[j]['heldoutResidual'],1e-30),
            worstColumn=abs(rows[i]['heldoutWorstColumn']-rows[j]['heldoutWorstColumn'])/max(rows[j]['heldoutWorstColumn'],1e-30))
    target=changes(2,3);source=changes(3,4)
    reliable=lambda r:max(r['prescribedWork'],r['computedWork'])<=.01 and max(r['residual'],r['worstColumn'])<=.05
    gate=reliable(target) and reliable(source) and all(r['partitionClosure']<=1e-10 for r in rows)
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,fixedDensity=True,fixedMesh=True,
        targetConvergence=target,sourceConvergence=source,degreeFourResidual=baseline['heldoutResidual'],
        finalEdgeResidual=rows[-1]['heldoutResidual'],finalEdgeWorstColumn=rows[-1]['heldoutWorstColumn'],
        physicalGatesUnchanged=True,solverApproved=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,degreeFourAudit=baseline,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_EDGE_AUDIT_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
