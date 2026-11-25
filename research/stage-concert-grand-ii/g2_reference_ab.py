"""G2.10d: development-reference A/B, no samples used in synthesis."""
import argparse, hashlib, json, math, urllib.request, shutil, random
from pathlib import Path
import numpy as np
import soundfile as sf
from g2_c5_analysis import measure,onset_details
BASE='226364d5c1808a9bd3ee70d0dab68c0dd51e254a'
CAND='93d4d046eddf4e490a6ce4f7a2a845e8e1d6f706'
FS=48000
LAYERS=((1,.5),(8,1.),(16,2.))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False))
def db(x):return 20*math.log10(x) if x>0 else None
def read(p):
    y,fs=sf.read(p,always_2d=True,dtype='float64')
    assert fs==FS and y.shape[1]==2 and np.isfinite(y).all()
    return y
def rms(y):return float(np.sqrt(np.mean(y*y)))
def attack(y,start):return rms(y[start+960:start+3840])
def reference(item,manifest,folder):
    url=f"https://raw.githubusercontent.com/sfzinstruments/SalamanderGrandPiano/{manifest['commit']}/{item['path']}"
    req=urllib.request.Request(url,headers={'User-Agent':'StageSynth-G2-development-AB'})
    with urllib.request.urlopen(req,timeout=60) as res:b=res.read(item['bytes']+1)
    assert len(b)==item['bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==item['git_blob_sha1']
    p=folder/Path(item['path']).name;p.write_bytes(b)
    return p,url
def metrics(y,midi):
    m=measure(y,FS,midi);w=m['windows'];a=w['0.02-0.08']['rms_dbfs']
    return dict(onset=m['onset_diagnostics'],peakDbfs=m['peak_dbfs'],
        belowPct=w['0.02-0.08'].get('below_0_7_f0_pct'),
        relativeDecayDb={k:v['rms_dbfs']-a for k,v in w.items()},
        partialsDb=w.get('0.25-0.75',{}).get('partial_band_relative_db'),
        absolutePartialsDbfs=w.get('0.25-0.75',{}).get('partial_band_power_dbfs'))
def compare(a,b):
    ar=a['partialsDb'];br=b['partialsDb'];ab=b['absolutePartialsDbfs'];diff=[];missing=[]
    if ar is not None and br is not None:
        for i in range(1,min(len(ar),len(br))):
            if ar[i]>-40:
                # Numerical/reporting floor, not a measured acoustic SNR.
                if ab[0]<-100 or ab[i]<-100:missing.append(i+1)
                else:diff.append(abs(ar[i]-br[i]))
    return dict(medianPartialDistanceDb=float(np.median(diff)) if diff else None,
        eligibleCompared=len(diff),belowReportingFloor=missing,
        decayDifferenceDb={k:b['relativeDecayDb'][k]-a['relativeDecayDb'][k] for k in ('.25-.75','0.25-0.75','0.8-1.3','2.5-3') if k in a['relativeDecayDb'] and k in b['relativeDecayDb']},
        limitation='partial bands approximate, -100dBFS reporting floor not SNR; reference and G2 capture and velocity not equivalent')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline',type=Path,required=True);ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    out=a.out;out.mkdir(parents=True,exist_ok=True)
    raw=out/'originals';raw.mkdir();blind=out/'escuta_cega';blind.mkdir();refdir=raw/'referencias';refdir.mkdir()
    m=json.loads((a.baseline/'pilot_manifest.json').read_text())
    assert m['commit']==BASE and m['gate'] and len(m['rows'])==14
    originals={r['id']:r for r in m['rows']}
    c5=json.loads(Path(__file__).with_name('c5_reference_manifest.json').read_text())
    lookup={r['path']:r for r in c5['files']}
    rows=[];key=[];rng=random.Random(20261125)
    for note,midi in [('C3',48),('C4',60),('C6',84)]:
        for layer,speed in LAYERS:
            item=lookup[f'Samples/{note}v{layer}.flac'];rp,url=reference(item,c5,refdir);ref=read(rp)
            ident=f'{note}-{speed:g}ms';p=a.baseline/(ident+'.wav')
            assert sha(p)==originals[ident]['wavSha256'];sources={'G2-original':p}
            if note=='C6':
                old=f'C6-light-{speed:g}ms';p=a.baseline/(old+'.wav');assert sha(p)==originals[old]['wavSha256'];sources['G2-3g-K1']=p
                folder=a.candidate/f'G2-C6-candidate-{speed:g}ms'
                cm=json.loads((folder/'comparison.json').read_text())
                p=folder/f'C6-3g-K3-{speed:g}ms.wav'
                assert cm['commit']==CAND and cm['baselineCommit']==BASE and cm['gain']==m['gain']['gain'] and cm['audit']['gate'] and cm['wavSha256']==sha(p)
                sources['G2-3g-K3']=p
            signals={'Yamaha-C5':ref}
            for name,p in sources.items():
                dst=raw/f'{ident}-{name}.wav';shutil.copyfile(p,dst);assert sha(dst)==sha(p)
                signals[name]=read(p)
            starts={k:onset_details(y,FS)['sample'] for k,y in signals.items()}
            rmses={k:attack(y,starts[k]) for k,y in signals.items()}
            assert all(v>0 and math.isfinite(v) for v in rmses.values())
            # One common target per group: attenuation only and at least 6dB peak headroom.
            target=min(min(rmses.values()),min(rmses[k]*10**(-6/20)/float(np.max(abs(y))) for k,y in signals.items()))
            length=min(5*FS,min(len(y)-starts[k] for k,y in signals.items()))
            assert length>=FS
            group=f'{note}-nivel{layer:02d}'
            folder=blind/group;folder.mkdir()
            order=list(signals);rng.shuffle(order);files=[]
            for i,k in enumerate(order):
                label=chr(65+i);gain=target/rmses[k];assert 0<gain<=1+1e-12
                # Crop at operational onset; no fade, EQ, compression, resynthesis or tail padding.
                z=signals[k][starts[k]:starts[k]+length]*gain
                assert np.max(abs(z))<=10**(-6/20)+1e-12
                p=folder/(label+'.wav');sf.write(p,z,FS,subtype='PCM_24')
                q=read(p);assert q.shape==z.shape and np.max(abs(q-z))<=2**-23+1e-12
                files.append(dict(label=label,source=k,gain=gain,gainDb=db(gain),sha256=sha(p)))
            key.append(dict(group=group,files=files))
            refmet=metrics(ref,midi)
            row=dict(group=group,note=note,midi=midi,layer=layer,speedMps=speed,
                refUrl=url,refSha256=sha(rp),refBlobSha1=item['git_blob_sha1'],
                durationOriginalS={k:len(y)/FS for k,y in signals.items()},blindDurationS=length/FS,
                targetAttackRmsDbfs=db(target),referenceMetrics=refmet,comparisons={})
            for k,y in signals.items():
                if k!='Yamaha-C5':
                    met=metrics(y,midi);row['comparisons'][k]=dict(metrics=met,**compare(refmet,met))
            rows.append(row)
            print('G2_10D_AB '+json.dumps(dict(group=group,reference=refmet,comparisons=row['comparisons'],blindDurationS=length/FS),allow_nan=False),flush=True)
    assert len(rows)==9 and sum(len(z['files']) for z in key)==24
    dump(out/'resultado_numerico.json',dict(baselineCommit=BASE,candidateCommit=CAND,referenceCommit=c5['commit'],rows=rows,limitations=['development corpus, not holdout','layers paired nominally, not equivalent hammer velocities','different microphones/capture, no absolute SPL comparisons','blind copies level matched per group; do not judge dynamic range from these','onset aligned and cropped to common available length; do not infer sustain from crop','no dampers/pedal, no claim of identified resonance source']))
    dump(out/'gabarito.json',key)
    (out/'LEIA-ME.txt').write_text("""Teste de desenvolvimento G2.10d. Ouça primeiro escuta_cega/ sem consultar gabarito.json. Cada pasta tem mesma nota e nível nominal; A/B ou A/B/C/D são rótulos aleatórios, não identidade fixa. Compare presença, corpo, naturalidade, brilho, ressonância e decaimento. Use mesmo dispositivo e volume. Cópias alinhadas ao onset, recortadas ao menor trecho disponível e niveladas por RMS 20–80ms exclusivamente por atenuação, não representam dinâmica absoluta. originals/ preserva os WAVs G2 em ganho original e os FLACs de referência intactos. Não confundir camada 1/8/16 com velocidade física .5/1/2m/s. Referência: Salamander Grand Piano v3, Alexander Holm, Yamaha C5, CC BY 3.0 https://creativecommons.org/licenses/by/3.0/ ; fonte https://github.com/sfzinstruments/SalamanderGrandPiano/tree/3382bf9496bba2486f5ab0de55a264d1dfc38404 . Cópias alteradas somente por recorte/alinhamento, atenuação e conversão PCM24. Áudio externo para comparação, nunca incorporado ao motor. Não representa homologação, holdout ou teste de frase. """,encoding='utf-8')
    print('G2_10D_GATE '+json.dumps(dict(groups=9,blindWavs=24,gate=True)),flush=True)
if __name__=='__main__':main()
