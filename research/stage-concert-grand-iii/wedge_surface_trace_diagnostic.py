"""Independent longitudinal/transverse sweep of the actual aperture trace.
Surface-only construction must pass equivalence with the volume mesh.
The sweep is not a convergence claim for the coupled acoustic response.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from inclined_lid import build
from lid_exterior import ports
from acoustic_trace_resolution import panel_capture
from acoustic_trace_resolution_diagnostic import report
from nested_acoustic_ports import embedding
from wedge_surface_trace import surface_panels,surface_capture
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));h=g['rimTopZ_m']
    field=lambda x:np.ones((len(x),1))
    model,C0,r=build(poly,40,1,h,a.angle,field,wedge_layers=8)
    pp,C=ports(model,C0,r,36,canonical=True);checks=[]
    for i,((p,x,f,d),v,ff) in enumerate(zip(surface_panels(poly,40,a.angle,h,8,36),pp,model['apertureFaces'])):
        G,n=surface_capture(p,x,f);H,m=panel_capture(model['xyz'],ff,C[:,36*i:36*(i+1)],v)
        T,_=embedding([p],[v]);assert n==m and len(f)==len(ff)
        checks.append(relative(T.T@G@T,H))
    assert len(checks)==len(pp) and max(checks)<=1e-8
    del model,C0,C
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'wedge_surface_trace.json';rows=[]
    for n,k in [(40,8),(40,12),(40,16),(60,8),(60,12),(60,16),(80,8),(80,12),(80,16),(100,12),(100,16),(120,16),(120,24),(160,24)]:
        panels=[]
        for i,(p,x,f,d) in enumerate(surface_panels(poly,n,a.angle,h,k,36)):
            G,nodes=surface_capture(p,x,f)
            panels.append(dict(panel=i,traceNodes=nodes,faces=len(f),longitudinalSegments=d,degrees=report(G,p)))
        worst={str(n):min(x['degrees'][j]['minimumCapturedEnergy'] for x in panels)
            for j,n in enumerate((3,6,10,15,21,28,36))}
        row=dict(planarN=n,wedgeLayers=k,traceFaces=sum(x['faces'] for x in panels),minimumCapture=worst,panels=panels)
        rows.append(row);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_WEDGE_SURFACE_CASE '+json.dumps({key:v for key,v in row.items() if key!='panels'}),flush=True)
    # 95% energy is a diagnostic screening level, not a physical gate.
    candidates=[dict(planarN=r['planarN'],wedgeLayers=r['wedgeLayers'],traceFaces=r['traceFaces'],minimumCapture=r['minimumCapture'])
        for r in rows if r['minimumCapture']['36']>=.95]
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,volumeTraceEquivalence=max(checks),
        screeningMinimumEnergy=.95,screeningCandidates=candidates,
        maximumCapture36=max(r['minimumCapture']['36'] for r in rows),
        fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_WEDGE_SURFACE_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
