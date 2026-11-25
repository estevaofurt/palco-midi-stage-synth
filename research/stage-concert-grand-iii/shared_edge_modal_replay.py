"""Replace only converged reactive blocks of edge-adjacent ports in the
archived 385-mode monopole reference. No new cavity assembly or solve.
The corrected reference is diagnostic, not the exterior Neumann solution.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from exterior_shared_edge import shared_edge,corrected_pair
from exterior_pair_stream import pair_integrals
from high_mode_quadrature_audit import changes
from high_modal_allocation import require_archive
from acoustic_matrix_archive import read_npz,replay_full,modal_replay
from dual_cavity_reference import couple
from dual_cavity_spatial_diagnostic import FREQ,compare_spatial,save_matrices
from nested_acoustic_ports import reduced_panels,embedding
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def edge_pairs(p):
    pairs=[]
    for i in range(len(p)):
        for j in range(i+1,len(p)):
            try:shared_edge(p[i],p[j])
            except ValueError:continue
            pairs.append((i,j))
    return pairs

def replace_block(Z,i,j,X,omega,rho=1.204,count=55):
    """Copy only imaginary mutual blocks; preserve resistance exactly."""
    if Z.ndim!=3 or Z.shape[1]!=Z.shape[2] or Z.shape[1]%count or not 0<=i<j<Z.shape[1]//count or X.shape!=(len(Z),count,count) or np.shape(omega)!=(len(Z),) or not np.isrealobj(X) or not np.isfinite(X).all():
        raise ValueError('invalid replacement block')
    I=slice(i*count,(i+1)*count);J=slice(j*count,(j+1)*count)
    V=rho*omega[:,None,None]/(4*np.pi)*X
    Z[:,I,J].imag=V;Z[:,J,I].imag=V.transpose(0,2,1)

def require_edge_proof(doc,angle,sha):
    s=doc.get('summary',{})
    if doc.get('scaleSha256')!=sha or any(s.get(k)!=v for k,v in dict(gate=True,angleDeg=angle,diagnosticOnly=True,modesPerPanel=55,smoothControlGate=True,representativeQuadratureGate=True).items()):
        raise ValueError('invalid shared-edge prerequisite')

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--edge-proof',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    ed=json.loads(a.edge_proof.read_text());require_edge_proof(ed,a.angle,sha)
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
    omega=2*np.pi*np.array(FREQ);k=omega/343.;Ze=sh['Ze'].copy();pairs=edge_pairs(ports)
    assert tuple(sorted((ed['summary']['panel'],ed['summary']['otherPanel']))) in pairs
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'shared_edge_modal_replay.json';rows=[]
    for i,j in pairs:
        start=time.perf_counter();I=slice(55*i,55*(i+1));J=slice(55*j,55*(j+1))
        p,q=ports[i],ports[j]
        _,x,w,A=p.samples(30);_,y,v,B=q.samples(30)
        _,original,_=pair_integrals(x,w[:,None]*A,y,v[:,None]*B,k,mutual=True,block=64)
        rawOld=sh['Ze'][:,I,J].imag/(1.204*omega[:,None,None]/(4*np.pi))
        oldReplay=max(z['relative'] for z in changes(original,rawOld));assert oldReplay<=1e-9
        _,mid,rm=corrected_pair(p,q,k,36,24);_,fine,rf=corrected_pair(p,q,k,42,28)
        convergence=changes(mid,fine);mx=max(z['relative'] for z in convergence)
        smooth=max(rm['smoothControlMaximum'],rf['smoothControlMaximum'])
        gate=bool(mx<=.01 and smooth<=1e-8)
        row=dict(panel=i,otherPanel=j,originalReplay=oldReplay,convergence=convergence,maximumRelative=mx,
            smoothControlMaximum=smooth,correction=changes(original,fine),gate=gate,seconds=time.perf_counter()-start)
        rows.append(row)
        if gate:replace_block(Ze,i,j,fine,omega)
        path.write_text(json.dumps(dict(pairs=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_EDGE_REPLAY_PAIR '+json.dumps(row),flush=True)
    assert np.array_equal(Ze.real,sh['Ze'].real)
    allPairs=all(r['gate'] for r in rows);old=[];new=[];mats=[];reports=[]
    for i,f in enumerate(FREQ):
        x=tuple(v[i] for v in (up['Zu'],up['Pu'],sh['Zl'],sh['Pl'],sh['Ze'],sh['Pe']))
        y,_=replay_full(*x,up['Y'][i],up['flow'][i],4);old.append(y)
        v=(*x[:4],Ze[i],x[5]);*out,r=couple(*v,4,reference_kind='common-free-space-monopole')
        assert r['gate'];new.append(tuple(out));mats.append(v);reports.append(dict(frequencyHz=f,**r))
    def reduced(cfg):
        lo=reduced_panels(ports,cfg);Tu,_=embedding(ports[:6],lo[:6],order=18);Tl,_=embedding(ports[6:],lo[6:],order=18)
        vals=[]
        for x,y in zip(mats,new):
            v,_=modal_replay(x,Tu,Tl,4,counts,areas,y);vals.append(v)
        return vals
    cfg=[55,55,55,45,45,55,45] if a.angle==30 else [55,45,55,45,55,55,45]
    cases=dict(correction=compare_spatial(FREQ,old,new,counts,areas),
        uniform315=compare_spatial(FREQ,reduced([45]*7),new,counts,areas),
        selected355=compare_spatial(FREQ,reduced(cfg),new,counts,areas))
    archive=save_matrices(a.out,'edge_corrected_reference',frequencies=FREQ,Ze=Ze,Y=np.stack([v[0] for v in new]),flow=np.stack([v[-1] for v in new]))
    summary=dict(gate=allPairs,angleDeg=a.angle,diagnosticOnly=True,reusedCavityMatrices=True,resistanceUnchanged=True,
        allSharedEdgePairsApproved=allPairs,correctedPairs=sum(r['gate'] for r in rows),totalSharedEdgePairs=len(rows),
        selectedCounts=cfg,comparisons={k:v['maximum'] for k,v in cases.items()},
        selectedRelativeTo385Gate=cases['selected355']['gate'],modalConvergenceCertified=False,
        fullExteriorQuadratureCertified=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,pairs=rows,cases=cases,reports=reports,archive=archive,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_EDGE_REPLAY_GATE '+json.dumps(summary),flush=True);assert allPairs
if __name__=='__main__':main()
