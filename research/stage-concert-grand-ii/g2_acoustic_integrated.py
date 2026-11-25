"""G2.09g-C: full board acceleration, causal pressure, finite-source far-field budget."""
import json
from pathlib import Path
import numpy as np
from g2_shared_hammer import run,data
from g2_radiation import grid,geometry,kernels,pressure,LISTENERS,RHO,C
OUT=Path('/tmp/g2-shared-board')
L,W=1.4,1.1;SR=96000
board=next(b for b in data['boards'] if b['basis']==6000)
modes=board['modes']
terms=sorted({(c['m'],c['n']) for m in modes for c in m['components']})
ix={t:i for i,t in enumerate(terms)}
U=np.zeros((len(modes),len(terms)))
for i,m in enumerate(modes):
    for c in m['components']:U[i,ix[c['m'],c['n']]]=c['coefficient']
freqs=np.array([m['f'] for m in modes])
def make_kernels(nx,ny):
    x,y,area=grid(L,W,nx,ny)
    S=np.array([np.sin(m*np.pi*x/L)*np.sin(n*np.pi*y/W) for m,n in terms])
    result=[]
    for loc in LISTENERS:
        d,w=geometry(x,y,area,loc)
        result.append(U@kernels(S,d,w,SR,'linear'))
    return result
medium=make_kernels(128,96);fine=make_kernels(256,192)
def render(acc,ks):
    return np.stack([pressure(acc,k[:acc.shape[0]]) for k in ks])
def rel(a,b):
    n=max(a.shape[-1],b.shape[-1])
    a=np.pad(a,((0,0),(0,n-a.shape[-1])));b=np.pad(b,((0,0),(0,n-b.shape[-1])))
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-30))
def bands(p):
    f=np.fft.rfftfreq(p.shape[1],1/SR);v=np.abs(np.fft.rfft(p,axis=1))**2
    # relative spectral sum, not acoustic power or loudness.
    return {str(lo)+'-'+str(hi):float(v[:,(f>=lo)&(f<hi)].sum()/max(v.sum(),1e-30)) for lo,hi in [(0,100),(100,500),(500,2000),(2000,5000),(5000,6000),(6000,8000),(8000,48001)]}
def J(z,length):
    return length*np.exp(.5j*z*length)*np.sinc(z*length/(2*np.pi))
def sine(m,length,z):
    a=m*np.pi/length
    return (J(z+a,length)-J(z-a,length))/(2j)
def angular_energy(acc,nt,np_,limit=8000):
    # Finite acceleration record tapered over final quarter; not energy of full note.
    n=acc.shape[1];N=1<<(2*n-1).bit_length()
    u=np.arange(n)/(n-1);taper=np.where(u<=.75,1,.5*(1+np.cos(np.pi*(u-.75)/.25)))
    # Transform modes to original sine coefficients before directional integration.
    A=U[:acc.shape[0]].T@np.fft.rfft(acc*taper,n=N,axis=1)
    mu=(np.arange(nt)+.5)/nt;az=2*np.pi*(np.arange(np_)+.5)/np_
    radial=np.sqrt(1-mu**2)[:,None]
    dx=(radial*np.cos(az)[None,:]).ravel();dy=(radial*np.sin(az)[None,:]).ravel()
    mm=np.array([t[0] for t in terms]);nn=np.array([t[1] for t in terms])
    total=0.
    for i in range(min(int(limit*N/SR),N//2-1)+1):
        k=2*np.pi*i*SR/(N*C)
        X=sine(mm[:,None],L,k*dx[None,:]);Y=sine(nn[:,None],W,k*dy[None,:])
        z=A[:,i]@(X*Y)
        total+=float(np.sum(abs(z)**2))*(.5 if i==0 else 1.)
    return total*(2/(N*SR))*RHO/(4*np.pi**2*C)*(2*np.pi/(nt*np_))
rows=[];checks=[]
for active,mass in [([0],6),([1],6),([2],6),([2],3),([0,1,2],6)]:
    label='-'.join(str([48,60,84][i]) for i in active)+'-m'+str(mass)
    captures={}
    for cut in [5000,6000,8000]:
        if cut==8000 and active not in ([2],[0,1,2]):continue
        cap={};r=run(active,1.,SR,cut,mass,capture=cap);acc=cap['acc']
        assert acc.shape[0]==int(np.sum(freqs<cut)) and np.all(np.isfinite(acc))
        assert cap['maxDerivativeError']<=1e-9*max(1.,cap['peakAcceleration'])
        p=render(acc,medium);assert np.all(np.isfinite(p)) and np.max(abs(p))>0
        # First physical propagation sample is fixed by receiver geometry.
        assert np.all(p[:,:int(np.floor(SR/C+.5))]==0)
        row=dict(label=label,cut=cut,modes=acc.shape[0],initialJ=r['initialJ'],boardWorkJ=r['boardJ']+r['boardLoss'],boardJ=r['boardJ'],peakPa=np.max(abs(p),axis=1).tolist(),rmsPa=np.sqrt(np.mean(p*p,axis=1)).tolist(),bands=bands(p),maxDerivativeError=cap['maxDerivativeError'],peakAcceleration=cap['peakAcceleration'],maxBalance=r['maxBalance'])
        if cut==6000:
            q=render(acc,fine);row['spatialError']=rel(p,q)
            # Angular convergence: 8x16 vs 16x32; report and gate separately.
            e1=angular_energy(acc,8,16);e2=angular_energy(acc,16,32)
            row.update(radiatedJ=e2,angularError=abs(e1-e2)/max(e2,1e-30),radiatedInitialFraction=e2/r['initialJ'],radiatedBoardWorkFraction=e2/max(row['boardWorkJ'],1e-30))
            checks.append(dict(label=label,kind='spatial',error=row['spatialError'],pass_=row['spatialError']<=.05))
            checks.append(dict(label=label,kind='angular',error=row['angularError'],pass_=row['angularError']<=.10))
            checks.append(dict(label=label,kind='initial-budget',error=row['radiatedInitialFraction'],pass_=e2<=r['initialJ']))
            if label=='60-m6':
                control=run(active,1.,SR,cut,mass)
                assert r==control,'observer changed mechanics'
                row['mechanicalParity']=True
        captures[cut]=p
        rows.append(row);print('G2_ACOUSTIC '+json.dumps(row),flush=True)
    for cut in [5000,8000]:
        if cut not in captures:continue
        error=rel(captures[cut],captures[6000])
        ck=dict(label=label,kind='band'+str(cut),error=error,pass_=error<=.10)
        checks.append(ck);print('G2_ACOUSTIC_CHECK '+json.dumps(ck),flush=True)
# 5k and 8k are diagnostic; do not select a reduced band on these results.
required=[r for r in checks if r['kind'] in ('spatial','angular','initial-budget')]
gate=all(r['pass_'] for r in required)
report=dict(scope='40ms finite prescribed source, one-way pressure and angular energy diagnostic; no feedback, no WAV or calibrated SPL',rows=rows,checks=checks,required=len(required),passed=sum(r['pass_'] for r in required),gate=gate)
(OUT/'acoustic_report.json').write_text(json.dumps(report,indent=2))
print('G2_ACOUSTIC_GATE '+json.dumps({k:report[k] for k in ('required','passed','gate')}),flush=True)
if not gate:raise SystemExit(1)
