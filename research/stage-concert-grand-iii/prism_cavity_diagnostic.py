"""Closed-cavity independent refinement for 150–300 Hz."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from prism_cavity import build,response
from closed_cavity import assemble,response as tet_response
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    mic=np.asarray(g['microphonesXYZ_m']);height=g['rimTopZ_m']
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    freq=[30.,80.,150.,200.,250.,300.];rows=[];outputs=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'prism_cavity.json'
    def compare(a,b):
        return [dict(frequencyHz=f,impedance=relative(x[0],y[0]),pressure=relative(x[1],y[1])) for f,x,y in zip(freq,a,b)]
    for n,cut in [(30,12),(40,12),(60,12),(80,12),(80,24),(80,48)]:
        m=build(poly,n,height,field);out=[];reps=[]
        for f in freq:
            z,p,r=response(m,2j*np.pi*f,mic,cut)
            out.append((z,p));reps.append(dict(frequencyHz=f,**r))
        row=dict(n=n,nodes=len(m['xy']),cutoff=cut,gate=all(r['gate'] for r in reps),reports=reps)
        rows.append(row);outputs.append(out)
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_PRISM_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    checks=[compare(x,y) for x,y in zip(outputs,outputs[1:])]
    # An independent uncorrected tail calculation checks the magnitude of the approximation.
    m=build(poly,80,height,field);unt=[]
    for f in freq:
        z,p,r=response(m,2j*np.pi*f,mic,96,tail=False)
        unt.append((z,p))
    tailCheck=compare(outputs[-1],unt)
    # Compare both discretizations on the validated low band without claiming 3D convergence at 300 Hz.
    t=assemble(poly,40,14,height,field);reference=[]
    for f in freq[:3]:
        z,p,r=tet_response(t,2j*np.pi*f,mic)
        reference.append((z,p));assert r['gate']
    cross=compare(outputs[-1][:3],reference)
    def good(v):return all(max(q['impedance'],q['pressure'])<=.05 for q in v)
    gate=all(r['gate'] for r in rows) and all(good(v) for v in checks[-3:]) and good(tailCheck) and good(cross)
    summary=dict(gate=gate,convergence=checks,uncorrectedTailCheck=tailCheck,lowBandTetrahedralCrossCheck=cross,
        closedPrismOnly=True,openLidReady=False,cabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_PRISM_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
