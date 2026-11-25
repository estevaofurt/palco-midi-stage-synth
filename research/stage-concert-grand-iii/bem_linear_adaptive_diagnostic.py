"""Same-mesh P0/P1 comparison; bounded adaptive P1 refinement."""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from exterior_bem import elements,topology
from bem_static_split import fit as fit0
from bem_adaptive import independent as audit0
from bem_linear import COL,CHECK,targets,fit,audit
from bem_linear_adaptive import MARK,indicator,budget_refine
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
    surf,ports,center=envelope(poly,g['rimTopZ_m'],a.angle,3,field);geo=geometry_audit(surf,ports,center)
    assert geo['gate']
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    freq=[30.,80.,150.];rows=[];outputs=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_linear_adaptive.json'
    t,labels,_=triangulate(surf,1)
    for step in range(4):
        # Final row repeats the identical mesh with finer integration.
        order,check=(4,6) if step<3 else (6,8)
        x,n,w,own=targets(t,COL);V=velocities(surf,ports,x,labels[own])
        xx,nn,ww,owner=targets(t,CHECK);Vh=velocities(surf,ports,xx,labels[owner])
        xm,nm,wm,om=targets(t,MARK);Vm=velocities(surf,ports,xm,labels[om])
        x0,n0,w0=elements(t);V0=velocities(surf,ports,x0,labels)
        vals=[];reps=[];scores=np.zeros(len(t))
        for f in freq:
            k=2*np.pi*f/343.
            start=time.perf_counter();q,r=fit(t,V,k,order);solve1=time.perf_counter()-start
            start=time.perf_counter();Z,P,rr=audit(t,q,Vh,k,far,check);audit1=time.perf_counter()-start
            if step<2:scores+=indicator(t,q,Vm,k,check)
            start=time.perf_counter();q0,r0=fit0(t,V0,k,order);solve0=time.perf_counter()-start
            start=time.perf_counter();Z0,P0,rr0=audit0(t,q0,Vh,k,far,check);audit0s=time.perf_counter()-start
            vals.append((Z,P))
            reps.append(dict(frequencyHz=f,P1=rr,P0=rr0,fitP1=r,fitP0=r0,
                difference=dict(impedance=relative(Z,Z0),pressure=relative(P,P0)),
                timingSeconds=dict(fitP1=solve1,auditP1=audit1,fitP0=solve0,auditP0=audit0s)))
        row=dict(step=step,order=order,auditOrder=check,elements=len(t),unknowns=3*len(t),geometry=topology(t),
            gate=all(r['P1']['gate'] and r['fitP1']['collocationResidual']<=1e-8 for r in reps),reports=reps)
        if step<2:
            t,labels,ref=budget_refine(t,labels,scores,[500,850][step]);row['refinement']=ref
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_BEM_P1_ADAPT_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='reports'},
            **{method:{key:max(r[method][key] for r in reps) for key in ('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative')} for method in ('P0','P1')}}),flush=True)
    def compare(a,b):return dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),pressure=max(relative(x[1],y[1]) for x,y in zip(a,b)))
    mesh=compare(outputs[1],outputs[2]);quad=compare(outputs[2],outputs[3])
    gate=rows[-1]['gate'] and max(mesh.values())<=.05 and max(quad.values())<=.05
    summary=dict(gate=gate,angleDeg=a.angle,meshConvergence=mesh,quadratureConvergence=quad,
        sameMeshAndAuditForP0P1=True,independentMarkingAndAudit=True,elementBudget=850,
        upperEnvelopeOnly=True,coupledCavityReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_BEM_P1_ADAPT_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
