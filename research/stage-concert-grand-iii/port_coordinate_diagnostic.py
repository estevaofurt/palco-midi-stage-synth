"""Audit old and canonical coordinate systems on actual G3 geometry."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from inclined_lid import build
from port_coordinates import audit,same_coordinates
from lid_exterior import load,pressure
from aperture_modes import response
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));mic=np.array(g['microphonesXYZ_m'])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'port_coordinates.json'
    rows=[];prev=None
    for n,nz in [(18,6),(24,8),(30,10)]:
        m,C,r=build(poly,n,nz,g['rimTopZ_m'],a.angle,field)
        old,new,Co,Cn,T,rep=audit(m,C,r,21)
        row=dict(n=n,nz=nz,audit=rep)
        if prev is not None:
            row['legacyMesh']=same_coordinates(prev[0],old)
            row['canonicalMesh']=same_coordinates(prev[1],new)
        prev=(old,new)
        rows.append(row)
        print('G3_COORD_CASE '+json.dumps(row),flush=True)
    # Compare independent assembly and transformed operator at moderate degree.
    old,new,Co,Cn,T,rep=audit(m,C,r,6)
    freqs=[30.,80.,150.];zo=load(old,freqs,16,28,24);zn=load(new,freqs,16,28,24);metrics=[]
    for f,(z,ro),(q,rn) in zip(freqs,zo,zn):
        zt=T.T@z@T
        y,p,u,r1=response(m,Co,2j*np.pi*f,mic,z)
        yt,pt,ut,r2=response(m,Cn,2j*np.pi*f,mic,zt)
        yn,pn,un,r3=response(m,Cn,2j*np.pi*f,mic,q)
        metrics.append(dict(frequencyHz=f,operator=relative(zt,q),mappedImpedance=relative(y,yt),mappedPressure=relative(p,pt),
            mappedFlow=relative(u,T@ut),independentImpedance=relative(y,yn),independentPressure=relative(p,pn),
            gates=all(v['gate'] for v in (ro,rn,r1,r2,r3))))
    gate=all(row['audit']['gate'] and row.get('canonicalMesh',dict(gate=True))['gate'] for row in rows)
    gate=gate and all(v['gates'] and max(v[k] for k in ('mappedImpedance','mappedPressure','mappedFlow'))<=1e-8 and max(v[k] for k in ('operator','independentImpedance','independentPressure'))<=.01 for v in metrics)
    summary=dict(gate=gate,angleDeg=a.angle,legacyMeshInvariant=all(row.get('legacyMesh',dict(gate=True))['gate'] for row in rows),
        canonicalMeshInvariant=all(row.get('canonicalMesh',dict(gate=True))['gate'] for row in rows),canonicalDefault=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,metrics=metrics,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_COORD_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
