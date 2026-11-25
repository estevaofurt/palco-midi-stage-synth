"""R2 preparation: exact recorded notes versus frozen G2, read-only diagnostics."""
import argparse,hashlib,json,urllib.request,urllib.parse,io
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import periodogram
from g2_c5_analysis import onset_details,measure
HERE=Path(__file__).parent
FS=48000
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def db(v):return float(10*np.log10(max(float(v),1e-30)))
def features(y,key):
    assert y.ndim==2 and y.shape[1]==2 and np.isfinite(y).all()
    det=onset_details(y,FS);x=y[det['sample']:]
    assert len(x)>=round(1.3*FS)
    n=round(.002*FS);p=np.mean(x[:round(.08*FS)].reshape(-1,n,2)**2,axis=(1,2));peak=float(p.max())
    indices={str(t):int(np.flatnonzero(p>=peak*t*t)[0])*2 for t in (.1,.5,.9)}
    at=float(np.mean(x[round(.02*FS):round(.08*FS)]**2))
    windows={}
    for a,b in [(0,.01),(.01,.02),(.02,.08),(.08,.25),(.25,.75),(.8,1.3)]:
        z=x[round(a*FS):round(b*FS)]
        f,P=periodogram(z,FS,axis=0,window='hann',nfft=131072,detrend=False);P=P.mean(axis=1);df=f[1]-f[0]
        def band(lo,hi):return float(P[(f>=lo)&(f<hi)].sum()*df)
        total=band(0,24000.001);common=band(0,6000);f0=440*2**((key-69)/12)
        windows[f'{a:g}-{b:g}']=dict(relativeRmsDb=db(np.mean(z*z))-db(at),
            bandsCommonPct=[100*band(lo,hi)/max(common,1e-30) for lo,hi in [(0,250),(250,1000),(1000,3000),(3000,6000)]],
            above6kPct=100*band(6000,24000.001)/max(total,1e-30),
            commonCentroidHz=float(np.sum(f[f<6000]*P[f<6000])/max(float(P[f<6000].sum()),1e-30)),
            fundamentalBandCommonPct=100*band(.95*f0,1.05*f0)/max(common,1e-30) if b-a>=.06 else None,
            monoToStereoPowerDb=db(np.mean(z.mean(axis=1)**2))-db(np.mean(z*z)),
            physicalWindowResolutionHz=1/(b-a))
    m=measure(y,FS,key)
    return dict(onset=det,first80msThresholdCrossingMs=indices,first80msPeakBlockMs=int(np.argmax(p))*2,
        windows=windows,partials=m['windows']['0.25-0.75']['partial_band_relative_db'],
        partialAbsoluteDbfs=m['windows']['0.25-0.75']['partial_band_power_dbfs'])
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    score=json.loads((HERE/'g2_octave_score.json').read_text());hold=json.loads((HERE/'holdout_g2.json').read_text())['c5']
    assert score['referenceCommit']==hold['commit'] and not ({z['path'] for z in score['files']} & {z['path'] for z in hold['files']})
    rows=[]
    for z in score['files']:
        k=z['key'];d=a.baseline/f'G2-11-audit-{k}';m=json.loads((d/'manifest.json').read_text());p=d/f'{k}-G2.wav'
        assert m['commit']=='dbd007fdeab3def76c3ff8cb3cae47741655429b' and m['case']==str(k) and m['audit']['gate'] and m['scoreSha256']==sha(HERE/'g2_octave_score.json') and sha(p)==m['wavSha256']
        y,fs=sf.read(p,always_2d=True);assert fs==FS and y.shape==(72000,2)
        url=f"https://raw.githubusercontent.com/sfzinstruments/SalamanderGrandPiano/{score['referenceCommit']}/"+urllib.parse.quote(z['path'],safe='/')
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'StageSynth-G2-clean-base-diagnostic'}),timeout=60) as response:b=response.read(z['bytes']+1)
        assert len(b)==z['bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==z['git_blob_sha1']
        q,fs=sf.read(io.BytesIO(b),always_2d=True);assert fs==FS
        g=features(y,k);v=features(q,k)
        row=dict(key=k,referenceLayer=score['referenceLayer'],speedMps=1.,referenceSha256=hashlib.sha256(b).hexdigest(),g2Sha256=sha(p),referenceSource=z,reference=v,G2=g,
            deltaRelativeRmsDb={w:g['windows'][w]['relativeRmsDb']-v['windows'][w]['relativeRmsDb'] for w in g['windows']},
            partialDifferenceDb=[g['partials'][i]-v['partials'][i] for i in range(1,min(len(g['partials']),len(v['partials'])))])
        rows.append(row);print('G2_R2_BASELINE '+json.dumps(row,allow_nan=False),flush=True)
    assert len(rows)==5 and {x['key'] for x in rows}=={60,63,66,69,72}
    report=dict(scope='preparation only; five exact development recordings, no new physical candidate or tuning',referenceCommit=score['referenceCommit'],baselineCommit='dbd007fdeab3def76c3ff8cb3cae47741655429b',rows=rows,limitations=['different microphone positions and velocities, layer8 not equivalent to 1m/s','2ms block threshold is not physical contact onset or reliable rise time','band fractions use common 0-6kHz; >6kHz reported separately; short spectral windows leak','partial band approximations; reference signal/noise not established','no absolute SPL or causal inference, no calibration or acceptance threshold','no release equivalence, no holdout'],gate=True)
    (a.out/'r2_baseline_attack.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G2_R2_BASELINE_GATE '+json.dumps(dict(cases=5,gate=True)),flush=True)
if __name__=='__main__':main()
