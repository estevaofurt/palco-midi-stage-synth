"""Fixed-space localized screen diagnostic using experimental pair quadrature.
Do not promote the new operator or substitute the existing weak residual gate.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry as cabinet
from inclined_lid import build
from lid_exterior import ports,load
from rigid_screen import geometry
from localized_edge_basis import LocalBasis
from joint_screen_operator import operators
from shared_edge_quadrature import assemble
from screen_aperture import correction,observe
from screen_residual_energy import audit
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=cabinet(poly,l,read('cabinet_geometry_hypothesis.json'))
    local,o,A,n=geometry(poly,a.angle,g['rimTopZ_m'])
    m,C0,rep=build(poly,12,4,g['rimTopZ_m'],a.angle,lambda x:np.ones((len(x),1)))
    panels,_=ports(m,C0,rep,3,canonical=True)
    b=LocalBasis(local,4,(.25,.08,.025,.008),order=56)
    freq=[30.,80.,150.];ks=2*np.pi*np.array(freq)/m['c']
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,1.5]])
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'localized_pair.json'
    rows=[];outputs=[];last=None
    for order,bo,outer,inner in [(12,24,18,34),(16,30,22,38),(20,36,26,48)]:
        W,qr=operators(b,np.r_[0.,ks],order)
        B,br=assemble(b,o,A,n,panels,ks,bo,True)
        assert br['sharedPairs']==len(panels)
        Z=load(panels,freq,outer,inner,28)
        matChange=None if last is None else dict(operator=relative(last[0],W),interaction=relative(last[1],B))
        last=(W,B);step=[];vals=[]
        for blocks in (0,1,2,3):
            N=b.prefix(blocks);reps=[];out=[]
            for i,f in enumerate(freq):
                z,Q,r=correction(b,W[i+1],o,A,n,panels,Z[i][0],f,4,outer,outer,28,
                    interaction_block=B[i],subspace=(N,b.count))
                e=audit(W[i+1],B[i],Q,W[0])
                pr=observe(b,Q,o,A,n,panels,np.eye(len(z)),far,f,outer)
                reps.append(dict(frequencyHz=f,operator=r,energy=e,freeGate=Z[i][1]['gate']))
                out.append((z,pr))
            row=dict(order=order,interactionOrder=bo,blocks=blocks,modes=N,testModes=b.count,
                gate=all(v['operator']['gate'] and v['freeGate'] for v in reps),reports=reps)
            for key in ('weakRelative','dualStaticRelative','enrichedSolutionRelative','enrichedResidual'):
                row[key]=max(v['energy'][key] for v in reps)
            row['rawScreenReciprocity']=max(v['operator']['rawScreenReciprocity'] for v in reps)
            step.append(row);vals.append(out)
            print('G3_LOCAL_PAIR_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
        rows.append(dict(order=order,quadrature=qr,interaction=br,matrixChange=matChange,cases=step));outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
    def compare(a,b):
        return dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),pressure=max(relative(x[1],y[1]) for x,y in zip(a,b)))
    modal=[compare(x,y) for x,y in zip(outputs[-1],outputs[-1][1:])]
    quad=[compare(x[-1],y[-1]) for x,y in zip(outputs,outputs[1:])]
    last=rows[-1];gate=last['cases'][-1]['gate'] and last['quadrature']['measureRelative']<=1e-9
    gate=gate and last['matrixChange']['operator']<=.05 and last['matrixChange']['interaction']<=.01
    gate=gate and max(modal[-1].values())<=.05 and max(quad[-1].values())<=.05
    summary=dict(gate=gate,angleDeg=a.angle,modalConvergence=modal,quadratureConvergence=quad,
        matrixConvergence=last['matrixChange'],staticEnergyDiagnosticOnly=True,weakResidualGateUnchanged=True,
        pairOperatorExperimental=True,apertureCouplingReady=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_LOCAL_PAIR_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
