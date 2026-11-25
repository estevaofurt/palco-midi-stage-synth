"""Independent tuning/audit of source depths and regularized rank."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,samples,geometry_audit
from envelope_membership import internal_exact
from exterior_neumann import audit
from neumann_regularized import fit,residual
from rigid_scattering import normal_derivative
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
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'neumann_stability.json'
    # Same final quadrature for every row, kept out of all selection.
    held=samples(surf,ports,13);xh,nh,wh,Vh=held
    for ns,nt,nv in [(2,6,7),(3,8,9),(4,10,11)]:
        train=samples(surf,ports,nt);tune=samples(surf,ports,nv)
        choices=[];placement=[]
        for scale in (.68,.85,.94):
            src,rep=internal_exact(poly,g['rimTopZ_m'],a.angle,surf,ports,center,ns,scale)
            placement.append(dict(scale=scale,**rep))
            if rep['gate']:choices.append((scale,src))
        if not choices:raise ValueError('no physically internal source placement')
        vals=[];reps=[]
        for f in freq:
            k=2*np.pi*f/343.;fits=[]
            for scale,src in choices:
                coeff,r=fit(train,tune,src,k);fits.append((r['selected']['score'],scale,src,coeff,r))
            _,scale,src,coeff,r=min(fits,key=lambda t:t[0])
            Z,P,rr=audit(*held,src,coeff,k,far)
            rr['heldoutWorstColumn']=residual(normal_derivative(xh,nh,src,k),coeff,-Vh,wh)['worstColumn']
            rr['gate']=rr['gate'] and rr['heldoutWorstColumn']<=.05
            vals.append((Z,P));reps.append(dict(frequencyHz=f,sourceScale=scale,
                selection=[dict(scale=t[1],**t[4]) for t in fits],audit=rr))
        row=dict(sourceOrder=ns,trainingOrder=nt,tuningOrder=nv,auditOrder=13,sources=len(choices[0][1]),placement=placement,
            gate=all(r['audit']['gate'] for r in reps),reports=reps)
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(geometry=geo,cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_NEUMANN_STABLE_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='reports'},
            'selectedScales':[r['sourceScale'] for r in reps],
            **{key:max(r['audit'][key] for r in reps) for key in ('heldoutResidual','heldoutWorstColumn','reciprocity','powerRelative')}}),flush=True)
    checks=[dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),
        pressure=max(relative(x[1],y[1]) for x,y in zip(a,b))) for a,b in zip(outputs,outputs[1:])]
    gate=rows[-1]['gate'] and max(checks[-1].values())<=.05
    summary=dict(gate=gate,angleDeg=a.angle,convergence=checks,independentTuningAndAudit=True,exactVolumeMembership=True,
        regularizationIsNumericalOnly=True,upperEnvelopeOnly=True,coupledCavityReady=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,geometry=geo,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_NEUMANN_STABLE_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
