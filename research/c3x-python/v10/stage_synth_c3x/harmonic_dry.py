"""V4.2: recuperação de parciais pelo sistema mecânico, sem efeito de sala.

Martelo e cordas: motor V3, com acoplamento local mais complacente.
Tampo: função de transferência MODAL SINTÉTICA do instrumento + 11 modos
mecânicos compartilhados. Nenhum sample, IR gravada ou reverberação de sala.

O acoplamento é experimental: NÃO foi calibrado com Yamaha C3X.
"""
from dataclasses import dataclass, asdict
from functools import lru_cache
import math
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from .engine import SR, soundboard_impulse
from .feedback import FeedbackConfig, string_soundboard_feedback
from .dry import shared_soundboard

@dataclass(frozen=True)
class HarmonicDryConfig:
    bridge_stiffness_N_m:float=350.
    bridge_damping_Ns_m:float=.025
    body_window_ms:float=170.
    body_decay_ms:float=140.
    body_gain:float=.0058
    direct_gain:float=.018
    board_mix:float=.024
    sympathetic_mix:float=.075
    profile:str='equal'

    def validate(self):
        v=(self.bridge_stiffness_N_m,self.bridge_damping_Ns_m,self.body_window_ms,
           self.body_decay_ms,self.body_gain,self.direct_gain,self.board_mix,self.sympathetic_mix)
        if not all(np.isfinite(x) and x>=0 for x in v):
            raise ValueError('Parâmetro de instrumento inválido')
        if not 20<=self.body_window_ms<=250 or not 10<=self.body_decay_ms<=500:
            raise ValueError('Duração da resposta do instrumento inválida')
        if not 0<=self.bridge_stiffness_N_m<=3000 or not 0<=self.bridge_damping_Ns_m<=.2:
            raise ValueError('Parâmetro do contato corda-ponte inválido')
        if self.profile not in ('equal','stretch_experimental'):
            raise ValueError('Afinação inválida')
        return self


def harmonic_preset(name='natural'):
    presets={
        'natural':HarmonicDryConfig(),
        'aberto':HarmonicDryConfig(bridge_stiffness_N_m=250.,bridge_damping_Ns_m=.018,
              body_window_ms=225.,body_decay_ms=200.,body_gain=.0065,
              board_mix=.025,sympathetic_mix=.080),
    }
    if name not in presets:raise ValueError('Preset desconhecido')
    return presets[name]

@lru_cache(maxsize=24)
def modal_body_ir(fs:int,side:int,window_ms:float,decay_ms:float):
    """Modo físico estimado do tampo, SEM reflexões ou impulsos de salas."""
    n=round(fs*window_ms/1000)
    h=soundboard_impulse(fs,side)[:n].copy()
    h*=np.exp(-np.arange(n)/(fs*decay_ms/1000))
    fade=min(max(1,round(.007*fs)),n)
    h[-fade:]*=np.linspace(1.,0.,fade)
    return h

@lru_cache(maxsize=16)
def _calibration(fs,profile,k,c):
    f=string_soundboard_feedback(69,90,.65,.85,fs,profile,
           FeedbackConfig(bridge_stiffness_N_m=k,bridge_damping_Ns_m=c))[0]
    l,r,s=shared_soundboard(f,fs,True,(69,),profile)
    i,j=int(.04*fs),int(.75*fs)
    rms=lambda x:max(float(np.sqrt(np.mean(x[i:j]**2))),1e-12)
    return rms(f),rms((l+r)*.5),rms(s)


def render_sequence_harmonic(events,length=10.,fs=SR,config=None,pedal_down=False,
                             normalize=True,return_stems=False):
    cfg=(config or harmonic_preset()).validate()
    if fs<16000 or length<=0 or not np.isfinite(length):
        raise ValueError('Parâmetros de áudio inválidos')
    n=round(fs*length)
    sources=np.zeros((n,2),dtype=np.float64)
    total=np.zeros(n,dtype=np.float64)
    notes=set()
    coupling=FeedbackConfig(bridge_stiffness_N_m=cfg.bridge_stiffness_N_m,
                           bridge_damping_Ns_m=cfg.bridge_damping_Ns_m)
    for start,midi,hold,velocity in events:
        if not all(np.isfinite(x) for x in (start,midi,hold,velocity)) or not (0<=start and 0<=hold and 21<=midi<=108 and 1<=velocity<=127):
            raise ValueError('Evento MIDI inválido')
        if start>=length: continue
        notes.add(int(midi))
        duration=min(length-start,max(hold+.85,2.6))
        force=string_soundboard_feedback(int(midi),int(velocity),min(hold,duration),
                      duration,fs,cfg.profile,config=coupling,pedal_down=pedal_down)[0]
        i=round(start*fs);j=min(n,i+len(force));u=force[:j-i]
        total[i:j]+=u
        pan=(midi-21)/87
        sources[i:j,0]+=u*(.6+.4*(1-pan))
        sources[i:j,1]+=u*(.6+.4*pan)

    instrument=np.zeros_like(sources)
    for channel in range(2):
        pressure=fftconvolve(sources[:,channel],
                    modal_body_ir(fs,channel,cfg.body_window_ms,cfg.body_decay_ms),
                    mode='full')[:n]
        instrument[:,channel]=cfg.direct_gain*sources[:,channel]+cfg.body_gain*pressure
    left,right,sym=shared_soundboard(total,fs,pedal_down,notes,cfg.profile)
    ref_f,ref_board,ref_sym=_calibration(fs,cfg.profile,cfg.bridge_stiffness_N_m,cfg.bridge_damping_Ns_m)
    board=np.column_stack((left,right))*cfg.board_mix*cfg.direct_gain*ref_f/ref_board
    sympathetic=np.column_stack((sym,sym))*cfg.sympathetic_mix*cfg.direct_gain*ref_f/ref_sym
    # Atenuação física de componentes fora da banda de radiação pretendida;
    # não há compressor, EQ de brilho, delay nem reverb de sala.
    filt=butter(2,[30.,min(13200.,fs*.44)],fs=fs,btype='bandpass',output='sos')
    instrument=sosfilt(filt,instrument,axis=0)
    board=sosfilt(filt,board,axis=0)
    sympathetic=sosfilt(filt,sympathetic,axis=0)
    mixed=instrument+board+sympathetic
    p=np.max(np.abs(mixed)) if mixed.size else 0.
    gain=(.85/p) if normalize and p>1e-12 else 1.
    mixed=(mixed*gain).astype(np.float32)
    if return_stems:
        return mixed,{'instrumento':(instrument*gain).astype(np.float32),
                      'tampo_compartilhado':(board*gain).astype(np.float32),
                      'simpaticas':(sympathetic*gain).astype(np.float32),
                      'ganho':gain}
    return mixed
