"""Test the corrected shared-edge pair at 55 modes on the actual geometry.
This is a representative correction only, not a promoted exterior load.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from high_mode_quadrature_audit import adjacent,changes,FREQ
from exterior_shared_edge import corrected_pair
from exterior_pair_stream import pair_integrals
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    _,ports,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,lambda x:np.ones((len(x),1)),55);assert geo['gate']
    i=min(range(6),key=lambda j:ports[j].basis.area);j=adjacent(ports,i);p,q=ports[i],ports[j]
    k=2*np.pi*np.asarray(FREQ)/343.;rows=[];mat=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'shared_edge_quadrature.json'
    for outer,edge in [(30,20),(36,24),(42,28)]:
        start=time.perf_counter();R,X,r=corrected_pair(p,q,k,outer,edge)
        _,x,w,A=p.samples(outer);_,y,v,B=q.samples(outer)
        S,Y,_=pair_integrals(x,w[:,None]*A,y,v[:,None]*B,k,mutual=True,block=64)
        smooth=max(x['relative'] for x in changes(R,S));assert smooth<=1e-12
        independentSmooth=r['smoothControlMaximum']
        row=dict(outerOrder=outer,edgeOrder=edge,seconds=time.perf_counter()-start,geometry=r,
            smoothKernelChange=smooth,independentSmoothControl=independentSmooth,
            smoothControlGate=bool(independentSmooth<=1e-8),reactiveCorrection=changes(Y,X))
        rows.append(row);mat.append((R,X,Y))
        path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_SHARED_EDGE_CASE '+json.dumps(row),flush=True)
    corrected=[changes(mat[i][1],mat[i+1][1]) for i in (0,1)]
    original=[changes(mat[i][2],mat[i+1][2]) for i in (0,1)]
    fine=max(x['relative'] for x in corrected[-1]);coarse=max(x['relative'] for x in corrected[0])
    smoothGate=all(r['smoothControlGate'] for r in rows)
    summary=dict(gate=smoothGate,angleDeg=a.angle,diagnosticOnly=True,panel=i,otherPanel=j,modesPerPanel=55,
        correctedChanges=corrected,originalChanges=original,maximumFineRelative=fine,maximumCoarseRelative=coarse,
        smoothControlGate=smoothGate,representativeQuadratureGate=bool(smoothGate and fine<=.01),fullExteriorQuadratureCertified=False,radiationReady=False)
    np.savez_compressed(a.out/'shared_edge_blocks.npz',frequencies=FREQ,corrected=np.stack([v[1] for v in mat]),original=np.stack([v[2] for v in mat]))
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_SHARED_EDGE_GATE '+json.dumps(summary),flush=True);assert smoothGate
if __name__=='__main__':main()
