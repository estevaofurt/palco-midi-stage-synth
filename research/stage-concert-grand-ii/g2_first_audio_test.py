"""G2.10a export contract; synthetic fixtures only, not a piano or physical validation."""
import json, os, tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from g2_first_audio import CASES, SR, FS, CUT, DURATION, digest, assemble

def reject(fn):
    try:
        fn()
    except (AssertionError, ValueError):
        return
    raise AssertionError('invalid manifest was accepted')

def main():
    with tempfile.TemporaryDirectory() as root:
        raw=Path(root)/'raw'; raw.mkdir()
        out=Path(root)/'out'
        n=SR*DURATION+512
        # Finite, causal deterministic signal, with separate center and asymmetric L/R.
        t=np.arange(SR)/SR
        signal=np.sin(2*np.pi*220*t)*np.exp(-4*t)
        p=np.zeros((3,n))
        p[:,300:300+SR]=np.array([.5,1.,.25])[:,None]*signal
        ids=list(CASES)
        for i,(ident,(group,active,mass,speed)) in enumerate(CASES.items(),1):
            file=raw/(ident+'.npz')
            np.savez_compressed(file,pressurePa=p*i/len(CASES))
            meta=dict(id=ident,commit=os.environ['GITHUB_SHA'],group=group,
                active=[[48,60,84][j] for j in active],trebleMassG=mass,speedMps=speed,
                sourceRate=SR,cutHz=CUT,pressureSamples=n,rawSha256=digest(file))
            file.with_suffix('.json').write_text(json.dumps(meta))
        # A complete set is necessary before a gain may be selected.
        first=raw/(ids[0]+'.npz')
        missing=first.with_suffix('.bak');first.rename(missing)
        reject(lambda:assemble(raw,out));missing.rename(first)
        side=first.with_suffix('.json')
        original=side.read_text()
        bad=json.loads(original);bad['rawSha256']='0'*64
        side.write_text(json.dumps(bad))
        reject(lambda:assemble(raw,out))
        bad=json.loads(original);bad['commit']='not-the-render-commit'
        side.write_text(json.dumps(bad))
        reject(lambda:assemble(raw,out));side.write_text(original)
        assemble(raw,out)
        manifest=json.loads((out/'pilot_manifest.json').read_text())
        assert manifest['gate'] and manifest['required']==manifest['passed']==14
        assert set(manifest['gain']['anchorIds'])==set(ids)
        peaks=[]
        for row in manifest['rows']:
            path=out/(row['id']+'.wav')
            info=sf.info(path)
            assert (info.frames,info.channels,info.samplerate,info.subtype)==(240000,2,48000,'PCM_24')
            assert digest(path)==row['wavSha256']
            x,_=sf.read(path,always_2d=True)
            assert np.max(abs(x[:,1]-.25*x[:,0]))<2**-21
            assert row.get('onset') and row.get('decayProxy')
            peaks.append(np.max(abs(x)))
        assert abs(peaks[-1]-10**(-6/20))<2**-23
        assert np.allclose(np.array(peaks)/peaks[-1],np.arange(1,15)/14,atol=1e-6,rtol=0)
        print('G2_10_EXPORT_CONTRACT_PASS: missing set, corrupt hash, wrong commit, 14 WAVs, fixed gain, stereo, PCM24, diagnostics')
if __name__=='__main__':main()
