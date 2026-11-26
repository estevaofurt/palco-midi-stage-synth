"""Fixed-node arithmetic sensitivity of enriched disjoint interactions.
No change to physical parameters, quadrature orders or approval limits."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from enriched_smooth_diagnostic import require_sources,read
from enriched_aperture_reference import enrich
from enriched_reactive_diagnostic import block_changes
from high_modal_allocation import require_archive
from high_modal_remaining_reactive import classify
from acoustic_matrix_archive import read_npz
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from exterior_pair_stream import pair_integrals
from dual_cavity_spatial_diagnostic import FREQ
from disjoint_enriched_refinement import scales,require_previous,TOL
def compensated_reactive(x,A,y,B,k,block=64):
    """Same nodes/kernel; compensated accumulation of BLAS tile results.
    Not extended precision and not a replacement quadrature."""
    from scipy.spatial.distance import cdist
    x,A,y,B,k=map(np.asarray,(x,A,y,B,k))
    total=np.zeros((len(k),A.shape[1],B.shape[1]));correction=np.zeros_like(total)
    for i in range(0,len(x),block):
        j=min(i+block,len(x));D=cdist(x[i:j],y)
        if D.min()<=0:raise ValueError('coincident nodes')
        for l,kl in enumerate(k):
            tile=A[i:j].T@((np.cos(kl*D)/D)@B)
            z=tile-correction[l];t=total[l]+z
            correction[l]=(t-total[l])-z;total[l]=t
    return total


def main():
    p=argparse.ArgumentParser()
    for key in ('scale','archive','consolidated','trace','previous','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw)
    assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    ex=json.loads((a.consolidated/'consolidated_exterior.json').read_text());require_sources(ex,json.loads(a.trace.read_text()),a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));nf=len(FREQ)
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,old,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate']
    panels,counts,idx,_=enrich(old);inv=classify(panels)
    d=json.loads((a.previous/'enriched_reactive.json').read_text())
    rows=require_previous(d,a.angle,sha,inv,counts,idx)
    archived=read_npz(a.previous,d['archive'],{f'block_{i}_{j}':(nf,counts[i],counts[j]) for i,j,k in inv if k=='disjoint'},FREQ)
    prior=read_npz(a.consolidated,ex['archive'],dict(Ze=(nf,385,385),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    omega=2*np.pi*np.asarray(FREQ);k=omega/343.;factor=1.204*omega[:,None,None]/(4*np.pi)
    a.out.mkdir(parents=True,exist_ok=True)
    failed=sorted((v for v in rows if not v['gate']),key=lambda v:max(v['changes'].values()),reverse=True)
    if not failed:raise ValueError('no failed block for arithmetic diagnosis')
    reports=[]
    for row in failed[:2]:
        i,j=row['panel'],row['otherPanel'];key=f'block_{i}_{j}'
        _,x,w,A=panels[i].samples(48);_,y,v,B=panels[j].samples(48)
        A=w[:,None]*A;B=v[:,None]*B
        old=archived[key]
        _,forward,_=pair_integrals(x,A,y,B,k,mutual=True,block=64);forward*=factor
        reverse=compensated_reactive(y,B,x,A,k,block=96).transpose(0,2,1)*factor
        comp=compensated_reactive(x,A,y,B,k,block=64)*factor
        result=dict(panel=i,otherPanel=j,order=48,previousOrderChange=row['changes'],
            reproduced=block_changes(old,forward),compensated=block_changes(forward,comp),
            reversed=block_changes(comp,reverse),reversedScales=scales(comp,reverse))
        reports.append(result)
        print('G3_FIXED_NODE_ARITHMETIC '+json.dumps(result,allow_nan=False),flush=True)
    summary=dict(gate=True,diagnosticOnly=True,angleDeg=a.angle,order=48,blocks=len(reports),
        quadratureCertified=False,modalConvergenceCertified=False,radiationReady=False)
    (a.out/'fixed_node_arithmetic.json').write_text(json.dumps(dict(summary=summary,cases=reports,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_FIXED_NODE_ARITHMETIC_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
