"""Controlled A/B of balanced and worst-column marking, same mesh budget.
Uses streamed experimental implementation; equivalence tested separately.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from exterior_bem import topology
from bem_linear import COL,targets
from bem_linear_adaptive import MARK,budget_refine
from bem_oversampled import audit_targets
from bem_p1_stream import fit,audit
from bem_p1_priority import scores,contribution
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
    surf,ports,center=envelope(poly,g['rimTopZ_m'],a.angle,3,field)
    geo=geometry_audit(surf,ports,center);assert geo['gate']
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    freq=[30.,80.,150.];rows=[];outputs={}
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_p1_priority.json'
    t0,labels0,_=triangulate(surf,1)
    def evaluate(t,labels,marking):
        gr=topology(t);assert gr['gate'] and abs(gr['volume']-geo['volume'])<1e-10
        x,n,w,o=targets(t,COL);V=velocities(surf,ports,x,labels[o])
        x,n,w,o=targets(t,MARK);Vm=velocities(surf,ports,x,labels[o])
        x,n,w,o=audit_targets(t);Va=velocities(surf,ports,x,labels[o])
        vals=[];reps=[];parts=[]
        for f in freq:
            k=2*np.pi*f/343.;q,r=fit(t,V,k,4);Z,P,rr=audit(t,q,Va,k,far,6)
            if marking:parts.append(contribution(t,q,Vm,k,6))
            vals.append((Z,P));reps.append(dict(frequencyHz=f,fit=r,audit=rr))
        return vals,reps,parts
    def record(policy,step,t,reps,ref=None):
        row=dict(policy=policy,step=step,elements=len(t),unknowns=3*len(t),
            gate=all(r['audit']['gate'] and r['fit']['collocationResidual']<=1e-8 for r in reps),reports=reps)
        if ref is not None:row['refinement']=ref
        rows.append(row)
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_BEM_PRIORITY_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='reports'},
            **{key:max(r['audit'][key] for r in reps) for key in ('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative')}}),flush=True)
    vals,reps,parts=evaluate(t0,labels0,True);record('common',0,t0,reps)
    for policy in ('balanced','worst'):
        t,labels=t0,labels0;cp=parts;out=[vals]
        for step,budget in [(1,500),(2,850)]:
            s,r=scores(cp,policy)
            t,labels,ref=budget_refine(t,labels,s,budget)
            v,reps,cp=evaluate(t,labels,step==1);record(policy,step,t,reps,dict(**ref,**r))
            out.append(v)
        outputs[policy]=out
    def compare(a,b):return dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),pressure=max(relative(x[1],y[1]) for x,y in zip(a,b)))
    results={}
    for policy in ('balanced','worst'):
        last=next(r for r in rows if r['policy']==policy and r['step']==2)
        conv=compare(outputs[policy][1],outputs[policy][2])
        results[policy]=dict(elements=last['elements'],meshConvergence=conv,physicalGate=last['gate'] and max(conv.values())<=.05)
    summary=dict(gate=all(r['physicalGate'] for r in results.values()),angleDeg=a.angle,results=results,
        comparison=compare(outputs['balanced'][-1],outputs['worst'][-1]),sameElementBudget=True,
        sameAuditRule=True,quadratureRefinementIncluded=False,diagnosticOnly=True,radiationReady=False)
    # This study intentionally does not certify either solver without a
    # separate final quadrature refinement; gate only records physical checks here.
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_BEM_PRIORITY_GATE '+json.dumps(summary),flush=True);assert summary['gate']
if __name__=='__main__':main()
