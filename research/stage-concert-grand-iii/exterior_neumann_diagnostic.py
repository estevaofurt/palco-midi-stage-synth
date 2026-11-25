"""Direct prescribed-velocity exterior reference on upper envelope.
No lower skirt, finite-thickness lid or full cabinet claim.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,samples,internal,geometry_audit
from exterior_neumann import fit,audit
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
    geo=geometry_audit(surf,ports,center);assert geo['gate'],geo
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    freq=[30.,80.,150.];rows=[];outputs=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'exterior_neumann.json'
    for ns,nt,nh in [(2,5,7),(3,7,9),(4,9,11)]:
        src=internal(surf,ports,center,ns)
        x,n,w,V=samples(surf,ports,nt);xh,nhat,wh,Vh=samples(surf,ports,nh)
        vals=[];reps=[]
        for f in freq:
            k=2*np.pi*f/343.;q,r=fit(x,n,w,V,src,k)
            Z,P,rr=audit(xh,nhat,wh,Vh,src,q,k,far)
            vals.append((Z,P));reps.append(dict(frequencyHz=f,fit=r,audit=rr))
        row=dict(sourceOrder=ns,trainingOrder=nt,heldoutOrder=nh,sources=len(src),
            gate=all(r['audit']['gate'] for r in reps),reports=reps)
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(geometry=geo,cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_NEUMANN_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='reports'},
            **{key:max(r['audit'][key] for r in reps) for key in ('heldoutResidual','reciprocity','powerRelative')}}),flush=True)
    checks=[dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),
        pressure=max(relative(x[1],y[1]) for x,y in zip(a,b))) for a,b in zip(outputs,outputs[1:])]
    gate=rows[-1]['gate'] and max(checks[-1].values())<=.05
    summary=dict(gate=gate,angleDeg=a.angle,convergence=checks,upperEnvelopeOnly=True,lowerSkirtIncluded=False,
        coupledCavityReady=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,geometry=geo,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_NEUMANN_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
