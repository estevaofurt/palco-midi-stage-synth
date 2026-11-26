"""Couple only after every 429-mode prerequisite is approved."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from enriched_smooth_diagnostic import read
from enriched_aperture_reference import enrich,restrict
from high_modal_allocation import require_archive
from high_modal_remaining_reactive import classify
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from dual_cavity_reference import couple
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial,save_matrices
from split_radiation import relative

def require(d,angle,sha,extra):
    if d.get('scaleSha256')!=sha or d.get('frequenciesHz')!=FREQ or any(d.get('summary',{}).get(k)!=v for k,v in dict(gate=True,angleDeg=angle,diagnosticOnly=True,radiationReady=False,**extra).items()):
        raise ValueError('incomplete enriched evidence')

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','archive','smooth','self','contact','disjoint','upper','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));nf=len(FREQ);nm=len(g['microphonesXYZ_m'])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,old,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate']
    panels,counts,idx,basis=enrich(old);areas=np.array([v.basis.area for v in panels]);offsets=np.r_[0,np.cumsum(counts)];inv=classify(panels)
    sd=json.loads((a.smooth/'enriched_smooth.json').read_text());require(sd,a.angle,sha,dict(modes=429,counts=counts,width=.06,smoothQuadratureApproved=True))
    assert sd['polynomialIndices']==idx.tolist()
    sm=read_npz(a.smooth,sd['archive'],dict(R=(nf,429,429),Pe=(nf,2,429)),FREQ)
    ud=json.loads((a.upper/'enriched_upper.json').read_text());require(ud,a.angle,sha,dict(modes=374,counts=counts[:6],width=.06,algebraicStabilityGate=True))
    assert ud['polynomialIndices']==np.r_[np.arange(4),4+idx[:330]].tolist()
    up=read_npz(a.upper,ud['archive'],dict(Zu=(nf,378,378),Pu=(nf,nm,378)),FREQ)
    sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    assert relative(areas,sh['areas'])<=1e-10
    X=np.zeros((nf,429,429));used=[]
    for kind in ('self','contact','disjoint'):
        root=getattr(a,kind);d=json.loads((root/'enriched_reactive.json').read_text());pairs=[(i,j) for i,j,k in inv if k==kind]
        require(d,a.angle,sha,dict(modes=429,counts=counts,width=.06,kind=kind,blocks=len(pairs),approvedBlocks=len(pairs),reactiveQuadratureApproved=True))
        assert d['inventory']==[list(v) for v in inv] and d['polynomialIndices']==idx.tolist()
        assert [(v['panel'],v['otherPanel']) for v in d['cases']]==pairs and all(v['gate'] for v in d['cases'])
        arrays=read_npz(root,d['archive'],{f'block_{i}_{j}':(nf,counts[i],counts[j]) for i,j in pairs},FREQ)
        for i,j in pairs:
            I=slice(offsets[i],offsets[i+1]);J=slice(offsets[j],offsets[j+1]);v=arrays[f'block_{i}_{j}'];X[:,I,J]=v
            if i!=j:X[:,J,I]=v.transpose(0,2,1)
            used.append((i,j))
    assert len(set(used))==28
    Ze=sm['R']+1j*X;Tu=np.eye(374)[:,idx[:330]];Tl=np.eye(55);full=[];reduced=[];reports=[]
    for i,f in enumerate(FREQ):
        x=tuple(v[i] for v in (up['Zu'],up['Pu'],sh['Zl'],sh['Pl'],Ze,sm['Pe']))
        *y,r=couple(*x,4,reference_kind='common-free-space-monopole');assert r['gate'];full.append(tuple(y))
        z,rr=modal_replay(x,Tu,Tl,4,counts,areas,y);reduced.append(z)
        reports.append(dict(frequencyHz=f,coupled=r,polynomial=rr))
    comp=compare_spatial(FREQ,reduced,full,counts,areas)
    a.out.mkdir(parents=True,exist_ok=True)
    archive=save_matrices(a.out,'enriched_coupled',frequencies=FREQ,Ze=Ze,Y=np.stack([v[0] for v in full]),flow=np.stack([v[-1] for v in full]))
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,modes=429,approvedBlocks=28,polynomial385RelativeGate=comp['gate'],
        comparison=comp['maximum'],modalConvergenceCertified=False,fullCabinetReady=False,radiationReady=False)
    (a.out/'enriched_coupled.json').write_text(json.dumps(dict(summary=summary,reports=reports,comparison=comp,archive=archive,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_ENRICH_COUPLED_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
