"""Extend weak P1 adaptive resolution with independent final quadrature.
Keep the same physical fixture, ports and degree-four audit as G3.07t.
"""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from exterior_bem import topology
from bem_linear import CHECK,targets
from bem_oversampled import audit_targets
from bem_p1_stream import audit,derivative
from bem_linear_adaptive import budget_refine
from bem_weak_p1_refined import fit
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
    freq=[30.,80.,150.];rows=[];outputs=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_weak_p1_refined.json'
    t,labels,_=triangulate(surf,1)
    for step,outer,inner,check in [(0,'symmetric5',5,7),(1,'symmetric5',5,7),(2,'symmetric5',5,7),(3,4,6,8),(4,5,7,9)]:
        velocity=lambda x,o:velocities(surf,ports,x,labels[o])
        xa,na,wa,oa=audit_targets(t);Va=velocity(xa,oa)
        xm,nm,wm,om=targets(t,CHECK);Vm=velocity(xm,om)
        vals=[];reps=[];scores=np.zeros(len(t))
        for f in freq:
            k=2*np.pi*f/343.;start=time.perf_counter()
            q,r=fit(t,k,outer,inner,velocity);elapsed=time.perf_counter()-start
            Z,P,rr=audit(t,q,Va,k,far,check)
            if step<2:
                D=derivative(t,xm,nm,om,k,check)
                R=np.sqrt(wm)[:,None]*(D@q+Vm);T=np.sqrt(wm)[:,None]*Vm
                scores+=np.sum(abs(R/np.maximum(np.linalg.norm(T,axis=0),1e-30))**2,axis=1).reshape(len(t),len(CHECK)).sum(1)
            vals.append((Z,P));reps.append(dict(frequencyHz=f,fit=r,audit=rr,fitSeconds=elapsed))
        gr=topology(t);assert gr['gate'] and abs(gr['volume']-geo['volume'])<1e-10
        row=dict(step=step,outerRule=outer,innerOrder=inner,auditOrder=check,elements=len(t),unknowns=3*len(t),
            geometry=gr,gate=all(r['audit']['gate'] and r['fit']['weakResidual']<=1e-8 for r in reps),reports=reps)
        rows.append(row);outputs.append(vals)
        if step<2:t,labels,ref=budget_refine(t,labels,scores,[500,750][step]);row['refinement']=ref
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_BEM_WEAK_REFINED_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='reports'},
            **{key:max(r['audit'][key] for r in reps) for key in ('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative')}}),flush=True)
    def compare(a,b):return dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),pressure=max(relative(x[1],y[1]) for x,y in zip(a,b)))
    mesh=compare(outputs[1],outputs[2]);quad=[compare(outputs[2],outputs[3]),compare(outputs[3],outputs[4])]
    gate=rows[-1]['gate'] and max(mesh.values())<=.05 and all(max(v.values())<=.05 for v in quad)
    summary=dict(gate=gate,angleDeg=a.angle,meshConvergence=mesh,quadratureConvergence=quad,
        sameMeshFinalQuadrature=True,elementBudget=750,streamedDerivative=True,
        upperEnvelopeOnly=True,coupledCavityReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_BEM_WEAK_REFINED_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
