"""Synthetic stereo fixtures test packaging, not the piano engine."""
import json,tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
import g2_r2_mass_pack as p
def main():
    with tempfile.TemporaryDirectory() as tmp:
        t=Path(tmp);root=t/'input';root.mkdir();ts=np.arange(72000)/p.FS
        x=np.column_stack([np.sin(2*np.pi*261.6*ts),np.sin(2*np.pi*261.6*ts+.1)])*.05*np.exp(-ts)[:,None]
        for k in p.KEYS:
            d=root/f'G2-R2C-note-{k}';d.mkdir();rows=[]
            for label,speed,scale in [('dry',1.,1.),('mass70-energy',(1/.7)**.5,.8)]:
                wav=d/f'{k}-{label}.wav';sf.write(wav,x*scale,p.FS,subtype='PCM_24')
                raw=d/f'{k}-{label}-pressure.npz';np.savez(raw,pressurePa=x.T)
                rows.append(dict(label=label,wavSha256=p.sha(wav),rawSha256=p.sha(raw),radiation={'gate':True},convergence={'trajectory':.001},events=[[0.,k,speed]],mechanical={'injectedJ':.005},baselineParity=0.,baselineWavMaxAbsDelta=0.,baselineOriginalSha256=p.sha(wav)))
            (d/'manifest.json').write_text(json.dumps(dict(commit=p.SOURCES[k]['commit'],key=k,gain=p.GAIN,durationS=1.5,gate=True,screen={'screen':k!=67},rows=rows,relativeEnvelopeDeltaDb={},partialDeltaDb=[])))
        p.pack(root,t/'valid')
        manifest=root/'G2-R2C-note-67'/'manifest.json';b=manifest.read_bytes()
        for name,mutate in [('hash',lambda m:m['rows'][0].update(wavSha256='invalid')),('radiation',lambda m:m['rows'][0]['radiation'].update(gate=False)),('energy',lambda m:m['rows'][1]['mechanical'].update(injectedJ=.004)),('negative-control',lambda m:m['screen'].update(screen=True)),('wrong-source',lambda m:m.update(commit=p.SOURCES[60]['commit']))]:
            m=json.loads(b);mutate(m);manifest.write_text(json.dumps(m))
            try:p.pack(root,t/name)
            except AssertionError:assert not (t/name).exists()
            else:raise AssertionError('accepted '+name)
            manifest.write_bytes(b)
        print('G2_R2C_PACK_SOFTWARE_GATE {"checks":6,"passed":6,"gate":true,"scope":"synthetic fixtures"}')
if __name__=='__main__':main()
