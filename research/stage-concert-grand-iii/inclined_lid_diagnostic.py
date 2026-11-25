"""Audit 3-D geometry and reciprocal ports, not exterior diffraction."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from inclined_lid import build,matched_fixture
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.array(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    mic=np.array(g['microphonesXYZ_m']);height=g['rimTopZ_m']
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'inclined_lid.json'
    rows=[];outputs=[];freq=[30.,50.,80.,110.,150.]
    for n,nz in [(12,4),(18,6),(24,8),(30,10)]:
        m,C,q=build(poly,n,nz,height,a.angle,field);Y=[];P=[];F=[];reports=[]
        for f in freq:
            y,p,u,rep=matched_fixture(m,C,q,2j*np.pi*f,mic);Y.append(y);P.append(p);F.append(u);reports.append(rep)
        q.update(n=n,nz=nz,responseGate=all(x['gate'] for x in reports),reports=reports)
        rows.append(q);outputs.append((np.array(Y),np.array(P),np.array(F)))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_LID_CASE '+json.dumps({k:v for k,v in q.items() if k!='reports'}),flush=True)
    checks=[]
    for x,y in zip(outputs,outputs[1:]):
        z,p,u=[relative(i,j) for i,j in zip(x,y)]
        checks.append(dict(impedance=z,pressure=p,portFlow=u,gate=max(z,p,u)<=.05))
    summary=dict(angleDeg=a.angle,geometryGate=all(q['gate'] for q in rows),fixtureGate=all(q['responseGate'] for q in rows),
        convergence=checks,gate=all(q['gate'] and q['responseGate'] for q in rows) and checks[-1]['gate'],
        exteriorDiffractionReady=False,openLidReady=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_LID_GATE '+json.dumps(summary),flush=True);assert summary['gate']
if __name__=='__main__':main()
