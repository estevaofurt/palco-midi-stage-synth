"""Archived 385-mode diagnostic: separate omitted modal energy from
resolved-flow error, and test selective enrichment without new FEM solves.
Selection is retrospective on the six sampled frequencies only.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from nested_acoustic_ports import embedding,reduced_panels
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def require_archive(doc,angle,sha):
    s=doc.get('summary',{})
    expected=dict(gate=True,angleDeg=angle,diagnosticOnly=True,maximumModes=385,upperConfig=[40,160,24],lowerN=72,
        commonFreeSpaceMonopolesOnly=True,quadratureConvergenceCertified=False,fullCabinetReady=False,radiationReady=False)
    if doc.get('scaleSha256')!=sha or doc.get('frequenciesHz')!=FREQ or any(s.get(k)!=v for k,v in expected.items()):
        raise ValueError('invalid 385-mode archive provenance')
    rows=doc.get('reports',[])
    if [r.get('frequencyHz') for r in rows]!=FREQ or any(any(r.get(k,{}).get('gate') is not True for k in ('upper','lower','exterior','coupled')) for r in rows):
        raise ValueError('incomplete acoustic checks')

def degree_energy(F,areas):
    F=np.asarray(F);areas=np.asarray(areas,float)
    if F.ndim!=2 or F.shape[0]!=55*len(areas) or np.any(areas<=0) or not np.isfinite(areas).all() or not np.isfinite(F).all():
        raise ValueError('invalid flux spectrum')
    bins=np.arange(1,11);ends=bins*(bins+1)//2;starts=np.r_[0,ends[:-1]]
    E=np.array([[np.linalg.norm(F[55*i+a:55*i+b])**2/A for a,b in zip(starts,ends)] for i,A in enumerate(areas)])
    total=E.sum()
    if total<=0:raise ValueError('zero reference flow')
    return E/total

def score(report):
    return report['maximum']['physicalVelocityRelative']

def select_next(current,proposals):
    if not proposals or any(len(x)!=len(current) or sum(a!=b for a,b in zip(x,current))!=1 for x,_ in proposals):
        raise ValueError('invalid single-panel proposals')
    return min(proposals,key=lambda pair:(score(pair[1]),max(pair[1]['maximum'].values()),pair[0]))

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));nm=len(g['microphonesXYZ_m']);nf=len(FREQ)
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,ports,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate'] and len(ports)==7
    areas=np.array([v.basis.area for v in ports]);counts=[55]*7
    sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    up=read_npz(a.archive,doc['upper'],dict(Zu=(nf,334,334),Pu=(nf,nm,334),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    assert relative(areas,sh['areas'])<=1e-10
    mats=[];full=[];replay=[];spectra=[]
    for i,f in enumerate(FREQ):
        x=tuple(v[i] for v in (up['Zu'],up['Pu'],sh['Zl'],sh['Pl'],sh['Ze'],sh['Pe']))
        y,d=replay_full(*x,up['Y'][i],up['flow'][i],4);mats.append(x);full.append(y);replay.append(d)
        E=degree_energy(y[-1],areas);spectra.append(dict(frequencyHz=f,degreeEnergyFractions=E.tolist(),
            panelEnergyFractions=E.sum(1).tolist(),degreeNineEnergyFraction=E[:,-1].tolist()))
    maps={}
    for i,panel in enumerate(ports):
        for n in (36,45,55):
            lo=reduced_panels([panel],[n]);T,_=embedding([panel],lo,order=18)
            # Verify that the QR basis is ordered by polynomial degree.
            expected=np.eye(55)[:,:n]
            if relative(T@T.T,expected@expected.T)>1e-8:raise ValueError('degree ordering not certified')
            maps[i,n]=T
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'high_modal_allocation.json';cache={};steps=[]
    def evaluate(cfg):
        if cfg in cache:return cache[cfg]
        T=[maps[i,n] for i,n in enumerate(cfg)];Tu=block_diag(*T[:6]);Tl=T[-1]
        vals=[];reports=[]
        for f,x,y in zip(FREQ,mats,full):
            v,r=modal_replay(x,Tu,Tl,4,counts,areas,y);vals.append(v);reports.append(dict(frequencyHz=f,**r))
        comp=compare_spatial(FREQ,vals,full,counts,areas)
        comp.update(counts=list(cfg),totalModes=sum(cfg),maximumOmitted=max(r['flow']['omittedRelative'] for r in reports),
            maximumResolved=max(r['flow']['resolvedRelative'] for r in reports),reports=reports)
        cache[cfg]=comp;return comp
    current=(45,)*7;baseline=evaluate(current)
    # Match archived global 45->55 comparison independently.
    for key,value in doc['summary']['comparisons']['modal45to55'].items():
        if abs(baseline['maximum'][key]-value)>1e-8:raise ValueError('archived modal comparison mismatch')
    while True:
        best=evaluate(current)
        step=dict(counts=list(current),totalModes=sum(current),maximum=best['maximum'],gate=best['gate'],
            maximumOmitted=best['maximumOmitted'],maximumResolved=best['maximumResolved'])
        steps.append(step);print('G3_ALLOCATION_STEP '+json.dumps(step),flush=True)
        path.write_text(json.dumps(dict(steps=steps,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        if best['gate'] or all(n==55 for n in current):break
        proposals=[]
        for i,n in enumerate(current):
            if n==55:continue
            nxt=list(current);nxt[i]=55;nxt=tuple(nxt);proposals.append((nxt,evaluate(nxt)))
        current,_=select_next(current,proposals)
    # Independently test lower 36 and 45 with full upper space.
    for cfg in ((55,)*6+(36,),(55,)*6+(45,)):evaluate(cfg)
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,reusedMatrices=True,referenceModes=385,
        maximumReplayDifference=max(max(v.values()) for v in replay),evaluatedConfigurations=len(cache),
        selectedCounts=list(current),selectedModes=sum(current),selectedRelativeTo385Gate=steps[-1]['gate'],
        retrospectiveSelection=True,modalConvergenceCertified=False,quadratureConvergenceCertified=False,
        fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,steps=steps,spectra=spectra,cases=list(cache.values()),scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_ALLOCATION_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
