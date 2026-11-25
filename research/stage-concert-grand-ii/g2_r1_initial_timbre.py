"""Read-only R1 acoustic follow-up: distinguish clarity from loss of musical body."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import periodogram
from g2_r2_baseline_attack import features,db,FS
COMMIT='95c2419c6a52289982e142669ee8ea610a8c7d89'
OLD='dbd007fdeab3def76c3ff8cb3cae47741655429b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    y,fs=sf.read(p,always_2d=True)
    assert fs==FS and y.shape==(72000,2) and np.isfinite(y).all() and sf.info(p).subtype=='PCM_24'
    return y
def load(root,case,mode):
    d=root/f'G2-R1-{case}-{mode}';m=json.loads((d/'manifest.json').read_text())
    assert m['case']==case and m['mode']==mode and m['commit']==COMMIT and m['originalCommit']==OLD and m['radiation']['gate']
    p=d/f'{case}-{mode}.wav';o=d/f'{case}-original.wav'
    assert sha(p)==m['wavSha256'] and sha(o)==m['originalSha256']
    assert sha(d/'pressure.npz')==m['rawSha256']
    return m,read(p),read(o)
def triad_bands(y):
    out=[]
    for lo,hi in ((.02,.08),(.08,.25),(.25,.5),(.55,.75),(.8,1.3)):
        z=y[round(lo*FS):round(hi*FS)]
        f,p=periodogram(z,FS,axis=0,nfft=131072,window='hann',detrend=False)
        p=p.mean(axis=1);df=f[1]-f[0];v={}
        for k in (60,64,67):
            f0=440*2**((k-69)/12)
            v[str(k)]=db(p[(f>=.97*f0)&(f<=1.03*f0)].sum()*df)
        out.append(dict(window=[lo,hi],bandDbfs=v,relativeToC4Db={k:x-v['60'] for k,x in v.items()},rmsDbfs=db(np.mean(z*z))))
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    baseline=json.loads((a.reference/'r2_baseline_attack.json').read_text())
    assert baseline['gate'] and baseline['baselineCommit']==OLD and len(baseline['rows'])==5
    ref=next(x for x in baseline['rows'] if x['key']==60)
    held,dry,orig=load(a.root,'C4-held','dry')
    assert not held['releases'] and held['originalSha256']==ref['g2Sha256']
    g=features(orig,60);d=features(dry,60);v=ref['reference']
    assert g==ref['G2']
    def compare(x):
        return dict(relativeRmsDifferenceToReferenceDb={w:x['windows'][w]['relativeRmsDb']-v['windows'][w]['relativeRmsDb'] for w in x['windows']},
                    partialDifferenceToReferenceDb=[z-q for z,q in zip(x['partials'],v['partials'])])
    c4=dict(original=g,dry=d,reference=v,originalDifference=compare(g),dryDifference=compare(d),
        attackAbsoluteDeltaDb=db(np.mean(dry[960:3840]**2))-db(np.mean(orig[960:3840]**2)))
    print('G2_R1_HELD_TIMBRE '+json.dumps(c4,allow_nan=False),flush=True)
    rows=[];gains={held['gain']}
    for case in ('C4-release','triad'):
        mr,rel,old=load(a.root,case,'release-only');md,dry,other=load(a.root,case,'dry')
        assert mr['originalSha256']==md['originalSha256'] and np.array_equal(old,other)
        assert all(mr[k]==md[k] for k in ('events','releases','gain','scoreSha256'))
        gains.add(md['gain'])
        if case=='C4-release':
            assert md['originalSha256']==held['originalSha256']
        result=dict(case=case,windows={m['mode']:m['windows'] for m in (mr,md)},gaps={m['mode']:m['postReleaseGaps'] for m in (mr,md)})
        if case=='triad':
            result['bands']={name:triad_bands(y) for name,y in [('original',old),('release-only',rel),('dry',dry)]}
        rows.append(result);print('G2_R1_CLARITY '+json.dumps(result,allow_nan=False),flush=True)
    assert len(gains)==1
    report=dict(scope='read-only diagnostic, no selection',heldC4=c4,releaseAndTriad=rows,gate=True,
        limitations=['different reference recording and velocity','short held note does not validate sustain','fundamental bands are approximate, not independent note stems','no perceptual approval or new physical parameters'])
    (a.out/'r1_initial_timbre.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G2_R1_INITIAL_TIMBRE_GATE '+json.dumps(dict(cases=5,gate=True)),flush=True)
if __name__=='__main__':main()
