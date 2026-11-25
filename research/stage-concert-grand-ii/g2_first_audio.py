"""G2.10a: exploratory 5 s pressure renders; no changes to the mechanical model."""
import argparse, hashlib, json, os
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from g2_pilot_metrics import freeze_gain, apply_gain, decay_proxy, FS
from g2_c5_analysis import measure, onset_details

DURATION=5
SR=96000
CUT=6000
BLOCK=2048
GROUPS={'C3':([0],6), 'C4':([1],6), 'C6':([2],6),
        'C6-light':([2],3), 'chord':([0,1,2],6)}
CASES={}
for group,(active,mass) in GROUPS.items():
    for speed in ((1.,2.) if group=='chord' else (.5,1.,2.)):
        CASES[f'{group}-{speed:g}ms']=(group,active,mass,speed)
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,obj):
    p.write_text(json.dumps(obj,indent=2,allow_nan=False))
def render_group(group,out):
    from g2_shared_hammer import run, KEYS
    from g2_acoustic_integrated import make_kernels, freqs, LISTENERS, C
    from g2_pressure_stream import PressureStream
    out.mkdir(parents=True,exist_ok=True)
    count=int(np.sum(freqs<CUT))
    ks=[k[:count] for k in make_kernels(128,96)]
    for ident,(g,active,mass,speed) in CASES.items():
        if g!=group:continue
        stream=PressureStream(ks,BLOCK)
        buf=np.empty((count,BLOCK)); n=0; chunks=[]
        def flush():
            nonlocal n
            if n:
                chunks.append(stream.process(buf[:,:n]));n=0
        def sink(acc):
            nonlocal n
            buf[:,n]=acc;n+=1
            if n==BLOCK:flush()
        report=run(active,speed,SR,CUT,mass,duration_s=DURATION,sink=sink)
        flush()
        pressure=np.concatenate([*chunks,stream.finish()],axis=1)
        assert stream.samples==SR*DURATION
        assert pressure.shape==(3,SR*DURATION+stream.tail)
        assert np.isfinite(pressure).all() and np.all(np.max(abs(pressure),axis=1)>0)
        assert np.all(pressure[:,:int(np.floor(SR/C+.5))]==0)
        file=out/(ident+'.npz')
        np.savez_compressed(file,pressurePa=pressure)
        report.pop('trace')
        meta=dict(id=ident,commit=os.environ['GITHUB_SHA'],group=g,active=[KEYS[i] for i in active],
            speedMps=speed,trebleMassG=mass,sourceSamples=SR*DURATION,pressureSamples=pressure.shape[1],
            sourceRate=SR,cutHz=CUT,blockSize=BLOCK,spatialGrid=[128,96],listenersM=LISTENERS.tolist(),
            channelOrder=['center','left','right'],rawSha256=digest(file),mechanical=report)
        dump(out/(ident+'.json'),meta)
        print('G2_10_RAW '+json.dumps(dict(id=ident,peakPa=np.max(abs(pressure),axis=1).tolist(),
             balance=report['maxBalance'])),flush=True)
def assemble(raw,out):
    out.mkdir(parents=True,exist_ok=True)
    files=list(raw.rglob('*.npz'))
    assert len(files)==len(CASES) and {f.stem for f in files}==set(CASES)
    clips={}; metas={}
    for file in files:
        ident=file.stem
        meta=json.loads(file.with_suffix('.json').read_text())
        group,active,mass,speed=CASES[ident]
        assert (meta['id'],meta['commit'],meta['group'],meta['active'],meta['trebleMassG'],meta['speedMps'])==(ident,os.environ['GITHUB_SHA'],group,[[48,60,84][i] for i in active],mass,speed)
        assert meta['rawSha256']==digest(file) and meta['sourceRate']==SR and meta['cutHz']==CUT
        with np.load(file,allow_pickle=False) as z:
            p=z['pressurePa']
        assert p.shape==(3,meta['pressureSamples']) and np.isfinite(p).all()
        # Keep raw center and full propagation tail; WAV uses physical L/R, exactly 5 s from hammer launch.
        # Resample whole captured pressure first, with fixed zero-padded anti-alias FIR.
        stereo=resample_poly(p[1:3].T,1,2,axis=0,window=('kaiser',5.0),padtype='constant')[:FS*DURATION]
        assert stereo.shape==(FS*DURATION,2)
        clips[ident]=stereo;metas[ident]=meta
    frozen=freeze_gain(clips,list(CASES))
    rows=[]
    for ident in CASES:
        x=apply_gain(clips[ident],frozen['gain'])
        path=out/(ident+'.wav')
        sf.write(path,x,FS,subtype='PCM_24')
        info=sf.info(path); y,fs=sf.read(path,always_2d=True,dtype='float64')
        assert fs==FS and info.subtype=='PCM_24' and y.shape==(FS*DURATION,2)
        assert np.isfinite(y).all() and np.max(abs(y-x))<=2**-23+1e-12 and np.max(abs(y))<1
        row=dict(**metas[ident],wavSha256=digest(path),wavSamples=len(y),
                 peakDbfs=float(20*np.log10(np.max(abs(y)))))
        try:
            onset=onset_details(y,FS)
            row['onset']=onset
            row['decayProxy']=decay_proxy(y,onset['sample'])
            if len(row['active'])==1:
                row['spectralDiagnostics']=measure(y,FS,row['active'][0])
        except ValueError as e:
            row['diagnosticLimitation']=str(e)
        rows.append(row)
        print('G2_10_WAV '+json.dumps(dict(id=ident,peakDbfs=row['peakDbfs'],onset=row.get('onset'),
              diagnosticLimitation=row.get('diagnosticLimitation')),allow_nan=False),flush=True)
    dump(out/'pilot_manifest.json',dict(scope='exploratory one-way pressure; no acoustic loading, dampers, pedal, calibrated SPL or sustain approval',
         commit=os.environ['GITHUB_SHA'],sourceRate=SR,wavRate=FS,durationS=DURATION,
         resampling="scipy resample_poly 1/2 Kaiser beta 5, zero padding; full raw pressure before crop",
         pcm='PCM24 no dither',gain=frozen,rows=rows,required=len(CASES),passed=len(rows),gate=len(rows)==len(CASES)))
    print('G2_10_RENDER_GATE '+json.dumps(dict(required=len(CASES),passed=len(rows),gate=True)),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('mode',choices=['render','assemble'])
    ap.add_argument('--group',choices=GROUPS)
    ap.add_argument('--raw',type=Path)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.mode=='render':
        assert args.group
        render_group(args.group,args.out)
    else:
        assert args.raw
        assemble(args.raw,args.out)
