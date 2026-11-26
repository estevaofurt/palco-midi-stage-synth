"""G3.10k: investigate failed disjoint enriched quadrature, without
relaxing subblock tolerance or using the result as a coupled reference."""
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
from dual_cavity_spatial_diagnostic import FREQ,save_matrices
from split_radiation import relative

TOL=1e-8
ORDERS=(56,64,72)
def scales(a,b):
    """Report subblock size and difference against full-block scale as
    diagnostics; the pass condition still uses the original relative error."""
    out={}
    for i,si in enumerate((slice(0,55),slice(55,None))):
        for j,sj in enumerate((slice(0,55),slice(55,None))):
            x=a[:,si,sj];y=b[:,si,sj]
            if not x.size:continue
            denom=np.maximum(np.linalg.norm(b,axis=(1,2)),1e-30)
            out[f'{i}{j}']=dict(maximumSubblockFraction=float(np.max(np.linalg.norm(y,axis=(1,2))/denom)),
                maximumDifferenceFraction=float(np.max(np.linalg.norm(x-y,axis=(1,2))/denom)))
    return out

def require_previous(d,angle,sha,inv,counts,idx):
    s=d.get('summary',{});rows=d.get('cases',[])
    expected=dict(angleDeg=angle,diagnosticOnly=True,modes=429,counts=counts,width=.06,kind='disjoint',modalConvergenceCertified=False,radiationReady=False)
    pairs=[(i,j) for i,j,k in inv if k=='disjoint']
    if d.get('scaleSha256')!=sha or d.get('polynomialIndices')!=idx.tolist() or d.get('inventory')!=[list(v) for v in inv] or any(s.get(k)!=v for k,v in expected.items()) or [(v.get('panel'),v.get('otherPanel')) for v in rows]!=pairs or s.get('blocks')!=len(pairs):
        raise ValueError('invalid disjoint archive')
    for v in rows:
        if v.get('kind')!='disjoint' or v.get('orders')!=[[40,0],[48,0]] or not isinstance(v.get('gate'),bool) or not all(np.isfinite(x) and x>=0 for x in [*v['changes'].values(),v['polynomialRestriction']]):
            raise ValueError('invalid disjoint evidence')
        if v['gate']!=(max(v['changes'].values())<=TOL and v['polynomialRestriction']<=TOL):
            raise ValueError('inconsistent disjoint gate')
    if s.get('approvedBlocks')!=sum(v['gate'] for v in rows) or s.get('gate')!=all(v['gate'] for v in rows):
        raise ValueError('invalid block count')
    return rows

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
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'disjoint_refinement.json';out=[];arrays={}
    for row in rows:
        i,j=row['panel'],row['otherPanel'];key=f'block_{i}_{j}';last=archived[key];order=48
        ref=prior['Ze'][:,55*i:55*(i+1),55*j:55*(j+1)].imag
        def restriction(X):return max(relative(u,v) for u,v in zip(X[:,:55,:55],ref))
        if abs(restriction(last)-row['polynomialRestriction'])>1e-10:raise ValueError('archived restriction mismatch')
        history=[];streak=0;gate=row['gate']
        if not gate:
            for n in ORDERS:
                start=time.perf_counter()
                _,x,w,A=panels[i].samples(n);_,y,v,B=panels[j].samples(n)
                _,X,_=pair_integrals(x,w[:,None]*A,y,v[:,None]*B,k,mutual=True,block=64);X*=factor
                changes=block_changes(last,X);r=restriction(X);passed=max(changes.values())<=TOL and r<=TOL
                streak=streak+1 if passed else 0
                item=dict(orders=[order,n],changes=changes,scales=scales(last,X),polynomialRestriction=r,gate=passed,seconds=time.perf_counter()-start)
                history.append(item);print('G3_DISJOINT_REFINEMENT_CASE '+json.dumps(dict(panel=i,otherPanel=j,**item)),flush=True)
                last=X;order=n
                if streak>=2:gate=True;break
        arrays[key]=last
        out.append(dict(panel=i,otherPanel=j,priorGate=row['gate'],finalOrder=order,history=history,gate=gate))
        path.write_text(json.dumps(dict(cases=out,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
    gate=all(r['gate'] for r in out)
    archive=save_matrices(a.out,'refined_disjoint',frequencies=FREQ,**arrays)
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,blocks=len(out),approvedBlocks=sum(r['gate'] for r in out),
        previousApproved=sum(r['priorGate'] for r in out),modes=429,subblockTolerance=TOL,requiredConsecutivePasses=2,
        modalConvergenceCertified=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=out,archive=archive,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_DISJOINT_REFINEMENT_GATE '+json.dumps(summary),flush=True)
    if not gate:raise ValueError('disjoint enriched quadrature remains unverified')
if __name__=='__main__':main()
