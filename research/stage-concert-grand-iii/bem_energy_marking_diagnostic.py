"""A/B energy-aware marking of analytic-moment weak P1.
Same initial mesh, equal refinement budget and independent degree-four audit.
Final repeat uses a finer weak quadrature. No solver promotion.
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
from bem_oversampled import audit_targets
from bem_p1_static_moments import fit,audit,operators
from bem_linear_adaptive import budget_refine
from bem_energy_marking import local_terms,score
from bem_power_partition import integrate,partition
from bem_linear import far_gram
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
    freq=[30.,80.,150.];rows=[];a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_energy_marking.json'
    t0,l0,_=triangulate(surf,1)
    def evaluate(t,labels,outer,inner,check,marking,energy_audit=False):
        gr=topology(t);assert gr['gate'] and abs(gr['volume']-geo['volume'])<1e-10
        v=lambda x,o:velocities(surf,ports,x,labels[o])
        xa,na,wa,oa=audit_targets(t);Va=v(xa,oa)
        vals=[];reps=[];parts=[]
        for f in freq:
            k=2*np.pi*f/343.;q,r=fit(t,k,outer,inner,v);Z,P,rr=audit(t,q,Va,k,far,check)
            rep=dict(frequencyHz=f,fit=r,audit=rr)
            if marking:
                R,E,lr=local_terms(t,q,v,k,check);assert lr['localWorkClosure']<=1e-10
                parts.append((R,E));rep['localIndicator']=lr
            if energy_audit:
                # Separate tensor work rule, not the marking or final degree-four
                # audit. Same analytic kernel as the solved density.
                F=1.204*343*k*k/(4*np.pi)*far_gram(t,q,k,order=24,surface_order=check)
                C,W,ar=integrate(t,q,v,k,6,check,operator=operators)
                rep['powerPartition']=dict(**ar,**partition(C,W,F))
            vals.append((Z,P));reps.append(rep)
        return vals,reps,parts
    def record(policy,step,t,reps,ref=None):
        row=dict(policy=policy,step=step,elements=len(t),unknowns=3*len(t),
            gate=all(r['audit']['gate'] and r['fit']['weakResidual']<=1e-8 for r in reps),reports=reps)
        if ref is not None:row['refinement']=ref
        rows.append(row);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_BEM_ENERGY_MARK_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='reports'},
            **{key:max(r['audit'][key] for r in reps) for key in ('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative')},
            **({'powerPartition':[r['powerPartition'] for r in reps]} if all('powerPartition' in r for r in reps) else {})}),flush=True)
    vals,reps,parts=evaluate(t0,l0,4,5,7,True);record('common',0,t0,reps)
    out={}
    for policy in ('residual','combined'):
        t,labels,ref=budget_refine(t0,l0,score(parts,policy),500)
        v,reps,_=evaluate(t,labels,4,5,7,False);record(policy,1,t,reps,ref)
        vf,reps,_=evaluate(t,labels,5,6,8,False,True);record(policy,2,t,reps)
        out[policy]=[vals,v,vf]
    def compare(a,b):return dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),pressure=max(relative(x[1],y[1]) for x,y in zip(a,b)))
    result={}
    for policy in out:
        row=next(r for r in rows if r['policy']==policy and r['step']==2)
        mesh=compare(out[policy][0],out[policy][1]);quad=compare(out[policy][1],out[policy][2])
        result[policy]=dict(elements=row['elements'],meshConvergence=mesh,quadratureConvergence=quad,
            physicalGate=row['gate'] and max(mesh.values())<=.05 and max(quad.values())<=.05)
    summary=dict(gate=all(r['physicalGate'] for r in result.values()),angleDeg=a.angle,results=result,
        comparison=compare(out['residual'][-1],out['combined'][-1]),sameElementBudget=True,
        energyPartitionDiagnosticOnly=True,upperEnvelopeOnly=True,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_BEM_ENERGY_MARK_GATE '+json.dumps(summary),flush=True);assert summary['gate']
if __name__=='__main__':main()
