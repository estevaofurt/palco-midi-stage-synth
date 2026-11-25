"""Closed lid cavity and separate open lower half-space diagnostic.
Not a model of the open cabinet; no superposition with existing upper load.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from closed_cavity import assemble,response
from split_radiation import split_load,relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));c=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.array(c['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    mic=np.array(g['microphonesXYZ_m']);height=g['rimTopZ_m']
    def field(xy,unused=None):
        x,y=(2*(xy-poly.min(0))/(poly.max(0)-poly.min(0))-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    # First real-positive Laplace probes, then damp-free harmonic points away from exact poles.
    freqs=[30.,50.,80.,110.,150.];samples=[20+2j*np.pi*f for f in freqs]+[2j*np.pi*f for f in freqs]
    rows=[];outputs=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'closed_cavity.json'
    for n,nz in [(8,3),(12,4),(18,6),(24,8)]:
        m=assemble(poly,n,nz,height,field);Z=[];P=[];metrics=[]
        for s in samples:
            z,p,rep=response(m,s,mic);Z.append(z);P.append(p);metrics.append(rep)
        row=dict(n=n,nz=nz,nodes=len(m['xyz']),tetrahedra=len(m['tet']),volumeM3=m['volume'],
            reciprocity=max(x['reciprocity'] for x in metrics),powerRelative=max(x['powerRelative'] for x in metrics),
            minPassivity=min(x['passivityMinRelative'] for x in metrics),residual=max(x['residual'] for x in metrics),gate=all(x['gate'] for x in metrics))
        rows.append(row);outputs.append((np.array(Z),np.array(P)));print('G3_CAVITY_CASE '+json.dumps(row),flush=True)
    checks=[]
    for (x,u),(y,v) in zip(outputs,outputs[1:]):
        a1=relative(x,y);a2=relative(u,v);checks.append(dict(impedance=a1,pressure=a2,gate=max(a1,a2)<=.05))
    # Mirror the coordinates only for a lower-side diagnostic observer; actual microphones remain upper.
    lower=mic.copy();lower[:,2]=abs(g['rimBottomZ_m'])+.12
    down=split_load(poly,field,freqs,lower,18,28,20)
    fine=split_load(poly,field,freqs,lower,24,36,28)
    lowerRel=relative([x[0] for x in down],[x[0] for x in fine]);lowerObs=relative([x[1] for x in down],[x[1] for x in fine])
    lowerGate=all(x[2]['gate'] for x in fine) and max(lowerRel,lowerObs)<=.05
    summary=dict(cases=rows,convergence=checks,lowerHalfspace=dict(impedanceRelative=lowerRel,pressureRelative=lowerObs,gate=lowerGate),
        gate=all(x['gate'] for x in rows) and checks[-1]['gate'] and lowerGate,
        closedLidOnly=True,openLidReady=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,frequenciesHz=freqs,laplaceRealPerS=[20,0],microphonesXYZ_m=mic.tolist(),
       scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_CAVITY_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'cavity and lower halfspace convergence'
if __name__=='__main__':main()
