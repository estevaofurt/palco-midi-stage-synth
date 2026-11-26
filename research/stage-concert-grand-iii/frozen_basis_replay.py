"""G3.11d2: reuse independently computed operators for both frozen bases.
Also benchmark preassembled harmonic linear solves, not audio rendering."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from high_modal_allocation import require_archive,read
from graded_reference_audit import require_graded
from fixed_355_validation import require_fine,valid_metrics
from new_frequency_validation import require_basis,NEW,FREQ
from dual_cavity_spatial_diagnostic import compare_spatial
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from split_radiation import relative

CFG=[16]*6+[24]

def require_120(d,angle,sha):
    s=d.get('summary',{})
    expected=dict(gate=True,angleDeg=angle,diagnosticOnly=True,rankDistribution=CFG,modes=120,referenceModes=385,
        trainingMesh=[40,160,24],validationMesh=[50,200,32],fixedBasis=True,trainedOnFine=False,
        independentUpperMeshValidated=True,continuousFrequencyValidated=False,timeDomainReady=False,modalConvergenceCertified=False,radiationReady=False)
    if d.get('scaleSha256')!=sha or d.get('frequenciesHz')!=FREQ or any(s.get(k)!=v for k,v in expected.items()) or set(s.get('maximum',{}))!={'coarseModal','fineModal','fullSpatial','reducedSpatial','combined'} or not all(valid_metrics(v) for v in s['maximum'].values()):
        raise ValueError('invalid 120-mode frozen basis')

def require_new(d,angle,sha,basis_hash):
    s=d.get('summary',{})
    expected=dict(angleDeg=angle,diagnosticOnly=True,referenceModes=385,reducedModes=168,frozenBasis=True,
        heldOutFrequencies=list(NEW),trainingFrequencies=FREQ,approvedReactiveBlocks=28,continuousFrequencyValidated=False,
        modalConvergenceCertified=False,timeDomainReady=False,radiationReady=False)
    if d.get('scaleSha256')!=sha or d.get('frequenciesHz')!=list(NEW) or d.get('basisManifestSha256')!=basis_hash or any(s.get(k)!=v for k,v in expected.items()):
        raise ValueError('invalid independent operators')
    # 168-mode reduction may fail while the physical reference remains valid.
    if s.get('gate') is not valid_metrics(s.get('maximum',{})):raise ValueError('inconsistent reduction gate')
    rows=d.get('reactive',[])
    if [(v.get('panel'),v.get('otherPanel')) for v in rows]!=[(i,j) for i in range(7) for j in range(i,7)] or not all(v.get('gate') is True for v in rows):
        raise ValueError('incomplete reactive evidence')
    for key in ('smooth','reports'):
        rows=d.get(key,[])
        if [v.get('frequencyHz') for v in rows]!=list(NEW):raise ValueError('incomplete frequency evidence')
        if key=='smooth' and not all(v.get('gate') is True for v in rows):raise ValueError('unapproved smooth operator')
        if key=='reports' and not all(all(v.get(k,{}).get('gate') is True for k in ('upper','lower','coupled')) for v in rows):raise ValueError('unapproved reference solve')

def benchmark(A,B,T,repeats=21):
    """Factorization + four RHS, preprojected matrices; no projection in timing."""
    if repeats<3:raise ValueError('too few samples')
    a=T.T@A@T;b=T.T@B
    x=np.linalg.solve(a,b)
    if relative(a@x,b)>1e-8:raise ValueError('benchmark residual')
    times=[]
    for _ in range(repeats):
        t=time.perf_counter_ns();np.linalg.solve(a,b);times.append((time.perf_counter_ns()-t)*1e-6)
    return dict(modes=T.shape[1],medianMs=float(np.median(times)),p95Ms=float(np.percentile(times,95)),repeats=repeats)

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','basis120','basis168','out'):p.add_argument('--'+key,type=Path,required=True)
    for key in ('new','archive','consolidated','fine'):p.add_argument('--'+key,type=Path)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw)
    assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    d120=json.loads((a.basis120/'common_snapshot_transfer.json').read_text());require_120(d120,a.angle,sha)
    raw168=(a.basis168/'fixed_snapshot_transfer.json').read_bytes()
    d168=json.loads(raw168);require_basis(d168,a.angle,sha)
    maps={}
    for n,d,root,nu in ((120,d120,a.basis120,96),(168,d168,a.basis168,144)):
        b=read_npz(root,d['archive'],dict(Tu=(330,nu),Tl=(55,24),areas=(7,)),FREQ)
        T=block_diag(b['Tu'],b['Tl'])
        if np.iscomplexobj(T) or relative(T.T@T,np.eye(n))>1e-8 or np.any(b['areas']<=0):raise ValueError('invalid basis')
        maps[n]=b
    areas=maps[120]['areas']
    if relative(areas,maps[168]['areas'])>1e-10:raise ValueError('area mismatch')
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    nm=len(geometry(np.asarray(q['contourXY_m']),l,read('cabinet_geometry_hypothesis.json'))['microphonesXYZ_m'])
    if a.new:
        d=json.loads((a.new/'new_frequency_validation.json').read_text())
        require_new(d,a.angle,sha,hashlib.sha256(raw168).hexdigest())
        freq=list(NEW);nf=len(freq)
        z=read_npz(a.new,d['archive'],dict(Zu=(nf,334,334),Pu=(nf,nm,334),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385),Y=(nf,4,4),flow=(nf,385,4)),freq)
    else:
        if not all((a.archive,a.consolidated,a.fine)):raise ValueError('missing fine reference')
        d=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(d,a.angle,sha)
        fd=json.loads((a.fine/'graded_combined_refinement.json').read_text());require_fine(fd,a.angle,sha)
        ed=json.loads((a.consolidated/'consolidated_exterior.json').read_text());s=ed['summary']
        if ed['scaleSha256']!=sha or ed['frequenciesHz']!=FREQ or any(s.get(k)!=v for k,v in dict(gate=True,angleDeg=a.angle,approvedBlocks=28,sampledBlockQuadratureApproved=True,radiationReady=False).items()):
            raise ValueError('invalid exterior')
        freq=FREQ;nf=len(freq)
        sh=read_npz(a.archive,d['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),freq)
        ex=read_npz(a.consolidated,ed['archive'],dict(Ze=(nf,385,385),Y=(nf,4,4),flow=(nf,385,4)),freq)
        if relative(sh['areas'],areas)>1e-10 or not np.array_equal(sh['Ze'].real,ex['Ze'].real):raise ValueError('reference mismatch')
        z=read_npz(a.fine,fd['archive'],dict(Zu=(nf,334,334),Pu=(nf,nm,334),Y=(nf,4,4),flow=(nf,385,4)),freq)
        z.update(Zl=sh['Zl'],Pl=sh['Pl'],Ze=ex['Ze'],Pe=sh['Pe'])
    full=[];reduced={n:[] for n in maps};timing=[]
    for i,f in enumerate(freq):
        x=tuple(z[k][i] for k in ('Zu','Pu','Zl','Pl','Ze','Pe'))
        y,_=replay_full(*x,z['Y'][i],z['flow'][i],4);full.append(y)
        for n,b in maps.items():
            v,_=modal_replay(x,b['Tu'],b['Tl'],4,[55]*7,areas,y);reduced[n].append(v)
        if not a.new:
            Zu,_,Zl,_,Ze,_=x
            A=block_diag(Zu[4:,4:],Zl[4:,4:])+Ze;B=np.vstack([Zu[4:,:4],-Zl[4:,:4]])
            ts=[benchmark(A,B,np.eye(385))]
            for n,b in maps.items():ts.append(benchmark(A,B,block_diag(b['Tu'],b['Tl'])))
            timing.append(dict(frequencyHz=f,solves=ts))
    comps={str(n):compare_spatial(freq,v,full,[55]*7,areas) for n,v in reduced.items()}
    reference={'120':d120,'168':d168}
    for n,c in comps.items():
        old=d['summary']['maximum'] if a.new and n=='168' else reference[n]['summary']['maximum']['fineModal'] if not a.new else None
        if old is not None and any(abs(v-old[k])>1e-8 for k,v in c['maximum'].items()):raise ValueError('stored comparison mismatch')
    summary=dict(gate=all(v['gate'] for v in comps.values()),angleDeg=a.angle,diagnosticOnly=True,
        independentFrequencies=bool(a.new),sameOperators=True,noRetuning=True,maximum={k:v['maximum'] for k,v in comps.items()},
        candidateGates={k:v['gate'] for k,v in comps.items()},harmonicSolveBenchmark=not bool(a.new),timeDomainReady=False,radiationReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'frozen_basis_replay.json').write_text(json.dumps(dict(summary=summary,comparisons=comps,timing=timing,scaleSha256=sha,frequenciesHz=freq),indent=2,allow_nan=False))
    print('G3_FROZEN_REPLAY_GATE '+json.dumps(summary),flush=True)
    if timing:print('G3_HARMONIC_BENCHMARK '+json.dumps(timing),flush=True)
    if not summary['gate']:raise ValueError('candidate reduction failed')
if __name__=='__main__':main()
