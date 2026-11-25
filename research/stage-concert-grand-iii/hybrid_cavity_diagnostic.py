"""Independent hybrid-vs-tetrahedral acoustic comparison, 30–300 Hz."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from hybrid_cavity import build,response,terminate
from closed_cavity import response as tetra
from lid_exterior import load
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));mic=np.asarray(g['microphonesXYZ_m'])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    freq=[30.,80.,150.,200.,250.,300.];rows=[];outputs=[];cross=[];ext=None
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'hybrid_cavity.json'
    for n,nz in [(18,6),(24,8),(30,10),(40,14)]:
        m=build(poly,n,nz,g['rimTopZ_m'],a.angle,field,6)
        if ext is None:ext=load(m['panels'],freq,22,38,32)
        vals=[];reps=[]
        for f,(ze,er) in zip(freq,ext):
            Z,P,r=response(m,f,mic);y,pr,u,q=terminate(Z,P,ze,4)
            vals.append((y,pr,u));reps.append(dict(frequencyHz=f,interior=r,termination=q,exterior=er))
            if n==24 and f<=150:
                full=dict(m['full'],B=np.column_stack([m['full']['B'],m['Cfull']]))
                z,p,tr=tetra(full,2j*np.pi*f,mic);yt,pt,ut,tt=terminate(z,p,ze,4)
                cross.append(dict(frequencyHz=f,impedance=relative(y,yt),pressure=relative(pr,pt),flow=relative(u,ut),gate=tr['gate'] and tt['gate']))
        row=dict(n=n,nz=nz,gate=all(all(v[k]['gate'] for k in ('interior','termination','exterior')) for v in reps),reports=reps)
        rows.append(row);outputs.append(vals)
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_HYBRID_CASE '+json.dumps({k:v for k,v in row.items() if k!='reports'}),flush=True)
    checks=[[dict(frequencyHz=f,impedance=relative(x[0],y[0]),pressure=relative(x[1],y[1]),flow=relative(x[2],y[2]))
        for f,x,y in zip(freq,a,b)] for a,b in zip(outputs,outputs[1:])]
    good=lambda v:all(max(q[k] for k in ('impedance','pressure','flow'))<=.05 for q in v)
    gate=all(r['gate'] for r in rows) and good(checks[-1]) and good(cross) and all(r['gate'] for r in cross)
    summary=dict(gate=gate,angleDeg=a.angle,convergence=checks,tetrahedralCrossCheck=cross,
        reducedApertureFixture=True,modesPerPanel=6,screenCorrectionIncluded=False,completeExteriorReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,frequenciesHz=freq,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_HYBRID_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
