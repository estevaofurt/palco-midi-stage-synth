"""R2.03 preparation: absolute vs relative partials and onset sensitivity, read-only."""
import argparse,json
from pathlib import Path
import numpy as np
from g2_r2_mass_pack import KEYS,SOURCES,GAIN,sha,read
from g2_r2_baseline_attack import features,db,FS
def fixed(y,start):
    x=y[start:]
    at=float(np.mean(x[960:3840]**2));assert at>0
    return {name:db(np.mean(x[round(lo*FS):round(hi*FS)]**2))-db(at)
            for name,lo,hi in [('0-0.01',0,.01),('0.01-0.02',.01,.02),('0.02-0.08',.02,.08),('0.08-0.25',.08,.25),('0.25-0.75',.25,.75),('0.8-1.3',.8,1.3)]}
def subtract(a,b):return {k:a[k]-b[k] for k in a}
def env(f):return {k:v['relativeRmsDb'] for k,v in f['windows'].items()}
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    ref=json.loads((a.reference/'r2_baseline_attack.json').read_text())
    assert ref['gate'] and ref['baselineCommit']=='dbd007fdeab3def76c3ff8cb3cae47741655429b' and {x['key'] for x in ref['rows']}=={60,63,66,69,72}
    refs={x['key']:x for x in ref['rows']};rows=[]
    for k,note in KEYS.items():
        d=a.root/f'G2-R2C-note-{k}';m=json.loads((d/'manifest.json').read_text())
        assert m['commit']==SOURCES[k]['commit'] and m['key']==k and m['gate'] and m['gain']==GAIN and m['durationS']==1.5
        assert m['screen']['screen']==(k!=67)
        f={};y={};attacks={};press={}
        for item in m['rows']:
            name=item['label'];wav=d/f'{k}-{name}.wav';raw=d/f'{k}-{name}-pressure.npz'
            assert name not in f and sha(wav)==item['wavSha256'] and sha(raw)==item['rawSha256'] and item['radiation']['gate']
            z=read(wav);ft=features(z,k)
            assert ft['onset']['sample']==item['features']['onset']['sample']
            for field in ('partials','partialAbsoluteDbfs'):
                assert np.max(abs(np.asarray(ft[field])-item['features'][field]))<=1e-7
            assert max(abs(v) for v in subtract(env(ft),env(item['features'])).values())<=1e-7
            f[name]=ft;y[name]=z;attacks[name]=db(np.mean(z[960:3840]**2))
            with np.load(raw,allow_pickle=False) as q:pr=q['pressurePa']
            assert pr.shape[0]==3 and pr.shape[1]>=144000 and np.isfinite(pr).all()
            press[name]=[db(np.mean(pr[:,round(lo*96000):round(hi*96000)]**2,axis=1)[i]) for i in range(3) for lo,hi in [(0,.01),(.02,.08)]]
        assert set(f)=={'dry','mass70-energy'}
        g,c=f['dry'],f['mass70-energy'];d0,c0=y['dry'],y['mass70-energy']
        absdelta=np.asarray(c['partialAbsoluteDbfs'])-g['partialAbsoluteDbfs']
        relative=np.asarray(c['partials'])-g['partials']
        assert np.max(abs(absdelta-absdelta[0]-relative))<=1e-7
        common=min(g['onset']['sample'],c['onset']['sample'])
        row=dict(note=note,key=k,source=SOURCES[k],onsetSamples={name:t['onset']['sample'] for name,t in f.items()},
            attackFixedDeltaDb=attacks['mass70-energy']-attacks['dry'],partialAbsoluteDeltaDb=absdelta.tolist(),partialRelativeDeltaDb=relative.tolist(),
            envelopeOwnOnsetDeltaDb=subtract(env(c),env(g)),envelopeCommonOnsetDeltaDb=subtract(fixed(c0,common),fixed(d0,common)),
            envelopeLaunchDeltaDb=subtract(fixed(c0,0),fixed(d0,0)),
            pressureByReceiverDeltaDb=(np.array(press['mass70-energy'])-press['dry']).reshape(3,2).tolist(),
            crossingMs={name:t['first80msThresholdCrossingMs'] for name,t in f.items()})
        if k in (60,72):
            v=refs[k]['reference'];re=np.asarray(v['partials'])
            row['reference']=dict(layer=refs[k]['referenceLayer'],sha256=refs[k]['referenceSha256'],
                envelopeDryGapDb=subtract(env(g),env(v)),envelopeCandidateGapDb=subtract(env(c),env(v)),
                partialDryGapDb=(np.asarray(g['partials'])-re).tolist(),partialCandidateGapDb=(np.asarray(c['partials'])-re).tolist(),
                referenceCrossingMs=v['first80msThresholdCrossingMs'])
        rows.append(row);print('G2_R2_ATTACK_COMPARE '+json.dumps(row,allow_nan=False),flush=True)
    report=dict(rows=rows,gate=True,scope='read-only; verified existing renders, exact C4/C5 reference metrics; no causal inference or selection',
        limitations=['onset operational not hammer contact','fixed pressure windows from launch include propagation','absolute partial powers comparable only between model versions with fixed gain','reference layer/recording not calibrated to model velocity','no release or sustain approval'])
    (a.out/'attack_comparison.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G2_R2_ATTACK_COMPARE_GATE '+json.dumps(dict(notes=4,exactReferenceNotes=2,gate=True)),flush=True)
if __name__=='__main__':main()
