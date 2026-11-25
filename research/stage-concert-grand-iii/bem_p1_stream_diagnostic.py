"""Compare streamed and dense P1 on the same physical fixture.
Equivalence only; no new physical approval gate.
"""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from bem_linear import COL,targets,fit as dense_fit
from bem_oversampled import audit as dense_audit,audit_targets
from bem_p1_stream import fit,audit
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
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    rows=[];a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_p1_stream.json'
    for level,frequencies in [(1,[30.,80.,150.]),(2,[80.])]:
        t,labels,gr=triangulate(surf,level);assert abs(gr['volume']-geo['volume'])<1e-10
        x,n,w,owner=targets(t,COL);V=velocities(surf,ports,x,labels[owner])
        x,n,w,owner=audit_targets(t);Va=velocities(surf,ports,x,labels[owner])
        for f in frequencies:
            k=2*np.pi*f/343.
            start=time.perf_counter();q0,r0=dense_fit(t,V,k,4,derivative_only=False);t0=time.perf_counter()-start
            start=time.perf_counter();q,r=fit(t,V,k,4);t1=time.perf_counter()-start
            start=time.perf_counter();z,p,rr0=dense_audit(t,q0,Va,k,far,6);a0=time.perf_counter()-start
            start=time.perf_counter();Z,P,rr=audit(t,q,Va,k,far,6);a1=time.perf_counter()-start
            delta=dict(coefficients=relative(q,q0),impedance=relative(Z,z),pressure=relative(P,p))
            metrics=['heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative','passivityMinRelative']
            err=max(abs(rr[m]-rr0[m]) for m in metrics)
            gate=max(delta.values())<=1e-9 and err<=1e-9 and rr['gate']==rr0['gate']
            row=dict(level=level,elements=len(t),frequencyHz=f,equivalenceGate=gate,difference=delta,
                maxAuditDifference=err,physicalGate=rr['gate'],denseAudit=rr0,streamAudit=rr,
                seconds=dict(denseFit=t0,streamFit=t1,denseAudit=a0,streamAudit=a1))
            rows.append(row);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
            print('G3_P1_STREAM_CASE '+json.dumps(dict(elements=len(t),frequencyHz=f,gate=gate,difference=delta,
                seconds=row['seconds'],denseTraceMatrixBytes=rr['denseTraceMatrixBytes'],streamTraceMatrixBytes=rr['streamTraceMatrixBytes'])),flush=True)
    gate=all(r['equivalenceGate'] for r in rows)
    summary=dict(gate=gate,angleDeg=a.angle,implementationEquivalenceOnly=True,
        physicalGatesUnchanged=True,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_P1_STREAM_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
