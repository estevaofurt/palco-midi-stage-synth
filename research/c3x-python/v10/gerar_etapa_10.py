"""Demonstrações V10 por síntese física; gravações anteriores não são fontes."""
from pathlib import Path
import csv, json, math, time
import numpy as np
import soundfile as sf
from stage_synth_c3x.continuous_action import schedule_continuous_action
from stage_synth_c3x.continuous_engine import render_sequence_v10_action
from stage_synth_c3x.action_engine import render_sequence_v9_action
from stage_synth_c3x.parameters import note_params
from stage_synth_c3x.engine import SR

R=Path(__file__).resolve().parent; A=R/'audios';M=R/'medicoes'
A.mkdir(exist_ok=True);M.mkdir(exist_ok=True)
MUSIC=[(.08,48,.66,75),(.48,55,.65,78),(.88,60,.58,88),
       (1.28,64,.7,97),(1.71,67,.7,103),(2.32,60,.13,82),
       (2.54,60,.11,91),(2.76,60,.10,100),(3.01,64,.8,83),
       (3.04,67,.8,92),(3.07,72,.8,108),(4.31,45,.58,66),
       (4.68,52,.56,83),(5.06,57,.55,91),(5.43,60,.67,105),
       (6.19,57,1.,85),(6.22,64,1.,90),(6.25,69,1.,98)]
LENGTH=7.65
PARTIALS=(2,3,4,5,6,7)
KEYFRAMES=[(.02,69,1.,90),(.12,69,.45,0),(.16,69,1.,99),
           (.26,69,.45,0),(.30,69,1.,105),(.40,69,0.,0)]

def write(name,x):
    x=np.asarray(x,dtype=np.float32)
    assert x.ndim==2 and x.shape[1]==2 and np.isfinite(x).all()
    pk=float(np.max(abs(x))) if len(x) else 0.
    assert pk<.99,(name,pk)
    sf.write(A/name,x,SR,subtype='PCM_16')
    info=sf.info(A/name)
    assert info.channels==2 and info.samplerate==SR and info.subtype=='PCM_16'
    print('Audio:',name, 'duração',round(len(x)/SR,2),flush=True)

def join_ab(x,y,level_match=True):
    x=np.asarray(x,dtype=np.float64);y=np.asarray(y,dtype=np.float64)
    if level_match:
        a=np.sqrt(np.mean(x*x));b=np.sqrt(np.mean(y*y))
        if a>1e-9 and b>1e-9:y*=a/b
    out=np.concatenate((x,np.zeros((round(.23*SR),2)),y),axis=0)
    peak=float(np.max(abs(out)))
    if peak>.87:out*=.87/peak
    return out.astype(np.float32)

def partials(y,midi,impact_s,fs=SR,window_s=.28):
    # Espectros com janela alinhada à colisão, em vez de tempo absoluto.
    start=round((impact_s+.04)*fs);finish=start+round(window_s*fs)
    mono=np.asarray(y[start:finish],dtype=float).mean(axis=1)
    if len(mono)<100:return {}
    nfft=2**math.ceil(math.log2(len(mono)*8))
    s=np.abs(np.fft.rfft(mono*np.hanning(len(mono)),nfft))
    freq=np.fft.rfftfreq(nfft,1/fs)
    base=440.*2**((midi-69)/12)
    b=note_params(midi).inarmonicidade_b
    def power(part):
        target=base*part*math.sqrt((1+b*part*part)/(1+b))
        cut=(freq>target*.985)&(freq<target*1.015)
        return max(float(np.max(s[cut])) if cut.any() else 0.,1e-14)
    unit=power(1)
    return {j:round(20*math.log10(power(j)/unit),3) for j in PARTIALS if base*j<fs*.45}

