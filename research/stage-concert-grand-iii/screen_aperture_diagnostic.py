"""Experimental actual shared-edge geometry, never promote as complete radiation."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry as cabinet
from inclined_lid import build
from lid_exterior import ports,load
from aperture_modes import response
from rigid_screen import geometry
from edge_screen import EdgeBasis,operators
from screen_aperture import correction,observe
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=cabinet(poly,l,read('cabinet_geometry_hypothesis.json'))
    local,o,A,n=geometry(poly,a.angle,g['rimTopZ_m']);mic=np.array(g['microphonesXYZ_m'])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    m,C0,rep=build(poly,18,6,g['rimTopZ_m'],a.angle,field)
    panels,C=ports(m,C0,rep,3)
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,1.5]])
    b=EdgeBasis(local,5);freq=[30.,80.,150.];k=2*np.pi*np.array(freq)/343.
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'screen_aperture.json'
    rows=[];outputs=[]
    for outer,inner in [(10,18),(16,28),(22,38)]:
        Ws=operators(b,k,outer,inner);free=load(panels,freq,outer,inner,24)
        Zs=[];Ps=[];reports=[]
        for f,W,(Z0,fr) in zip(freq,Ws,free):
            Z,Q,rr=correction(b,W,o,A,n,panels,Z0,f,4,outer,outer,28)
            # Do not bypass the strict physical acceptance of aperture_modes.response.
            pass_gate=rr['passivityMinRelative']>=-1e-10 and rr['reciprocity']<=1e-8
            response_report=None
            if pass_gate and rr['gate'] and fr['gate']:
                y,pr,U,response_report=response(m,C,2j*np.pi*f,mic,Z)
                P=observe(b,Q,o,A,n,panels,U,far,f,outer)
            else:
                # Still preserve operator convergence at failed resolutions.
                P=observe(b,Q,o,A,n,panels,np.eye(len(Z)),far,f,outer)
            Zs.append(Z);Ps.append(observe(b,Q,o,A,n,panels,np.eye(len(Z)),far,f,outer))
            reports.append(dict(frequencyHz=f,operator=rr,free=fr,response=response_report,strictCouplingGate=pass_gate))
        row=dict(outer=outer,inner=inner,gate=all(r['operator']['gate'] and r['free']['gate'] and r['response'] is not None and r['response']['gate'] for r in reports),reports=reports)
        rows.append(row);outputs.append((np.array(Zs),np.array(Ps)))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_SCREEN_PORT_CASE '+json.dumps(dict(outer=outer,inner=inner,gate=row['gate'],maxPowerError=max(r['operator']['powerRelative'] for r in reports),maxWeakResidual=max(r['operator']['weakResidual'] for r in reports),maxReciprocity=max(r['operator']['reciprocity'] for r in reports))),flush=True)
    checks=[dict(impedance=relative(x[0],y[0]),pressureOperator=relative(x[1],y[1])) for x,y in zip(outputs,outputs[1:])]
    gate=rows[-1]['gate'] and max(checks[-1].values())<=.05
    summary=dict(angleDeg=a.angle,gate=gate,convergence=checks,apertureModes=18,screenModes=15,sharedEdgeQuadratureValidated=gate,completeExteriorReady=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_SCREEN_PORT_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
