"""Controlled equal-count comparison of physical-edge strip and red refinement.
30 Hz diagnostic only; same analytic P1 fit and independent edge audit.
"""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from bem_p1_static_moments import fit as tensor_fit,operators
from bem_edge_localization import localize,inventory
from bem_edge_matched import matched
from bem_edge_audit import edge_samples
from bem_power_partition import integrate,partition,herm
from bem_linear import far_gram,observe
from bem_mesh_guard import signature,require_same_mesh
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
    f=30.;k=2*np.pi*f/343.
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    rows=[];outputs=[];a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_edge_matched.json'
    q0,r0=tensor_fit(t,k,5,6,velocity);assert r0['weakResidual']<=1e-8
    kinds=[s['kind'] for s in surf]
    classes,_=inventory(t,labels,kinds)
    marking=localize(t,labels,kinds,q0,velocity,k,5,6)
    scores=np.asarray(marking['sectorIndicator']);eligible=np.isin(classes,['crease','crease-port-transition'])
    red,strip,match=matched(t,labels,scores,eligible,448)
    print('G3_EDGE_MATCHED_GEOMETRY '+json.dumps(match),flush=True)
    for name,tt,ll,refinement in [('baseline',t,labels,{}),('red',*red),('strip',*strip)]:
        gr=__import__('exterior_bem').topology(tt);assert gr['gate'] and abs(gr['volume']-geo['volume'])<=1e-10
        v=lambda x,o:velocities(surf,ports,x,ll[o])
        start=time.perf_counter();q,r=(q0,r0) if name=='baseline' else tensor_fit(tt,k,5,6,v)
        elapsed=time.perf_counter()-start;assert r['weakResidual']<=1e-8
        # All candidates are evaluated using exactly the same higher-order
        # independent target/source and spherical integration rules.
        P,C,ar=integrate(tt,q,v,k,8,8,operator=operators,sample_rule=edge_samples)
        F=1.204*343*k*k/(4*np.pi)*far_gram(tt,q,k,order=28,surface_order=8)
        part=partition(P,C,F);H=herm(P);scale=max(np.linalg.norm(P),1e-30)
        pas=float(np.linalg.eigvalsh(H).min()/scale)
        rep=dict(**ar,**part,passivityMinRelative=pas,powerRelative=part['totalPowerRelative'])
        physical=max(rep['heldoutResidual'],rep['heldoutWorstColumn'])<=.05 and rep['reciprocity']<=.01 and rep['powerRelative']<=.01 and pas>=-1e-8
        pf=1j*1.204*343*k*observe(tt,q,far,k,8)
        outputs.append((P,pf))
        row=dict(method=name,fitOuter=5,fitInner=6,fitSeconds=elapsed,meshSha256=signature(tt,ll),elements=len(tt),refinement=refinement,
            frequencyHz=f,fit=r,audit=rep,physicalGate=bool(physical))
        rows.append(row);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_EDGE_MATCHED_CASE '+json.dumps(row),flush=True)
    change=dict(impedance=relative(outputs[1][0],outputs[2][0]),pressure=relative(outputs[1][1],outputs[2][1]))
    # A diagnostic comparison is not a convergence or solver approval.
    gate=all(r['audit']['partitionClosure']<=1e-10 for r in rows) and rows[1]['elements']==rows[2]['elements']
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,frequencyHz=f,matched=match,
        sameAudit=True,sameFitRule=True,betweenMeshDifference=change,
        physicalGates={r['method']:r['physicalGate'] for r in rows},
        solverApproved=False,upperEnvelopeOnly=True,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_EDGE_MATCHED_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
