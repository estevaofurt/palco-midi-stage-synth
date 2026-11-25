"""Compare exact Schur elimination to the existing dense reference.
Large layered cases test algebra and storage, not mesh convergence.
"""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from hybrid_cavity import build,response
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));mic=np.asarray(g['microphonesXYZ_m'])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    rows=[];a.out.mkdir(parents=True,exist_ok=True);path=a.out/'hybrid_schur.json'
    for n,k,modes,control,freq in [(18,1,21,True,[30.,80.,150.,250.]),(18,4,21,True,[30.,80.,150.,250.]),(40,8,36,False,[30.,150.,250.]),(40,12,36,False,[30.,150.,250.])]:
        m=build(poly,n,1,g['rimTopZ_m'],a.angle,field,modes,wedge_layers=k)
        for f in freq:
            start=time.perf_counter();Z,P,r=response(m,f,mic,solver='schur');elapsed=time.perf_counter()-start
            row=dict(planarN=n,wedgeLayers=k,modesPerPanel=modes,frequencyHz=f,schurSeconds=elapsed,report=r,gate=r['gate'])
            if control:
                start=time.perf_counter();z,p,rr=response(m,f,mic);row['denseSeconds']=time.perf_counter()-start
                row['equivalence']=dict(impedance=relative(Z,z),pressure=relative(P,p))
                row['gate']=bool(row['gate'] and rr['gate'] and max(row['equivalence'].values())<=1e-9)
            rows.append(row);path.write_text(json.dumps(dict(cases=rows,complete=False),indent=2,allow_nan=False))
            print('G3_HYBRID_SCHUR_CASE '+json.dumps(row),flush=True)
    summary=dict(gate=all(r['gate'] for r in rows),angleDeg=a.angle,maximumDenseEquivalence=max(max(r['equivalence'].values()) for r in rows if 'equivalence' in r),
        noModalTruncation=True,diagnosticOnly=True,meshConvergenceCertified=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=hashlib.sha256(raw).hexdigest()),indent=2,allow_nan=False))
    print('G3_HYBRID_SCHUR_GATE '+json.dumps(summary),flush=True);assert summary['gate']
if __name__=='__main__':main()
