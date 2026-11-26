"""G3.11e: diagnostic positive-real fit of the four board impedance fields.
Fixed oscillator dictionary; PSD matrix coefficients by projected gradient.
Sparse harmonic samples cannot certify broadband fit or physical damping."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from acoustic_matrix_archive import read_npz
from fixed_355_validation import require_fine
from dual_cavity_spatial_diagnostic import FREQ,save_matrices
from high_modal_allocation import read
from spatial_layout import build as layout_build
from board_contour import build as contour_build
from cabinet_geometry import geometry
from split_radiation import relative

CENTERS=np.arange(20.,401.,10.)
GAMMA_HZ=5.
def dictionary(s,centers=CENTERS,gamma_hz=GAMMA_HZ):
    s=np.atleast_1d(np.asarray(s,complex))
    om=2*np.pi*np.asarray(centers,float);gamma=2*np.pi*gamma_hz
    if np.any(s==0) or not np.isfinite(s).all() or np.any(s.real<0) or not np.isfinite(om).all() or np.any(om<=0) or not np.isfinite(gamma) or gamma<=0:raise ValueError('invalid positive-real dictionary')
    return np.column_stack([np.ones_like(s),s,1/s,s[:,None]/(s[:,None]**2+2*gamma*s[:,None]+om**2)])

def psd(X):
    d,U=np.linalg.eigh((X+X.transpose(0,2,1))/2)
    return (U*np.maximum(d,0)[:,None,:])@U.transpose(0,2,1)

def fit(freq,Z,centers=CENTERS,gamma_hz=GAMMA_HZ,iterations=8000):
    freq=np.asarray(freq,float);Z=np.asarray(Z,complex)
    if freq.ndim!=1 or len(freq)<2 or np.any(freq<=0) or len(np.unique(freq))!=len(freq) or Z.ndim!=3 or Z.shape[0]!=len(freq) or Z.shape[1]!=Z.shape[2] or not np.isfinite(Z).all() or iterations<1:raise ValueError('invalid fit data')
    if any(relative(v,v.T)>1e-8 or np.linalg.eigvalsh((v+v.conj().T)/2).min()<-1e-8*max(np.linalg.norm(v),1e-30) for v in Z):raise ValueError('nonpassive training sample')
    # Normalize each sample by its Frobenius norm; no held-out values enter fit.
    weight=1/np.maximum(np.linalg.norm(Z,axis=(1,2)),1e-30)
    D=dictionary(2j*np.pi*freq,centers,gamma_hz)*weight[:,None]
    norm=np.linalg.norm(D,axis=0)
    D=D/norm
    A=np.concatenate([D.real,D.imag]);Y=np.concatenate([Z.real*weight[:,None,None],Z.imag*weight[:,None,None]])
    H=A.T@A;rhs=np.einsum('ij,ikl->jkl',A,Y)
    # Weak dimensionless ridge makes the underdetermined fit well posed.
    ridge=1e-8;H+=ridge*np.eye(len(H));L=np.linalg.eigvalsh(H)[-1]
    X=np.zeros_like(rhs);V=X.copy();t=1.
    for i in range(iterations):
        N=psd(V-(np.einsum('ij,jkl->ikl',H,V)-rhs)/L)
        u=(1+np.sqrt(1+4*t*t))/2
        V=N+(t-1)/u*(N-X);X=N;t=u
    residual=np.linalg.norm(X-psd(X-(np.einsum('ij,jkl->ikl',H,X)-rhs)/L))/max(np.linalg.norm(X),1e-30)
    C=X/norm[:,None,None]
    if not np.isfinite(C).all():raise ValueError('nonfinite coefficient')
    return C,dict(projectedGradientRelative=float(residual),iterations=iterations,optimizerConverged=bool(residual<=1e-7))

def evaluate(s,C,centers=CENTERS,gamma_hz=GAMMA_HZ):
    return np.einsum('ij,jkl->ikl',dictionary(s,centers,gamma_hz),C)

def audit(C,centers=CENTERS,gamma_hz=GAMMA_HZ):
    if not np.isfinite(C).all():raise ValueError('nonfinite coefficient')
    eig=min(float(np.linalg.eigvalsh(v).min()/max(np.linalg.norm(v),1e-30)) for v in C)
    symmetry=max(relative(v,v.T) for v in C)
    f=np.geomspace(1,20000,241)
    s=np.concatenate([2j*np.pi*f,2*np.pi*10+2j*np.pi*f])
    Z=evaluate(s,C,centers,gamma_hz)
    realpart=min(float(np.linalg.eigvalsh((v+v.conj().T)/2).min()/max(np.linalg.norm(v),1e-30)) for v in Z)
    return dict(coefficientMinRelative=eig,coefficientSymmetry=symmetry,positiveRealSampleMin=realpart,
        gate=bool(eig>=-1e-10 and symmetry<=1e-10 and realpart>=-1e-10))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','fine','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    raw=a.scale.read_bytes();sha=hashlib.sha256(raw).hexdigest();sc=json.loads(raw)
    assert sc['version']=='G3-scale-hypothesis-02' and sc['summary']['gate']
    d=json.loads((a.fine/'graded_combined_refinement.json').read_text());require_fine(d,a.angle,sha)
    l=layout_build(sc,read('layout_hypothesis.json'));q=contour_build(l,read('board_contour_hypothesis.json'),read('board_interface_hypothesis.json'))
    nm=len(geometry(np.asarray(q['contourXY_m']),l,read('cabinet_geometry_hypothesis.json'))['microphonesXYZ_m'])
    nf=len(FREQ);z=read_npz(a.fine,d['archive'],dict(Zu=(nf,334,334),Pu=(nf,nm,334),Y=(nf,4,4),flow=(nf,385,4)),FREQ)['Y']
    # Y is named historically; it is the opposing force / board velocity impedance.
    rows=[]
    for i,f in enumerate(FREQ):
        train=[j for j in range(nf) if j!=i];C,opt=fit(np.asarray(FREQ)[train],z[train])
        rep=audit(C);err=relative(evaluate([2j*np.pi*f],C)[0],z[i])
        row=dict(heldOutHz=f,trainingHz=[FREQ[j] for j in train],relativeError=err,passivity=rep,optimization=opt)
        rows.append(row);print('G3_PASSIVE_FOLD '+json.dumps(row),flush=True)
    C,opt=fit(FREQ,z);rep=audit(C)
    training=max(relative(x,y) for x,y in zip(evaluate(2j*np.pi*np.asarray(FREQ),C),z))
    passive=rep['gate'] and all(v['passivity']['gate'] for v in rows)
    convergence=opt['optimizerConverged'] and all(v['optimization']['optimizerConverged'] for v in rows)
    maxcv=max(v['relativeError'] for v in rows)
    a.out.mkdir(parents=True,exist_ok=True)
    archive=save_matrices(a.out,'passive_board_fit',frequencies=FREQ,coefficients=C,centersHz=CENTERS)
    summary=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,boardFields=4,oscillatorAtoms=len(CENTERS),
        gammaHz=GAMMA_HZ,passiveStructureGate=passive,optimizerGate=convergence,trainingError=training,
        maximumHeldOutError=maxcv,fitGate=bool(passive and convergence and max(training,maxcv)<=.05),
        continuousFrequencyValidated=False,timeDomainReady=False,radiationReady=False)
    (a.out/'passive_board_fit.json').write_text(json.dumps(dict(summary=summary,folds=rows,optimization=opt,passivity=rep,
        archive=archive,scaleSha256=sha,frequenciesHz=FREQ),indent=2,allow_nan=False))
    print('G3_PASSIVE_BOARD_GATE '+json.dumps(summary),flush=True)
if __name__=='__main__':main()
