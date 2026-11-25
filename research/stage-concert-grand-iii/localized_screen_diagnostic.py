"""Test local enrichment with a fixed independent test space and joint edge B."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry as cabinet
from inclined_lid import build
from lid_exterior import ports,load
from rigid_screen import geometry
from edge_screen import operators
from localized_edge_basis import LocalBasis
from shared_edge_quadrature import assemble
from screen_aperture import correction,observe
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
    b=LocalBasis(local,4);freq=[30.,80.,150.];k=2*np.pi*np.array(freq)/m['c']
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,1.5]])
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'localized_screen.json'
    rows=[];outputs=[];cache={}
    for blocks,outer,inner,bo in [(0,18,34,22),(1,18,34,22),(2,18,34,22),(2,26,48,28)]:
        key=(outer,inner,bo)
        if key not in cache:
            W=operators(b,k,outer,inner)
            B,br=assemble(b,o,A,n,panels,k,bo,True)
            assert br['sharedPairs']==len(panels)
            Z=load(panels,freq,outer,inner,28)
            cache[key]=(W,B,Z,br)
        W,B,Z,br=cache[key];vals=[];reps=[]
        for i,f in enumerate(freq):
            z,Q,r=correction(b,W[i],o,A,n,panels,Z[i][0],f,4,outer,outer,28,
                interaction_block=B[i],subspace=(b.prefix(blocks),b.count))
            pr=observe(b,Q,o,A,n,panels,np.eye(len(z)),far,f,outer)
            vals.append((z,pr));reps.append(dict(frequencyHz=f,**r,freeGate=Z[i][1]['gate']))
        row=dict(blocks=blocks,modes=b.prefix(blocks),testModes=b.count,outer=outer,inner=inner,interactionOrder=bo,
            gate=all(r['gate'] and r['freeGate'] for r in reps),reports=reps)
        for name in ('weakResidual','rawScreenReciprocity','reciprocity','powerRelative'):
            row[name]=max(r[name] for r in reps)
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_LOCAL_EDGE_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    checks=[dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),pressure=max(relative(x[1],y[1]) for x,y in zip(a,b))) for a,b in zip(outputs,outputs[1:])]
    first=cache[(18,34,22)][1];last=cache[(26,48,28)][1]
    interactionChange=relative(first,last)
    gate=rows[-1]['gate'] and interactionChange<=.01 and all(max(v.values())<=.05 for v in checks[-2:])
    summary=dict(gate=gate,angleDeg=a.angle,convergence=checks,interactionChange=interactionChange,
        localWidths=list(b.widths),independentNarrowTestFunctions=True,apertureCouplingReady=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_LOCAL_EDGE_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
