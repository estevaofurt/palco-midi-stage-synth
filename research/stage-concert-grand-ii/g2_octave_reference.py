"""G2.11 reference side only: build declared musical events from licensed samples."""
import argparse, hashlib, json, math, urllib.request, urllib.parse, tempfile
from fractions import Fraction
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from g2_c5_analysis import onset_details
HERE=Path(__file__).parent
FS=48000
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((HERE/'g2_octave_score.json').read_text())
    holdout=json.loads((HERE/'holdout_g2.json').read_text())['c5']
    assert manifest['referenceCommit']==holdout['commit']
    assert not ({p['path'] for p in manifest['files']} & {p['path'] for p in holdout['files']})
    assert {p['key'] for p in manifest['files']}=={60,63,66,69,72}
    assert [len(s['events']) for s in manifest['scores']]==[15,10,15]
    assert all(60<=k<=72 and v==1 and 0<=t<s['durationS'] for s in manifest['scores'] for t,k,v in s['events'])
    sources={};meta={}
    with tempfile.TemporaryDirectory() as tmp:
        for f in manifest['files']:
            url=f"https://raw.githubusercontent.com/sfzinstruments/SalamanderGrandPiano/{manifest['referenceCommit']}/"+urllib.parse.quote(f['path'],safe='/')
            req=urllib.request.Request(url,headers={'User-Agent':'StageSynth-G2-development-reference'})
            with urllib.request.urlopen(req,timeout=60) as res:b=res.read(f['bytes']+1)
            assert len(b)==f['bytes'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==f['git_blob_sha1']
            p=Path(tmp)/Path(f['path']).name;p.write_bytes(b)
            y,fs=sf.read(p,always_2d=True,dtype='float64')
            assert fs==FS and y.shape[1]==2 and np.isfinite(y).all()
            onset=onset_details(y,FS)
            sources[f['key']]=y[onset['sample']:]
            meta[f['key']]=dict(**f,sha256=sha(p),onset=onset)
    rendered={};mappings={}
    for s in manifest['scores']:
        z=np.zeros((round(s['durationS']*FS),2))
        for t,k,v in s['events']:
            if k not in mappings:
                source=min(sources,key=lambda j:(abs(j-k),j))
                ratio=Fraction(2**((source-k)/12)).limit_denominator(4096)
                y=sources[source] if source==k else resample_poly(sources[source],ratio.numerator,ratio.denominator,axis=0,window=('kaiser',5.),padtype='constant')
                mappings[k]=dict(sourceKey=source,semitones=k-source,ratio=[ratio.numerator,ratio.denominator],sample=y)
            y=mappings[k]['sample'];i=round(t*FS);n=min(len(y),len(z)-i);z[i:i+n]+=y[:n]
        assert np.isfinite(z).all() and np.max(abs(z))>0
        rendered[s['id']]=z
    maximum=max(float(np.max(abs(z))) for z in rendered.values())
    gain=min(1.,10**(-6/20)/maximum)
    rows=[]
    for name,z in rendered.items():
        x=z*gain;p=a.out/(name+'-Yamaha-C5.wav');sf.write(p,x,FS,subtype='PCM_24')
        q,fs=sf.read(p,always_2d=True);assert fs==FS and q.shape==x.shape and np.max(abs(q-x))<=2**-23+1e-12
        rows.append(dict(id=name,sha256=sha(p),samples=len(q),peakDbfs=float(20*np.log10(np.max(abs(q))))))
    for v in mappings.values():v.pop('sample')
    report=dict(scoreSha256=sha(HERE/'g2_octave_score.json'),sourceCommit=manifest['referenceCommit'],referenceGain=gain,sourceFiles=meta,mappings=mappings,rows=rows,limitations=['reference only; not G2 synthesis','nearest recorded notes pitch-shifted by resampling, changes attack and decay duration','independent recordings summed without sympathetic interaction, no release samples or pedals','layer 8 is not measured hammer velocity','one common reference attenuation, not physical SPL'])
    (a.out/'reference_manifest.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    (a.out/'LEIA-ME.txt').write_text('Referência experimental apenas. Salamander Grand Piano v3, Alexander Holm, Yamaha C5, CC BY 3.0 https://creativecommons.org/licenses/by/3.0/ ; fonte https://github.com/sfzinstruments/SalamanderGrandPiano/tree/3382bf9496bba2486f5ab0de55a264d1dfc38404 . Alterações: recorte pelo onset, transposição por resampling, soma de eventos e atenuação global. Não é gravação de uma execução real nem contém G2. Não usar para avaliar dinâmica absoluta ou ressonância simpática.',encoding='utf-8')
    print('G2_11_REFERENCE '+json.dumps(dict(rows=rows,referenceGain=gain,keys=sorted(mappings),gate=len(rows)==3)),flush=True)
if __name__=='__main__':main()
