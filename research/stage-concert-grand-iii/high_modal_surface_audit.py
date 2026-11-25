"""Convergence of the smooth exterior operators with changing surface order.
Independent of reactive corrections; reuse fixed archived flow for a
physical-power comparison without rerunning the cavity solutions.
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
from exterior_angular_panels import angular_panels
from lid_exterior import pressure
from dual_cavity_spatial_diagnostic import FREQ
from split_radiation import relative
ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def require_angular(doc,angle,sha):
    s=doc.get('summary',{})
    expected=dict(gate=True,angleDeg=angle,diagnosticOnly=True,modes=385,fixedSurfaceOrder=30,
        angularOrders=[32,40,48],angularConvergenceAtFixedSurfaceOrder=True,radiationReady=False)
    if doc.get('scaleSha256')!=sha or any(s.get(k)!=v for k,v in expected.items()):
        raise ValueError('invalid angular prerequisite')
    if [v.get('frequencyHz') for v in doc.get('cases',[])]!=FREQ or any(v.get('gate') is not True for v in doc['cases']):
        raise ValueError('incomplete angular proof')

def compare_smooth(old,new,F):
    R,P=old;S,Q=new
    return dict(resistance=relative(R,S),pressure=relative(P,Q),
        fixedFlowPower=relative(F.conj().T@R@F,F.conj().T@S@F),
        fixedFlowPressure=relative(P@F,Q@F))

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--angular',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw);assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    doc=json.loads((a.archive/'dual_cavity_high_modal.json').read_text());require_archive(doc,a.angle,sha)
    require_angular(json.loads(a.angular.read_text()),a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    poly=np.asarray(q['contourXY_m']);g=geometry(poly,l,read('cabinet_geometry_hypothesis.json'));nm=len(g['microphonesXYZ_m']);nf=len(FREQ)
    def field(xy):
        x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        return np.stack([np.ones(len(x)),x,y,x*y],axis=1)
    _,ports,_,geo=envelope(poly,g['rimTopZ_m'],g['rimBottomZ_m'],a.angle,55,field,55);assert geo['gate'] and len(ports)==7
    sh=read_npz(a.archive,doc['shared'],dict(areas=(7,),Zl=(nf,59,59),Pl=(nf,2,59),Ze=(nf,385,385),Pe=(nf,2,385)),FREQ)
    up=read_npz(a.archive,doc['upper'],dict(Zu=(nf,334,334),Pu=(nf,nm,334),Y=(nf,4,4),flow=(nf,385,4)),FREQ)
    assert relative(np.array([v.basis.area for v in ports]),sh['areas'])<=1e-10
    far=np.array([[poly[:,0].max()+2.,poly[:,1].mean(),1.5],[poly[:,0].mean(),poly[:,1].max()+2.,-.8]])
    orders=(30,36,42);parts={}
    for order in orders:
        parts[order]=[]
        for panel in ports:
            _,x,w,A=panel.samples(order);parts[order].append((x,w[:,None]*A))
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'high_modal_surface.json';rows=[];RR=[];PP=[]
    for i,f in enumerate(FREQ):
        start=time.perf_counter();omega=2*np.pi*f;k=omega/343.;F=up['flow'][i];vals=[]
        for order in orders:
            G,_=angular_panels(parts[order],k,32)
            R=1.204*omega*k/(4*np.pi)*G
            P=pressure(ports,np.eye(385),far,f,order)
            assert relative(R,R.T)<=1e-12 and np.linalg.eigvalsh(R).min()>=-1e-10*np.linalg.norm(R)
            vals.append((R,P))
        replay=compare_smooth((sh['Ze'][i].real,sh['Pe'][i]),vals[0],F)
        coarse=compare_smooth(vals[0],vals[1],F);fine=compare_smooth(vals[1],vals[2],F)
        # Explicitly retain the 30->42 difference, not only adjacent changes.
        total=compare_smooth(vals[0],vals[2],F)
        row=dict(frequencyHz=f,archivedReplay=replay,coarseToMid=coarse,midToFine=fine,coarseToFine=total,
            seconds=time.perf_counter()-start,gate=bool(max(replay.values())<=1e-9 and max(v for d in (coarse,fine,total) for v in d.values())<=1e-8))
        rows.append(row);RR.append(np.stack([v[0] for v in vals]));PP.append(np.stack([v[1] for v in vals]))
        path.write_text(json.dumps(dict(cases=rows,complete=False,scaleSha256=sha),indent=2,allow_nan=False))
        print('G3_SMOOTH_SURFACE_CASE '+json.dumps(row),flush=True)
    gate=all(r['gate'] for r in rows)
    np.savez_compressed(a.out/'smooth_surface_operators.npz',frequencies=FREQ,surfaceOrders=orders,resistance=np.stack(RR),pressure=np.stack(PP))
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,modes=385,surfaceOrders=list(orders),angularOrder=32,
        maximumArchiveReplay=max(max(r['archivedReplay'].values()) for r in rows),
        maximumSurfaceChange=max(v for r in rows for key in ('coarseToMid','midToFine','coarseToFine') for v in r[key].values()),
        smoothSurfaceConvergence=gate,fixedArchivedFlow=True,fullExteriorQuadratureCertified=False,modalConvergenceCertified=False,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,cases=rows,scaleSha256=sha),indent=2,allow_nan=False))
    print('G3_SMOOTH_SURFACE_GATE '+json.dumps(summary),flush=True);assert gate
if __name__=='__main__':main()
