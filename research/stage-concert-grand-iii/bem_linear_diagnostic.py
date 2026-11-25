"""P1 comparison to P0 at equal triangle counts, independent heldout audit."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from exterior_bem import elements,heldout
from bem_static_split import fit as fit0,audit as audit0
from bem_linear import COL,CHECK,targets,fit,audit
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
    freq=[30.,80.,150.];rows=[];outputs=[];cross=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_linear.json'
    for level,order,check in [(0,4,6),(1,4,6),(1,7,9),(2,4,6)]:
        t,labels,gr=triangulate(surf,level);assert abs(gr['volume']-geo['volume'])<1e-10
        x,n,w,own=targets(t,COL);V=velocities(surf,ports,x,labels[own])
        xx,nn,ww,owner=targets(t,CHECK);Vh=velocities(surf,ports,xx,labels[owner])
        vals=[];reps=[]
        for f in freq:
            k=2*np.pi*f/343.;q,r=fit(t,V,k,order);Z,P,rr=audit(t,q,Vh,k,far,check)
            vals.append((Z,P));reps.append(dict(frequencyHz=f,fit=r,audit=rr))
            if level<=1 and order==4:
                x0,n0,w0=elements(t);v0=velocities(surf,ports,x0,labels)
                xh,nh,wh,ow=heldout(t);vh=velocities(surf,ports,xh,labels[ow])
                q0,_=fit0(t,v0,k,order);z0,p0,r0=audit0(t,q0,vh,k,far,check)
                cross.append(dict(level=level,frequencyHz=f,impedance=relative(Z,z0),pressure=relative(P,p0),P0=r0,P1=rr))
        row=dict(level=level,order=order,auditOrder=check,elements=len(t),unknowns=3*len(t),
            gate=all(r['audit']['gate'] and r['fit']['collocationResidual']<=1e-8 for r in reps),reports=reps)
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,p0Comparison=cross,complete=False),indent=2,allow_nan=False))
        print('G3_BEM_LINEAR_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='reports'},
            **{key:max(r['audit'][key] for r in reps) for key in ('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative')}}),flush=True)
    def compare(a,b):return dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),pressure=max(relative(x[1],y[1]) for x,y in zip(a,b)))
    quad=compare(outputs[1],outputs[2]);mesh=compare(outputs[1],outputs[3])
    gate=rows[-1]['gate'] and max(quad.values())<=.05 and max(mesh.values())<=.05
    summary=dict(gate=gate,angleDeg=a.angle,meshConvergence=mesh,quadratureConvergence=quad,
        discontinuousP1=True,upperEnvelopeOnly=True,coupledCavityReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,p0Comparison=cross,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_BEM_LINEAR_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