def main():
    started=time.monotonic()
    print('Renderizando mesma partitura na V9 / V10...',flush=True)
    a=render_sequence_v9_action(MUSIC,LENGTH)
    b,diag=render_sequence_v10_action(MUSIC,LENGTH,return_diagnostics=True)
    write('C3X_V10_DRY_acao_continua_7s.wav',b)
    write('C3X_AB_V9_vs_V10_DRY_15s.wav',join_ab(a,b))
    print('Testes de meia liberação...',flush=True)
    d,dd=render_sequence_v10_action((),1.05,keyframes=KEYFRAMES,
              action_mode='double',return_diagnostics=True)
    s,ss=render_sequence_v10_action((),1.05,keyframes=KEYFRAMES,
              action_mode='single',return_diagnostics=True)
    write('C3X_V10_meia_liberacao_dupla_repeticao.wav',d)
    write('C3X_V10_meia_liberacao_repeticao_simples.wav',s)
    write('C3X_AB_V10_dupla_vs_simples.wav',join_ab(d,s))
    print('Pedal...',flush=True)
    pedal=render_sequence_v10_action(MUSIC,LENGTH,
        pedal_events=[(1.6,1.),(3.9,.5),(4.35,0.),(5.3,1.),(6.95,0.)])
    write('C3X_V10_DRY_pedal_dinamico_7s.wav',pedal)
    print('Dinâmica e espectro...',flush=True)
    sep=np.zeros((round(.12*SR),2),np.float32)
    dynamics=[];notes=[]
    for velocity in (25,55,85,115):
        snd=render_sequence_v10_action([(.04,69,.62,velocity)],.91,normalize=False)
        dynamics.append(snd)
        notes.append({'velocity':velocity,'rms':float(np.sqrt(np.mean(snd**2))),
                      'peak':float(np.max(abs(snd)))})
    out=np.concatenate([z if i==0 else np.concatenate((sep,z))
                        for i,z in enumerate(dynamics)])
    out*=.83/max(.83,float(np.max(abs(out))))
    write('C3X_V10_A4_quatro_intensidades.wav',out)
    compare=[]
    for midi in (48,57,69,81,93):
        event=[(.04,midi,.64,90)]
        x,dx=render_sequence_v9_action(event,.86,normalize=False,return_diagnostics=True)
        y,dy=render_sequence_v10_action(event,.86,normalize=False,return_diagnostics=True)
        p9=partials(x,midi,dx['action_events'][0]['strike_at_s'])
        p10=partials(y,midi,dy['action_events'][0]['impact_s'])
        for k in sorted(p9.keys()&p10.keys()):
            compare.append({'midi':midi,'parcial':k,'v9_rel_db':p9[k],
                            'v10_rel_db':p10[k], 'delta_db':round(p10[k]-p9[k],3)})
        if midi==69:
            write('C3X_AB_V9_vs_V10_A4_isolada.wav',join_ab(x,y))
            write('C3X_V10_A4_isolada.wav',render_sequence_v10_action(event,.86))
    with (M/'comparacao_parciais_v9_v10.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(compare[0]));w.writeheader();w.writerows(compare)
    _,trace=schedule_continuous_action((),1.05,keyframes=KEYFRAMES,include_trajectories=True)
    with (M/'trajetoria_tecla_A4.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['tempo_s','profundidade_0_1','estado_martelo'])
        w.writerows(trace['key_trajectories'][69])
    summary={'v10_strikes_musical':diag['strike_count'],
             'v10_key_count':diag['unique_key_count'],
             'meia_liberacao_double_strikes':dd['strike_count'],
             'meia_liberacao_single_strikes':ss['strike_count'],
             'meia_liberacao_single_blocked':ss['blocked_count'],
             'dynamics':notes,
             'parciais':compare,
             'impactos_teste':dd['action_events'],
             'duration_work_s':round(time.monotonic()-started,2)}
    (M/'resumo_v10.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
    print('Concluido em',summary['duration_work_s'],'s',flush=True)

if __name__=='__main__':main()
