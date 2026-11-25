"""Reproduce fixed-density edge audit with a spatial residual partition.
Only 30 Hz and the existing upper-envelope fixture. No solver promotion.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from neumann_envelope import envelope,geometry_audit
from bem_envelope import triangulate,velocities
from bem_p1_static_moments import fit
from bem_edge_localization import localize
from bem_mesh_guard import signature,require_same_mesh
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    s,ports,c=envelope(poly,g['rimTopZ_m'],a.angle,3,field);geo=geometry_audit(s,ports,c);assert geo['gate']
    t,labels,top=triangulate(s,1);sig=signature(t,labels);assert abs(top['volume']-geo['volume'])<=1e-10
    v=lambda x,o:velocities(s,ports,x,labels[o]);k=2*np.pi*30/343.
    q,fr=fit(t,k,5,6,v);assert fr['weakResidual']<=1e-8
    qsig=hashlib.sha256(np.ascontiguousarray(q).tobytes()).hexdigest()
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'bem_edge_localization.json';rows=[]
    for outer,inner in ((6,6),(8,8)):
        require_same_mesh(sig,signature(t,labels))
        assert qsig==hashlib.sha256(np.ascontiguousarray(q).tobytes()).hexdigest()
        r=localize(t,labels,[x['kind'] for x in s],q,v,k,outer,inner)
        rows.append(r);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
        print('G3_EDGE_LOCAL_CASE '+json.dumps({key:value for key,value in r.items() if key!='elementIndicator'}),flush=True)
    first,last=rows
    changes={b['kind']:abs(x['residualEnergyFraction']-b['residualEnergyFraction']) for x,b in zip(first['categories'],last['categories'])}
    assert [r['kind'] for r in first['categories']]==[r['kind'] for r in last['categories']]
    resChange=abs(first['heldoutResidual']-last['heldoutResidual'])/max(last['heldoutResidual'],1e-30)
    gate=resChange<=.05 and max(changes.values())<=.02 and max(r['energyClosure'] for r in rows)<=1e-10
    summary=dict(gate=gate,angleDeg=a.angle,frequencyHz=30.,meshSha256=sig,densitySha256=qsig,
        residualConvergence=resChange,categoryFractionAbsoluteChanges=changes,diagnosticOnly=True,
        solverApproved=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_EDGE_LOCAL_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
