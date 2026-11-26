"""Independent reactive convergence for every enriched block.
Check whole blocks and every polynomial/edge subblock. No acoustic solve.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from enriched_smooth_diagnostic import require_sources,read
from enriched_aperture_reference import enrich
from high_modal_allocation import require_archive
from high_modal_remaining_reactive import classify
from acoustic_matrix_archive import read_npz
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from exterior_self_stream import self_react_blocked
from exterior_pair_stream import pair_integrals
from exterior_shared_edge import corrected_pair
from exterior_shared_vertex import vertex_delta,contacts
from dual_cavity_spatial_diagnostic import FREQ,save_matrices
from split_radiation import relative

def block_changes(a,b):
    rows={}
    for i,si in enumerate((slice(0,55),slice(55,None))):
        for j,sj in enumerate((slice(0,55),slice(55,None))):
            x=a[:,si,sj];y=b[:,si,sj]
            if x.size:rows[f'{i}{j}']=max(relative(u,v) for u,v in zip(x,y))
    rows['whole']=max(relative(u,v) for u,v in zip(a,b))
    return rows

def audit_block(p,q,k,kind):
    if kind=='self':
        orders=[(36,64),(42,72)];raw=[self_react_blocked(p,p.samples(o),k,s,block=8) for o,s in orders]
        asym=[max(relative(v,v.T) for v in x) for x in raw]
        vals=[(x+x.transpose(0,2,1))/2 for x in raw];controls=[0.,0.]
    else:
        orders=[(36,24),(42,28)] if kind=='contact' else [(40,0),(48,0)]
        vals=[];controls=[];asym=[]
        for o,s in orders:
            if kind=='contact':
                if any(n==2 for _,_,n,_ in contacts(p,q)):
                    _,X,r=corrected_pair(p,q,k,o,s);ctrl=r['smoothControlMaximum']
                else:
                    _,x,w,A=p.samples(o);_,y,v,B=q.samples(o)
                    _,X,_=pair_integrals(x,w[:,None]*A,y,v[:,None]*B,k,mutual=True,block=64);ctrl=0.
                D,r=vertex_delta(p,q,k,o,s);X+=D;ctrl=max(ctrl,r['smoothControlMaximum'])
            else:
                _,x,w,A=p.samples(o);_,y,v,B=q.samples(o)
                _,X,_=pair_integrals(x,w[:,None]*A,y,v[:,None]*B,k,mutual=True,block=64);ctrl=0.
            vals.append(X);controls.append(ctrl)
    change=block_changes(*vals)
    return vals[-1],dict(orders=orders,changes=change,rawAsymmetry=asym,smoothControls=controls,
        gate=bool(max(change.values())<=(1e-8 if kind=='disjoint' else .01) and max(asym,default=0.)<=.001 and max(controls)<=1e-8))

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','archive','consolidated','trace','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True)
    p.add_argument('--kind',choices=['self','contact','disjoint'],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    ex=json.loads((a.consolidated/'consolidated_exterior.json').read_text())
    require_sources(ex,json.loads(a.trace.read_text()),a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));nf=len(FREQ)
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,old,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate']
    panels,counts,idx,basis=enrich(old);inv=classify(panels)
    prior=read_npz(a.consolidated,ex['archive'],dict(Ze=(nf,385,385),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    omega=2*np.pi*np.asarray(FREQ);k=omega/343.;scale=1.204*omega[:,None,None]/(4*np.pi)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'enriched_reactive.json';rows=[];arrays={}
    for i,j,kind in inv:
        if kind!=a.kind:continue
        start=time.perf_counter();X,rep=audit_block(panels[i],panels[j],k,kind);X*=scale
        ref=prior['Ze'][:,55*i:55*(i+1),55*j:55*(j+1)].imag
        restriction=max(relative(u,v) for u,v in zip(X[:,:55,:55],ref))
        rep['gate']=bool(rep['gate'] and restriction<=(1e-8 if kind=='disjoint' else .01))
        row=dict(panel=i,otherPanel=j,kind=kind,polynomialRestriction=restriction,seconds=time.perf_counter()-start,**rep)
        rows.append(row);arrays[f'block_{i}_{j}']=X
        path.write_text(json.dumps(dict(cases=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_ENRICH_REACTIVE_CASE '+json.dumps(row),flush=True)
    assert len(rows)==sum(v[2]==a.kind for v in inv)>0
    gate=all(v['gate'] for v in rows)
    archive=save_matrices(a.out,'enriched_reactive',frequencies=FREQ,**arrays)
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,modes=429,counts=counts,width=.06,kind=a.kind,
        approvedBlocks=sum(v['gate'] for v in rows),blocks=len(rows),reactiveQuadratureApproved=gate,
        modalConvergenceCertified=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,inventory=inv,polynomialIndices=idx.tolist(),archive=archive,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_ENRICH_REACTIVE_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
