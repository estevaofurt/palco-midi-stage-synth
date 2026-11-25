"""G2.11b diagnostic follow-up: read existing verified pressure, no new synthesis."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import periodogram
FS=48000
SR=96000
COMMIT='dbd007fdeab3def76c3ff8cb3cae47741655429b'
CASES=[str(k) for k in range(60,73)]+['triad']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def powerdb(p):return float(10*np.log10(max(p,1e-300)))
def normdb(x):return powerdb(float(np.mean(x*x)))
def load(root,c):
    d=root/('G2-11-audit-'+c);m=json.loads((d/'manifest.json').read_text())
    assert m['commit']==COMMIT and m['case']==c and m['mode']=='audit' and m['audit']['gate']
    raw=d/(c+'-pressure.npz');wav=d/(c+'-G2.wav')
    assert sha(raw)==m['rawSha256'] and sha(wav)==m['wavSha256']
    with np.load(raw,allow_pickle=False) as a:p=a['pressurePa']
    y,fs=sf.read(wav,always_2d=True)
    assert p.ndim==2 and p.shape[0]==3 and p.shape[1]>=144000 and np.isfinite(p).all()
    assert fs==FS and y.shape==(72000,2) and np.isfinite(y).all()
    return m,p,y
def bands(x,keys,lo,hi):
    y=x[:,round(lo*SR):round(hi*SR)]
    f,p=periodogram(y,SR,axis=1,window='hann',nfft=262144,detrend=False)
    p=p.mean(axis=0);df=f[1]-f[0]
    return {str(k):float(p[(f>=.97*(440*2**((k-69)/12)))&(f<=1.03*(440*2**((k-69)/12)))].sum()*df) for k in keys}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    cases={c:load(a.root,c) for c in CASES}
    assert len({x[0]['gain'] for x in cases.values()})==1
    assert len({x[0]['scoreSha256'] for x in cases.values()})==1
    assert len({x[1].shape for x in cases.values()})==1
    rows=[]
    for c in CASES[:-1]:
        m,p,y=cases[c];r=m['mechanical'];w=m['metrics']['windows'];f=float(r['injectedJ']);rebound=float(r['reboundRemovedJ']);felt=float(r['feltJ'])
        delivered=f-rebound-felt
        assert delivered>0
        # Net board work over full 1.5s, not same as finite 160ms acoustic budget.
        board=float(r['boardJ']+r['boardLoss'])
        pitch=m['pitchDiagnostic'];cents=[x['centsFromNominal'] for x in pitch]
        row=dict(key=int(c),attackDbfs=w['0.02-0.08']['rms_dbfs'],peakDbfs=m['peakDbfs'],
            injectedJ=f,deliveredJ=delivered,deliveredFraction=delivered/f,boardWorkJ=board,boardFraction=board/f,
            attackPressureRmsPa=np.sqrt(np.mean(p[:,1920:7680]**2,axis=1)).tolist(),
            pitchPeakCents=cents,pitchPeakRangeCents=max(cents)-min(cents),pitchPeakAbsMaxCents=max(map(abs,cents)),
            pitchScreenExceeds5c=max(map(abs,cents))>5 or max(cents)-min(cents)>5,
            spectralH2RelativeDb=w['0.25-0.75']['partial_band_relative_db'][1],
            bodyDecayDb=w['0.25-0.75']['rms_dbfs']-w['0.02-0.08']['rms_dbfs'],
            lateDecayDb=w['0.8-1.3']['rms_dbfs']-w['0.02-0.08']['rms_dbfs'])
        rows.append(row);print('G2_11_OCTAVE_DIAG '+json.dumps(row,allow_nan=False),flush=True)
    keys=[60,64,67];m,p,y=cases['triad'];isolated=sum(cases[str(k)][1] for k in keys)
    err=float(np.linalg.norm(p-isolated)/np.linalg.norm(p))
    windows=[]
    for lo,hi in ((.02,.08),(.08,.25),(.25,.75),(.8,1.3)):
        joint=bands(p,keys,lo,hi);summed=bands(isolated,keys,lo,hi)
        # Each isolated source can contribute in another note's band: no attribution of overlapping modes.
        matrix={str(k):bands(cases[str(k)][1],keys,lo,hi) for k in keys}
        dbs={k:powerdb(v) for k,v in joint.items()}
        windows.append(dict(window=[lo,hi],jointBandPa2=joint,sumBandPa2=summed,
            jointBandDbRelativeToC4={k:v-dbs['60'] for k,v in dbs.items()},
            jointMinusSumDb={k:powerdb(v)-powerdb(summed[k]) for k,v in joint.items()},
            isolatedBandPa2=matrix))
    chord=dict(rawRelativeNormDifference=err,windows=windows,
        limitation='local nominal fundamental bands, not independent note stems or perceptual polyphony')
    print('G2_11_TRIAD_DIAG '+json.dumps(chord,allow_nan=False),flush=True)
    report=dict(commit=COMMIT,scope='read-only diagnostic from existing octave renders, no tuning acceptance',
        rows=rows,chord=chord,limitations=['one physical hammer speed only','zero-padded local spectral peaks are not reliable F12.5 pitch estimates','pressure is uncalibrated, not SPL','one-way radiation estimate is not a closed energy balance','bands are not isolated note stems','no pedal/damper simulation or auditory approval'],
        required=14,passed=len(cases),gate=len(cases)==14)
    (a.out/'octave_diagnostic.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G2_11_DIAG_GATE '+json.dumps({k:report[k] for k in ('required','passed','gate')}),flush=True)
if __name__=='__main__':main()
