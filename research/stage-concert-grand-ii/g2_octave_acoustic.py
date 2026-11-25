"""G2.11b/c: octave pressure audits and continuous musical renders."""
import argparse, hashlib, json, os
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly,periodogram
from g2_octave_events import run_events,ROOT,data
from g2_acoustic_integrated import make_kernels,render,rel,freqs,SR,C,LISTENERS
from g2_treble_candidate_audio import energy
from g2_pressure_stream import PressureStream
from g2_pilot_metrics import apply_gain,FS
from g2_c5_analysis import measure,onset_details
HERE=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj):p.write_text(json.dumps(obj,indent=2,allow_nan=False))
def db(x):return float(20*np.log10(x)) if x>0 else None
def pitch(y,key):
    f0=440*2**((key-69)/12);start=onset_details(y,FS)['sample'];rows=[]
    for lo,hi in ((.08,.25),(.25,.75),(.8,1.3)):
        z=y[start+round(lo*FS):start+round(hi*FS)]
        if len(z)!=round(hi*FS)-round(lo*FS):continue
        f,p=periodogram(z,FS,axis=0,window='hann',nfft=262144,detrend=False);p=p.mean(axis=1)
        ix=np.flatnonzero((f>=.95*f0)&(f<=1.05*f0));j=ix[np.argmax(p[ix])]
        freq=float(f[j]);power=float(p[ix].sum()*(f[1]-f[0]))
        rows.append(dict(window=[lo,hi],peakHz=freq,centsFromNominal=float(1200*np.log2(freq/f0)),bandRmsDbfs=db(np.sqrt(power)),windowBinHz=1/(hi-lo)))
    return rows
def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['audit','music']);ap.add_argument('--case',required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    model=json.loads((ROOT/'octave.json').read_text());score=json.loads((HERE/'g2_octave_score.json').read_text())
    assert model['playable']==list(range(60,73))
    # Board modal basis unchanged; only the new joint port columns differ.
    ob=model['boards'][0];orig=next(b for b in data['boards'] if b['basis']==6000)
    assert len(ob['modes'])==len(orig['modes']) and all(all(m[k]==n[k] for k in ('f','lambda','components')) for m,n in zip(ob['modes'],orig['modes']))
    manifest=json.loads((a.baseline/'pilot_manifest.json').read_text())
    assert manifest['commit']=='226364d5c1808a9bd3ee70d0dab68c0dd51e254a' and manifest['gate']
    gain=manifest['gain']['gain'];count=int(np.sum(freqs<6000));ks=[k[:count] for k in make_kernels(128,96)]
    if a.mode=='audit':
        key=None if a.case=='triad' else int(a.case);assert key is None or 60<=key<=72
        events=[(0.,k,1.) for k in ([60,64,67] if key is None else [key])]
        dur=1.5;short=.16;acc=np.empty((count,round(short*SR)));idx=0
        def capture(x):
            nonlocal idx
            acc[:,idx]=x;idx+=1
        report=run_events(model,events,SR,short,sink=capture)
        assert idx==acc.shape[1] and np.isfinite(acc).all()
        p=render(acc,ks);fine=[k[:count] for k in make_kernels(256,192)];q=render(acc,fine)
        spatial=rel(p,q)
        e1=energy(acc,8,16);e2=energy(acc,16,32);err=abs(e1-e2)/max(e2,1e-30);grid=[16,32]
        if err>.10:
            e3=energy(acc,32,64);err=abs(e2-e3)/max(e3,1e-30);e2=e3;grid=[32,64]
        work=report['boardJ']+report['boardLoss']
        audit=dict(case=a.case,spatialError=spatial,angularError=err,grid=grid,radiatedJ=e2,boardWorkJ=work,injectedJ=report['injectedJ'],boardLossJ=report['boardLoss'],radiatedBoardWorkFraction=e2/work,radiatedBoardLossFraction=e2/report['boardLoss'],gate=bool(spatial<=.05 and err<=.10 and e2<=min(work,report['injectedJ'])))
        dump(a.out/'audit.json',audit);print('G2_11B_AUDIT '+json.dumps(audit,allow_nan=False),flush=True)
        if not audit['gate']:raise SystemExit('radiation gate failed')
        del acc,p,q,fine
    else:
        s=next(s for s in score['scores'] if s['id']==a.case);events=s['events'];dur=s['durationS']
    stream=PressureStream(ks,2048);buf=np.empty((count,2048));n=0;parts=[]
    def flush():
        nonlocal n
        if n:parts.append(stream.process(buf[:,:n]));n=0
    def sink(x):
        nonlocal n
        buf[:,n]=x;n+=1
        if n==2048:flush()
    report=run_events(model,events,SR,dur,sink=sink);flush()
    p=np.concatenate([*parts,stream.finish()],axis=1)
    assert stream.samples==round(dur*SR) and p.shape==(3,round(dur*SR)+stream.tail) and np.isfinite(p).all()
    assert np.all(p[:,:int(np.floor(SR/C+.5))]==0)
    stereo=resample_poly(p[1:3].T,1,2,axis=0,window=('kaiser',5.),padtype='constant')[:round(dur*FS)]
    x=apply_gain(stereo,gain);wav=a.out/(a.case+'-G2.wav');sf.write(wav,x,FS,subtype='PCM_24')
    y,fs=sf.read(wav,always_2d=True);assert fs==FS and y.shape==x.shape and sf.info(wav).subtype=='PCM_24' and np.max(abs(y-x))<=2**-23+1e-12
    report.pop('trace')
    raw=a.out/(a.case+'-pressure.npz');np.savez_compressed(raw,pressurePa=p)
    row=dict(case=a.case,mode=a.mode,commit=os.environ['GITHUB_SHA'],scoreSha256=sha(HERE/'g2_octave_score.json'),gain=gain,events=events,mechanical=report,wavSha256=sha(wav),rawSha256=sha(raw),peakDbfs=db(np.max(abs(y))),durationS=dur,listenerPositions=LISTENERS.tolist())
    if a.mode=='audit':
        row['audit']=audit
        if key is not None:row.update(metrics=measure(y,FS,key),pitchDiagnostic=pitch(y,key))
    dump(a.out/'manifest.json',row);print('G2_11_RENDER '+json.dumps({k:v for k,v in row.items() if k not in ('mechanical',)},allow_nan=False),flush=True)
if __name__=='__main__':main()
