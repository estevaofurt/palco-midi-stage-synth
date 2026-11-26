"""G3.11c: exhaustive binary allocation of snapshot ranks by panel.
Train only on five coarse frequencies per fold; choose a common rank
distribution retrospectively across both angles. No fine data used."""
import argparse,hashlib,itertools,json,math
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from high_modal_allocation import require_archive,read
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial
from graded_reference_audit import require_graded
from split_radiation import relative
from snapshot_reduction import snapshot_bases
from fixed_355_validation import METRICS,valid_metrics

def configurations():
    return list(itertools.product((16,24),repeat=7))

def choose(rows):
    good=[r for r in rows if r['gate']]
    return min(good,key=lambda r:(sum(r['counts']),max(r['maximum'].values()),r['counts'])) if good else None

def require_report(d,angle,sha):
    s=d.get('summary',{});rows=d.get('cases',[])
    expected=dict(gate=True,angleDeg=angle,diagnosticOnly=True,referenceModes=385,leaveOneFrequencyOut=True,
        trainedOnFine=False,exhaustiveAllocations=128,retrospectiveSelection=True,timeDomainReady=False,radiationReady=False)
    if d.get('scaleSha256')!=sha or d.get('frequenciesHz')!=FREQ or any(s.get(k)!=v for k,v in expected.items()) or [tuple(v.get('counts',[])) for v in rows]!=configurations():
        raise ValueError('invalid allocation evidence')
    for r in rows:
        m=r.get('maximum',{})
        if set(m)!=METRICS or not all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in m.values()) or r.get('gate') is not valid_metrics(m) or r.get('totalModes')!=sum(r['counts']):
            raise ValueError('invalid allocation metric')
    if s.get('selected')!=choose(rows):raise ValueError('inconsistent allocation selection')
    return rows

def common_report(d30,d55,sha):
    rows=[]
    for a,b in zip(require_report(d30,30.,sha),require_report(d55,55.,sha)):
        m={k:max(a['maximum'][k],b['maximum'][k]) for k in sorted(METRICS)}
        rows.append(dict(counts=a['counts'],totalModes=a['totalModes'],gate=valid_metrics(m),maximum=m))
    chosen=choose(rows)
    return dict(summary=dict(gate=True,diagnosticOnly=True,angles=[30,55],exhaustiveAllocations=128,retrospectiveSelection=True,
        commonSelection=chosen,selectionApproved=chosen is not None,trainedOnFine=False,timeDomainReady=False,radiationReady=False),
        cases=rows,scaleSha256=sha,frequenciesHz=FREQ)

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','archive','consolidated','graded','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    ex=json.loads((a.consolidated/'consolidated_exterior.json').read_text());s=ex['summary']
    assert ex['scaleSha256']==sha and ex['frequenciesHz']==FREQ and s['gate'] and s['angleDeg']==a.angle and s['approvedBlocks']==28 and s['diagnosticOnly'] and not s['radiationReady']
    gd=json.loads((a.graded/'graded_cavity_replay.json').read_text());require_graded(gd,a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));nf=len(FREQ);nm=len(g['microphonesXYZ_m'])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,ports,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate'] and len(ports)==7
    areas=np.array([v.basis.area for v in ports]);counts=[55]*7
    sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    shapes=dict(Zu=(nf,334,334),Pu=(nf,nm,334),Y=(nf,4,4),flow=(nf,385,4))
    up=read_npz(a.archive,doc['upper'],shapes,FREQ);gr=read_npz(a.graded,gd['archive'],shapes,FREQ)
    prior=read_npz(a.consolidated,ex['archive'],dict(Ze=(nf,385,385),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    assert relative(areas,sh['areas'])<=1e-10 and np.array_equal(prior['Ze'].real,sh['Ze'].real)
    mats=[];full=[]
    for i,f in enumerate(FREQ):
        x=tuple(v[i] for v in (gr['Zu'],gr['Pu'],sh['Zl'],sh['Pl'],prior['Ze'],sh['Pe']))
        y,_=replay_full(*x,gr['Y'][i],gr['flow'][i],4);mats.append(x);full.append(y)
    # Cache the 24-dimensional training subspace for each fold.
    folded=[]
    for i in range(len(FREQ)):
        bases,_=snapshot_bases([v[-1] for j,v in enumerate(full) if j!=i],counts,areas,24)
        if any(b.shape[1]!=24 for b in bases):raise ValueError('unexpected rank deficiency')
        folded.append(bases)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'snapshot_allocation.json';rows=[]
    for cfg in configurations():
        vals=[]
        for i,bases in enumerate(folded):
            T=[b[:,:n] for b,n in zip(bases,cfg)]
            v,_=modal_replay(mats[i],block_diag(*T[:6]),T[-1],4,counts,areas,full[i]);vals.append(v)
        c=compare_spatial(FREQ,vals,full,counts,areas)
        rows.append(dict(counts=list(cfg),totalModes=sum(cfg),gate=c['gate'],maximum=c['maximum']))
    selected=choose(rows)
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,referenceModes=385,leaveOneFrequencyOut=True,
        trainedOnFine=False,exhaustiveAllocations=128,retrospectiveSelection=True,timeDomainReady=False,radiationReady=False,
        selected=selected,approvedAllocations=sum(r['gate'] for r in rows))
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_SNAPSHOT_ALLOCATION_GATE '+json.dumps(summary),flush=True)

def consolidate():
    p=argparse.ArgumentParser()
    for k in ('scale','angle30','angle55','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();sha=hashlib.sha256(a.scale.read_bytes()).hexdigest()
    d=common_report(json.loads(a.angle30.read_text()),json.loads(a.angle55.read_text()),sha)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'snapshot_common_allocation.json').write_text(json.dumps(d,indent=2,allow_nan=False))
    print('G3_SNAPSHOT_COMMON_GATE '+json.dumps(d['summary']),flush=True)

if __name__=='__main__':
    import sys
    if len(sys.argv)>1 and sys.argv[1]=='common':
        del sys.argv[1];consolidate()
    else:main()
