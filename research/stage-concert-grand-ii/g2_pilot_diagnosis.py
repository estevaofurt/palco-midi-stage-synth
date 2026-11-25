"""G2.10b diagnostic of existing 5 s pilot; no physical parameter changes."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import periodogram

SOURCE='226364d5c1808a9bd3ee70d0dab68c0dd51e254a'
USER_CHORD_SHA='e54fcff0f4d4463ce675bd00490e54fd117fab014c565e03e711e6d0d554c117'
WINDOWS=[(.02,.08),(.08,.25),(.25,.75),(.8,1.3),(2.5,3)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def db(x):return float(10*np.log10(x)) if x>0 else None
def spectral(x,fs,f0):
    f,p=periodogram(x,fs=fs,axis=0,window='hann',detrend=False,scaling='density')
    p=p.mean(axis=1);df=f[1]-f[0];total=float(p.sum()*df)
    def band(lo,hi):return float(p[(f>=lo)&(f<hi)].sum()*df)
    partials=[band(k*f0*.965,k*f0*1.08) for k in range(1,9) if k*f0*1.08<fs/2]
    return dict(rmsDbfs=db(float(np.mean(x*x))),fundamentalBandDbfs=db(partials[0]),
        partialBandDbfs=[db(z) for z in partials],
        partialBandRelativeDb=[db(z/partials[0]) if partials[0]>0 else None for z in partials],
        belowPoint7Fraction=band(80,.7*f0)/total if total else None,
        totalBandPower=total,
        fundamentalFraction=partials[0]/total if total else None)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--wav',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    manifest=json.loads((a.wav/'pilot_manifest.json').read_text())
    assert manifest['commit']==SOURCE and manifest['gate'] and len(manifest['rows'])==14
    rows={r['id']:r for r in manifest['rows']}
    raw={p.stem:p for p in a.raw.rglob('*.npz')}
    assert len(raw)==14 and set(raw)==set(rows)
    results=[];signals={}
    for ident,r in rows.items():
        path=a.wav/(ident+'.wav');assert sha(path)==r['wavSha256']
        assert sha(raw[ident])==r['rawSha256']
        with np.load(raw[ident],allow_pickle=False) as z:p=z['pressurePa']
        assert p.shape==(3,r['pressureSamples']) and np.isfinite(p).all()
        y,fs=sf.read(path,always_2d=True);assert fs==48000 and y.shape==(240000,2)
        signals[ident]=p
        m=r['mechanical'];initial=m['initialJ'];work=m['boardJ']+m['boardLoss']
        row=dict(id=ident,active=r['active'],speed=r['speedMps'],trebleMassG=r['trebleMassG'],
            initialJ=initial,boardWorkFraction=work/initial,boardLossFraction=m['boardLoss']/initial,
            groupEnergyFractions=[v/initial for v in m['groupJ']],groupLossFraction=m['groupLoss']/initial,
            feltLossFraction=m['feltJ']/initial,jointLossFraction=m['jointLoss']/initial,
            contactMs=m['duration'],contactPeakN=m['peak'],contactImpulseNs=m['impulse'],
            peakDbfs=r['peakDbfs'],onset=r.get('onset'),windows={})
        start=r['onset']['sample']
        for lo,hi in WINDOWS:
            zz=y[start+round(lo*fs):start+round(hi*fs)]
            pp=p[:,2*start+round(lo*96000):2*start+round(hi*96000)]
            w=dict(pressureRmsPa=np.sqrt(np.mean(pp*pp,axis=1)).tolist(),rmsDbfs=db(float(np.mean(zz*zz))))
            if len(r['active'])==1:
                w.update(spectral(zz,fs,440*2**((r['active'][0]-69)/12)))
            row['windows'][f'{lo:g}-{hi:g}']=w
        results.append(row);print('G2_10B_NOTE '+json.dumps(row,allow_nan=False),flush=True)
    comparisons=[]
    for s in (1,2):
        chord=signals[f'chord-{s}ms']
        isolated=sum(signals[f'{n}-{s}ms'] for n in ('C3','C4','C6'))
        assert chord.shape==isolated.shape
        comparison=dict(speed=s,relativeWaveformDifference=float(np.linalg.norm(chord-isolated)/np.linalg.norm(chord)),
            scope='difference from independently excited groups; not a gate or attribution of individual notes in octave stack')
        comparisons.append(comparison);print('G2_10B_OCTAVES '+json.dumps(comparison),flush=True)
    match=sha(a.wav/'chord-2ms.wav')==USER_CHORD_SHA
    report=dict(sourceCommit=SOURCE,userUploadHashMatch=match,rows=results,octaveComparisons=comparisons,
        limitations=['same gain, no SPL calibration','partial bands include coincident modes, not uniquely attributed string energy','final mechanical energy partition is not time-resolved radiation','octave stack is not a musical triad'])
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G2_10B_DIAGNOSTIC_COMPLETE '+json.dumps(dict(cases=len(results),userUploadHashMatch=match)),flush=True)
if __name__=='__main__':main()
