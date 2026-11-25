"""R1 listening pack, only after all eleven acoustic renders are verified."""
import argparse, hashlib, json, random, shutil
from pathlib import Path
import numpy as np
import soundfile as sf
FS=48000
CASES=('C4-held','C4-release','triad','escala-do-maior','arpejo-do-maior','progressoes')
COMMIT='95c2419c6a52289982e142669ee8ea610a8c7d89'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def db(x):return float(20*np.log10(max(float(x),1e-15)))
def rms(x):return float(np.sqrt(np.mean(x*x)))
def read(p,n):
    y,fs=sf.read(p,always_2d=True);assert fs==FS and y.shape==(n,2) and np.isfinite(y).all() and sf.info(p).subtype=='PCM_24'
    return y
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--proof',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    proof=json.loads((a.proof/'r1_report.json').read_text());assert proof['gate'] and proof['passed']==proof['required']==6
    a.out.mkdir(parents=True,exist_ok=True)
    blind=a.out/'escuta-cega';blind.mkdir();originals=a.out/'ganho-original';originals.mkdir()
    rng=random.Random(20261125);key=[];results=[];count=0;global_gain=set()
    for case in CASES:
        modes=['dry'] if case=='C4-held' else ['release-only','dry']
        signals={};meta={};source_files={};n=round((1.5 if case in CASES[:3] else 5.)*FS)
        for mode in modes:
            folder=a.root/f'G2-R1-{case}-{mode}';m=json.loads((folder/'manifest.json').read_text())
            assert m['case']==case and m['mode']==mode and m['commit']==COMMIT and m['originalCommit']=='dbd007fdeab3def76c3ff8cb3cae47741655429b' and m['radiation']['gate']
            p=folder/f'{case}-{mode}.wav';o=folder/f'{case}-original.wav'
            assert sha(p)==m['wavSha256'] and sha(o)==m['originalSha256'] and sha(folder/'pressure.npz')==m['rawSha256']
            if 'original' in source_files:assert sha(o)==sha(source_files['original'])
            else:source_files['original']=o;signals['original']=read(o,n)
            source_files[mode]=p;signals[mode]=read(p,n);meta[mode]=m;global_gain.add(m['gain']);count+=1
        if len(modes)==2:
            x,y=[meta[v] for v in modes]
            assert all(x[k]==y[k] for k in ('events','releases','scoreSha256','gain','durationS','originalSha256'))
        m=meta['dry'];last=max(e[0] for e in m['events'])
        # Isolated notes: match pre-release attack. Musical sequences: whole active phrase window.
        start,end=(round(.02*FS),round(.08*FS)) if case in CASES[:3] else (0,round((last+.16)*FS))
        levels={k:rms(v[start:end]) for k,v in signals.items()};assert min(levels.values())>0
        target=min(min(levels.values()),min(levels[k]*10**(-6/20)/float(np.max(abs(v))) for k,v in signals.items()))
        bd=blind/case;bd.mkdir();od=originals/case;od.mkdir();order=list(signals);rng.shuffle(order);entries=[]
        for i,k in enumerate(order):
            label='ABC'[i];g=target/levels[k];assert 0<g<=1+1e-12
            p=bd/(label+'.wav');z=signals[k]*g;assert np.max(abs(z))<=10**(-6/20)+1e-12
            sf.write(p,z,FS,subtype='PCM_24');assert np.max(abs(read(p,n)-z))<=2**-23+1e-12
            dst=od/(k+'.wav');shutil.copyfile(source_files[k],dst);assert sha(dst)==sha(source_files[k])
            entries.append(dict(label=label,source=k,gain=g,sha256=sha(p)))
        key.append(dict(case=case,files=entries))
        row=dict(case=case,events=m['events'],releases=m['releases'],matchingWindowS=[start/FS,end/FS],targetRmsDbfs=db(target),
            measurements={k:dict(windows=v['windows'],gaps=v['postReleaseGaps'],peakDbfs=v['peakDbfs'],damperLossJ=v['mechanical']['damperLossJ'],damperGroupLossJ=v['mechanical']['damperGroupLossJ'],radiation=v['radiation']) for k,v in meta.items()})
        if len(modes)==2:
            # Dry vs release-only at identical gain and event schedule; no assertion of perceptual causality.
            x,y=signals['dry'],signals['release-only']
            row['dryMinusReleaseOnlyRmsDb']=db(rms(x))-db(rms(y))
            row['dryVsReleaseOnlyRelativeNorm']=float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-30))
        results.append(row);print('G2_R1_PACK '+json.dumps(row,allow_nan=False),flush=True)
    assert count==11 and len(global_gain)==1 and sum(len(x['files']) for x in key)==17
    (a.out/'gabarito.json').write_text(json.dumps(key,indent=2,allow_nan=False))
    (a.out/'relatorio.json').write_text(json.dumps(dict(sourceRun=45617749735,sourceCommit=COMMIT,originalGain=next(iter(global_gain)),rows=results,gate=True),indent=2,allow_nan=False))
    (a.out/'LEIA-ME.txt').write_text('R1: comparação G2 com G2, 6 grupos, 17 arquivos cegos. Escute primeiro escuta-cega/ sem gabarito. C4-held tem duas versões, demais três. Rótulos aleatórios por grupo. Original = cordas livres; release-only = abafamento após soltura; dry = também cordas não pressionadas amortecidas. Cópias cegas usam apenas atenuação por arquivo (RMS ataque 20–80ms nas notas/acorde e janela ativa nas frases), sem cortes, EQ, reverb ou ajuste por nota. Ganho-original/ preserva todos os arquivos. Compare ataque, corpo, separação, cauda após soltura e naturalidade. A C4 mantida de 1,5s não valida sustain longo. Sem pedal nem abafador calibrado. O Yamaha C5 anterior é contexto, não par equivalente de soltura. O relatório e gabarito identificam origens; abra só depois da escuta.',encoding='utf-8')
    print('G2_R1_PACK_GATE '+json.dumps(dict(groups=6,candidates=count,blindWavs=17,gate=True)),flush=True)
if __name__=='__main__':main()
