"""Audit all self and non-contact mutual reactive blocks of the 385-mode
monopole reference. Edge/vertex contact blocks are excluded explicitly.
No cavity solve and no changes to the original archive.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from high_modal_allocation import require_archive
from acoustic_matrix_archive import read_npz
from exterior_self_stream import self_react_blocked
from exterior_pair_stream import pair_integrals
from exterior_shared_vertex import contacts
from high_mode_quadrature_audit import changes,self_metrics
from dual_cavity_spatial_diagnostic import FREQ
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def classify(ports):
    rows=[]
    for i,p in enumerate(ports):
        for j in range(i,len(ports)):
            if i==j:kind='self'
            else:kind='contact' if contacts(p,ports[j]) else 'disjoint'
            rows.append((i,j,kind))
    return rows

def compare_self(values,archived):
    if len(values)!=3:raise ValueError('three quadrature levels required')
    coarse,mid,fine=values
    replay=max(r['relative'] for r in changes((coarse+coarse.transpose(0,2,1))/2,archived))
    source=changes(coarse,mid);target=changes(mid,fine);joint=changes(coarse,fine)
    maximum=max(v['relative'] for seq in (source,target,joint) for v in seq)
    asym=[max(v['rawAsymmetry'] for v in self_metrics(x)) for x in values]
    return dict(replayRelative=replay,source=source,target=target,joint=joint,maximumRelative=maximum,
        rawAsymmetries=asym,gate=bool(replay<=1e-9 and maximum<=.01 and asym[-1]<=.001))

def compare_pair(values,archived):
    if len(values)!=3:raise ValueError('three quadrature levels required')
    replay=max(v['relative'] for v in changes(values[0],archived))
    coarse=changes(values[0],values[1]);fine=changes(values[1],values[2]);joint=changes(values[0],values[2])
    maximum=max(v['relative'] for seq in (coarse,fine,joint) for v in seq)
    return dict(replayRelative=replay,coarseToMid=coarse,midToFine=fine,coarseToFine=joint,
        maximumRelative=maximum,gate=bool(replay<=1e-9 and maximum<=.01))

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True)
    p.add_argument('--kind',choices=['self','disjoint'],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,ports,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate'] and len(ports)==7
    nf=len(FREQ);sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    assert relative(np.array([v.basis.area for v in ports]),sh['areas'])<=1e-10
    omega=2*np.pi*np.array(FREQ);k=omega/343.;scale=1.204*omega[:,None,None]/(4*np.pi)
    inv=classify(ports);assert len(inv)==28 and sum(kind=='self' for _,_,kind in inv)==7
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'remaining_reactive.json';rows=[];arrays={}
    for i,j,kind in inv:
        if kind!=a.kind:continue
        start=time.perf_counter();I=slice(55*i,55*(i+1));J=slice(55*j,55*(j+1))
        old=sh['Ze'][:,I,J].imag/scale
        if kind=='self':
            orders=[(30,52),(30,64),(36,64)]
            vals=[self_react_blocked(ports[i],ports[i].samples(o),k,s,block=8) for o,s in orders]
            rep=compare_self(vals,old)
        else:
            orders=[30,36,42];vals=[]
            for o in orders:
                _,x,w,A=ports[i].samples(o);_,y,v,B=ports[j].samples(o)
                _,X,_=pair_integrals(x,w[:,None]*A,y,v[:,None]*B,k,mutual=True,block=64);vals.append(X)
            rep=compare_pair(vals,old)
        key=f'block_{i}_{j}';arrays[key]=np.stack(vals)
        row=dict(panel=i,otherPanel=j,kind=kind,orders=orders,seconds=time.perf_counter()-start,**rep);rows.append(row)
        path.write_text(json.dumps(dict(cases=rows,inventory=inv,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_REMAINING_REACTIVE_CASE '+json.dumps(row),flush=True)
    assert rows and len(rows)==sum(kind==a.kind for _,_,kind in inv)
    archive=a.out/'remaining_reactive_blocks.npz';np.savez_compressed(archive,frequencies=FREQ,**arrays)
    approved=all(r['gate'] for r in rows)
    summary=dict(gate=all(r['replayRelative']<=1e-9 for r in rows),angleDeg=a.angle,diagnosticOnly=True,kind=a.kind,
        modesPerPanel=55,blocks=len(rows),approvedBlocks=sum(r['gate'] for r in rows),quadratureGate=approved,
        maximumRelative=max(r['maximumRelative'] for r in rows),maximumReplay=max(r['replayRelative'] for r in rows),
        fullExteriorQuadratureCertified=False,modalConvergenceCertified=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,inventory=inv,scaleSha256=sha,frequenciesHz=FREQ,
        archive=dict(file=archive.name,sha256=hashlib.sha256(archive.read_bytes()).hexdigest())),indent=2,allow_nan=False))
    print('G3_REMAINING_REACTIVE_GATE '+json.dumps(summary),flush=True);assert summary['gate']
if __name__=='__main__':main()
