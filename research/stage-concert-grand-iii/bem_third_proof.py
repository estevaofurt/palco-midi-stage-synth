"""Third-generation 80 Hz BEM candidate, same fit and audit rules as parent."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import velocities
from bem_third_strip_replay import validate_source
from bem_prepared_operator import PreparedOperator
from bem_candidate_guard import validate_candidate
from bem_weak_blocked import fit
from bem_power_partition import integrate
from bem_edge_audit import edge_samples
from bem_linear import far_gram,observe
from bem_strip_audit import physical,audit_change,reliable
from bem_mesh_guard import signature
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def require_refinement(doc,base,angle,sha,budget):
    s=doc.get('summary',{})
    expected=dict(gate=True,angleDeg=angle,frequencyHz=80.,diagnosticOnly=True,fixedDensity=True,
        sourceElements={30:628,55:626}[angle],sourceMeshSha256=base['summary']['meshSha256'],
        sourceDensitySha256=base['summary']['densitySha256'],solverApproved=False,radiationReady=False)
    if doc.get('scaleSha256')!=sha or any(s.get(k)!=v for k,v in expected.items()):
        raise ValueError('third-generation refinement provenance mismatch')
    if s.get('convergence',{}).get('gate') is not True or max(s['againstArchivedAudit'].values())>.05:
        raise ValueError('unreliable residual localization')
    rows=[x for x in s['candidateMeshes'] if x.get('elementBudget')==budget]
    if len(rows)!=1 or rows[0].get('file')!=f'third_strip_{budget}.npz' or rows[0].get('geometryAudit',{}).get('gate') is not True:
        raise ValueError('missing audited candidate')
    return rows[0]

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);p.add_argument('--budget',type=int,choices=[850,1050],default=850);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    base=json.loads((a.archive/'bem_candidate.json').read_text())
    with np.load(a.archive/'candidate_matrices.npz',allow_pickle=False) as z:arrays={k:z[k] for k in ('triangles','labels','density','prescribed','computed','radiation','pressure')}
    ar=validate_source(base,arrays,a.angle,sha)
    candidate=json.loads((a.candidate/'bem_third_strip_replay.json').read_text())
    entry=require_refinement(candidate,base,a.angle,sha,a.budget)
    with np.load(a.candidate/entry['file'],allow_pickle=False) as z:t,l,parents=(z[k] for k in ('triangles','labels','parents'))
    guard=validate_candidate(arrays['triangles'],arrays['labels'],t,l,parents,entry,a.budget)
    ll=layout_build(sc,read('layout_hypothesis.json'));co=contour_build(ll,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(co['contourXY_m']);g=geometry(poly,ll,read('cabinet_geometry_hypothesis.json'))
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    surf,ports,center=envelope(poly,g['rimTopZ_m'],a.angle,3,field);assert geometry_audit(surf,ports,center)['gate']
    v=lambda x,o:velocities(surf,ports,x,l[o]);k=2*np.pi*80/343.
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_third_proof.json';rows=[];mat=[]
    start=time.perf_counter();q,r=fit(t,k,5,6,v,block=32,reuse_sources=True);assert r['weakResidual']<=1e-8
    sig=signature(t,l);qs=hashlib.sha256(np.ascontiguousarray(q).tobytes()).hexdigest()
    print('G3_THIRD_PROOF_FIT '+json.dumps(dict(elements=len(t),seconds=time.perf_counter()-start,**r)),flush=True)
    F0=1.204*343*k*k/(4*np.pi)*far_gram(t,q,k,order=28,surface_order=8)
    F=1.204*343*k*k/(4*np.pi)*far_gram(t,q,k,order=36,surface_order=10)
    prepared={order:PreparedOperator(t,order) for order in (8,10)}
    for outer,inner in [(6,8),(8,8),(8,10)]:
        assert signature(t,l)==sig and hashlib.sha256(np.ascontiguousarray(q).tobytes()).hexdigest()==qs
        P,C,aa=integrate(t,q,v,k,outer,inner,operator=prepared[inner],sample_rule=edge_samples)
        rep=physical(aa,P,C,F);row=dict(frequencyHz=80.,elements=len(t),meshSha256=sig,densitySha256=qs,outerOrder=outer,innerOrder=inner,audit=rep)
        rows.append(row);mat.append((P,C))
        path.write_text(json.dumps(dict(cases=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_THIRD_PROOF_CASE '+json.dumps(row),flush=True)
    target=audit_change(rows[0]['audit'],rows[1]['audit'],*mat[0],*mat[1]);source=audit_change(rows[1]['audit'],rows[2]['audit'],*mat[1],*mat[2])
    farChange=relative(F0,F);gate=bool(reliable(target) and reliable(source) and farChange<=.01 and all(x['audit']['partitionClosure']<=1e-10 for x in rows))
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    pf=1j*1.204*343*k*observe(t,q,far,k,10)
    last=rows[-1]['audit'];changes={k:dict(baseline=ar[k],candidate=last[k]) for k in ('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative','passivityMinRelative')}
    summary=dict(gate=gate,angleDeg=a.angle,frequencyHz=80.,diagnosticOnly=True,geometry=guard,
        sourceElements=len(arrays['triangles']),elements=len(t),elementBudget=a.budget,preparedSources=True,
        sourceMeshSha256=base['summary']['meshSha256'],sourceDensitySha256=base['summary']['densitySha256'],
        meshSha256=sig,densitySha256=qs,targetConvergence=target,sourceConvergence=source,farConvergence=farChange,
        changes=changes,impedanceChange=relative(arrays['prescribed'],mat[-1][0]),pressureChange=relative(arrays['pressure'],pf),
        physicalGate=last['physicalGate'],solverApproved=False,radiationReady=False)
    np.savez_compressed(a.out/'third_proof_matrices.npz',triangles=t,labels=l,density=q,prescribed=mat[-1][0],computed=mat[-1][1],radiation=F,pressure=pf)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_THIRD_PROOF_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
