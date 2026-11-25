"""Consolidate approved sampled 385-mode exterior block evidence.
The original smooth resistance and observer map are retained because their
independent surface/angle audits passed. This is a monopole diagnostic.
"""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from high_modal_allocation import require_archive
from high_modal_remaining_reactive import classify,compare_self,compare_pair
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from shared_edge_modal_replay import replace_block
from dual_cavity_reference import couple
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial,save_matrices
from nested_acoustic_ports import reduced_panels,embedding
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def require(doc,angle,sha,keys):
    if doc.get('scaleSha256')!=sha or any(doc.get('summary',{}).get(k)!=v for k,v in dict(gate=True,angleDeg=angle,diagnosticOnly=True,radiationReady=False,**keys).items()):
        raise ValueError('invalid source evidence')

def block_keys(inv,kind):
    return [(i,j) for i,j,k in inv if k==kind]

def apply_remaining(Z,original,arrays,pairs,kind,omega,count=55):
    scale=1.204*omega[:,None,None]/(4*np.pi);rows=[]
    for i,j in pairs:
        I=slice(count*i,count*(i+1));J=slice(count*j,count*(j+1))
        vals=arrays[f'block_{i}_{j}'];raw=original[:,I,J].imag/scale
        if not np.array_equal(Z[:,I,J],original[:,I,J]):raise ValueError('overlapping corrections')
        rep=compare_self(vals,raw) if kind=='self' else compare_pair(vals,raw)
        if not rep['gate']:raise ValueError('recomputed block gate failed')
        fine=vals[-1]
        if kind=='self':
            fine=(fine+fine.transpose(0,2,1))/2
            Z[:,I,I].imag=scale*fine
        else:replace_block(Z,i,j,fine,omega,count=count)
        rows.append(dict(panel=i,otherPanel=j,kind=kind,**rep))
    return rows

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','archive','vertex','self','disjoint','smooth','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    vd=json.loads((a.vertex/'shared_vertex_modal_replay.json').read_text())
    require(vd,a.angle,sha,dict(allVertexPairsApproved=True,resistanceUnchanged=True))
    smooth=json.loads((a.smooth/'high_modal_surface.json').read_text())
    require(smooth,a.angle,sha,dict(smoothSurfaceConvergence=True,modes=385,surfaceOrders=[30,36,42],fixedArchivedFlow=True))
    assert [x['frequencyHz'] for x in smooth['cases']]==FREQ and all(x['gate'] for x in smooth['cases'])
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));nf=len(FREQ);nm=len(g['microphonesXYZ_m'])
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,ports,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate'] and len(ports)==7
    inv=classify(ports);areas=np.array([v.basis.area for v in ports]);counts=[55]*7
    assert len(inv)==28
    sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    up=read_npz(a.archive,doc['upper'],dict(Zu=(nf,334,334),Pu=(nf,nm,334),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    prior=read_npz(a.vertex,vd['archive'],dict(Ze=(nf,385,385),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    assert relative(areas,sh['areas'])<=1e-10 and np.array_equal(prior['Ze'].real,sh['Ze'].real)
    cp=block_keys(inv,'contact')
    assert vd['frequenciesHz']==FREQ and [(x['panel'],x['otherPanel']) for x in vd['pairs']]==cp and all(x['gate'] and x['maximumRelative']<=.01 and x['smoothControlMaximum']<=1e-8 for x in vd['pairs'])
    Z=prior['Ze'].copy();omega=2*np.pi*np.array(FREQ);rows=[]
    for kind in ('self','disjoint'):
        root=getattr(a,kind);d=json.loads((root/'remaining_reactive.json').read_text());pairs=block_keys(inv,kind)
        require(d,a.angle,sha,dict(kind=kind,modesPerPanel=55,quadratureGate=True,blocks=len(pairs),approvedBlocks=len(pairs)))
        assert d['inventory']==[list(v) for v in inv] and d['frequenciesHz']==FREQ
        assert [(x['panel'],x['otherPanel']) for x in d['cases']]==pairs and all(x['gate'] for x in d['cases'])
        arrays=read_npz(root,d['archive'],{f'block_{i}_{j}':(3,nf,55,55) for i,j in pairs},FREQ)
        rows.extend(apply_remaining(Z,sh['Ze'],arrays,pairs,kind,omega))
    assert len(rows)+len(cp)==28 and np.array_equal(Z.real,sh['Ze'].real)
    old=[];contact=[];new=[];mats=[];reports=[]
    for i,f in enumerate(FREQ):
        x=tuple(v[i] for v in (up['Zu'],up['Pu'],sh['Zl'],sh['Pl'],sh['Ze'],sh['Pe']))
        y,_=replay_full(*x,up['Y'][i],up['flow'][i],4);old.append(y)
        v=(*x[:4],prior['Ze'][i],x[5]);y,_=replay_full(*v,prior['Y'][i],prior['flow'][i],4);contact.append(y)
        v=(*x[:4],Z[i],x[5]);*out,rr=couple(*v,4,reference_kind='common-free-space-monopole')
        assert rr['gate'];new.append(tuple(out));mats.append(v);reports.append(dict(frequencyHz=f,**rr))
    def reduced(cfg):
        lo=reduced_panels(ports,cfg);Tu,_=embedding(ports[:6],lo[:6],order=18);Tl,_=embedding(ports[6:],lo[6:],order=18)
        return [modal_replay(x,Tu,Tl,4,counts,areas,y)[0] for x,y in zip(mats,new)]
    cfg=vd['summary']['selectedCounts'];assert len(cfg)==7 and sum(cfg)==355 and all(n in (45,55) for n in cfg)
    cases=dict(totalCorrection=compare_spatial(FREQ,old,new,counts,areas),remainingCorrection=compare_spatial(FREQ,contact,new,counts,areas),
        uniform315=compare_spatial(FREQ,reduced([45]*7),new,counts,areas),selected355=compare_spatial(FREQ,reduced(cfg),new,counts,areas))
    a.out.mkdir(parents=True,exist_ok=True)
    archive=save_matrices(a.out,'consolidated_reference',frequencies=FREQ,Ze=Z,Y=np.stack([v[0] for v in new]),flow=np.stack([v[-1] for v in new]))
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,approvedBlocks=28,sampledBlockQuadratureApproved=True,
        resistanceUnchanged=True,observerMapUnchanged=True,reusedCavityMatrices=True,selectedCounts=cfg,
        comparisons={k:v['maximum'] for k,v in cases.items()},selectedRelativeTo385Gate=cases['selected355']['gate'],
        modalConvergenceCertified=False,fullExteriorQuadratureCertified=False,fullCabinetReady=False,radiationReady=False)
    (a.out/'consolidated_exterior.json').write_text(json.dumps(dict(summary=summary,cases=cases,reports=reports,remainingBlocks=rows,archive=archive,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_CONSOLIDATED_EXTERIOR_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
