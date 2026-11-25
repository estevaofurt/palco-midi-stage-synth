"""G3.01e: shared 3D geometry fixture, not a measured or manufacturing layout."""
import argparse,copy,hashlib,json,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).parent
def cross(a,b):return float(a[0]*b[1]-a[1]*b[0])
def point_segment(p,a,b):
    u=b-a;t=np.clip(float((p-a)@u/(u@u)),0.,1.)
    return float(np.linalg.norm(p-(a+t*u)))
def segment_distance_xy(a,b,c,d):
    u=b-a;v=d-c;den=cross(u,v)
    if abs(den)>1e-14:
        t=cross(c-a,v)/den;s=cross(c-a,u)/den
        if 0<=t<=1 and 0<=s<=1:return 0.,True
    return min(point_segment(a,c,d),point_segment(b,c,d),point_segment(c,a,b),point_segment(d,a,b)),False
def build(scale,cfg):
    assert scale['summary']['gate'] and len(scale['rows'])==88 and len(scale['wires'])==226
    g=cfg['layout'];W,D=cfg['externalEnvelopeM'];bb=cfg['boardEnvelope'];rows={r['key']:r for r in scale['rows']}
    wires=[];bridge={'bass':[],'treble':[]};anchors={}
    for src in scale['wires']:
        w=copy.deepcopy(src);k=w['key'];r=rows[k];L=r['lengthM'];section=w['bridgeId']
        bass=section=='bass';theta=g['bassAngleFromYM'] if bass else g['trebleAngleFromYM']
        z=g['bassHeightM'] if bass else g['trebleHeightM']
        axis=np.array([math.sin(theta),math.cos(theta),0.]);vert=np.array([0.,0.,1.]);side=np.cross(vert,axis)
        # Right-handed local frame [longitudinal, lateral, vertical].
        frame=np.stack([axis,side,vert],axis=1)
        assert np.max(abs(frame.T@frame-np.eye(3)))<1e-12 and abs(np.linalg.det(frame)-1)<1e-12
        h=np.array([g['firstGroupX']+(k-21)*g['groupPitch']+(w['unisonIndex']-(r['count']+1)/2)*g['withinGroupPitchX'],g['hammerLineY'],z])
        front=h-r['hammerPositionM']*axis;end=front+L*axis
        rad=r['outerDiameterM']/2
        for point in (front,end):
            assert rad<=point[0]<=W-rad and rad<=point[1]<=D-rad
        assert bb['x'][0]<=end[0]<=bb['x'][1] and bb['y'][0]<=end[1]<=bb['y'][1]
        for p in w['ports']:
            s=p['localS_m']
            if s is not None:
                p['worldXYZ_m']=(front+s*axis).tolist();p['axes']=frame.tolist()
            else:
                assert p['role']=='damper'
        assert abs(np.linalg.norm(end-front)-L)<1e-12
        w.update(globalFrame={'originXYZ_m':front.tolist(),'basisColumns':frame.tolist()},geometryStatus='engineering_layout_hypothesis',radiusM=rad,
                 frontXYZ_m=front.tolist(),bridgeXYZ_m=end.tolist(),hammerXYZ_m=h.tolist())
        bridge[section].append(dict(wireId=w['id'],key=k,xyzM=end.tolist(),footProjectionXYZ_m=[float(end[0]),float(end[1]),0.]))
        wires.append(w)
        if w['unisonIndex']==(r['count']+1)//2 and k in cfg['capture']['anchorKeys']:
            anchors[k]=front+cfg['capture']['anchorFraction']*L*axis
    # Surface clearance conservatively uses maximum wound radius along entire wire.
    min_clear=float('inf');min_pair=None;crossings=0;min_cross=float('inf')
    for i,a in enumerate(wires):
        A=np.array(a['frontXYZ_m']);B=np.array(a['bridgeXYZ_m'])
        for b in wires[i+1:]:
            C=np.array(b['frontXYZ_m']);E=np.array(b['bridgeXYZ_m'])
            d,hit=segment_distance_xy(A[:2],B[:2],C[:2],E[:2]);dz=abs(A[2]-C[2])
            clearance=math.hypot(d,dz)-a['radiusM']-b['radiusM']
            if clearance<min_clear:min_clear=clearance;min_pair=[a['id'],b['id']]
            if hit:
                assert a['bridgeId']!=b['bridgeId'] and dz>0
                crossings+=1;min_cross=min(min_cross,clearance)
    assert crossings>0 and min_clear>=g['minimumStringSurfaceClearanceM']
    capture=[]
    for k in cfg['capture']['anchorKeys']:
        anchor=anchors[k];xyz=anchor+np.array([0.,0.,cfg['capture']['heightAboveAnchorStringM']])
        assert abs(xyz[2]-anchor[2]-.12)<1e-12
        capture.append(dict(anchorKey=k,anchorXYZ_m=anchor.tolist(),xyzM=xyz.tolist(),heightAboveAnchorM=float(xyz[2]-anchor[2]),
                            heightAboveBoardDatumM=float(xyz[2]),pattern='ideal pressure point (fixture only)'))
    assert len(capture)==2 and np.linalg.norm(np.array(capture[0]['xyzM'])-capture[1]['xyzM'])>0
    # Bridge nodes are attachment coordinates only, not continuous beams or actual board shape.
    summary=dict(keys=88,strings=len(wires),ports=sum(len(w['ports']) for w in wires),
        locatedPorts=sum(p['worldXYZ_m'] is not None for w in wires for p in w['ports']),
        bassBridgeNodes=len(bridge['bass']),trebleBridgeNodes=len(bridge['treble']),projectedCrossings=crossings,
        minSurfaceClearanceM=min_clear,minClearancePair=min_pair,minCrossingClearanceM=min_cross,
        microphoneSpacingM=float(np.linalg.norm(np.array(capture[0]['xyzM'])-capture[1]['xyzM'])),
        geometryReady=False,scaleReady=False,gate=True)
    return dict(version='G3-layout-01',status=cfg['status'],summary=summary,frame=cfg['frame'],boardEnvelope=bb,externalEnvelopeM=[W,D],
                wires=wires,bridgeAttachmentNodes=bridge,capture=capture,legacyControlXYZ_m=cfg['capture']['controlXYZ'],limitations=cfg['limitations'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    cfgraw=(ROOT/'layout_hypothesis.json').read_bytes();raw=a.scale.read_bytes();scale=json.loads(raw)
    assert scale['version']=='G3-scale-hypothesis-02'
    assert scale['sourceSha256']==hashlib.sha256((ROOT/'scale_hypothesis.json').read_bytes()).hexdigest()
    report=build(scale,json.loads(cfgraw));report.update(scaleReportSha256=hashlib.sha256(raw).hexdigest(),layoutConfigSha256=hashlib.sha256(cfgraw).hexdigest())
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'layout.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G3_LAYOUT_GATE '+json.dumps(report['summary']),flush=True)
    print('G3_LAYOUT_CAPTURE '+json.dumps(report['capture']),flush=True)
if __name__=='__main__':main()
