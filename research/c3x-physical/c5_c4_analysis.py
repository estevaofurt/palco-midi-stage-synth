#!/usr/bin/env python3
"""Analyze authorized, exact-SHA FLAC Yamaha C5 C4 references without redistributing audio.
The result is a descriptive acoustic comparison, NOT Yamaha C3X metrology.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.optimize import least_squares
from scipy.signal import find_peaks
from scipy.fft import rfft, next_fast_len

TARGET_C4 = 261.6255653005986
SOURCES = {
    'v1': {'file':'C4v1.flac','sha256':'ca44d2e906110ebc2f67ae4c233e84cbbf0e657fe53e1c6724e4f31409478f11','size_bytes':1265676},
    'v8': {'file':'C4v8.flac','sha256':'36fb0535a1f21fe1dfc367c361dedda73710144e8c4940b40e97e6e5f8a3c694','size_bytes':1774472},
    'v16': {'file':'C4v16.flac','sha256':'e2944a0d1b31ea0ff8eb82b20ae2108027f111d96fb680c6e36d01f40582c252','size_bytes':1772214},
}
SAMPLE_LICENSE = 'CC BY 3.0; Alexander Holm; Salamander Grand Piano v3; Yamaha C5'
PINNED_COMMIT = '3382bf9496bba2486f5ab0de55a264d1dfc38404'
REPO = 'https://raw.githubusercontent.com/sfzinstruments/SalamanderGrandPiano/'


def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):h.update(chunk)
    return h.hexdigest()


def onset_sample(y:np.ndarray,fs:int)->int:
    # 5ms rms windows; avoids confusing transport silence with slow piano attack.
    mono=np.asarray(y,dtype=np.float64).mean(axis=1) if y.ndim==2 else np.asarray(y,dtype=np.float64)
    width=max(64,int(fs*.005)); n=len(mono)//width
    if n<10:return 0
    rms=np.sqrt(np.mean(mono[:n*width].reshape(n,width)**2,axis=1))
    p=float(np.max(rms));threshold=max(p*.03, 2e-5)
    if p<threshold:return 0
    for idx in range(n-1):
        if rms[idx]>=threshold and rms[idx+1]>=threshold:return max(0,(idx-1)*width)
    return int(np.argmax(rms)*width)


def peak_interpolated(spec:np.ndarray,idx:int,step:float)->tuple[float,float]:
    if 0<idx<len(spec)-1:
        y=np.log(np.maximum(spec[idx-1:idx+2],1e-20))
        den=float(y[0]-2*y[1]+y[2]);shift=float(.5*(y[0]-y[2])/den) if abs(den)>1e-12 else 0.
        shift=float(np.clip(shift,-.5,.5))
        return (idx+shift)*step, float(spec[idx])
    return idx*step,float(spec[idx])


def window_partials(mono:np.ndarray,fs:int,start_s:float,duration_s:float,base_hz:float=TARGET_C4):
    a=round(start_s*fs); n=round(duration_s*fs)
    if a<0 or a+n>len(mono) or n<512:return None
    x=mono[a:a+n]; w=np.hanning(n); norm=max(float(np.sum(w)),1.)
    nfft=next_fast_len(n*8); spec=np.abs(rfft(x*w,n=nfft))/norm
    step=fs/nfft; out=[]
    for k in range(1,13):
        if k*base_hz>=fs*.46:break
        low=base_hz*k*.974; high=base_hz*k*(1.045 if k>=5 else 1.024)
        l=max(1,int(low/step));r=min(len(spec)-2,math.ceil(high/step))
        if l>=r:continue
        local=spec[l:r+1]
        cand,_=find_peaks(local,prominence=max(float(np.max(local))*.004,1e-10))
        if len(cand):best=int(cand[np.argmax(local[cand])])+l
        else:best=l+int(np.argmax(local))
        freq,amp=peak_interpolated(spec,best,step)
        # Absolute noise-floor/sideband filter; retain missing harmonics as None.
        baseline=float(np.median(local));snr=20*math.log10(max(amp,1e-12)/max(baseline,1e-12))
        out.append({'n':k,'freq_hz':round(freq,5),'amplitude':amp,'contrast_db':round(snr,2)})
    if not out:return None
    fund=next((p['amplitude'] for p in out if p['n']==1),None)
    if not fund or fund<1e-9:return None
    for p in out:
        p['relative_db']=round(20*math.log10(max(p['amplitude'],1e-12)/fund),2)
        p['amplitude']=round(p['amplitude'],9)
    return out


def estimate_B(partials):
    if not partials:return None
    # Fit only credible partials (avoid sideband/noise as if real harmonics).
    strong=[p for p in partials if p['n']<=10 and p['relative_db']>=-42 and p['contrast_db']>4]
    if len(strong)<4:return None
    ks=np.array([p['n'] for p in strong],float)
    fs=np.array([p['freq_hz'] for p in strong],float)
    def res(p):
        f1,b=p
        return (f1*ks*np.sqrt((1+b*ks**2)/(1+b))-fs)/ks
    opt=least_squares(res,[TARGET_C4,.0004],bounds=([TARGET_C4*.90,0.],[TARGET_C4*1.10,.012]),max_nfev=250)
    err=float(np.sqrt(np.mean(res(opt.x)**2)))
    if not opt.success or err>4:return None
    return {'fundamental_fit_hz':round(float(opt.x[0]),5), 'B_fit':round(float(opt.x[1]),9),'fit_residual_hz_rms':round(err,5),'partials_used':len(strong)}


def measure(y:np.ndarray,fs:int,origin:str):
    if y.ndim!=2 or y.shape[1]!=2:raise ValueError('expected original stereo')
    if fs!=48000:raise ValueError('expected original 48kHz')
    if not np.isfinite(y).all():raise ValueError('non finite')
    mono=np.mean(y.astype(np.float64),axis=1)
    onset=onset_sample(y,fs)
    u=mono[onset:]
    # Envelope relative to onset; all outputs retain same unmodified input level.
    windows={'attack_35_255ms':(.035,.22),'body_260_700ms':(.26,.44),'tail_900_1400ms':(.9,.50)}
    partials={}
    for name,(start,length) in windows.items():
        p=window_partials(u,fs,start,length)
        if p:partials[name]=p
    attack=partials.get('attack_35_255ms')
    fit=estimate_B(partials.get('body_260_700ms',attack))
    diff=None
    if attack and 'body_260_700ms' in partials:
        a={p['n']:p['relative_db'] for p in attack};b={p['n']:p['relative_db'] for p in partials['body_260_700ms']}
        diff={str(n):round(b[n]-a[n],2) for n in a.keys()&b.keys() if n<=9}
    # Condense complex arrays, retain all 12 harmonic curves per window for reproduction.
    return {
        'origin':origin,'sample_rate_hz':fs,'channels':2,'duration_s':round(len(y)/fs,5),
        'onset_s':round(onset/fs,5),'peak':round(float(np.max(np.abs(y))),6),
        'rms':round(float(np.sqrt(np.mean(y**2))),7),'samples_at_or_above_unit_amplitude':int(np.count_nonzero(np.abs(y)>=.999999)),
        'note_on_level_limitations':'Float V10 has no PCM full-scale restriction; this count is NOT evidence of digital clipping',
        'spectral_windows':partials,'inharmonicity_estimate':fit,
        'relative_partial_shift_attack_to_body_db':diff,
        'not_a_measurement_of_C3X':True,
    }


def compare(reference, v10):
    # Physically different pianos and not velocity-matched. Descriptive distance only.
    out={}
    for label in ('attack_35_255ms','body_260_700ms','tail_900_1400ms'):
        rp={p['n']:p['relative_db'] for p in reference['spectral_windows'].get(label,[])}
        vp={p['n']:p['relative_db'] for p in v10['spectral_windows'].get(label,[])}
        common=[n for n in range(2,9) if n in rp and n in vp]
        out[label]={'mean_absolute_difference_db':round(float(np.mean([abs(rp[n]-vp[n]) for n in common])),3) if common else None,
                    'per_partial_reference_minus_v10_db':{str(n):round(rp[n]-vp[n],2) for n in common},
                    'notes':'Comparacao espectral descritiva entre C5 real e C3X V10 estimado; camadas nao calibradas por velocidade fisica'}
    return out


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--source-dir',type=Path);ap.add_argument('--v10-profiles',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args(argv)
    report={'schema':'c3x-f1-c5-c4-spectral-comparison-v1','source_instrument':'Yamaha C5, not Yamaha C3X',
       'license':SAMPLE_LICENSE,'source_commit':PINNED_COMMIT,
       'origin':'https://github.com/sfzinstruments/SalamanderGrandPiano','reference_note':'C4 MIDI60',
       'source_audio_distributed':False,'commercial_c3x_calibration_approved':False,
       'layers':{},'c5_vs_v10':{},'limitations':['Not measured hammer velocities; microphone and room impact spectra',
         'Yamaha C5 is not Yamaha C3X; no C3X-identification gate fulfilled','No imported samples in synthesis engine',
         'v10 normalization disabled for independent same-gain DSP output; layer gains not physically standardized']}
    refs=json.loads(a.v10_profiles.read_text(encoding='utf-8'))['layers'] if a.v10_profiles else {}
    for layer,desc in SOURCES.items():
        if a.source_dir:
            path=a.source_dir/desc['file']
            if path.stat().st_size != desc['size_bytes']:raise ValueError(f'Unexpected source size {path}')
            digest=sha256_file(path)
            if digest!=desc['sha256']:raise ValueError(f'Source SHA mismatch {path}: {digest}')
            audio,fs=sf.read(path,always_2d=True,dtype='float64')
            measured=measure(audio,fs,'C5 '+layer)
            measured['verified_sha256']=digest
            report['layers'][layer]=measured
            if layer in refs:report['c5_vs_v10'][layer]=compare(measured,refs[layer])
        else:
            report['layers'][layer]={'downloaded':False,'expected_sha256':desc['sha256']}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('C5_REFERENCE_ANALYSIS',json.dumps({'verified_layers':sum('verified_sha256' in x for x in report['layers'].values()),
      'comparisons':len(report['c5_vs_v10']),'complete':a.source_dir is not None},ensure_ascii=False))
    return report

if __name__=='__main__':main()
