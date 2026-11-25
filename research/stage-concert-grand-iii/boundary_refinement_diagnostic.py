"""Independent boundary refinement, with fixed planar interior resolution.
Validate geometry and trace equivalence; do not claim acoustic convergence.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build,properties
from cabinet_geometry import geometry
from inclined_lid import build
from lid_exterior import ports
from acoustic_trace_resolution import panel_capture,describe
from wedge_surface_trace import surface_panels,surface_capture
from nested_acoustic_ports import embedding
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));h=g['rimTopZ_m']
    field=lambda x:np.ones((len(x),1));rows=[];a.out.mkdir(parents=True,exist_ok=True);path=a.out/'boundary_refinement.json'
    for n,b,k in [(40,100,16),(40,120,24),(60,100,16)]:
        m,C0,r=build(poly,n,1,h,a.angle,field,wedge_layers=k,boundary_n=b)
        pp,C=ports(m,C0,r,36,canonical=True);checks=[];cap=[]
        ss=surface_panels(poly,b,a.angle,h,k,36)
        assert len(ss)==len(pp)
        for i,((p,x,f,d),v,ff) in enumerate(zip(ss,pp,m['apertureFaces'])):
            G,nn=surface_capture(p,x,f);H,mm=panel_capture(m['xyz'],ff,C[:,36*i:36*(i+1)],v)
            T,_=embedding([p],[v]);assert nn==mm and len(f)==len(ff)
            checks.append(relative(T.T@G@T,H));cap.append(describe(H)['minimumCapturedEnergy'])
        tri=m['xy'][m['tri']];det=abs(np.linalg.det(tri[:,1:]-tri[:,:1]))
        area=properties(poly)[0];assert abs(det.sum()/2-area)<1e-10
        row=dict(planarN=n,boundaryN=b,wedgeLayers=k,nodes=r['nodes'],tetrahedra=r['tetrahedra'],
            planarNodes=len(m['xy']),traceEquivalence=max(checks),minimumCapture36=min(cap),
            minimumPlanarAreaRatio=float(det.min()/(max(np.ptp(poly,axis=0))/n)**2),
            wedgeVolume=r['wedgeVolumeM3'],portAreas=r['portAreasM2'])
        row['gate']=row['traceEquivalence']<=1e-8 and row['minimumCapture36']>=.95
        rows.append(row);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_BOUNDARY_REFINEMENT_CASE '+json.dumps(row),flush=True)
        del m,C0,C
    summary=dict(gate=all(r['gate'] for r in rows),angleDeg=a.angle,diagnosticOnly=True,
        screeningEnergy=.95,independentBoundaryResolution=True,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_BOUNDARY_REFINEMENT_GATE '+json.dumps(summary),flush=True);assert summary['gate']
if __name__=='__main__':main()
