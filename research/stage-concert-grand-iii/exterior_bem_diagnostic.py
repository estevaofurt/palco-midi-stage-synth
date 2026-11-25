"""Direct exterior BEM on upper envelope, independent boundary/power audits."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from exterior_bem import elements,heldout,fit,audit
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
    freq=[30.,80.,150.];rows=[];outputs=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'exterior_bem.json'
    for level,order,check in [(0,5,7),(1,5,7),(2,5,7),(2,8,10)]:
        t,labels,gr=triangulate(surf,level)
        assert abs(gr['volume']-geo['volume'])<1e-10
        x,n,w=elements(t);V=velocities(surf,ports,x,labels)
        xx,nn,ww,owner=heldout(t);Vh=velocities(surf,ports,xx,labels[owner])
        vals=[];reps=[]
        for f in freq:
            k=2*np.pi*f/343.;q,r=fit(t,V,k,order)
            Z,P,rr=audit(t,q,Vh,k,far,check)
            vals.append((Z,P));reps.append(dict(frequencyHz=f,fit=r,audit=rr))
        row=dict(level=level,order=order,auditOrder=check,elements=len(t),geometry=gr,
            gate=all(r['audit']['gate'] and r['fit']['collocationResidual']<=1e-8 for r in reps),reports=reps)
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_BEM_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='reports'},
            **{key:max(r['audit'][key] for r in reps) for key in ('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative')}}),flush=True)
    checks=[dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),
        pressure=max(relative(x[1],y[1]) for x,y in zip(a,b))) for a,b in zip(outputs,outputs[1:])]
    gate=rows[-1]['gate'] and all(max(v.values())<=.05 for v in checks[-2:])
    summary=dict(gate=gate,angleDeg=a.angle,convergence=checks,upperEnvelopeOnly=True,
        p0Collocation=True,combinedFieldIncluded=False,coupledCavityReady=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_BEM_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
