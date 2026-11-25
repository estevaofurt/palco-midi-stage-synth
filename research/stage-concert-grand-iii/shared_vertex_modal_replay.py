"""Replay all mutual vertex contacts on the archived edge-corrected reference."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from exterior_shared_vertex import contacts,vertex_delta
from exterior_shared_edge import corrected_pair
from exterior_pair_stream import pair_integrals
from shared_edge_modal_replay import edge_pairs,replace_block
from high_mode_quadrature_audit import changes
from high_modal_allocation import require_archive
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from dual_cavity_reference import couple
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial,save_matrices
from nested_acoustic_ports import reduced_panels,embedding
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def inventory(ports):
    rows=[]
    for i in range(len(ports)):
        for j in range(i+1,len(ports)):
            c=contacts(ports[i],ports[j])
            if c:rows.append(dict(panel=i,otherPanel=j,vertexPairs=sum(n==1 for _,_,n,_ in c),edgePairs=sum(n==2 for _,_,n,_ in c)))
    return rows

def require_sources(ed,vd,angle,sha,inv):
    for doc,keys in ((ed,dict(gate=True,angleDeg=angle,diagnosticOnly=True,allSharedEdgePairsApproved=True,resistanceUnchanged=True)),
                     (vd,dict(gate=True,angleDeg=angle,diagnosticOnly=True,representativeQuadratureGate=True,modesPerPanel=55))):
        if doc.get('scaleSha256')!=sha or any(doc.get('summary',{}).get(k)!=v for k,v in keys.items()):
            raise ValueError('invalid singular quadrature source')
    if vd.get('inventory')!=inv or ed.get('frequenciesHz')!=FREQ:
        raise ValueError('contact inventory or frequency mismatch')
    pairs=[(r['panel'],r['otherPanel']) for r in inv if r['edgePairs']]
    if [(r['panel'],r['otherPanel']) for r in ed.get('pairs',[])]!=pairs or any(r.get('gate') is not True for r in ed['pairs']):
        raise ValueError('incomplete edge corrections')

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--edge',type=Path,required=True);p.add_argument('--vertex',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    ed=json.loads((a.edge/'shared_edge_modal_replay.json').read_text());vd=json.loads((a.vertex/'shared_vertex_diagnostic.json').read_text())
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));nm=len(g['microphonesXYZ_m']);nf=len(FREQ)
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,ports,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate'] and len(ports)==7
    inv=inventory(ports);require_sources(ed,vd,a.angle,sha,inv)
    areas=np.array([v.basis.area for v in ports]);counts=[55]*7
    sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    up=read_npz(a.archive,doc['upper'],dict(Zu=(nf,334,334),Pu=(nf,nm,334),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    prior=read_npz(a.edge,ed['archive'],dict(Ze=(nf,385,385),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    assert relative(areas,sh['areas'])<=1e-10 and np.array_equal(prior['Ze'].real,sh['Ze'].real)
    omega=2*np.pi*np.array(FREQ);k=omega/343.;Ze=prior['Ze'].copy();ep=set(edge_pairs(ports))
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'shared_vertex_modal_replay.json';rows=[]
    for item in inv:
        if not item['vertexPairs']:continue
        start=time.perf_counter();i,j=item['panel'],item['otherPanel'];p,q=ports[i],ports[j]
        I=slice(55*i,55*(i+1));J=slice(55*j,55*(j+1));rawPrior=prior['Ze'][:,I,J].imag/(1.204*omega[:,None,None]/(4*np.pi))
        vals=[];controls=[];bases=[]
        for outer,order in ((36,24),(42,28)):
            if (i,j) in ep:
                _,X,r=corrected_pair(p,q,k,outer,order)
                edgeSmooth=r['smoothControlMaximum']
            else:
                _,x,w,A=p.samples(outer);_,y,v,B=q.samples(outer)
                _,X,_=pair_integrals(x,w[:,None]*A,y,v[:,None]*B,k,mutual=True,block=64)
                edgeSmooth=0.
            D,r=vertex_delta(p,q,k,outer,order);assert r['vertexPairs']==item['vertexPairs']
            bases.append(X);vals.append(X+D);controls.append(max(edgeSmooth,r['smoothControlMaximum']))
        if (i,j) in ep:
            replay=max(v['relative'] for v in changes(bases[-1],rawPrior))
        else:
            _,x,w,A=p.samples(30);_,y,v,B=q.samples(30)
            _,X,_=pair_integrals(x,w[:,None]*A,y,v[:,None]*B,k,mutual=True,block=64)
            replay=max(v['relative'] for v in changes(X,rawPrior))
        assert replay<=1e-9
        conv=changes(vals[0],vals[1]);mx=max(v['relative'] for v in conv);smooth=max(controls)
        gate=bool(mx<=.01 and smooth<=1e-8)
        row=dict(**item,previousReplay=replay,convergence=conv,maximumRelative=mx,smoothControlMaximum=smooth,
            correction=changes(rawPrior,vals[-1]),gate=gate,seconds=time.perf_counter()-start)
        rows.append(row)
        if gate:replace_block(Ze,i,j,vals[-1],omega)
        path.write_text(json.dumps(dict(pairs=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_VERTEX_REPLAY_PAIR '+json.dumps(row),flush=True)
    assert rows and np.array_equal(Ze.real,sh['Ze'].real)
    allPairs=all(r['gate'] for r in rows);old=[];edge=[];new=[];mats=[];reports=[]
    for i,f in enumerate(FREQ):
        x=tuple(v[i] for v in (up['Zu'],up['Pu'],sh['Zl'],sh['Pl'],sh['Ze'],sh['Pe']))
        y,_=replay_full(*x,up['Y'][i],up['flow'][i],4);old.append(y)
        v=(*x[:4],prior['Ze'][i],x[5]);y,_=replay_full(*v,prior['Y'][i],prior['flow'][i],4);edge.append(y)
        v=(*x[:4],Ze[i],x[5]);*out,r=couple(*v,4,reference_kind='common-free-space-monopole')
        assert r['gate'];new.append(tuple(out));mats.append(v);reports.append(dict(frequencyHz=f,**r))
    def reduced(cfg):
        lo=reduced_panels(ports,cfg);Tu,_=embedding(ports[:6],lo[:6],order=18);Tl,_=embedding(ports[6:],lo[6:],order=18)
        return [modal_replay(x,Tu,Tl,4,counts,areas,y)[0] for x,y in zip(mats,new)]
    cfg=ed['summary']['selectedCounts'];assert len(cfg)==7 and sum(cfg)==355 and all(n in (45,55) for n in cfg)
    cases=dict(vertexCorrection=compare_spatial(FREQ,edge,new,counts,areas),combinedCorrection=compare_spatial(FREQ,old,new,counts,areas),
        uniform315=compare_spatial(FREQ,reduced([45]*7),new,counts,areas),selected355=compare_spatial(FREQ,reduced(cfg),new,counts,areas))
    archive=save_matrices(a.out,'vertex_corrected_reference',frequencies=FREQ,Ze=Ze,Y=np.stack([v[0] for v in new]),flow=np.stack([v[-1] for v in new]))
    summary=dict(gate=allPairs,angleDeg=a.angle,diagnosticOnly=True,reusedCavityMatrices=True,resistanceUnchanged=True,
        allVertexPairsApproved=allPairs,correctedPanelPairs=sum(r['gate'] for r in rows),totalPanelPairs=len(rows),
        vertexTrianglePairs=sum(r['vertexPairs'] for r in rows),selectedCounts=cfg,
        comparisons={k:v['maximum'] for k,v in cases.items()},selectedRelativeTo385Gate=cases['selected355']['gate'],
        modalConvergenceCertified=False,fullExteriorQuadratureCertified=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,pairs=rows,cases=cases,reports=reports,archive=archive,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_VERTEX_REPLAY_GATE '+json.dumps(summary),flush=True);assert allPairs
if __name__=='__main__':main()
