"""G3.10m: promote only independently verified disjoint block evidence.
Preserve the original archive; the output is a separate coupling input."""
import argparse,hashlib,json,math
from pathlib import Path
import numpy as np
from acoustic_matrix_archive import read_npz
from dual_cavity_spatial_diagnostic import FREQ,save_matrices
from disjoint_enriched_refinement import require_previous,TOL,ORDERS
from enriched_reactive_diagnostic import block_changes
from split_radiation import relative

COUNTS=[61,63,63,63,63,61,55]
IDX=np.concatenate([np.arange(j,j+55) for j in np.r_[0,np.cumsum(COUNTS)[:-1]]])

def check_history(old,new):
    if new.get('priorGate') is not old['gate'] or new.get('gate') is not True:
        raise ValueError('block not approved')
    h=new.get('history',[])
    if old['gate']:
        if h or new.get('finalOrder')!=48:raise ValueError('reused block changed')
        return
    if not 2<=len(h)<=len(ORDERS):raise ValueError('missing consecutive evidence')
    prev=48;streak=0
    for j,row in enumerate(h):
        n=ORDERS[j]
        if row.get('orders')!=[prev,n] or set(row.get('changes',{}))!=set(old['changes']):
            raise ValueError('invalid order sequence')
        vals=[*row['changes'].values(),row['polynomialRestriction']]
        if not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>=0 for v in vals):
            raise ValueError('invalid error metric')
        passed=max(vals)<=TOL
        if row.get('gate') is not passed:raise ValueError('inconsistent history gate')
        streak=streak+1 if passed else 0
        prev=n
        if streak>=2 and j!=len(h)-1:raise ValueError('unexpected extra orders')
    if streak<2 or new.get('finalOrder')!=prev:raise ValueError('missing successive convergence')

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','previous','refined','consolidated','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    sha=hashlib.sha256(a.scale.read_bytes()).hexdigest()
    old=json.loads((a.previous/'enriched_reactive.json').read_text())
    new=json.loads((a.refined/'disjoint_refinement.json').read_text())
    inv=[tuple(v) for v in old['inventory']]
    if len(inv)!=28 or {(i,j) for i,j,k in inv}!={(i,j) for i in range(7) for j in range(i,7)} or sum(k=='disjoint' for i,j,k in inv)!=16:
        raise ValueError('invalid inventory')
    rows=require_previous(old,a.angle,sha,inv,COUNTS,IDX)
    s=new['summary'];expected=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,blocks=16,approvedBlocks=16,
        previousApproved=sum(v['gate'] for v in rows),modes=429,subblockTolerance=TOL,requiredConsecutivePasses=2,modalConvergenceCertified=False,radiationReady=False)
    if new.get('scaleSha256')!=sha or new.get('frequenciesHz')!=FREQ or any(s.get(k)!=v for k,v in expected.items()):
        raise ValueError('refined evidence not approved')
    pairs=[(v['panel'],v['otherPanel']) for v in rows];nr=new['cases']
    if [(v['panel'],v['otherPanel']) for v in nr]!=pairs:raise ValueError('different block inventory')
    shapes={f'block_{i}_{j}':(len(FREQ),COUNTS[i],COUNTS[j]) for i,j in pairs}
    previous=read_npz(a.previous,old['archive'],shapes,FREQ)
    final=read_npz(a.refined,new['archive'],shapes,FREQ)
    ex=json.loads((a.consolidated/'consolidated_exterior.json').read_text());es=ex['summary']
    if ex.get('scaleSha256')!=sha or ex.get('frequenciesHz')!=FREQ or es.get('angleDeg')!=a.angle or es.get('gate') is not True or es.get('approvedBlocks')!=28 or es.get('radiationReady') is not False:raise ValueError('invalid polynomial reference')
    nf=len(FREQ)
    prior=read_npz(a.consolidated,ex['archive'],dict(Ze=(nf,385,385),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    result=[]
    for x,y in zip(rows,nr):
        check_history(x,y)
        i,j=x['panel'],x['otherPanel'];key=f'block_{i}_{j}';v=final[key]
        ref=prior['Ze'][:,55*i:55*(i+1),55*j:55*(j+1)].imag
        restriction=max(relative(u,w) for u,w in zip(v[:,:55,:55],ref))
        if restriction>TOL:raise ValueError('polynomial restriction failed')
        if x['gate'] and not np.array_equal(v,previous[key]):raise ValueError('reused matrix changed')
        result.append(dict(panel=i,otherPanel=j,gate=True,priorGate=x['gate'],finalOrder=y['finalOrder'],
            polynomialRestriction=restriction,history=y['history'],originalChanges=x['changes']))
    a.out.mkdir(parents=True,exist_ok=True)
    archive=save_matrices(a.out,'verified_disjoint',frequencies=FREQ,**final)
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,modes=429,counts=COUNTS,width=.06,kind='disjoint',
        blocks=16,approvedBlocks=16,reactiveQuadratureApproved=True,modalConvergenceCertified=False,radiationReady=False)
    provenance=dict(previousArchive=old['archive'],refinedArchive=new['archive'],polynomialArchive=ex['archive'],
        previousManifestSha256=hashlib.sha256((a.previous/'enriched_reactive.json').read_bytes()).hexdigest(),
        refinedManifestSha256=hashlib.sha256((a.refined/'disjoint_refinement.json').read_bytes()).hexdigest())
    (a.out/'enriched_reactive.json').write_text(json.dumps(dict(summary=summary,cases=result,inventory=old['inventory'],
        polynomialIndices=IDX.tolist(),archive=archive,provenance=provenance,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_VERIFIED_DISJOINT_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
