"""G3.11w: physical-hypothesis dry structural modal export.
Audit diagonal damping and four-field surface projection independently;
neither is assumed adequate. No acoustic fit or string model promotion."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from scipy.linalg import solve
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from bridge_strings import centerline
from spline_plate import assemble
from structural_assembly import assemble as structure
from structural_response import response as direct
from polygon_radiation import modes,SurfaceModes
from ribbed_plate import quadrature
from dual_cavity_spatial_diagnostic import save_matrices
from split_radiation import relative

ROOT=Path(__file__).parent
def read(n):return json.loads((ROOT/n).read_text())

def projection(fields,shapes,w):
    F=np.asarray(fields,float);S=np.asarray(shapes,float);w=np.asarray(w,float)
    if F.ndim!=2 or S.ndim!=2 or len(F)!=len(S) or w.shape!=(len(F),) or not all(np.isfinite(x).all() for x in (F,S,w)) or np.any(w<=0):raise ValueError('invalid quadrature')
    gram=F.T@(w[:,None]*F);rhs=F.T@(w[:,None]*S)
    A=solve(gram,rhs,assume_a='pos')
    defect=S-F@A
    total=np.sum(w[:,None]*S*S,axis=0);residual=np.sum(w[:,None]*defect*defect,axis=0)
    normal=relative(gram@A,rhs)
    return A,dict(normalResidual=normal,maximumModeResidual=float(np.sqrt(np.max(residual/np.maximum(total,1e-30)))),
        aggregateResidual=float(np.sqrt(residual.sum()/max(total.sum(),1e-30))),
        capturedEnergyByMode=(1-residual/np.maximum(total,1e-30)).tolist())

def mobility(k,D,P,freq):
    Y=[]
    for f in freq:
        w=2*np.pi*f
        Y.append(1j*w*(P.T@solve(np.diag(k-w*w)+1j*w*D,P)))
    return np.stack(Y)

def compare(freq,k,D,P,reference):
    full=mobility(k,D,P,freq);diag=mobility(k,np.diag(np.diag(D)),P,freq)
    errors=[relative(x,y) for x,y in zip(full,reference)]
    damping=[relative(x,y) for x,y in zip(diag,full)]
    return dict(fullReferenceRelative=relative(full,reference),maximumReferenceRelative=max(errors),
        diagonalRelative=relative(diag,full),maximumDiagonalRelative=max(damping),
        diagonalDampingGate=bool(max(damping)<=.05),referenceGate=bool(max(errors)<=.05),
        frequencies=[dict(frequencyHz=float(f),referenceRelative=x,diagonalRelative=y) for f,x,y in zip(freq,errors,damping)])

def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sc=json.loads(raw)
    if sc['version']!='G3-scale-hypothesis-02' or sc['summary']['gate'] is not True:raise ValueError('unapproved scale hypothesis')
    l=layout_build(sc,read('layout_hypothesis.json'));mat=read('board_interface_hypothesis.json')
    c=contour_build(l,read('board_contour_hypothesis.json'),mat);rib=read('ribbed_plate_hypothesis.json')['rib']
    poly=np.array(c['contourXY_m']);centers={s:centerline(l['bridgeAttachmentNodes'][s]) for s in ('bass','treble')}
    m=assemble(poly,c['ribs'],mat['plate'],rib,30,14,False)
    z=structure(m,centers,read('bridge_hypothesis.json'),mat,read('rim_structure_hypothesis.json'),2,8,14,True)
    M=z['M'];K=z['K']+z['Jrim']+z['Jbridge'];D=z['D'];P=z['P'][:,[0,2,4,5]]
    q=modes(M,K,D,P,256);freq=np.geomspace(30,500,32)
    reference,ds,_=direct(M,K,D,P,freq,np.ones(4))
    if not ds['gate']:raise ValueError('dry full reference failed')
    eig=bool(q['massError']<=1e-5 and q['scaledEigenResidual']<=1e-8 and q['originalEigenResidual']<=1e-5)
    if not eig:raise ValueError('eigenbasis failed')
    field=SurfaceModes(m,q['U'][:z['plateDofs']]);maps=[];reports=[]
    for order in (30,42):
        xy,w=quadrature(poly,order);x,y=(2*(xy-poly.min(0))/np.ptp(poly,axis=0)-1).T
        F=np.stack([np.ones(len(x)),x,y,x*y],axis=1)
        A,report=projection(F,field(xy),w);maps.append(A);reports.append(report)
    drift=relative(maps[0],maps[1])
    if max(r['normalResidual'] for r in reports)>1e-8 or drift>1e-5:raise ValueError('projection quadrature failed')
    rows=[]
    for n in (64,128,192,256):
        Dm=q['D'][:n,:n];k=np.diag(q['K'])[:n];Pm=q['P'][:n]
        row=compare(freq,k,Dm,Pm,reference)
        row.update(modes=n,highestModeHz=float(q['Hz'][n-1]),offDiagonalDampingRelative=relative(np.diag(np.diag(Dm)),Dm),
            minimumDampingEigenvalue=float(np.linalg.eigvalsh(Dm).min()),surfaceProjection=reports[-1]['capturedEnergyByMode'][:n])
        rows.append(row)
    a.out.mkdir(parents=True,exist_ok=True)
    archive=save_matrices(a.out,'dry_structural_modal',frequencies=freq,modalHz=q['Hz'],stiffness=np.diag(q['K']),damping=q['D'],ports=q['P'],fourFieldMap=maps[-1],dryReference=reference)
    summary=dict(gate=True,diagnosticOnly=True,physicalHypothesis=True,calibratedParameters=False,eigenGate=eig,
        massError=q['massError'],scaledEigenResidual=q['scaledEigenResidual'],originalEigenResidual=q['originalEigenResidual'],
        fourFieldQuadratureRelative=drift,fourFieldAggregateResidual=reports[-1]['aggregateResidual'],
        fourFieldMaximumModeResidual=reports[-1]['maximumModeResidual'],fourFieldApproximationGate=reports[-1]['maximumModeResidual']<=.05,
        fullDampingPreserved=True,maximumModes=256,acousticFitAccepted=False,timeDomainReady=False,radiationReady=False,polyphonyValidated=False)
    (a.out/'dry_structural_modal.json').write_text(json.dumps(dict(summary=summary,scaleSha256=hashlib.sha256(raw).hexdigest(),
        archive=archive,frequencyHz=freq.tolist(),dryReference=ds,projection=reports,comparisons=rows),indent=2,allow_nan=False))
    print('G3_DRY_MODAL_GATE '+json.dumps(summary),flush=True)
    for row in rows:print('G3_DRY_MODAL_CASE '+json.dumps({k:v for k,v in row.items() if k not in ('frequencies','surfaceProjection')}),flush=True)
if __name__=='__main__':main()
