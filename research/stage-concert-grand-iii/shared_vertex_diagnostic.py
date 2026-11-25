"""Representative vertex correction on the actual 55-mode panel pair.
Keep the approved shared-edge correction separate from vertex deltas.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from high_mode_quadrature_audit import adjacent,changes,FREQ
from exterior_shared_vertex import contacts,vertex_delta
from exterior_shared_edge import corrected_pair
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    _,ports,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,lambda x:np.ones((len(x),1)),55);assert geo['gate']
    inventory=[]
    for i in range(len(ports)):
        for j in range(i+1,len(ports)):
            rows=contacts(ports[i],ports[j])
            if rows:inventory.append(dict(panel=i,otherPanel=j,vertexPairs=sum(n==1 for _,_,n,_ in rows),edgePairs=sum(n==2 for _,_,n,_ in rows)))
    i=min(range(6),key=lambda j:ports[j].basis.area);j=adjacent(ports,i);p,q=ports[i],ports[j]
    k=2*np.pi*np.asarray(FREQ)/343.;rows=[];mat=[]
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'shared_vertex_diagnostic.json'
    for outer,edge,vertex in [(36,24,24),(42,28,28)]:
        start=time.perf_counter();R,X,e=corrected_pair(p,q,k,outer,edge)
        delta,v=vertex_delta(p,q,k,outer,vertex);Y=X+delta
        assert v['vertexPairs']>0
        row=dict(outerOrder=outer,edgeOrder=edge,vertexOrder=vertex,seconds=time.perf_counter()-start,
            edgeSmoothControl=e['smoothControlMaximum'],vertexControl=v,vertexCorrection=changes(X,Y))
        rows.append(row);mat.append((X,Y,delta));path.write_text(json.dumps(dict(inventory=inventory,cases=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_VERTEX_CASE '+json.dumps(row),flush=True)
    edgeChange=changes(mat[0][0],mat[1][0]);bothChange=changes(mat[0][1],mat[1][1])
    smooth=max(max(r['edgeSmoothControl'],r['vertexControl']['smoothControlMaximum']) for r in rows)
    fine=max(v['relative'] for v in bothChange)
    summary=dict(gate=bool(smooth<=1e-8),angleDeg=a.angle,diagnosticOnly=True,panel=i,otherPanel=j,modesPerPanel=55,
        vertexPairs=rows[-1]['vertexControl']['vertexPairs'],edgeOnlyChange=edgeChange,edgeAndVertexChange=bothChange,
        maximumFineRelative=fine,maximumSmoothControl=smooth,representativeQuadratureGate=bool(smooth<=1e-8 and fine<=.01),
        fullExteriorQuadratureCertified=False,radiationReady=False)
    np.savez_compressed(a.out/'shared_vertex_blocks.npz',frequencies=FREQ,edgeOnly=np.stack([v[0] for v in mat]),corrected=np.stack([v[1] for v in mat]),vertexDelta=np.stack([v[2] for v in mat]))
    path.write_text(json.dumps(dict(summary=summary,inventory=inventory,cases=rows,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_VERTEX_GATE '+json.dumps(summary),flush=True);assert summary['gate']
if __name__=='__main__':main()
