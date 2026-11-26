"""G3.10q: full edge-edge block extended precision pilot at one frequency.
Keep weighted samples fixed per quadrature order; no alteration of basis or physics."""
import argparse,hashlib,json,time
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
from dual_cavity_spatial_diagnostic import FREQ,save_matrices
from disjoint_enriched_refinement import require_previous,TOL
from disjoint_extended_scalar_control import scalar_integral

def extended_block(x,A,y,B,k,block=32):
    """Compute a narrow matrix, not a dense all-mode operator.
    Kernel evaluated once per tile, then reused for all columns."""
    dtype=np.longdouble
    x,A,y,B=(np.asarray(v,dtype=dtype) for v in (x,A,y,B))
    k=dtype(k)
    if x.ndim!=2 or y.ndim!=2 or x.shape[1:]!=(3,) or y.shape[1:]!=(3,) or A.ndim!=2 or B.ndim!=2 or len(x)!=len(A) or len(y)!=len(B) or min(len(x),len(y),A.shape[1],B.shape[1])<1 or block<1 or not all(np.isfinite(v).all() for v in (x,A,y,B,k)) or k<=0:raise ValueError('invalid extended block input')
    total=np.zeros((A.shape[1],B.shape[1]),dtype=dtype);correction=np.zeros_like(total)
    for i in range(0,len(x),block):
        z=x[i:i+block,None,:]-y[None,:,:];D=np.sqrt(np.sum(z*z,axis=-1,dtype=dtype))
        if np.any(D<=0):raise ValueError('coincident nodes')
        K=np.cos(k*D)/D
        tile=A[i:i+block].T@(K@B)
        q=tile-correction;t=total+q;correction=(t-total)-q;total=t
    return total

def rel(a,b):
    a,b=map(lambda v:np.asarray(v,dtype=np.longdouble),(a,b))
    return float(np.sqrt(np.sum((a-b)**2))/max(np.sqrt(np.sum(b*b)),np.longdouble('1e-30')))

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
    i,j=0,4;key=f'block_{i}_{j}';row=next(v for v in rows if (v['panel'],v['otherPanel'])==(i,j))
    if row['gate']:raise ValueError('expected unresolved block')
    f=FREQ.index(30. if a.angle==30 else 80.)
    a.out.mkdir(parents=True,exist_ok=True)
    history=[];arrays={};last=None;streak=0
    for order in (40,48,56):
        start=time.perf_counter()
        _,x,w,A=panels[i].samples(order);_,y,v,B=panels[j].samples(order)
        A=w[:,None]*A[:,55:];B=v[:,None]*B[:,55:]
        factor64=np.longdouble(factor[f,0,0])
        forward=extended_block(x,A,y,B,k[f])*factor64
        reverse=extended_block(y,B,x,A,k[f],block=48).T*factor64
        reverse_error=rel(forward,reverse);change=None if last is None else rel(last,forward)
        m,n=np.unravel_index(np.argmax(np.abs(forward-reverse)),forward.shape)
        direct=scalar_integral(x,A[:,m],y,B[:,n],k[f])*factor64
        scalar_error=float(abs(forward[m,n]-direct)/max(np.sqrt(np.sum(forward**2)),np.longdouble('1e-30')))
        passed=change is not None and max(change,reverse_error,scalar_error)<=TOL
        streak=streak+1 if passed else 0
        item=dict(order=order,reversalRelative=reverse_error,orderChangeRelative=change,scalarControlRelativeToBlock=scalar_error,
            archived48Relative=rel(archived[key][f,55:,55:],forward) if order==48 else None,gate=passed,seconds=time.perf_counter()-start)
        history.append(item);arrays[f'forward_{order}']=forward.astype(float);arrays[f'reverse_{order}']=reverse.astype(float)
        last=forward
        print('G3_EXTENDED_EDGE_BLOCK_CASE '+json.dumps(item,allow_nan=False),flush=True)
        (a.out/'extended_edge_block.json').write_text(json.dumps(dict(complete=False,cases=history),indent=2,allow_nan=False))
    archive=save_matrices(a.out,'extended_edge_block',frequencies=[FREQ[f]],**arrays)
    summary=dict(gate=True,angleDeg=a.angle,frequencyHz=FREQ[f],panel=i,otherPanel=j,diagnosticOnly=True,
        edgeEdgeConsecutiveGate=streak>=2,precisionMantissaBits=int(np.finfo(np.longdouble).nmant+1),extendedBasisEvaluation=False,
        quadratureCertified=False,modalConvergenceCertified=False,radiationReady=False)
    (a.out/'extended_edge_block.json').write_text(json.dumps(dict(summary=summary,cases=history,archive=archive,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_EXTENDED_EDGE_BLOCK_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
