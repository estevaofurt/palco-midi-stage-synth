"""G3.05a: explicit bounded contour and rib centerline geometry.
Independent inventory: not a measured soundboard, no stiffness or acoustic output.
"""
import argparse,json,hashlib,math
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
ROOT=Path(__file__).parent
def cross(a,b):return float(a[0]*b[1]-a[1]*b[0])
def hull(points):
    pts=sorted(set(map(tuple,points)))
    if len(pts)<3:raise ValueError('polygon needs at least 3 points')
    def half(pts):
        out=[]
        for p in pts:
            p=np.asarray(p,dtype=float)
            while len(out)>=2 and cross(out[-1]-out[-2],p-out[-1])<=1e-14:out.pop()
            out.append(p)
        return out
    return np.array(half(pts)[:-1]+half(reversed(pts))[:-1])
def margins(poly,points):
    p=np.atleast_2d(points);a=poly;b=np.roll(poly,-1,axis=0);d=b-a
    return np.min((d[:,0]*(p[:,None,1]-a[:,1])-d[:,1]*(p[:,None,0]-a[:,0]))/np.linalg.norm(d,axis=1),axis=1)
def properties(poly):
    a=poly;b=np.roll(poly,-1,axis=0);cr=a[:,0]*b[:,1]-a[:,1]*b[:,0];area=float(sum(cr)/2)
    assert area>0
    centroid=np.sum((a+b)*cr[:,None],axis=0)/(6*area)
    return area,centroid,float(np.sum(np.linalg.norm(b-a,axis=1)))
def clip_line(poly,point,direction):
    lo=-math.inf;hi=math.inf
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        edge=b-a;u=cross(edge,direction);v=cross(edge,point-a)
        if abs(u)<1e-14:
            if v<0:return None
        elif u>0:lo=max(lo,-v/u)
        else:hi=min(hi,-v/u)
    if hi<=lo:return None
    return lo,hi
def build(layout,cfg,material):
    bb=layout['boardEnvelope'];low=np.array([bb['x'][0],bb['y'][0]]);high=np.array([bb['x'][1],bb['y'][1]])
    c=cfg['construction'];pad=c['attachmentMarginM']
    nodes=[n for s in ('bass','treble') for n in layout['bridgeAttachmentNodes'][s]]
    xy=np.array([n['footProjectionXYZ_m'][:2] for n in nodes])
    assert len(nodes)==226 and len({n['wireId'] for n in nodes})==226
    corners=np.array([[i,j] for i in (-pad,pad) for j in (-pad,pad)])
    expanded=(xy[:,None,:]+corners).reshape(-1,2)
    if np.any(expanded<low) or np.any(expanded>high):raise ValueError('attachment clearance cannot fit original envelope')
    anchors=low+np.asarray(c['normalizedEnvelopeAnchors'])*(high-low)
    poly=hull(np.vstack([anchors,expanded]))
    area,centroid,perim=properties(poly);dist=margins(poly,xy)
    assert np.min(dist)>=pad-1e-12 and np.all(poly>=low-1e-12) and np.all(poly<=high+1e-12)
    assert area<np.prod(high-low)
    direction=np.array(cfg['ribs']['directionXY'],dtype=float);direction/=np.linalg.norm(direction)
    normal=np.array([direction[1],-direction[0]])
    extent=poly@normal;count=cfg['ribs']['count'];clear=cfg['ribs']['endClearanceM'];ribs=[]
    offsets=np.linspace(min(extent),max(extent),count+2)[1:-1]
    for j,offset in enumerate(offsets):
        p=offset*normal;interval=clip_line(poly,p,direction)
        assert interval is not None
        lo,hi=interval;assert hi-lo>2*clear
        a=p+(lo+clear)*direction;b=p+(hi-clear)*direction
        assert min(margins(poly,[a,b]))>=-1e-12
        ribs.append(dict(id=f'rib-{j+1:02}',startXYZ_m=[*a.tolist(),0.],endXYZ_m=[*b.tolist(),0.],lengthM=float(np.linalg.norm(b-a)),section=None))
    p=material['plate'];mass=area*p['thicknessM']*p['densityKgM3']
    summary=dict(attachmentCount=len(nodes),minAttachmentMarginM=float(min(dist)),polygonVertices=len(poly),areaM2=area,
       envelopeFraction=float(area/np.prod(high-low)),perimeterM=perim,plateOnlyMassKg=mass,ribCount=len(ribs),
       ribTotalLengthM=sum(q['lengthM'] for q in ribs),gate=True,geometryReady=False,boardReady=False)
    return dict(version=cfg['version'],summary=summary,contourXY_m=poly.tolist(),centroidXY_m=centroid.tolist(),ribs=ribs,
       attachmentClearance=[dict(wireId=n['wireId'],marginM=float(d)) for n,d in zip(nodes,dist)],
       frame=layout['frame'],config=cfg,materialPrior=p)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    layout=layout_build(sc,json.loads((ROOT/'layout_hypothesis.json').read_text()))
    cfg=json.loads((ROOT/'board_contour_hypothesis.json').read_text());material=json.loads((ROOT/'board_interface_hypothesis.json').read_text())
    z=build(layout,cfg,material);z['scaleSha256']=hashlib.sha256(raw).hexdigest()
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'board_contour.json').write_text(json.dumps(z,indent=2,allow_nan=False))
    print('G3_BOARD_CONTOUR_GATE '+json.dumps(z['summary']),flush=True)
if __name__=='__main__':main()
