"""R2c: verify and render one energy-equivalent mass candidate against frozen Dry."""
import argparse,copy,hashlib,json,math,os,shutil
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from g2_damped_events import run_damped,ROOT
from g2_damper_test import convergence
from g2_acoustic_integrated import make_kernels,render,rel,freqs,SR,C
from g2_treble_candidate_audio import energy
from g2_pressure_stream import PressureStream
from g2_pilot_metrics import apply_gain,FS
from g2_r2_baseline_attack import features
GAIN=.18491857409775692
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o):p.write_text(json.dumps(o,indent=2,allow_nan=False))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--key',type=int,required=True);ap.add_argument('--screen',type=Path,required=True);ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    assert a.key in (60,64,67,72)
    a.out.mkdir(parents=True,exist_ok=True)
    prev=json.loads((a.screen/'mass_screen.json').read_text())
    assert prev['gate'] and prev['key']==a.key and len(prev['rows'])==3
    screen=next(x for x in prev['checks'] if x['label']=='mass-70-same-energy')
    assert screen['screen']==(a.key!=67)
    base=json.loads((ROOT/'octave.json').read_text());j=next(i for i,x in enumerate(base['groups']) if x['key']==a.key)
    count=int(np.sum(freqs<6000));ks=[k[:count] for k in make_kernels(128,96)]
    fine=[k[:count] for k in make_kernels(256,192)]
    variants=[]
    for label,scale,speed in [('dry',1.,1.),('mass70-energy',.7,math.sqrt(1/.7))]:
        model=copy.deepcopy(base);model['groups'][j]['massKg']*=scale
        events=[(0.,a.key,speed)];short=.16
        acc=np.empty((count,round(short*SR)));i=0
        def capture(x):
            nonlocal i
            acc[:,i]=x;i+=1
        m=run_damped(model,events,SR,short,sink=capture,mode='dry',retain_trace=True)
        assert i==acc.shape[1] and np.isfinite(acc).all()
        old=prev['rows'][0 if scale==1 else 2]['mechanical']
        for k in ('injectedJ','mechanicalJ','boardJ','boardLoss','feltJ','jointLoss','damperLossJ','reboundRemovedJ'):
            assert abs(m[k]-old[k])<=1e-10
        hi=run_damped(model,events,192000,short,mode='dry',retain_trace=True);conv=convergence(m,hi)
        p=render(acc,ks);q=render(acc,fine);spatial=rel(p,q)
        e1=energy(acc,8,16);e2=energy(acc,16,32);angular=abs(e1-e2)/max(e2,1e-30);grid=[16,32]
        if angular>.10:
            e3=energy(acc,32,64);angular=abs(e3-e2)/max(e3,1e-30);e2=e3;grid=[32,64]
        work=m['boardJ']+m['boardLoss'];rad=dict(spatialError=spatial,angularError=angular,grid=grid,radiatedJ=e2,boardWorkJ=work,gate=bool(spatial<=.05 and angular<=.10 and e2<=min(work,m['injectedJ'])))
        print('G2_R2C_AUDIT '+json.dumps(dict(key=a.key,label=label,convergence=conv,radiation=rad),allow_nan=False),flush=True)
        assert rad['gate']
        variants.append(dict(label=label,model=model,events=events,shortPressure=p[:,:round(short*SR)].copy(),convergence=conv,radiation=rad,shortMechanical={k:v for k,v in m.items() if k!='trace'}))
    assert abs(variants[0]['shortMechanical']['injectedJ']-variants[1]['shortMechanical']['injectedJ'])<=1e-12
    # Both conditions must pass before writing WAVs.
    dur=1.5;rows=[];signals={}
    for item in variants:
        label=item['label'];stream=PressureStream(ks,2048);buf=np.empty((count,2048));n=0;parts=[]
        def flush():
            nonlocal n
            if n:parts.append(stream.process(buf[:,:n]));n=0
        def sink(x):
            nonlocal n
            buf[:,n]=x;n+=1
            if n==2048:flush()
        report=run_damped(item['model'],item['events'],SR,dur,sink=sink,mode='dry');flush()
        p=np.concatenate([*parts,stream.finish()],axis=1)
        assert stream.samples==round(dur*SR) and p.shape==(3,round(dur*SR)+stream.tail) and np.isfinite(p).all()
        assert np.all(p[:,:int(np.floor(SR/C+.5))]==0)
        short=item['shortPressure'];assert np.linalg.norm(p[:,:short.shape[1]]-short)/np.linalg.norm(short)<=1e-9
        parity=None;pcmDelta=None;originalWavSha=None
        if a.key==60 and label=='dry':
            d=a.baseline;manifest=json.loads((d/'manifest.json').read_text());raw=d/'pressure.npz'
            assert manifest['commit']=='95c2419c6a52289982e142669ee8ea610a8c7d89' and manifest['case']=='C4-held' and manifest['mode']=='dry' and sha(raw)==manifest['rawSha256'] and manifest['gain']==GAIN
            with np.load(raw,allow_pickle=False) as z:old=z['pressurePa']
            parity=float(np.linalg.norm(p-old)/np.linalg.norm(old));assert parity<=1e-9
        x=apply_gain(resample_poly(p[1:3].T,1,2,axis=0,window=('kaiser',5.),padtype='constant')[:round(dur*FS)],GAIN)
        wav=a.out/f'{a.key}-{label}.wav';sf.write(wav,x,FS,subtype='PCM_24')
        y,fs=sf.read(wav,always_2d=True);assert fs==FS and y.shape==x.shape and np.max(abs(y-x))<=2**-23+1e-12
        if a.key==60 and label=='dry':
            orig=a.baseline/'C4-held-dry.wav';assert sha(orig)==manifest['wavSha256']
            z,fs=sf.read(orig,always_2d=True);assert fs==FS and z.shape==y.shape and sf.info(orig).subtype=='PCM_24'
            pcmDelta=float(np.max(abs(z-y)))
            assert pcmDelta<=2**-23+1e-12, 'PCM difference exceeds one 24-bit quantization step'
            # Preserve original bytes and raw pressure, not an independently quantized copy.
            shutil.copyfile(orig,wav);assert sha(wav)==manifest['wavSha256'];y=z;p=old
            originalWavSha=manifest['wavSha256']
            print('G2_R2C_BASELINE_PARITY '+json.dumps(dict(pressureRelativeError=parity,pcmMaxAbsDelta=pcmDelta,originalWavSha256=originalWavSha)),flush=True)
        signals[label]=y
        raw=a.out/f'{a.key}-{label}-pressure.npz';np.savez_compressed(raw,pressurePa=p)
        row=dict(label=label,events=item['events'],convergence=item['convergence'],radiation=item['radiation'],mechanical={k:v for k,v in report.items() if k!='trace'},baselineParity=parity,baselineWavMaxAbsDelta=pcmDelta,baselineOriginalSha256=originalWavSha,wavSha256=sha(wav),rawSha256=sha(raw),peakDbfs=float(20*np.log10(np.max(abs(y)))),features=features(y,a.key))
        rows.append(row)
    g,c=[x['features'] for x in rows]
    delta={w:c['windows'][w]['relativeRmsDb']-g['windows'][w]['relativeRmsDb'] for w in g['windows']}
    result=dict(key=a.key,commit=os.environ['GITHUB_SHA'],gain=GAIN,durationS=dur,screen=screen,rows=rows,relativeEnvelopeDeltaDb=delta,partialDeltaDb=[b-a for a,b in zip(g['partials'],c['partials'])],gate=True,scope='one experimental equal-energy comparison, no candidate adoption, no calibrated dynamics or sustain')
    dump(a.out/'manifest.json',result)
    print('G2_R2C_AUDIO '+json.dumps({k:v for k,v in result.items() if k!='rows'},allow_nan=False),flush=True)
if __name__=='__main__':main()
