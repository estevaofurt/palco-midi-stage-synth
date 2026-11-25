"""Independent reciprocal pair quadrature versus directional integration."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build,properties
from cabinet_geometry import geometry as cabinet
from rigid_screen import geometry
from edge_screen import EdgeBasis,operators as directional,solve
from joint_screen_operator import operators
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=cabinet(poly,l,read('cabinet_geometry_hypothesis.json'))
    local,o,A,n=geometry(poly,a.angle,g['rimTopZ_m']);_,center,_=properties(local);mid=o+center@A.T
    # Fixed cabinet-frame offsets, not a co-rotating source/observer fixture.
    h=g['rimTopZ_m'];cxy=poly.mean(0);sx,sy=cxy
    sources=np.array([[sx,sy,h-.45],[sx-.25,sy,h-.55],[sx,sy+.3,h+2.]])
    observers=np.array([[sx,sy,h+2.5],[sx,sy,h-1.5],[sx+2.,sy,h+1.]])
    freq=[30.,80.,150.];k=2*np.pi*np.array(freq)/343.
    b=EdgeBasis(local,9)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'joint_screen.json'
    rows=[];outputs=[]
    for order in (8,12,16,20):
        W,qr=operators(b,k,order);vals=[];reps=[]
        for f,kl,w in zip(freq,k,W):
            p,z,r=solve(b,w,kl,o,A,n,sources,observers,8,28)
            vals.append((p,z));reps.append(dict(frequencyHz=f,**r))
        row=dict(order=order,quadrature=qr,gate=qr['measureRelative']<=1e-9 and all(r['gate'] for r in reps),reports=reps)
        rows.append(row);outputs.append((W,vals))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_PAIR_SCREEN_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='reports'},'weakResidual':max(r['weakResidual'] for r in reps)}),flush=True)
    checks=[dict(operator=relative(x[0],y[0]),pressure=max(relative(a[0],b[0]) for a,b in zip(x[1],y[1])),
        impedance=max(relative(a[1],b[1]) for a,b in zip(x[1],y[1]))) for x,y in zip(outputs,outputs[1:])]
    D=directional(b,k,22,38);W=outputs[-1][0]
    audit=dict(directionalAsymmetry=max(relative(d,d.T) for d in D),independentOperator=relative(D,W))
    gate=rows[-1]['gate'] and max(checks[-1].values())<=.05 and audit['independentOperator']<=.05
    summary=dict(gate=gate,angleDeg=a.angle,convergence=checks,independentAudit=audit,
        reciprocityByPairedIntegration=True,isolatedScreenOnly=True,apertureCouplingReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_PAIR_SCREEN_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
