"""Compare adaptive P0 surface refinement to a uniform 1024-element reference."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from exterior_bem import elements,heldout,topology
from bem_static_split import fit
from bem_linear import targets,CHECK
from bem_adaptive import refine,mark,indicator,independent
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
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_adaptive.json'
    t,labels,_=triangulate(surf,1)
    for step in range(4):
        if step==3:t,labels,_=triangulate(surf,2)
        x,n,w=elements(t);V=velocities(surf,ports,x,labels)
        xh,nh,wh,own=heldout(t);Vm=velocities(surf,ports,xh,labels[own])
        xx,nn,ww,owner=targets(t,CHECK);Vh=velocities(surf,ports,xx,labels[owner])
        vals=[];reps=[];scores=np.zeros(len(t))
        for f in freq:
            k=2*np.pi*f/343.;q,r=fit(t,V,k,4)
            scores+=indicator(t,q,Vm,k,5)
            Z,P,rr=independent(t,q,Vh,k,far,6)
            vals.append((Z,P));reps.append(dict(frequencyHz=f,fit=r,audit=rr))
        row=dict(step=step,kind='uniformReference' if step==3 else 'adaptive',elements=len(t),
            geometry=topology(t),gate=all(r['audit']['gate'] and r['fit']['collocationResidual']<=1e-8 for r in reps),reports=reps)
        if step<2:
            mask=mark(scores);row['marked']=int(sum(mask));t,labels=refine(t,labels,mask)
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_BEM_ADAPT_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='reports'},
            **{key:max(r['audit'][key] for r in reps) for key in ('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative')}}),flush=True)
    def compare(a,b):return dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),pressure=max(relative(x[1],y[1]) for x,y in zip(a,b)))
    conv=compare(outputs[1],outputs[2]);cross=compare(outputs[2],outputs[3])
    gate=rows[2]['gate'] and max(conv.values())<=.05 and max(cross.values())<=.05
    summary=dict(gate=gate,angleDeg=a.angle,adaptiveConvergence=conv,uniformComparison=cross,
        independentMarkingAndAudit=True,uniformReferenceGate=rows[3]['gate'],upperEnvelopeOnly=True,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_BEM_ADAPT_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
