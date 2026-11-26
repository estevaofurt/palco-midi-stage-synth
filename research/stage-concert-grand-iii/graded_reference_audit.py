"""Archive-only sensitivity and exhaustive 45/55 allocation on the
approved graded 385-mode reference. No new PDE or physical calibration."""
import argparse,hashlib,json,itertools
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from high_modal_allocation import require_archive,degree_energy,read
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from nested_acoustic_ports import embedding,reduced_panels
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial
from coupling_sensitivity import prepare,compare_sensitivity
from split_radiation import relative

def require_graded(d,angle,sha):
    s=d.get('summary',{})
    expected=dict(gate=True,angleDeg=angle,diagnosticOnly=True,upperConfig=[40,160,24],edgeGrading=.5,layerGrading=.5,
        modes=385,algebraicStabilityGate=True,gradedVsUniformGate=True,reusedLowerAndExterior=True,radiationReady=False)
    if d.get('scaleSha256')!=sha or d.get('frequenciesHz')!=FREQ or any(s.get(k)!=v for k,v in expected.items()):
        raise ValueError('invalid graded archive')
    if [v.get('frequencyHz') for v in d['reports']]!=FREQ or any(not v['upper']['gate'] or not v['coupled']['gate'] for v in d['reports']):
        raise ValueError('incomplete graded report')

def configurations(k):
    if not isinstance(k,int) or isinstance(k,bool) or not 0<=k<=7:raise ValueError('invalid mode budget')
    return [tuple(55 if i in active else 45 for i in range(7)) for active in itertools.combinations(range(7),k)]

def choose(rows):
    approved=[x for x in rows if x['gate']]
    if not approved:raise ValueError('no approved allocation')
    return min(approved,key=lambda x:(sum(x['counts']),x['maximum']['physicalVelocityRelative'],max(x['maximum'].values()),x['counts']))

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
    mats=[];full=[];old=[];sensitivity=[];spectra=[]
    for i,f in enumerate(FREQ):
        x=tuple(v[i] for v in (up['Zu'],up['Pu'],sh['Zl'],sh['Pl'],prior['Ze'],sh['Pe']))
        y,_=replay_full(*x,prior['Y'][i],prior['flow'][i],4)
        z=(gr['Zu'][i],gr['Pu'][i],*x[2:]);v,_=replay_full(*z,gr['Y'][i],gr['flow'][i],4)
        old.append(y);full.append(v);mats.append(z)
        A=prepare(x[0],x[2],x[4],4,counts,areas);B=prepare(z[0],z[2],z[4],4,counts,areas)
        rr=compare_sensitivity(A,B,y[-1],v[-1])
        sensitivity.append(dict(frequencyHz=f,oldCondition=A['report'],gradedCondition=B['report'],**rr))
        spectra.append(dict(frequencyHz=f,degreeEnergy=degree_energy(v[-1],areas).tolist()))
    compare=compare_spatial(FREQ,old,full,counts,areas)
    assert all(abs(v-gd['summary']['comparison'][k])<=1e-8 for k,v in compare['maximum'].items())
    # Prefix projectors are proven against the actual QR bases, not assumed.
    for panel in ports:
        lo=reduced_panels([panel],[45]);T,_=embedding([panel],lo,order=18);Q=np.eye(55)[:,:45]
        assert relative(T@T.T,Q@Q.T)<=1e-8
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'graded_reference_audit.json';rows=[]
    for k in range(8):
        for cfg in configurations(k):
            T=[np.eye(55)[:,:n] for n in cfg];Tu=block_diag(*T[:6]);Tl=T[-1]
            vals=[];om=[];res=[]
            for x,y in zip(mats,full):
                v,r=modal_replay(x,Tu,Tl,4,counts,areas,y);vals.append(v);om.append(r['flow']['omittedRelative']);res.append(r['flow']['resolvedRelative'])
            c=compare_spatial(FREQ,vals,full,counts,areas)
            rows.append(dict(counts=list(cfg),totalModes=sum(cfg),gate=c['gate'],maximum=c['maximum'],maximumOmitted=max(om),maximumResolved=max(res)))
        print('G3_GRADED_BUDGET '+json.dumps(dict(totalModes=315+10*k,evaluated=len(configurations(k)),approved=sum(v['gate'] for v in rows if v['totalModes']==315+10*k))),flush=True)
        path.write_text(json.dumps(dict(cases=rows,sensitivity=sensitivity,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
    assert len(rows)==128
    best=choose(rows);previous=next(v for v in rows if v['counts']==s['selectedCounts'])
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,referenceModes=385,exhaustiveBinaryAllocations=128,
        selected=best,previousSelection=previous,retrospectiveSelection=True,maximumSensitivityClosure=max(v['decompositionClosure'] for v in sensitivity),
        maximumGradedPhysicalCondition=max(v['gradedCondition']['physicalCondition'] for v in sensitivity),modalConvergenceCertified=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,sensitivity=sensitivity,spectra=spectra,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_GRADED_REFERENCE_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
