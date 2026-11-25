"""Trace observability on the actual cabinet with independent wedge layers.
Only geometric FEM trace projection; no exterior or frequency-domain proof.
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
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    field=lambda x:np.ones((len(x),1));rows=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'layered_wedge.json';base=None
    for k in (1,2,4,8,12):
        m,C0,r=build(poly,40,1,g['rimTopZ_m'],a.angle,field,wedge_layers=k)
        if base is None:base=r
        np.testing.assert_allclose(r['portAreasM2'],base['portAreasM2'],atol=1e-10,rtol=0)
        assert abs(r['wedgeVolumeM3']-base['wedgeVolumeM3'])<=1e-10
        pp,C=ports(m,C0,r,36,canonical=True);panels=[]
        for i,(f,p) in enumerate(zip(m['apertureFaces'],pp)):
            G,nodes=panel_capture(m['xyz'],f,C[:,36*i:36*(i+1)],p)
            panels.append(dict(panel=i,traceNodes=nodes,faces=len(f),degrees=report(G,p)))
        worst={str(n):min(x['degrees'][j]['minimumCapturedEnergy'] for x in panels)
            for j,n in enumerate((3,6,10,15,21,28,36))}
        nulls={str(n):sum(x['degrees'][j]['nearNullModes'] for x in panels)
            for j,n in enumerate((3,6,10,15,21,28,36))}
        row=dict(wedgeLayers=k,planarN=40,nodes=r['nodes'],tetrahedra=r['tetrahedra'],minimumCapture=worst,
            nearNullModes=nulls,panels=panels)
        rows.append(row);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_LAYERED_WEDGE_CASE '+json.dumps({key:v for key,v in row.items() if key!='panels'}),flush=True)
    gate=rows[0]['nearNullModes']['36']>0 and rows[-1]['nearNullModes']['36']==0 and rows[-1]['minimumCapture']['36']>rows[0]['minimumCapture']['36']+.1
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,geometryPreserved=True,traceRecovery=gate,
        finalMinimumCapture=rows[-1]['minimumCapture'],finalNearNullModes=rows[-1]['nearNullModes'],
        fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_LAYERED_WEDGE_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
