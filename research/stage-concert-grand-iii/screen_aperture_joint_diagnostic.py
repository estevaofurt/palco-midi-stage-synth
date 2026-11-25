"""Compare joint and tensor coupling, then refine the screen basis.
Experimental free-space correction only; no production promotion.
"""
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
from shared_edge_quadrature import assemble
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
    m,C0,rep=build(poly,18,6,g['rimTopZ_m'],a.angle,field);panels,C=ports(m,C0,rep,3)
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,1.5]])
    b=EdgeBasis(local,9);freq=[30.,80.,150.];k=2*np.pi*np.array(freq)/m['c']
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'screen_aperture_joint.json'
    rows=[];outputs=[];cache={}
    for d,outer,inner,joint in [(4,22,38,False),(4,22,38,True),(6,22,38,True),(8,22,38,True),(8,30,56,True)]:
        key=(outer,inner)
        if key not in cache:
            Ws=operators(b,k,outer,inner)
            free=load(panels,freq,outer,inner,28)
            B,br=assemble(b,o,A,n,panels,k,22,True)
            assert br['sharedPairs']==len(panels)
            cache[key]=(Ws,free,B,br)
        Ws,free,B,br=cache[key];Zs=[];Ps=[];reports=[]
        for i,(f,W,(Z0,fr)) in enumerate(zip(freq,Ws,free)):
            Z,Q,rr=correction(b,W,o,A,n,panels,Z0,f,d,outer,outer,28,
                interaction_block=B[i] if joint else None)
            strict=rr['passivityMinRelative']>=-1e-10 and rr['reciprocity']<=1e-8
            response_report=None
            if strict and rr['gate'] and fr['gate']:
                y,pr,U,response_report=response(m,C,2j*np.pi*f,mic,Z)
                assert np.isfinite(observe(b,Q,o,A,n,panels,U,far,f,outer)).all()
            Zs.append(Z);Ps.append(observe(b,Q,o,A,n,panels,np.eye(len(Z)),far,f,outer))
            reports.append(dict(frequencyHz=f,operator=rr,free=fr,response=response_report,strictCouplingGate=strict))
        row=dict(degree=d,screenModes=(d+1)*(d+2)//2,outer=outer,inner=inner,joint=joint,interaction=br if joint else None,
            gate=all(r['operator']['gate'] and r['free']['gate'] and r['response'] is not None and r['response']['gate'] for r in reports),reports=reports)
        for name in ('weakResidual','rawScreenReciprocity','reciprocity','powerRelative'):
            row[name]=max(r['operator'][name] for r in reports)
        rows.append(row);outputs.append((np.array(Zs),np.array(Ps)))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_JOINT_PORT_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    checks=[dict(impedance=relative(x[0],y[0]),pressureOperator=relative(x[1],y[1])) for x,y in zip(outputs,outputs[1:])]
    gate=rows[-1]['gate'] and all(max(q.values())<=.05 for q in checks[-2:])
    summary=dict(angleDeg=a.angle,gate=gate,convergence=checks,comparisonTypes=['integrationMethod','basis','basis','quadrature'],
        apertureModes=18,screenModes=45,jointInteractionPreviouslyValidated=True,completeExteriorReady=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_JOINT_PORT_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
