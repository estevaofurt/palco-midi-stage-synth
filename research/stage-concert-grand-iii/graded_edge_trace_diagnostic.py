"""Screen symmetric edge grading at fixed face counts.
This is a surface-only trial; graded volume tetrahedra are not constructed.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from wedge_surface_trace import surface_panels
from edge_enriched_trace_diagnostic import screen
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def require_source(doc,angle,sha):
    s=doc.get('summary',{})
    if doc.get('scaleSha256')!=sha or any(s.get(k)!=v for k,v in dict(gate=True,angleDeg=angle,diagnosticOnly=True,polynomialModes=55,screeningMinimumEnergy=.95,assumedPhysicalSingularity=False,radiationReady=False).items()):
        raise ValueError('invalid edge screening archive')
    cases=doc.get('cases',[])
    if [(r.get('boundaryN'),r.get('wedgeLayers'),r.get('width')) for r in cases]!=[(n,k,w) for n,k in ((160,24),(200,32),(200,40)) for w in (.03,.06)]:
        raise ValueError('incomplete source screening')
    if any(len(r.get('panels',[]))!=6 for r in cases):raise ValueError('incomplete panel inventory')
    return {(r['boundaryN'],r['wedgeLayers'],r['width']):r for r in cases}

def geometry_check(old,new):
    if len(old)!=len(new):raise ValueError('changed panel inventory')
    for (p,x,f,m),(q,y,g,n) in zip(old,new):
        if m!=n or x.shape!=y.shape or not np.array_equal(f,g) or relative(p.poly,q.poly)>1e-12 or abs(p.basis.area-q.basis.area)>1e-10:
            raise ValueError('graded trace changed geometry or connectivity')
    return sum(len(v[2]) for v in new)

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    source=require_source(json.loads(a.source.read_text()),a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));height=g['rimTopZ_m']
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'graded_edge_trace.json';rows=[]
    # Directional screening first, then combined grading, same topology/count.
    for n,k,eg,lg in ((200,40,.5,0.),(200,40,0.,.5),(200,40,.5,.5),(200,40,.85,.85),(200,32,.5,.5),(160,24,.5,.5)):
        old=surface_panels(poly,n,a.angle,height,k,55);new=surface_panels(poly,n,a.angle,height,k,55,edge_grading=eg,layer_grading=lg)
        faces=geometry_check(old,new)
        for width in (.03,.06):
            parts=[]
            for i,(p,x,f,d) in enumerate(new):
                t=x[f];area=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)/2
                lengths=np.linalg.norm(t-np.roll(t,-1,axis=1),axis=2)
                aspect=np.max(lengths,axis=1)**2/(2*area)
                parts.append(dict(panel=i,faces=len(f),minimumTriangleArea=float(area.min()),maximumAspectIndicator=float(aspect.max()),**screen(p,x,f,width)))
            cap=min(v['full']['minimumCapturedEnergy'] for v in parts);prev=source[n,k,width]
            row=dict(boundaryN=n,wedgeLayers=k,edgeGrading=eg,layerGrading=lg,width=width,traceFaces=faces,panels=parts,
                minimumCapture=cap,uniformCapture=prev['minimumCapture'],captureImprovement=cap-prev['minimumCapture'],
                minimumPolynomialCapture=min(v['polynomial']['minimumCapturedEnergy'] for v in parts),
                minimumEdgeCapture=min(v['edgeOnly']['minimumCapturedEnergy'] for v in parts),
                maximumAspectIndicator=max(v['maximumAspectIndicator'] for v in parts),
                screenGate=bool(cap>=.95))
            rows.append(row);path.write_text(json.dumps(dict(cases=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
            print('G3_GRADED_EDGE_CASE '+json.dumps({k:v for k,v in row.items() if k!='panels'}),flush=True)
    candidates=[{k:v for k,v in r.items() if k!='panels'} for r in rows if r['screenGate']]
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,surfaceOnly=True,volumeMeshValidated=False,
        screenedConfigurations=len(candidates),candidates=candidates,maximumCapture=max(r['minimumCapture'] for r in rows),
        screeningMinimumEnergy=.95,modalConvergenceCertified=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_GRADED_EDGE_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
