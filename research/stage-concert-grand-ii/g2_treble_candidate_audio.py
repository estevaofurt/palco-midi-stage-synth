"""G2.10c-C: candidate C6 3g x3, fixed original gain; exploratory only."""
import argparse, hashlib, json, os
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from g2_shared_hammer import run
from g2_acoustic_integrated import make_kernels,render,U,terms,freqs,SR,L,W,RHO,C,sine,LISTENERS
from g2_pressure_stream import PressureStream
from g2_pilot_metrics import apply_gain,decay_proxy,FS
from g2_c5_analysis import measure,onset_details
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
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--speed',type=float,choices=(.5,1.,2.),required=True)
    ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((a.baseline/'pilot_manifest.json').read_text())
    assert manifest['commit']=='226364d5c1808a9bd3ee70d0dab68c0dd51e254a' and manifest['gate'] and len(manifest['rows'])==14
    gain=manifest['gain']['gain'];s=a.speed
    assert np.isfinite(gain) and gain>0
    count=int(np.sum(freqs<6000));ks=[k[:count] for k in make_kernels(128,96)]
    cap={};audit=run([2],s,SR,6000,3,capture=cap,duration_s=.16,trebleStiffnessScale=3.)
    assert cap['maxDerivativeError']<=1e-9*max(1.,cap['peakAcceleration'])
    acc=cap['acc'];e1=energy(acc,8,16);e2=energy(acc,16,32)
    er=float(abs(e1-e2)/max(e2,1e-30));coarse=er;grid=[16,32]
    if er>.10:
        e3=energy(acc,32,64);er=float(abs(e2-e3)/max(e3,1e-30));e2=e3;grid=[32,64]
    e2=float(e2);work=float(audit['boardJ']+audit['boardLoss'])
    auditrow=dict(speed=s,angularError=er,coarseAngularError=coarse,grid=grid,radiatedJ=e2,
        initialJ=audit['initialJ'],boardWorkJ=work,boardLossJ=audit['boardLoss'],
        radiatedInitialFraction=e2/audit['initialJ'],radiatedBoardWorkFraction=e2/work,
        radiatedBoardLossFraction=e2/audit['boardLoss'],gate=bool(er<=.10 and e2<=min(work,audit['initialJ'])))
    dump(a.out/'audit.json',auditrow);print('G2_10C_C_AUDIT '+json.dumps(auditrow),flush=True)
    if not auditrow['gate']:raise SystemExit('radiation audit failed; no candidate audio')
    del cap,acc
    stream=PressureStream(ks,2048);buf=np.empty((count,2048));n=0;parts=[]
    def flush():
        nonlocal n
        if n:parts.append(stream.process(buf[:,:n]));n=0
    def sink(x):
        nonlocal n
        buf[:,n]=x;n+=1
        if n==2048:flush()
    mechanics=run([2],s,SR,6000,3,duration_s=5.,sink=sink,trebleStiffnessScale=3.)
    flush();p=np.concatenate([*parts,stream.finish()],axis=1)
    assert p.shape==(3,SR*5+stream.tail) and np.isfinite(p).all()
    assert np.all(p[:,:int(np.floor(SR/C+.5))]==0)
    raw=a.out/f'C6-3g-K3-{s:g}ms.npz';np.savez_compressed(raw,pressurePa=p)
    stereo=resample_poly(p[1:3].T,1,2,axis=0,window=('kaiser',5.),padtype='constant')[:FS*5]
    assert stereo.shape==(240000,2)
    x=apply_gain(stereo,gain);wav=a.out/f'C6-3g-K3-{s:g}ms.wav'
    sf.write(wav,x,FS,subtype='PCM_24')
    y,fs=sf.read(wav,always_2d=True);assert fs==FS and y.shape==x.shape and sf.info(wav).subtype=='PCM_24'
    assert np.max(abs(y-x))<=2**-23+1e-12
    onset=onset_details(y,FS);met=measure(y,FS,84);decay=decay_proxy(y,onset['sample'])
    comparisons={}
    for ident in (f'C6-{s:g}ms',f'C6-light-{s:g}ms'):
        path=a.baseline/(ident+'.wav');old=next(z for z in manifest['rows'] if z['id']==ident)
        assert sha(path)==old['wavSha256']
        z,fs=sf.read(path,always_2d=True);assert fs==FS and z.shape==y.shape
        # Copy original bytes, no gain changes.
        (a.out/(ident+'-original.wav')).write_bytes(path.read_bytes())
        oldmet=measure(z,FS,84)
        comparisons[ident]=dict(originalSha256=old['wavSha256'],originalMetrics=oldmet,
            peakDeltaDb=met['peak_dbfs']-oldmet['peak_dbfs'])
    mechanics.pop('trace')
    row=dict(commit=os.environ['GITHUB_SHA'],baselineCommit=manifest['commit'],baselineManifestSha256=sha(a.baseline/'pilot_manifest.json'),
        gain=gain,speedMps=s,massG=3,stiffnessScale=3,sourceRate=SR,wavRate=FS,sourceSamples=SR*5,wavSamples=len(y),
        listenersM=LISTENERS.tolist(),rawSha256=sha(raw),wavSha256=sha(wav),audit=auditrow,
        mechanics=mechanics,metrics=met,decay=decay,comparisons=comparisons,
        limitations=['one-way uncalibrated pressure','five-second exploratory render only','no sustain or tuning approval','no independent acoustic damping added'])
    dump(a.out/'comparison.json',row)
    print('G2_10C_C_RENDER '+json.dumps(dict(speed=s,gain=gain,peakDbfs=met['peak_dbfs'],windows=met['windows'],comparisons={k:v['peakDeltaDb'] for k,v in comparisons.items()}),allow_nan=False),flush=True)
if __name__=='__main__':main()
