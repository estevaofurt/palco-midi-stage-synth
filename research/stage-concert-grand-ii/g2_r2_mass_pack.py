"""R2c fixed-gain originals and attenuation-only blind note pairs."""
import argparse,hashlib,json,random,shutil
from pathlib import Path
import numpy as np
import soundfile as sf
FS=48000
KEYS={60:'C4',64:'E4',67:'G4',72:'C5'}
SOURCES={k:dict(commit='335775e31f22c54cf425975bfa102dcd4247f67e',run=45625084768) for k in KEYS}
SOURCES[60]=dict(commit='b767cc0e15a9e406444f221891d5e615da740206',run=45626307034)
GAIN=.18491857409775692
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    y,fs=sf.read(p,always_2d=True)
    assert fs==FS and y.shape==(72000,2) and sf.info(p).subtype=='PCM_24' and np.isfinite(y).all()
    return y
def rms(y):return float(np.sqrt(np.mean(y*y)))
def db(y):return float(20*np.log10(max(y,1e-15)))
def pack(root,out):
    # Verify all inputs before writing any output.
    inputs={}
    for k,note in KEYS.items():
        d=root/f'G2-R2C-note-{k}';m=json.loads((d/'manifest.json').read_text())
        assert m['commit']==SOURCES[k]['commit'] and m['key']==k and m['gain']==GAIN and m['durationS']==1.5 and m['gate']
        assert m['screen']['screen']==(k!=67)
        rows={x['label']:x for x in m['rows']};assert len(m['rows'])==2 and set(rows)=={'dry','mass70-energy'}
        signals={};paths={}
        for label,row in rows.items():
            p=d/f'{k}-{label}.wav';raw=d/f'{k}-{label}-pressure.npz'
            assert sha(p)==row['wavSha256'] and sha(raw)==row['rawSha256'] and row['radiation']['gate']
            assert max(row['convergence'].values())<=.10
            assert row['events']==[[0.,k,1. if label=='dry' else (1/.7)**.5]]
            signals[label]=read(p);paths[label]=p
        assert abs(rows['dry']['mechanical']['injectedJ']-rows['mass70-energy']['mechanical']['injectedJ'])<=1e-12
        if k==60:
            dry=rows['dry'];assert dry['baselineParity']<=1e-9
            assert 0<=dry['baselineWavMaxAbsDelta']<=2**-23+1e-12
            assert dry['baselineOriginalSha256']==dry['wavSha256']
        inputs[k]=(m,signals,paths)
    out.mkdir(parents=True,exist_ok=True)
    blind=out/'escuta-cega';orig=out/'ganho-original';blind.mkdir();orig.mkdir()
    rng=random.Random(20261125);key=[];metrics=[]
    for k,note in KEYS.items():
        m,signals,paths=inputs[k];d=blind/note;d.mkdir();o=orig/note;o.mkdir()
        at={v:rms(y[960:3840]) for v,y in signals.items()};assert min(at.values())>0
        target=min(min(at.values()),min(at[v]*10**(-6/20)/float(np.max(abs(y))) for v,y in signals.items()))
        order=list(signals);rng.shuffle(order);pair=[]
        for i,label in enumerate(order):
            g=target/at[label];assert 0<g<=1+1e-12
            y=signals[label]*g;assert np.max(abs(y))<=10**(-6/20)+1e-12
            p=d/(('A','B')[i]+'.wav');sf.write(p,y,FS,subtype='PCM_24')
            assert np.max(abs(read(p)-y))<=2**-23+1e-12
            dst=o/(label+'.wav');shutil.copyfile(paths[label],dst);assert sha(dst)==sha(paths[label])
            pair.append(dict(label=('A','B')[i],source=label,attenuationDb=db(g),sha256=sha(p)))
        key.append(dict(note=note,pair=pair))
        metrics.append(dict(note=note,source=SOURCES[k],screen=m['screen'],attackRmsDbfs={v:db(x) for v,x in at.items()},relativeEnvelopeDeltaDb=m['relativeEnvelopeDeltaDb'],partialDeltaDb=m['partialDeltaDb']))
    assert len(list(blind.rglob('*.wav')))==len(list(orig.rglob('*.wav')))==8
    (out/'gabarito.json').write_text(json.dumps(key,indent=2,allow_nan=False))
    (out/'relatorio.json').write_text(json.dumps(dict(gate=True,sources=SOURCES,rows=metrics),indent=2,allow_nan=False))
    (out/'LEIA-ME.txt').write_text('R2c: quatro notas mantidas de 1,5s, pares A/B. Escute primeiro sem gabarito. Versões Dry e massa efetiva 70% com velocidade compensada para energia inicial equivalente. Não é calibração MIDI. Cópias cegas atenuadas exclusivamente para igualar RMS 20–80ms, margem de pico -6dBFS. Originais preservados com ganho único. Avalie ataque, definição, corpo, caráter amadeirado e ressonância; G4 é controle da falha na triagem harmônica. Não avalia sustain longo ou soltura; nenhum candidato adotado.',encoding='utf-8')
    print('G2_R2C_PACK_GATE '+json.dumps(dict(notes=4,blindWavs=8,originalWavs=8,gate=True)),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();pack(a.root,a.out)
