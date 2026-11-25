"""G2.09g-D: streamed pressure parity and longer finite-source energy audit."""
import json
from pathlib import Path
import numpy as np
from g2_shared_hammer import run
from g2_acoustic_integrated import make_kernels,render,rel,U,terms,freqs,SR,L,W,RHO,C,sine
from g2_pressure_stream import PressureStream
OUT=Path('/tmp/g2-shared-board')
count=int(np.sum(freqs<6000))
ks=[k[:count] for k in make_kernels(128,96)]
class Collector:
    def __init__(self,block_size):
        self.stream=PressureStream(ks,block_size)
        self.buffer=np.empty((count,block_size));self.n=0;self.parts=[]
    def __call__(self,acc):
        self.buffer[:,self.n]=acc;self.n+=1
        if self.n==self.buffer.shape[1]:self.flush()
    def flush(self):
        if self.n:self.parts.append(self.stream.process(self.buffer[:,:self.n]));self.n=0
    def finish(self):
        self.flush();return np.concatenate([*self.parts,self.stream.finish()],axis=1)
def energy(acc,nt,np_,limit=8000):
    # Same integral as G2.09g-C; reuse sine integrals for equal integer m or n.
    n=acc.shape[1];N=1<<(2*n-1).bit_length()
    u=np.arange(n)/(n-1);taper=np.where(u<=.75,1,.5*(1+np.cos(np.pi*(u-.75)/.25)))
    A=U[:acc.shape[0]].T@np.fft.rfft(acc*taper,n=N,axis=1)
    mu=(np.arange(nt)+.5)/nt;az=2*np.pi*(np.arange(np_)+.5)/np_
    radial=np.sqrt(1-mu**2)[:,None]
    dx=(radial*np.cos(az)[None,:]).ravel();dy=(radial*np.sin(az)[None,:]).ravel()
    mm,mi=np.unique([t[0] for t in terms],return_inverse=True)
    nn,ni=np.unique([t[1] for t in terms],return_inverse=True)
    total=0.
    for i in range(min(int(limit*N/SR),N//2-1)+1):
        k=2*np.pi*i*SR/(N*C)
        X=sine(mm[:,None],L,k*dx[None,:]);Y=sine(nn[:,None],W,k*dy[None,:])
        z=A[:,i]@(X[mi]*Y[ni])
        total+=float(np.sum(abs(z)**2))*(.5 if i==0 else 1.)
    return total*(2/(N*SR))*RHO/(4*np.pi**2*C)*(2*np.pi/(nt*np_))
rows=[];checks=[]
# Pinned published 40 ms energies from approved run 45597800837.
published={'60-m6':4.2544807839738725e-5,'84-m6':2.8892947174052195e-6,'84-m3':8.548991642785546e-6}
for active,mass,label in [([0],6,'48-m6'),([1],6,'60-m6'),([2],6,'84-m6'),([2],3,'84-m3'),([0,1,2],6,'48-60-84-m6')]:
    capture={};a=run(active,1.,SR,6000,mass,capture=capture)
    collect=Collector(512);b=run(active,1.,SR,6000,mass,sink=collect)
    assert a==b,'streaming changed mechanical report'
    p=collect.finish();q=render(capture['acc'],ks)
    assert p.shape==q.shape
    error=float(np.max(abs(p-q)));relative=rel(p,q)
    assert error<=1e-10*max(1.,float(np.max(abs(q))))
    assert np.all(p[:,:int(np.floor(SR/C+.5))]==0)
    r=dict(label=label,kind='stream-parity',maxErrorPa=error,relative=relative,mechanicalParity=True,pass_=True)
    rows.append(r);checks.append(r);print('G2_STREAM_INTEGRATED '+json.dumps(r),flush=True)
    if label not in published:continue
    e40=energy(capture['acc'],16,32)
    er=float(abs(e40-published[label])/published[label])
    checks.append(dict(label=label,kind='angular-parity',error=er,pass_=er<=1e-8))
    del capture
    # 160 ms bounded audit; capture dense only for angular energy calculation, not production.
    cap={};collect=Collector(2048)
    a=run(active,1.,SR,6000,mass,capture=cap,duration_s=.16,sink=collect)
    p=collect.finish();acc=cap['acc'];assert np.all(np.isfinite(p))
    assert p.shape[1]==round(.16*SR)+max(k.shape[1] for k in ks)-1
    assert cap['maxDerivativeError']<=1e-9*max(1.,cap['peakAcceleration'])
    e1=energy(acc,8,16);e2=energy(acc,16,32)
    coarseError=float(abs(e1-e2)/max(e2,1e-30))
    angular=coarseError;angularGrid=[16,32];energies=[float(e1),float(e2)]
    if coarseError>.10:
        e3=energy(acc,32,64)
        energies.append(float(e3));angular=float(abs(e2-e3)/max(e3,1e-30));e2=e3;angularGrid=[32,64]
    e2=float(e2);e40=float(e40);work=float(a['boardJ']+a['boardLoss'])
    r=dict(label=label,kind='longer-energy',durationS=.16,radiatedJ=e2,radiated40msJ=e40,angularError=angular,coarseAngularError=coarseError,angularGrid=angularGrid,angularEnergiesJ=energies,initialJ=a['initialJ'],boardWorkJ=work,boardLossJ=a['boardLoss'],boardEnergyJ=a['boardJ'],radiatedInitialFraction=e2/a['initialJ'],radiatedBoardWorkFraction=e2/work,radiatedBoardLossFraction=e2/a['boardLoss'],peakPa=np.max(abs(p),axis=1).tolist(),rmsLast40msPa=np.sqrt(np.mean(p[:,round(.12*SR):round(.16*SR)]**2,axis=1)).tolist(),maxBalance=a['maxBalance'],maxDerivativeError=cap['maxDerivativeError'])
    rows.append(r);print('G2_EXTENDED_ACOUSTIC '+json.dumps(r),flush=True)
    checks.extend([dict(label=label,kind='angular',error=angular,pass_=angular<=.10),dict(label=label,kind='initial-budget',error=e2/a['initialJ'],pass_=e2<=a['initialJ']),dict(label=label,kind='board-work-budget',error=e2/work,pass_=e2<=work)])
    del cap,acc
for ck in checks:ck['pass_']=bool(ck['pass_'])
gate=all(r['pass_'] for r in checks)
report=dict(scope='one-way finite 160ms radiation diagnostic and streamed pressure equivalence; not full decay or acoustic loading',rows=rows,checks=checks,required=len(checks),passed=sum(r['pass_'] for r in checks),gate=gate)
(OUT/'extended_acoustic_report.json').write_text(json.dumps(report,indent=2,allow_nan=False))
print('G2_EXTENDED_ACOUSTIC_GATE '+json.dumps({k:report[k] for k in ('required','passed','gate')}),flush=True)
if not gate:raise SystemExit(1)
