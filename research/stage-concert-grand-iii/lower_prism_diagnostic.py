"""Validate the lower domain independently of any unapproved exterior solver."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build,properties
from cabinet_geometry import geometry
from lower_prism import build,response
from recess_envelope import build as envelope
from bem_envelope import triangulate
from closed_cavity import assemble,response as tetra_response
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    h=-g['rimBottomZ_m'];_,center,_=properties(poly)
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    points=np.array([np.r_[center,-h*.25],np.r_[center,-h*.75]])
    freq=[30.,80.,150.,200.,250.,300.];rows=[];outputs=[];geos=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'lower_prism.json'
    for angle in (30,55):
        s,p,c,r=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],angle,6,field,10)
        t,labels,gr=triangulate(s,1);assert abs(gr['volume']-r['volume'])<=1e-10
        geos.append(dict(angleDeg=angle,geometry=r,topology=gr,elements=len(t)))
    for n in (18,24,30,40,50,60,72):
        m=build(poly,n,h,field,10);vals=[];reps=[]
        poles=(m['c']/(2*np.pi))*np.sqrt(np.maximum(m['lam'],0.))
        for f in freq:
            Z,P,r=response(m,2j*np.pi*f,points);vals.append((Z,P));reps.append(dict(frequencyHz=f,nearestPlanarPoleHz=float(poles[np.argmin(abs(poles-f))]),nearestPlanarPoleDistanceHz=float(min(abs(poles-f))),**r))
        outputs.append(vals);rows.append(dict(n=n,gate=all(r['gate'] for r in reps),reports=reps))
        rows[-1]['planarNodes']=len(m['xy'])
        if len(outputs)>1:
            rows[-1]['changesByFrequency']=[dict(frequencyHz=f,impedance=relative(x[0],y[0]),pressure=relative(x[1],y[1])) for f,x,y in zip(freq,outputs[-2],outputs[-1])]
        path.write_text(json.dumps(dict(cases=rows,geometry=geos,complete=False),indent=2,allow_nan=False))
        print('G3_LOWER_PRISM_CASE '+json.dumps(rows[-1]),flush=True)
    def compare(a,b):
        return dict(impedance=max(relative(x[0],y[0]) for x,y in zip(a,b)),pressure=max(relative(x[1],y[1]) for x,y in zip(a,b)))
    mesh=compare(outputs[-2],outputs[-1]);previous=compare(outputs[-3],outputs[-2])
    # Independent tetrahedral model with board and mouth trace columns on
    # opposite horizontal faces. No shared exact vertical propagation.
    m=build(poly,24,h,field,10);t=assemble(poly,24,10,h,m['combined']);N=len(t['xy']);nb=m['nb']
    B=t['B'].copy();B[-N:,nb:]=B[:N,nb:];B[:N,nb:]=0.;t['B']=B
    pp=points.copy();pp[:,2]*=-1;tet=[]
    for f in freq:
        Z,P,r=tetra_response(t,2j*np.pi*f,pp);assert r['gate'];tet.append((Z,P))
    cross=compare(outputs[1],tet)
    gate=all(r['gate'] for r in rows) and max(mesh.values())<=.05 and max(previous.values())<=.05 and max(cross.values())<=.05
    summary=dict(gate=gate,meshConvergence=mesh,previousMeshConvergence=previous,tetrahedralComparison=cross,perFrequencyConvergence=rows[-1]['changesByFrequency'],depthM=h,
        boardFields=4,mouthModes=10,artificialLowerMouth=True,lowerDomainOnly=True,
        lowerExteriorReady=False,coupledCavityReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,geometry=geos,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_LOWER_PRISM_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
