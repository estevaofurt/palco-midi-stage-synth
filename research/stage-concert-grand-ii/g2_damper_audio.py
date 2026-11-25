"""R1 acoustic comparison: same events, explicit key releases, fixed gain."""
import argparse,hashlib,json,os,shutil
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from g2_damped_events import run_damped,ROOT
from g2_acoustic_integrated import make_kernels,render,rel,freqs,SR,C
from g2_treble_candidate_audio import energy
from g2_pressure_stream import PressureStream
from g2_pilot_metrics import apply_gain,FS
HERE=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,indent=2,allow_nan=False))
def rmsdb(x):return float(20*np.log10(max(float(np.sqrt(np.mean(x*x))),1e-15)))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--case',required=True);ap.add_argument('--mode',choices=['release-only','dry'],required=True);ap.add_argument('--original',type=Path,required=True);ap.add_argument('--proof',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    proof=json.loads((a.proof/'r1_report.json').read_text());assert proof['gate'] and proof['passed']==proof['required']==6
    a.out.mkdir(parents=True,exist_ok=True)
    model=json.loads((ROOT/'octave.json').read_text())
    score=json.loads((HERE/'g2_octave_score.json').read_text())
    if a.case in ('C4-held','C4-release','triad'):
        keys=[60,64,67] if a.case=='triad' else [60]
        events=[(0.,k,1.) for k in keys];dur=1.5
        releases=[] if a.case=='C4-held' else [(.5,k) for k in keys]
        orig='triad' if a.case=='triad' else '60'
    else:
        s=next(s for s in score['scores'] if s['id']==a.case)
        events=s['events'];dur=s['durationS'];orig=a.case
        hold={'escala-do-maior':.18,'arpejo-do-maior':.12,'progressoes':.55}[a.case]
        releases=[(round(t+hold,6),k) for t,k,_ in events]
    m=json.loads((a.original/'manifest.json').read_text());p0=a.original/(orig+'-G2.wav');raw0=a.original/(orig+'-pressure.npz')
    assert m['commit']=='dbd007fdeab3def76c3ff8cb3cae47741655429b' and m['case']==orig and m['scoreSha256']==sha(HERE/'g2_octave_score.json')
    assert m['events']==[list(e) for e in events] and m['durationS']==dur and sha(p0)==m['wavSha256'] and sha(raw0)==m['rawSha256']
    gain=m['gain'];assert gain>0
    old,fs=sf.read(p0,always_2d=True);assert fs==FS and old.shape==(round(dur*FS),2)
    count=int(np.sum(freqs<6000));ks=[k[:count] for k in make_kernels(128,96)]
    short=.16;acc=np.empty((count,round(short*SR)));i=0
    def capture(x):
        nonlocal i
        acc[:,i]=x;i+=1
    audit=run_damped(model,[e for e in events if e[0]<short],SR,short,sink=capture,mode=a.mode,releases=[e for e in releases if e[0]<short])
    assert i==acc.shape[1] and np.isfinite(acc).all()
    p=render(acc,ks);q=render(acc,[k[:count] for k in make_kernels(256,192)])
    spatial=rel(p,q);e1=energy(acc,8,16);e2=energy(acc,16,32);angular=abs(e1-e2)/max(e2,1e-30);grid=[16,32]
    if angular>.10:
        e3=energy(acc,32,64);angular=abs(e3-e2)/max(e3,1e-30);e2=e3;grid=[32,64]
    work=audit['boardJ']+audit['boardLoss']
    gate=bool(spatial<=.05 and angular<=.10 and e2<=min(work,audit['injectedJ']))
    rad=dict(spatialError=spatial,angularError=angular,grid=grid,radiatedJ=e2,boardWorkJ=work,boardLossJ=audit['boardLoss'],gate=gate)
    dump(a.out/'audit.json',rad);print('G2_R1_AUDIO_AUDIT '+json.dumps(rad),flush=True)
    assert gate
    del acc,p,q
    stream=PressureStream(ks,2048);buf=np.empty((count,2048));n=0;parts=[]
    def flush():
        nonlocal n
        if n:parts.append(stream.process(buf[:,:n]));n=0
    def sink(x):
        nonlocal n
        buf[:,n]=x;n+=1
        if n==2048:flush()
    report=run_damped(model,events,SR,dur,sink=sink,mode=a.mode,releases=releases);flush()
    pressure=np.concatenate([*parts,stream.finish()],axis=1)
    assert stream.samples==round(dur*SR) and np.isfinite(pressure).all() and pressure.shape==(3,round(dur*SR)+stream.tail)
    assert np.all(pressure[:,:int(np.floor(SR/C+.5))]==0)
    if a.mode=='release-only':
        with np.load(raw0,allow_pickle=False) as z:oldp=z['pressurePa']
        first=round(min(t for t,_ in releases)*SR) if releases else round(dur*SR)
        assert np.linalg.norm(pressure[:,:first]-oldp[:,:first])/np.linalg.norm(oldp[:,:first])<=1e-9
    x=apply_gain(resample_poly(pressure[1:3].T,1,2,axis=0,window=('kaiser',5.),padtype='constant')[:round(dur*FS)],gain)
    wav=a.out/(a.case+'-'+a.mode+'.wav');sf.write(wav,x,FS,subtype='PCM_24')
    y,fs=sf.read(wav,always_2d=True);assert fs==FS and y.shape==x.shape and np.max(abs(y-x))<=2**-23+1e-12
    shutil.copyfile(p0,a.out/(a.case+'-original.wav'))
    raw=a.out/'pressure.npz';np.savez_compressed(raw,pressurePa=pressure)
    windows=[]
    for lo,hi in [(0,.02),(.02,.08),(.08,.25),(.25,.5),(.5,.75),(.8,1.3),(dur-.5,dur)]:
        z=slice(round(lo*FS),round(hi*FS));u,v=rmsdb(old[z]),rmsdb(y[z]);windows.append(dict(start=lo,end=hi,originalDbfs=u,candidateDbfs=v,deltaDb=v-u))
    gaps=[]
    for t in sorted({t for t,_ in releases}):
        next_t=min([e[0] for e in events if e[0]>t]+[dur])
        if next_t-t>=.03:
            lo=t+.025;hi=next_t;z=slice(round(lo*FS),round(hi*FS));gaps.append(dict(release=t,start=lo,end=hi,originalDbfs=rmsdb(old[z]),candidateDbfs=rmsdb(y[z]),deltaDb=rmsdb(y[z])-rmsdb(old[z])))
    report.pop('trace')
    row=dict(case=a.case,mode=a.mode,commit=os.environ['GITHUB_SHA'],originalCommit=m['commit'],scoreSha256=m['scoreSha256'],events=events,releases=releases,gain=gain,durationS=dur,wavSha256=sha(wav),originalSha256=sha(p0),rawSha256=sha(raw),radiation=rad,mechanical=report,windows=windows,postReleaseGaps=gaps,peakDbfs=float(20*np.log10(np.max(abs(y)))),scope='diagnostic only; fixed gain, no pedal, no calibrated damper or full phrase radiation budget')
    dump(a.out/'manifest.json',row)
    print('G2_R1_AUDIO '+json.dumps({k:v for k,v in row.items() if k!='mechanical'},allow_nan=False),flush=True)
if __name__=='__main__':main()
