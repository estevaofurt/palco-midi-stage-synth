"""G3.01c: nonuniform wound-wire Rayleigh-Ritz eigenproblem, no audio.
Fixed simply supported ends, core EI, piecewise constant line density.
Only the centered winding geometry is a hypothesis. No bridge or final tuning.
"""
import argparse,json,math,hashlib
from pathlib import Path
import numpy as np
from scipy.linalg import eigh
from scipy.optimize import brentq
from scale_hypothesis import build,area
ROOT=Path(__file__).parent
def mass_matrix(L,core,extra,start,end,N):
    if not (L>0 and core>0 and extra>=0 and 0<=start<end<=L and N>=8):raise ValueError('mass domain')
    n=np.arange(1,N+1,dtype=float)
    # Orthonormal sine basis, integral 2/L sin(n*pi*x/L) sin(m*pi*x/L).
    def integral(q):
        # numpy sinc is sin(pi*x)/(pi*x); analytic at q=0.
        width=(end-start)/L;center=(end+start)/(2*L)
        return width*np.cos(np.pi*q*center)*np.sinc(q*width/2)
    Q=integral(n[:,None]-n[None,:])-integral(n[:,None]+n[None,:])
    M=core*np.eye(N)+extra*Q
    return (M+M.T)/2
def stiffness(L,EI,T,N):
    k=np.arange(1,N+1)*np.pi/L
    return EI*k**4+T*k*k
def modes(M,L,EI,T,count=8):
    N=len(M)
    if not (T>0 and EI>0):raise ValueError('stiffness domain')
    w=eigh(np.diag(stiffness(L,EI,T,N)),M,subset_by_index=[0,count-1],eigvals_only=True,driver='gvx')
    if np.any(w<=0) or not np.isfinite(w).all():raise ValueError('eigenvalues')
    return np.sqrt(w)/(2*np.pi)
def cents(a,b):return 1200*np.log2(np.asarray(a)/np.asarray(b))
def solve(r,N,q,screen):
    L=r['lengthM'];EI=r['bendingNm2'];core=r['coreMassPerM'];T=r['tensionPerStringN'];f=r['nominalHz']
    extra=(r['linearDensityKgM']-core)/q
    # No claim that the actual winding is centered. Explicitly define this fixture.
    start=L*(1-q)/2;end=L-start
    M=mass_matrix(L,core,extra,start,end,N)
    original=modes(M,L,EI,T)
    fit=brentq(lambda t:modes(M,L,EI,t,count=1)[0]-f,screen['minTensionN'],screen['maxTensionN'],xtol=1e-9)
    corrected=modes(M,L,EI,fit)
    return dict(T=fit,original=original,corrected=corrected,start=start,end=end,localMu=core+extra)
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    raw=(ROOT/'scale_hypothesis.json').read_bytes();c=json.loads(raw);base=build(c);rows=[]
    for r in base['rows']:
        if r['wrapLayers']==0:continue
        L=r['lengthM'];f=r['nominalHz'];q=c['wrappedFraction'];s=c['screen']
        x=solve(r,64,q,s);y=solve(r,128,q,s)
        conv=float(np.max(abs(cents(x['corrected'],y['corrected']))))
        fit=y['T'];stress=fit/area(r['coreDiameterM'])
        assert conv<=.1 and abs(cents(y['corrected'][0],f))<=1e-4
        assert stress<=s['maxCoreStressPa']
        n=np.arange(1,9);B=r['inharmonicity']
        old=f*n*np.sqrt((1+B*n*n)/(1+B))
        delta=cents(y['corrected'],old)
        # Local travelling-wave impedances are distinct from bridge admittance.
        rows.append(dict(key=r['key'],windingIntervalM=[y['start'],y['end']],windingLocationStatus='centered_hypothesis',
            nominalHz=f,oldTensionN=r['tensionPerStringN'],retunedTensionN=fit,tensionChangePct=100*(fit/r['tensionPerStringN']-1),
            oldTensionFundamentalErrorCents=float(cents(y['original'][0],f)),coreStressPa=stress,
            modalFrequenciesHz=y['corrected'].tolist(),partialDeltaCents=delta.tolist(),convergenceCents=conv,
            bareImpedanceNsM=math.sqrt(fit*r['coreMassPerM']),wrappedImpedanceNsM=math.sqrt(fit*y['localMu']),
            oldAverageGroupZ=r['groupImpedanceNsM'],newAverageGroupZ=r['count']*math.sqrt(fit*r['linearDensityKgM'])))
    assert len(rows)==29
    summary=dict(keys=len(rows),maxConvergenceCents=max(r['convergenceCents'] for r in rows),
        maxOldTensionPitchErrorCents=max(abs(r['oldTensionFundamentalErrorCents']) for r in rows),
        maxTensionChangePct=max(abs(r['tensionChangePct']) for r in rows),
        maxPartialChangeCents=max(abs(x) for r in rows for x in r['partialDeltaCents']),
        gate=True,scaleReady=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'wound_modes.json').write_text(json.dumps(dict(summary=summary,rows=rows,sourceSha256=hashlib.sha256(raw).hexdigest(),
        scope='fixed ends, lossless, symmetric winding hypothesis; not acoustic tuning or chosen scale',
        limitations=['uniform core EI, copper bending/axial stiffness ignored','winding position not measured','no termination compliance or bridge','no material calibration, no audio']),indent=2,allow_nan=False))
    print('G3_WOUND_GATE '+json.dumps(summary),flush=True)
    for r in rows:
        if r['key'] in (21,29,30,46,47,49):print('G3_WOUND_KEY '+json.dumps(r),flush=True)
if __name__=='__main__':main()
