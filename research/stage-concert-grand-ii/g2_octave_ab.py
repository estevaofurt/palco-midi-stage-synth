"""G2.11d: level-matched listening copies, original G2 and C5 retained."""
import argparse,hashlib,json,random,shutil
from pathlib import Path
import numpy as np
import soundfile as sf
FS=48000
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--g2',type=Path,required=True);p.add_argument('--ref',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);blind=a.out/'escuta_cega';blind.mkdir();orig=a.out/'originais';orig.mkdir()
    ref=json.loads((a.ref/'reference_manifest.json').read_text());rng=random.Random(20261125);key=[]
    for s in ('escala-do-maior','arpejo-do-maior','progressoes'):
        d=a.g2/('G2-11-music-'+s);m=json.loads((d/'manifest.json').read_text());assert m['scoreSha256']==ref['scoreSha256'] and m['mode']=='music'
        files={'G2':d/(s+'-G2.wav'),'Yamaha-C5':a.ref/(s+'-Yamaha-C5.wav')}
        assert sha(files['G2'])==m['wavSha256'] and sha(files['Yamaha-C5'])==next(r['sha256'] for r in ref['rows'] if r['id']==s)
        sig={}
        for name,f in files.items():
            shutil.copyfile(f,orig/f.name);y,fs=sf.read(f,always_2d=True);assert fs==FS and y.shape==(240000,2) and np.isfinite(y).all();sig[name]=y
        # Whole common active phrase window, not note-by-note matching; attenuation only.
        end=round((max(e[0] for e in m['events'])+.16)*FS)
        rms={k:float(np.sqrt(np.mean(y[:end]**2))) for k,y in sig.items()}
        target=min(min(rms.values()),min(rms[k]*10**(-6/20)/np.max(abs(y)) for k,y in sig.items()))
        assert target>0
        folder=blind/s;folder.mkdir();order=list(sig);rng.shuffle(order);rows=[]
        for i,k in enumerate(order):
            g=target/rms[k];x=sig[k]*g;label='AB'[i];f=folder/(label+'.wav')
            assert 0<g<=1+1e-12 and np.max(abs(x))<=10**(-6/20)+1e-12
            sf.write(f,x,FS,subtype='PCM_24');q,fs=sf.read(f,always_2d=True);assert fs==FS and np.max(abs(q-x))<=2**-23+1e-12
            rows.append(dict(label=label,source=k,gain=g,sha256=sha(f)))
        key.append(dict(score=s,files=rows))
    (a.out/'gabarito.json').write_text(json.dumps(key,indent=2))
    (a.out/'LEIA-ME.txt').write_text('A/B exploratório G2.11. Escute primeiro os pares cegos A/B, sem olhar o gabarito. Os originais preservam ganho de cada fonte; as cópias cegas usam uma atenuação por frase inteira, nunca por nota. Sem efeitos ou normalização de caudas. G2 é síntese física contínua; Yamaha é montagem de samples independentes, alguns transpostos. Sem abafadores/pedal na G2, sem dinâmica equivalente. Referência Salamander Grand Piano v3, Alexander Holm, Yamaha C5, CC BY 3.0 https://creativecommons.org/licenses/by/3.0/ fonte https://github.com/sfzinstruments/SalamanderGrandPiano/tree/3382bf9496bba2486f5ab0de55a264d1dfc38404 ; alterações: recorte onset, resampling, soma e atenuação. Comparar naturalidade, corpo, clareza, equilíbrio, ressonância e decaimento; não é homologação nem prova de ressonância simpática real.',encoding='utf-8')
    print('G2_11_AB_GATE '+json.dumps(dict(pairs=3,blindWavs=6,gate=True)))
if __name__=='__main__':main()
