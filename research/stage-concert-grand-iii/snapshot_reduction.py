"""G3.11a: provisional snapshot reduction on the archived 385-mode
graded reference. Leave one frequency out; no new FEM or time-domain fit."""
import argparse,hashlib,json
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

RANKS=(2,4,8,12,16,24,32)

def snapshot_bases(flows,counts,areas,rank):
    """Real per-panel bases from complex training snapshots. Normalize
    each frequency/board excitation by its total physical velocity norm."""
    flows=np.asarray(flows);areas=np.asarray(areas,float)
    if flows.ndim!=3 or flows.shape[1]!=sum(counts) or areas.shape!=(len(counts),) or not np.isfinite(flows).all() or not np.isfinite(areas).all() or np.any(areas<=0) or not isinstance(rank,int) or rank<1:raise ValueError('invalid snapshots')
    w=np.repeat(1/np.sqrt(areas),counts)
    scale=np.maximum(np.linalg.norm(flows*w[None,:,None],axis=1),1e-30)
    X=(flows/scale[:,None,:]).transpose(1,0,2).reshape(sum(counts),-1)
    bases=[];spectra=[];off=0
    for n in counts:
        z=X[off:off+n];off+=n
        U,S,_=np.linalg.svd(np.column_stack([z.real,z.imag]),full_matrices=False)
        if not len(S) or S[0]<=0:raise ValueError('empty panel snapshot energy')
        k=min(rank,int(np.sum(S>1e-12*S[0])))
        bases.append(U[:,:k]);spectra.append(S.tolist())
    return bases,spectra

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
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'snapshot_reduction.json';results=[]
    for rank in RANKS:
        vals=[];folds=[]
        for i,f in enumerate(FREQ):
            train=[j for j in range(len(FREQ)) if j!=i]
            bases,spectra=snapshot_bases([full[j][-1] for j in train],counts,areas,rank)
            Tu=block_diag(*bases[:6]);Tl=bases[-1]
            z,rep=modal_replay(mats[i],Tu,Tl,4,counts,areas,full[i]);vals.append(z)
            folds.append(dict(heldOutHz=f,trainingHz=[FREQ[j] for j in train],counts=[b.shape[1] for b in bases],singularValues=spectra,
                pressureDefect=rep['pressureDefect'],omittedRelative=rep['flow']['omittedRelative']))
        comp=compare_spatial(FREQ,vals,full,counts,areas)
        row=dict(rankLimit=rank,maximumModes=max(sum(x['counts']) for x in folds),gate=comp['gate'],comparison=comp,folds=folds)
        results.append(row);print('G3_SNAPSHOT_RANK '+json.dumps(dict(rankLimit=rank,maximumModes=row['maximumModes'],gate=row['gate'],maximum=comp['maximum']),allow_nan=False),flush=True)
        path.write_text(json.dumps(dict(complete=False,cases=results,scaleSha256=sha),indent=2,allow_nan=False))
    good=[v for v in results if v['gate']]
    selected=min(good,key=lambda v:(v['maximumModes'],v['rankLimit'])) if good else None
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,referenceModes=385,leaveOneFrequencyOut=True,
        provisionalRank=None if selected is None else selected['rankLimit'],provisionalModes=None if selected is None else selected['maximumModes'],
        reductionGate=bool(good),independentGeometryValidated=False,continuousFrequencyValidated=False,
        timeDomainReady=False,modalConvergenceCertified=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=results,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_SNAPSHOT_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
