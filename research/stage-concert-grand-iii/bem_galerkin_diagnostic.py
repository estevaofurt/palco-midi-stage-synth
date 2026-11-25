"""Compare integrated Neumann testing and point collocation on equal meshes."""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from exterior_bem import elements
from bem_static_split import fit as collocate
from bem_galerkin import assembly,fit,weak_impedance,static_audit
from bem_adaptive import independent
from bem_linear import CHECK,targets
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
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_galerkin.json'
    from exterior_bem import samples
    for level,outer,inner in [(0,4,4),(1,4,4),(1,6,5),(2,4,4)]:
        t,labels,gr=triangulate(surf,level);assert abs(gr['volume']-geo['volume'])<1e-10
        x,n,areas=elements(t);V0=velocities(surf,ports,x,labels)
        xx,nn,ww,owner=targets(t,CHECK);Vh=velocities(surf,ports,xx,labels[owner])
        # Degree-two aperture/board fields are projected using a fixed
        # positive order-5 quadrature independent of operator order.
        y,w=samples(t,5);nv=y.shape[1]
        V=velocities(surf,ports,y.reshape(-1,3),np.repeat(labels,nv)).reshape(len(t),nv,-1)
        B=np.einsum('tq,tqm->tm',w,V)
        vals=[];reps=[]
        for f in freq:
            k=2*np.pi*f/343.
            start=time.perf_counter();S,D,ar=assembly(t,k,outer,inner);q,r=fit(S,D,B);elapsed=time.perf_counter()-start
            Z,P,rr=independent(t,q,Vh,k,far,6)
            Zweak=weak_impedance(S,B,q,areas,k)
            q0,r0=collocate(t,V0,k,inner);z0,p0,rr0=independent(t,q0,Vh,k,far,6)
            vals.append((Z,P))
            reps.append(dict(frequencyHz=f,assembly=ar,fit=r,weak=rr,collocation=rr0,
                projectedWorkDifference=relative(Zweak,Z),comparison=dict(impedance=relative(Z,z0),pressure=relative(P,p0)),
                assemblyAndSolveSeconds=elapsed))
        row=dict(level=level,outerOrder=outer,innerOrder=inner,elements=len(t),geometry=gr,
            gate=all(r['weak']['gate'] and r['fit']['weakResidual']<=1e-8 and r['assembly']['singleLayerReciprocity']<=.01 and r['projectedWorkDifference']<=.05 for r in reps),reports=reps)
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_BEM_GALERKIN_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='reports'},
            **{m:{key:max(r[m][key] for r in reps) for key in ('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative')} for m in ('weak','collocation')},
            'singleLayerReciprocity':max(r['assembly']['singleLayerReciprocity'] for r in reps)}),flush=True)
    def compare(a,b):return dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),pressure=max(relative(x[1],y[1]) for x,y in zip(a,b)))
    quad=compare(outputs[1],outputs[2]);mesh=compare(outputs[1],outputs[3])
    gate=rows[-1]['gate'] and max(quad.values())<=.05 and max(mesh.values())<=.05
    summary=dict(gate=gate,angleDeg=a.angle,quadratureConvergence=quad,meshConvergence=mesh,
        p0WeakTesting=True,fullySymmetricCalderon=False,upperEnvelopeOnly=True,coupledCavityReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_BEM_GALERKIN_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
