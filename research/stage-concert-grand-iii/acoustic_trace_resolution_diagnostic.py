"""Check spatial observability before attributing modal-flow differences
solely to polynomial order. Do not assemble any exterior load.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from inclined_lid import build as inclined_build
from lid_exterior import ports
from lower_prism import mouth_panel
from prism_cavity import build as prism_build
from nested_acoustic_ports import embedding,reduced_panels
from acoustic_trace_resolution import panel_capture,capture,describe
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def report(G,p):
    result=[]
    for n in (3,6,10,15,21,28,36):
        lo=reduced_panels([p],[n]);T,_=embedding([p],lo)
        result.append(describe(G,T))
    return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    field=lambda x:np.ones((len(x),1))
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'acoustic_trace_resolution.json';rows=[]
    def record(row):
        rows.append(row);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_TRACE_RESOLUTION_CASE '+json.dumps({**{k:v for k,v in row.items() if k!='degrees'},
            'degreeSummary':[{k:v for k,v in x.items() if k!='eigenvalues'} for x in row['degrees']]}),flush=True)
    # The prism layers do not alter rim/lid trace triangulation (unit test).
    # The existing inclined wedge has only rim and lid nodes along the opening.
    for angle in (30,55):
        for n in (24,30,40,50):
            m,C0,r=inclined_build(poly,n,1,g['rimTopZ_m'],angle,field)
            panels,C=ports(m,C0,r,36,canonical=True)
            for i,(f,p) in enumerate(zip(m['apertureFaces'],panels)):
                G,nodes=panel_capture(m['xyz'],f,C[:,36*i:36*(i+1)],p)
                record(dict(domain='upper',angleDeg=angle,planarN=n,panel=i,traceNodes=nodes,
                    faces=len(f),areaM2=p.basis.area,degrees=report(G,p)))
    h=-g['rimBottomZ_m'];p=mouth_panel(poly,h,36)
    for n in (50,60,72,84):
        m=prism_build(poly,n,h,lambda x:p.basis(p.local(np.c_[x,np.full(len(x),-h)])),field_order=5)
        G=capture(m['M'],m['B'],p.basis.area)
        record(dict(domain='lower',planarN=n,panel=0,traceNodes=len(m['xy']),faces=len(m['tri']),
            areaM2=p.basis.area,degrees=report(G,p)))
    # A successful diagnostic does not require a well-resolved trace;
    # poor representation is the result to expose, not hide.
    summary=dict(gate=True,diagnosticOnly=True,upperTraceLayerInvariantTest=True,
        upperMinimumCapture36=min(r['degrees'][-1]['minimumCapturedEnergy'] for r in rows if r['domain']=='upper' and r['planarN']==40),
        lowerMinimumCapture36=next(r['degrees'][-1]['minimumCapturedEnergy'] for r in rows if r['domain']=='lower' and r['planarN']==72),
        radiationReady=False,fullCabinetReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_TRACE_RESOLUTION_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
