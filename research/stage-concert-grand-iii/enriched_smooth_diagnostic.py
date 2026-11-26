"""Audit smooth 429-mode exterior resistance and observer maps independently
of the graded FEM and singular reactive blocks. No acoustic solve.
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
from enriched_aperture_reference import enrich,restrict
from exterior_angular_panels import angular_panels
from lid_exterior import pressure
from dual_cavity_spatial_diagnostic import FREQ,save_matrices
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def require_sources(ext,trace,angle,sha):
    for d,keys in ((ext,dict(approvedBlocks=28,sampledBlockQuadratureApproved=True,resistanceUnchanged=True,observerMapUnchanged=True)),(trace,dict(surfaceOnly=True,screeningMinimumEnergy=.95))):
        s=d.get('summary',{})
        if d.get('scaleSha256')!=sha or any(s.get(k)!=v for k,v in dict(gate=True,angleDeg=angle,diagnosticOnly=True,radiationReady=False,**keys).items()):
            raise ValueError('invalid enrichment source')
    rows=[v for v in trace['cases'] if (v['boundaryN'],v['wedgeLayers'],v['edgeGrading'],v['layerGrading'],v['width'])==(160,24,.5,.5,.06)]
    if len(rows)!=1 or not rows[0]['screenGate'] or rows[0]['minimumCapture']<.95 or len(rows[0]['panels'])!=6 or sum(v['full']['modes'] for v in rows[0]['panels'])!=374:
        raise ValueError('missing approved trace')
    return rows[0]

def main():
    p=argparse.ArgumentParser()
    for key in ('scale','archive','consolidated','trace','out'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
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
    panels,counts,idx,basis=enrich(old)
    sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    prior=read_npz(a.consolidated,ex['archive'],dict(Ze=(nf,385,385),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    assert np.array_equal(prior['Ze'].real,sh['Ze'].real) and relative(np.array([v.basis.area for v in panels]),sh['areas'])<=1e-10
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    orders=(40,48,56);parts={}
    for o in orders:
        parts[o]=[]
        for panel in panels:
            _,x,w,A=panel.samples(o);parts[o].append((x,w[:,None]*A))
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'enriched_smooth.json';rows=[];RR=[];PP=[]
    for i,f in enumerate(FREQ):
        start=time.perf_counter();omega=2*np.pi*f;k=omega/343.;factor=1.204*omega*k/(4*np.pi);vals=[]
        for o in orders:
            G,_=angular_panels(parts[o],k,32);R=factor*G;P=pressure(panels,np.eye(429),far,f,o)
            assert relative(R,R.T)<=1e-12 and np.linalg.eigvalsh(R).min()>=-1e-10*np.linalg.norm(R)
            vals.append((R,P))
        R,P=vals[-1];G,_=angular_panels(parts[56],k,40);A=factor*G
        replay=dict(resistance=relative(restrict(R,idx),prior['Ze'][i].real),pressure=relative(P[:,idx],sh['Pe'][i]))
        surface=[dict(resistance=relative(v[0],R),pressure=relative(v[1],P)) for v in vals[:-1]]
        angular=relative(R,A)
        gate=bool(max(replay.values())<=1e-9 and max(v for d in surface for v in d.values())<=1e-8 and angular<=1e-8)
        row=dict(frequencyHz=f,archiveRestriction=replay,surfaceChanges=surface,angularChange=angular,gate=gate,seconds=time.perf_counter()-start)
        rows.append(row);RR.append(R);PP.append(P)
        path.write_text(json.dumps(dict(cases=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_ENRICH_SMOOTH_CASE '+json.dumps(row),flush=True)
    gate=all(r['gate'] for r in rows)
    archive=save_matrices(a.out,'enriched_smooth',frequencies=FREQ,R=np.stack(RR),Pe=np.stack(PP))
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,modes=429,counts=counts,width=.06,
        surfaceOrders=list(orders),angularOrders=[32,40],smoothQuadratureApproved=gate,
        maximumArchiveRestriction=max(max(r['archiveRestriction'].values()) for r in rows),
        maximumSurfaceChange=max(v for r in rows for d in r['surfaceChanges'] for v in d.values()),
        maximumAngularChange=max(r['angularChange'] for r in rows),
        reactiveQuadratureApproved=False,modalConvergenceCertified=False,fullCabinetReady=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,basis=basis,polynomialIndices=idx.tolist(),cases=rows,archive=archive,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_ENRICH_SMOOTH_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
