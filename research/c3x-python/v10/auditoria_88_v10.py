"""88 pitch checks from actually rendered V10, not just the theoretical target table.

A fundamental can be weak at low notes due to 30 Hz high-pass and inharmonicity;
flag unreliable spectral peaks instead of claiming exact pitch.
"""
from pathlib import Path
import csv, math, json, time
import numpy as np
import soundfile as sf
from stage_synth_c3x.continuous_engine import render_sequence_v10_action
from stage_synth_c3x.tuning import tune_note
from stage_synth_c3x.engine import SR

ROOT=Path(__file__).resolve().parent
MED=ROOT/'medicoes'; AUD=ROOT/'audios'; MED.mkdir(exist_ok=True); AUD.mkdir(exist_ok=True)

def analyze_pitch(x,midi,start,end):
    z=np.asarray(x,dtype=np.float64).mean(axis=1)
    z=z[int(start*SR):int(end*SR)]
    z=z-np.mean(z)
    win=np.hanning(len(z));z=z*win
    nfft=1<<20 if midi<37 else 1<<19
    freqs=np.fft.rfftfreq(nfft,1/SR)
    spec=np.abs(np.fft.rfft(z,nfft))
    f=tune_note(midi,'equal').target_hz
    indices=np.flatnonzero((freqs>f*.972)&(freqs<f*1.028))
    if not len(indices):return np.nan,np.nan,False,0.
    pk=indices[np.argmax(spec[indices])]
    # Parabolic interpolation of log spectrum helps beyond FFT bin resolution.
    offset=0.
    if pk>0 and pk<len(spec)-1:
        a,b,c=np.log(np.maximum(spec[pk-1:pk+2],1e-30))
        denominator=a-2*b+c
        if abs(denominator)>1e-15:
            offset=np.clip(.5*(a-c)/denominator,-.5,.5)
    measured=float((pk+offset)*SR/nfft)
    cents=float(1200*math.log2(measured/f))
    # local signal/noise proxy: no claims about perceptual audibility.
    neigh=np.flatnonzero((freqs>f*.88)&(freqs<f*1.12))
    floor=float(np.median(spec[neigh])) if len(neigh) else 0
    snr=float(20*np.log10(max(spec[pk],1e-25)/max(floor,1e-25)))
    reliable=bool(snr>7. and abs(cents)<45.)
    return measured,cents,reliable,snr

rows=[]
t0=time.perf_counter()
for midi in range(21,109):
    if midi<=36:
        length=1.6;hold=1.5;lo=.18;hi=1.35
    elif midi<=79:
        length=.85;hold=.78;lo=.12;hi=.70
    else:
        # Agudos: evita que um modo transitorio da ponte supere a fundamental
        # no início da nota (caso E6). A inspeção precoce é relatada à parte.
        length=.65;hold=.59;lo=.24;hi=.58
    vel=94
    x=render_sequence_v10_action([(0.,midi,hold,vel)],length,normalize=False)
    est,cents,reliable,snr=analyze_pitch(x,midi,lo,hi)
    target=tune_note(midi,'equal').target_hz
    name=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][midi%12]+str(midi//12-1)
    rows.append(dict(midi=midi,nota=name,frequencia_alvo_hz=round(target,6),
                     frequencia_espectral_hz=round(est,6) if np.isfinite(est) else '',
                     desvio_cents=round(cents,3) if np.isfinite(cents) else '',
                     proxy_snr_db=round(snr,2),detector_confiavel=reliable,
                     duracao_analisada_s=round(hi-lo,2),origem='WAV sintese V10; pedal solto'))
    if midi in (21,48,57,69,81,108):
        x2=render_sequence_v10_action([(0.,midi,hold,vel)],length,normalize=True)
        sf.write(AUD/('C3X_V10_nota_'+name.replace('#','s')+'.wav'),x2,SR,subtype='PCM_16')
    if (midi-20)%11==0:
        print(f'Auditoria {midi-20}/88 | {name}: {cents:.2f} cents | tempo={time.perf_counter()-t0:.1f}s',flush=True)
with (MED/'auditoria_afinacao_V10_88_notas.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter=';');w.writeheader();w.writerows(rows)
valid=[r for r in rows if r['detector_confiavel']]
errors=np.array([r['desvio_cents'] for r in valid],dtype=float)
stat={'notas_total':88,'avaliadas_confiaveis':len(valid),'inconclusivas':88-len(valid),
      'mediana_desvio_abs_cents':float(np.median(abs(errors))) if len(errors) else None,
      'p95_desvio_abs_cents':float(np.percentile(abs(errors),95)) if len(errors) else None,
      'maior_desvio_abs_cents':float(np.max(abs(errors))) if len(errors) else None,
      'notas_inconclusivas':[r['nota'] for r in rows if not r['detector_confiavel']],
      'notas_desvio_acima_5c':[dict(nota=r['nota'],cents=r['desvio_cents']) for r in valid if abs(r['desvio_cents'])>5],
      'tempo_total_s':round(time.perf_counter()-t0,2),
      'limites':'Pico da fundamental estimado em janela FFT, não um analisador de afinação perceptual e não medição do C3X físico.'}
(MED/'resumo_auditoria_88_v10.json').write_text(json.dumps(stat,indent=2,ensure_ascii=False),encoding='utf-8')
print('RESUMO',stat,flush=True)
