"""Screen degree eight/nine aperture bases on surface meshes only.
No FEM volume solve or exterior radiation calculation.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from wedge_surface_trace import surface_panels,surface_capture
from acoustic_trace_resolution import describe,panel_capture
from nested_acoustic_ports import reduced_panels,embedding
from lower_prism import mouth_panel
from prism_cavity import build as prism_build
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def capture_report(p,G):
    rows={}
    for count in (36,45,55):
        q=reduced_panels([p],[count]);T,r=embedding([p],q,order=18)
        rows[str(count)]=describe(G,T)
    return rows
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'high_flux_trace.json';rows=[]
    for b,k in [(100,16),(120,24),(160,24),(160,32),(200,32),(200,40)]:
        pp=[]
        for i,(p,x,f,d) in enumerate(surface_panels(poly,b,a.angle,g['rimTopZ_m'],k,55)):
            G,n=surface_capture(p,x,f);pp.append(dict(panel=i,nodes=n,faces=len(f),condition=p.basis.condition,degrees=capture_report(p,G)))
        assert len(pp)==6
        minimum={str(c):min(v['degrees'][str(c)]['minimumCapturedEnergy'] for v in pp) for c in (36,45,55)}
        row=dict(boundaryN=b,wedgeLayers=k,traceFaces=sum(v['faces'] for v in pp),minimumCapture=minimum,panels=pp)
        rows.append(row);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_HIGH_FLUX_CASE '+json.dumps({k:v for k,v in row.items() if k!='panels'}),flush=True)
    lower=[];h=-g['rimBottomZ_m'];p=mouth_panel(poly,h,55)
    def field(x):return p.basis(p.local(np.c_[x,np.full(len(x),-h)]))
    for n in (72,96):
        m=prism_build(poly,n,h,field,field_order=6)
        xyz=np.c_[m['xy'],np.full(len(m['xy']),-h)]
        G,nodes=panel_capture(xyz,m['tri'],m['B'],p)
        row=dict(planarN=n,nodes=nodes,degrees=capture_report(p,G));lower.append(row)
        print('G3_HIGH_FLUX_LOWER '+json.dumps(dict(planarN=n,nodes=nodes,minimumCapture={c:v['minimumCapturedEnergy'] for c,v in row['degrees'].items()})),flush=True)
    candidates={str(c):[dict(boundaryN=r['boundaryN'],wedgeLayers=r['wedgeLayers'],traceFaces=r['traceFaces'],minimumCapture=r['minimumCapture'][str(c)]) for r in rows if r['minimumCapture'][str(c)]>=.95] for c in (45,55)}
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,screeningMinimumEnergy=.95,upperCandidates=candidates,
        lowerCandidates={str(c):[r['planarN'] for r in lower if r['degrees'][str(c)]['minimumCapturedEnergy']>=.95] for c in (45,55)},
        modalConvergenceCertified=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,lower=lower,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_HIGH_FLUX_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
