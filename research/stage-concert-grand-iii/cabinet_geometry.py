"""Independent candidate cabinet/lid surface inventory in the shared layout frame.
Not a measured piano or an acoustic solver. No reflected sound or new loads yet.
"""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from board_contour import properties,margins,build as contour_build
from spatial_layout import build as layout_build
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def area(tri):
    t=np.asarray(tri);return float(np.linalg.norm(np.cross(t[1]-t[0],t[2]-t[0]))/2)
def geometry(poly,layout,cfg):
    poly=np.asarray(poly,dtype=float);A,center,perimeter=properties(poly)
    top=float(cfg['rimTopZ_m']);bottom=float(cfg['rimBottomZ_m'])
    assert bottom<0<top
    hinge=float(poly[:,0].min());flat=np.c_[poly,np.full(len(poly),top)]
    walls=[]
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        p=np.r_[a,bottom];q=np.r_[b,bottom];u=np.r_[a,top];v=np.r_[b,top]
        walls.extend([np.stack([p,q,v]),np.stack([p,v,u])])
    mic=np.array([p['xyzM'] for p in layout['capture']])
    assert mic.shape==(2,3) and np.all(mic[:,2]>0)
    # Check the source and observation geometry independently; do not move microphones.
    src=np.array([p['bridgeXYZ_m'] for p in layout['wires']])
    radii=np.array([p['radiusM'] for p in layout['wires']])
    assert min(margins(poly,src[:,:2]))>=0
    assert np.all(src[:,2]+radii<top)
    panels=[]
    for deg in cfg['lidAnglesDeg']:
        assert 0<=deg<90
        a=np.deg2rad(deg);c=np.cos(a);s=np.sin(a)
        lid=flat.copy();lid[:,0]=hinge+c*(flat[:,0]-hinge);lid[:,2]=top+s*(flat[:,0]-hinge)
        mid=np.r_[hinge+c*(center[0]-hinge),center[1],top+s*(center[0]-hinge)]
        triangles=[np.stack([mid,p,q]) for p,q in zip(lid,np.roll(lid,-1,axis=0))]
        projected=lid[:,:2];Ap,_,_=properties(projected)
        # Orthogonal plan coverage, NOT the full 3-D aperture or an enclosed volume.
        assert abs(Ap-A*c)<=1e-10
        assert abs(sum(area(t) for t in triangles)-A)<=1e-10
        assert np.min(lid[:,2])>=top-1e-12
        back=np.c_[hinge+(mic[:,0]-hinge)/c,mic[:,1]]
        covered=margins(poly,back)>=-1e-12
        height=top+(mic[:,0]-hinge)*np.tan(a)
        clear=[float(h-p[2]) if yes else None for h,p,yes in zip(height,mic,covered)]
        assert all(x is None or x>0 for x in clear)
        panels.append(dict(angleDeg=deg,panelAreaM2=A,projectedAreaM2=Ap,uncoveredPlanAreaM2=A-Ap,
           verticesXYZ_m=lid.tolist(),trianglesXYZ_m=[t.tolist() for t in triangles],micUnderProjection=covered.tolist(),micVerticalClearanceM=clear))
    wallArea=sum(area(t) for t in walls);assert abs(wallArea-perimeter*(top-bottom))<1e-10
    return dict(version=cfg['version'],status='engineering_hypothesis',summary=dict(gate=True,geometryReady=False,acousticsReady=False,
       footprintAreaM2=A,sideWallAreaM2=wallArea,closedUpperPrismM3=A*top,lowerPrismInventoryM3=A*(-bottom),
       lidCases=len(panels),minimumBridgeSourceClearanceM=float(min(top-src[:,2]-radii))),
       rimTopZ_m=top,rimBottomZ_m=bottom,hingeAxis=dict(x=hinge,z=top,direction=[0,1,0]),
       wallTrianglesXYZ_m=[t.tolist() for t in walls],lidCases=panels,microphonesXYZ_m=mic.tolist(),
       limitations=cfg['limitations'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));c=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    q=geometry(c['contourXY_m'],l,read('cabinet_geometry_hypothesis.json'));q['scaleSha256']=hashlib.sha256(raw).hexdigest()
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'cabinet_geometry.json').write_text(json.dumps(q,indent=2,allow_nan=False))
    print('G3_CABINET_GEOMETRY_GATE '+json.dumps(dict(summary=q['summary'],lidCases=[{k:v for k,v in x.items() if k not in ('verticesXYZ_m','trianglesXYZ_m')} for x in q['lidCases']])),flush=True)
if __name__=='__main__':main()
