"""Full 385-mode resistance angular audit at fixed surface quadrature.
Compare original dense Gram, panel-local Gram, and archived resistance.
No cavity solve or reactive quadrature change.
"""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from recess_envelope import build as envelope
from high_modal_allocation import require_archive
from acoustic_matrix_archive import read_npz
from exterior_angular_panels import angular_panels
from lid_exterior import angular
from dual_cavity_spatial_diagnostic import FREQ
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'))
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,ports,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55)
    assert geo['gate'] and len(ports)==7
    nf=len(FREQ);sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    assert relative(np.array([v.basis.area for v in ports]),sh['areas'])<=1e-10
    parts=[]
    for p in ports:
        _,x,w,A=p.samples(30);parts.append((x,w[:,None]*A))
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'high_modal_angular.json';rows=[];grams=[]
    for i,f in enumerate(FREQ):
        omega=2*np.pi*f;k=omega/343.;expected=sh['Ze'][i].real/(1.204*omega*k/(4*np.pi));values=[];times=[]
        for order in (32,40,48):
            start=time.perf_counter();G,mem=angular_panels(parts,k,order);times.append(time.perf_counter()-start)
            assert relative(G,G.T)<=1e-12 and np.linalg.eigvalsh(G).min()>=-1e-10*np.linalg.norm(G)
            values.append(G)
        # Verify full geometry directly at the frequency with highest k.
        direct=None;directSeconds=None
        if i==nf-1:
            xx=np.vstack([x for x,A in parts]);AA=block_diag(*[A for x,A in parts])
            start=time.perf_counter();ref=angular(xx,AA,k,40);directSeconds=time.perf_counter()-start
            direct=relative(values[1],ref);assert direct<=1e-12
        replay=relative(values[1],expected)
        coarse=relative(values[0],values[1]);fine=relative(values[1],values[2])
        row=dict(frequencyHz=f,replayRelative=replay,coarseToMid=coarse,midToFine=fine,denseEquivalence=direct,
            denseSeconds=directSeconds,panelSeconds=times,allocationEstimate=mem,
            gate=bool(replay<=1e-9 and max(coarse,fine)<=1e-8))
        rows.append(row);grams.append(np.stack(values))
        path.write_text(json.dumps(dict(cases=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_ANGULAR_CASE '+json.dumps(row),flush=True)
    gate=all(r['gate'] for r in rows)
    np.savez_compressed(a.out/'angular_grams.npz',frequencies=FREQ,orders=[32,40,48],gram=np.stack(grams))
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,modes=385,fixedSurfaceOrder=30,angularOrders=[32,40,48],
        maximumReplayRelative=max(r['replayRelative'] for r in rows),maximumAngularChange=max(max(r['coarseToMid'],r['midToFine']) for r in rows),
        angularConvergenceAtFixedSurfaceOrder=gate,fullExteriorQuadratureCertified=False,modalConvergenceCertified=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_ANGULAR_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
