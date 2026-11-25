"""Controlled same-mesh P1 collocation/oversampling comparison."""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from exterior_bem import topology
from bem_linear import COL,CHECK,targets,operators,fit as collocate
from bem_linear_adaptive import budget_refine
from bem_oversampled import TRAIN,AUDIT,audit_targets,fit,audit
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def marking(t,q,V,k,order):
    x,n,w,owner=targets(t,CHECK);_,D=operators(t,x,n,owner,k,order)
    R=np.sqrt(w)[:,None]*(D@q+V);T=np.sqrt(w)[:,None]*V
    return np.sum(abs(R/np.maximum(np.linalg.norm(T,axis=0),1e-30))**2,axis=1).reshape(len(t),len(CHECK)).sum(1)
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
    freq=[30.,80.,150.];rows=[];outputs=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_oversampled.json'
    t,labels,_=triangulate(surf,1)
    for step in range(4):
        order,check=(4,6) if step<3 else (6,8)
        x,n,w,own=targets(t,TRAIN);V=velocities(surf,ports,x,labels[own])
        xc,nc,wc,oc=targets(t,COL);Vc=velocities(surf,ports,xc,labels[oc])
        xa,na,wa,oa=audit_targets(t);Va=velocities(surf,ports,xa,labels[oa])
        xm,nm,wm,om=targets(t,CHECK);Vm=velocities(surf,ports,xm,labels[om])
        vals=[];reps=[];scores=np.zeros(len(t))
        for f in freq:
            k=2*np.pi*f/343.
            start=time.perf_counter();q,r=fit(t,V,k,order);elapsed=time.perf_counter()-start
            Z,P,rr=audit(t,q,Va,k,far,check)
            start=time.perf_counter();qc,rc=collocate(t,Vc,k,order);elapsedC=time.perf_counter()-start
            zc,pc,rrc=audit(t,qc,Va,k,far,check)
            if step<2:scores+=marking(t,q,Vm,k,check)
            vals.append((Z,P));reps.append(dict(frequencyHz=f,fit=r,fitCollocation=rc,oversampled=rr,collocation=rrc,
                comparison=dict(impedance=relative(Z,zc),pressure=relative(P,pc)),
                fitSeconds=dict(oversampled=elapsed,collocation=elapsedC)))
        row=dict(step=step,order=order,auditOrder=check,elements=len(t),unknowns=3*len(t),equations=6*len(t),
            geometry=topology(t),gate=all(r['oversampled']['gate'] and r['fit']['normalEquationResidual']<=1e-8 for r in reps),reports=reps)
        if step<2:t,labels,ref=budget_refine(t,labels,scores,[500,750][step]);row['refinement']=ref
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_BEM_OVER_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='reports'},
            **{m:{key:max(r[m][key] for r in reps) for key in ('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative')} for m in ('oversampled','collocation')}}),flush=True)
    def compare(a,b):return dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),pressure=max(relative(x[1],y[1]) for x,y in zip(a,b)))
    mesh=compare(outputs[1],outputs[2]);quad=compare(outputs[2],outputs[3])
    gate=rows[-1]['gate'] and max(mesh.values())<=.05 and max(quad.values())<=.05
    summary=dict(gate=gate,angleDeg=a.angle,meshConvergence=mesh,quadratureConvergence=quad,
        sameMeshAndAudit=True,independentTrainingMarkingAudit=True,degreeFourAudit=True,
        upperEnvelopeOnly=True,coupledCavityReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_BEM_OVER_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
