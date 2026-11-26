"""G3.10n: extended-precision scalar control on a weak edge-edge entry.
Only the kernel and accumulation are extended precision: geometry, weights
and basis samples remain the same double precision discretization."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from enriched_smooth_diagnostic import require_sources,read
from enriched_aperture_reference import enrich
from high_modal_allocation import require_archive
from high_modal_remaining_reactive import classify
from acoustic_matrix_archive import read_npz
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from exterior_pair_stream import pair_integrals
from dual_cavity_spatial_diagnostic import FREQ
from disjoint_enriched_refinement import require_previous
from disjoint_fixed_node_arithmetic import compensated_reactive

def scalar_integral(x,A,y,B,k,block=32):
    """Evaluate the same weighted scalar kernel without constructing a dense
    longdouble operator. Compensated scalar sum across tiles."""
    dtype=np.longdouble
    x,A,y,B=(np.asarray(v,dtype=dtype) for v in (x,A,y,B))
    k=dtype(k);total=dtype(0);correction=dtype(0)
    if x.ndim!=2 or y.ndim!=2 or x.shape[1]!=3 or y.shape[1]!=3 or A.shape!=(len(x),) or B.shape!=(len(y),) or block<1 or not np.isfinite(k):
        raise ValueError('invalid inputs')
    for i in range(0,len(x),block):
        z=x[i:i+block,None,:]-y[None,:,:];D=np.sqrt(np.sum(z*z,axis=-1,dtype=dtype))
        if np.any(D<=0):raise ValueError('coincident nodes')
        v=np.sum((A[i:i+block,None]*B[None,:])*(np.cos(k*D)/D),dtype=dtype)
        q=v-correction;t=total+q;correction=(t-total)-q;total=t
    return total

def as_string(v):
    return np.format_float_scientific(np.longdouble(v),precision=20,unique=False)

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
    if np.finfo(np.longdouble).nmant<=np.finfo(np.float64).nmant:raise RuntimeError('extended precision unavailable')
    if a.angle!=55:raise ValueError('55-degree evidence only')
    i,j=0,4;key=f'block_{i}_{j}';row=next(v for v in rows if (v['panel'],v['otherPanel'])==(i,j))
    if row['gate']:raise ValueError('expected unresolved block')
    def samples(n):
        _,x,w,A=panels[i].samples(n);_,y,v,B=panels[j].samples(n)
        return x,w[:,None]*A,y,v[:,None]*B
    x,A,y,B=samples(48)
    _,forward,_=pair_integrals(x,A,y,B,k,mutual=True,block=64);forward*=factor
    reverse=compensated_reactive(y,B,x,A,k,block=96).transpose(0,2,1)*factor
    if not np.array_equal(forward,archived[key]):raise ValueError('archived calculation did not reproduce exactly')
    # Select the frequency with largest relative reversal error in the
    # edge-edge block, then its entry of largest absolute disagreement.
    u=forward[:,55:,55:];v=reverse[:,55:,55:]
    norm=np.maximum(np.linalg.norm(v,axis=(1,2)),1e-30)
    f=int(np.argmax(np.linalg.norm(u-v,axis=(1,2))/norm))
    m,n=np.unravel_index(np.argmax(np.abs(u[f]-v[f])),u[f].shape);m+=55;n+=55
    records={}
    for order in (40,48):
        xx,AA,yy,BB=samples(order)
        value=scalar_integral(xx,AA[:,m],yy,BB[:,n],k[f])*np.longdouble(factor[f,0,0])
        rev=scalar_integral(yy,BB[:,n],xx,AA[:,m],k[f])*np.longdouble(factor[f,0,0])
        records[order]=(value,rev)
    scale=np.longdouble(norm[f])
    a40,b40=records[40];a48,b48=records[48]
    result=dict(panel=i,otherPanel=j,frequencyHz=FREQ[f],entry=[int(m),int(n)],precisionMantissaBits=int(np.finfo(np.longdouble).nmant+1),
        float64Forward=as_string(forward[f,m,n]),float64Reverse=as_string(reverse[f,m,n]),
        extended40=as_string(a40),extended40Reverse=as_string(b40),extended48=as_string(a48),extended48Reverse=as_string(b48),
        float64ReversalRelativeToSubblock=float(abs(np.longdouble(forward[f,m,n])-reverse[f,m,n])/scale),
        extendedReversalRelativeToSubblock=float(abs(a48-b48)/scale),
        extendedOrderChangeRelativeToSubblock=float(abs(a48-a40)/scale),
        float64ToExtendedRelativeToSubblock=float(abs(np.longdouble(forward[f,m,n])-a48)/scale))
    a.out.mkdir(parents=True,exist_ok=True)
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,scalarOnly=True,extendedBasisEvaluation=False,
        quadratureCertified=False,modalConvergenceCertified=False,radiationReady=False)
    (a.out/'extended_scalar_control.json').write_text(json.dumps(dict(summary=summary,result=result,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_EXTENDED_SCALAR_CONTROL '+json.dumps(result,allow_nan=False),flush=True)
if __name__=='__main__':main()
