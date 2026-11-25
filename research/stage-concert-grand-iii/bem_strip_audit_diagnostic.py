"""Repeat the matched strip geometry, then audit at independent frequencies.
Same density for every quadrature comparison. No solver promotion.
"""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from bem_p1_static_moments import fit,operators
from bem_edge_localization import localize,inventory
from bem_edge_matched import matched
from bem_edge_audit import edge_samples
from bem_power_partition import integrate
from bem_linear import far_gram,observe
from bem_mesh_guard import signature,require_same_mesh
from bem_strip_audit import audit_change,reliable,physical
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def digest(q):return hashlib.sha256(np.ascontiguousarray(q).tobytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);p.add_argument('--frequency',type=float,choices=[30.,80.,150.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    surf,ports,center=envelope(poly,g['rimTopZ_m'],a.angle,3,field);geo=geometry_audit(surf,ports,center);assert geo['gate']
    t,l,top=triangulate(surf,1);assert abs(top['volume']-geo['volume'])<=1e-10
    v=lambda x,o:velocities(surf,ports,x,l[o])
    k0=2*np.pi*30/343.;q0,r0=fit(t,k0,5,6,v);assert r0['weakResidual']<=1e-8
    kinds=[s['kind'] for s in surf];classes,_=inventory(t,l,kinds)
    mark=localize(t,l,kinds,q0,v,k0,5,6)
    _,strip,match=matched(t,l,np.asarray(mark['sectorIndicator']),np.isin(classes,['crease','crease-port-transition']),448)
    t,l,refinement=strip;sig=signature(t,l)
    # Reproduce the element count of the previously compared strip mesh.
    assert len(t)==(444 if a.angle==30 else 446)
    v=lambda x,o:velocities(surf,ports,x,l[o]);k=2*np.pi*a.frequency/343.
    q,r=fit(t,k,5,6,v);assert r['weakResidual']<=1e-8
    qs=digest(q);a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_strip_audit.json';rows=[];mat=[]
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    F0=1.204*343*k*k/(4*np.pi)*far_gram(t,q,k,order=28,surface_order=8)
    F=1.204*343*k*k/(4*np.pi)*far_gram(t,q,k,order=36,surface_order=10)
    farChange=relative(F0,F)
    for outer,inner in [(6,8),(8,8),(8,10)]:
        require_same_mesh(sig,signature(t,l));assert digest(q)==qs
        start=time.perf_counter();P,C,ar=integrate(t,q,v,k,outer,inner,operator=operators,sample_rule=edge_samples)
        rep=physical(ar,P,C,F)
        row=dict(frequencyHz=a.frequency,elements=len(t),meshSha256=sig,densitySha256=qs,
            outerOrder=outer,innerOrder=inner,audit=rep,seconds=time.perf_counter()-start)
        rows.append(row);mat.append((P,C))
        path.write_text(json.dumps(dict(cases=rows,complete=False,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
        print('G3_STRIP_AUDIT_CASE '+json.dumps(row),flush=True)
    target=audit_change(rows[0]['audit'],rows[1]['audit'],*mat[0],*mat[1])
    source=audit_change(rows[1]['audit'],rows[2]['audit'],*mat[1],*mat[2])
    gate=bool(reliable(target) and reliable(source) and farChange<=.01 and all(x['audit']['partitionClosure']<=1e-10 for x in rows))
    np.savez_compressed(a.out/'strip_matrices.npz',triangles=t,labels=l,density=q,prescribed=mat[-1][0],computed=mat[-1][1],radiation=F,
        pressure=1j*1.204*343*k*observe(t,q,far,k,10))
    summary=dict(gate=gate,angleDeg=a.angle,frequencyHz=a.frequency,diagnosticOnly=True,meshSha256=sig,densitySha256=qs,
        fixedMesh=True,fixedDensity=True,targetConvergence=target,sourceConvergence=source,farConvergence=farChange,
        refinement=refinement,physicalGate=rows[-1]['audit']['physicalGate'],solverApproved=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_STRIP_AUDIT_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
