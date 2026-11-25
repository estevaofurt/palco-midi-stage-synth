"""Geometric trace screening of edge-local trial functions.
No FEM volume solve, no exterior load, no assumed edge singular exponent.
"""
import argparse,copy,hashlib,json
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from wedge_surface_trace import surface_panels,trace_matrix
from acoustic_trace_resolution import describe,panel_capture
from edge_enriched_flux import EdgeEnrichedFlux
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def screen(panel,x,f,width):
    p=copy.copy(panel);p.basis=EdgeEnrichedFlux(panel.poly,panel.basis,width)
    audit=p.basis.audit()
    assert audit['massRelative']<=1e-8 and audit['maximumIntegralError']<=1e-8 and audit['baselineRelative']<=1e-14
    C0=trace_matrix(panel,x,f,order=6)
    C=trace_matrix(p,x,f,order=10);D=trace_matrix(p,x,f,order=14)
    eq=relative(C,D);base=relative(C0,D[:,:55])
    assert eq<=1e-8 and base<=1e-8
    G,n=panel_capture(x,f,D,p);full=describe(G);poly=describe(G[:55,:55]);extra=describe(G[55:,55:])
    return dict(nodes=n,mass=audit,traceQuadratureRelative=eq,baselineTraceRelative=base,
        full=full,polynomial=poly,edgeOnly=extra,screenGate=bool(full['minimumCapturedEnergy']>=.95))

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'edge_enriched_trace.json';rows=[]
    for n,k in ((160,24),(200,32),(200,40)):
        panels=surface_panels(poly,n,a.angle,g['rimTopZ_m'],k,55);assert len(panels)==6
        for width in (.03,.06):
            parts=[]
            for i,(p,x,f,d) in enumerate(panels):
                parts.append(dict(panel=i,faces=len(f),**screen(p,x,f,width)))
            row=dict(boundaryN=n,wedgeLayers=k,width=width,panels=parts,
                minimumCapture=min(v['full']['minimumCapturedEnergy'] for v in parts),
                minimumEdgeCapture=min(v['edgeOnly']['minimumCapturedEnergy'] for v in parts),
                minimumPolynomialCapture=min(v['polynomial']['minimumCapturedEnergy'] for v in parts),
                totalUpperModes=sum(v['full']['modes'] for v in parts),screenGate=all(v['screenGate'] for v in parts))
            rows.append(row)
            path.write_text(json.dumps(dict(cases=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
            print('G3_EDGE_ENRICH_CASE '+json.dumps({k:v for k,v in row.items() if k!='panels'}),flush=True)
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,polynomialModes=55,widths=[.03,.06],
        screenedConfigurations=sum(r['screenGate'] for r in rows),screeningMinimumEnergy=.95,
        assumedPhysicalSingularity=False,modalConvergenceCertified=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_EDGE_ENRICH_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
