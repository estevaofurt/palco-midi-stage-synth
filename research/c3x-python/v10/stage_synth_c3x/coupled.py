"""STAGE SYNTH C3X — Etapa 2 experimental; não altera engine.py da V1.

Aproximação passiva da ponte comum dos uníssonos, por parcial:
 q_s'' + 2 sigma_s q_s' + omega_s² q_s = F_s/m
                   - k_ponte <q> - 2 gamma_ponte <q'>

Não utiliza samples, IRs gravadas, nem parâmetros medidos no C3X.
"""
from dataclasses import dataclass
import math
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from .parameters import note_params
from .engine import SR, soundboard_impulse
try:
    from numba import njit
except ImportError:
    def njit(fn): return fn

@dataclass(frozen=True)
class CouplingConfig:
    gamma_rad_1khz: float = 0.45          # s^-1; perda no movimento comum
    stiffness_fraction: float = 0.00010 # k / omega², ponte reduzida
    damper_loss_per_s: float = 85.0     # s^-1; contato do abafador
    damper_touch_s: float = 0.014       # segundos de entrada do feltro

@njit
def _impact_coupled(nframes,nstrings,nmodes,cosine,sine,decay,omega2,
                    omega_d,damping,hammer_shape,bridge_shape,mass_modal,
                    hammer_mass,hammer_vel,hammer_K,hammer_p,hold_frames,
                    fs,gamma_rad,k_rel,damper_loss,damper_touch_frames,pedal):
    q=np.zeros((nstrings,nmodes),dtype=np.float64)
    v=np.zeros((nstrings,nmodes),dtype=np.float64)
    out=np.zeros(nframes,dtype=np.float64)
    forces_trace=np.zeros(nframes,dtype=np.float64)
    mean_q=np.zeros(nmodes,dtype=np.float64)
    mean_v=np.zeros(nmodes,dtype=np.float64)
    forces=np.zeros(nstrings,dtype=np.float64)
    z=0.0; vz=hammer_vel
    touched=False; escaped=False
    dt=1.0/fs
    for i in range(nframes):
        total_force=0.0
        if not escaped:
            for s in range(nstrings):
                displacement=0.0
                for k in range(nmodes):
                    displacement+=q[s,k]*hammer_shape[k]
                delta=z-displacement
                if delta>0:
                    forces[s]=hammer_K*delta**hammer_p
                    total_force+=forces[s]
                else:
                    forces[s]=0.0
            if total_force>0:
                touched=True
            elif touched:
                escaped=True
        else:
            for s in range(nstrings):
                forces[s]=0.0
        forces_trace[i]=total_force
        if nstrings>1:
            for k in range(nmodes):
                a=0.0; b=0.0
                for s in range(nstrings):
                    a+=q[s,k]; b+=v[s,k]
                mean_q[k]=a/nstrings
                mean_v[k]=b/nstrings
        # Abafador dissipa energia NA corda, não no sinal pós-síntese.
        factor=1.0
        if not pedal and i>=hold_frames:
            ramp=(i-hold_frames+1)/max(1,damper_touch_frames)
            if ramp>1: ramp=1.0
            factor=math.exp(-damper_loss*ramp*dt)
        for s in range(nstrings):
            for k in range(nmodes):
                drive=hammer_shape[k]*forces[s]/mass_modal
                if nstrings>1:
                    drive-=k_rel*omega2[0,k]*mean_q[k]
                    drive-=2.0*gamma_rad[k]*mean_v[k]
                eq=drive/omega2[s,k]
                Q=q[s,k]-eq
                V=v[s,k]
                c=cosine[s,k]; h=sine[s,k]; a=decay[s,k]
                q[s,k]=(eq+a*(Q*c+(V+damping[s,k]*Q)*h/omega_d[s,k]))*factor
                v[s,k]=(a*(V*c-(omega2[s,k]*Q+damping[s,k]*V)*h/omega_d[s,k]))*factor
        vz-=dt*total_force/hammer_mass
        z+=dt*vz
        bridge=0.0
        for s in range(nstrings):
            for k in range(nmodes):
                bridge+=q[s,k]*bridge_shape[k]
        out[i]=bridge
    return out,forces_trace

def string_bridge_coupled(midi:int,velocity:int=90,hold:float=1.3,
                          total:float=3.0,fs:int=SR, config=None,
                          pedal_down:bool=False, return_force=False):
    """Força calculada na ponte, sem nenhuma leitura de arquivos de áudio."""
    config=CouplingConfig() if config is None else config
    values=(config.gamma_rad_1khz,config.stiffness_fraction,
            config.damper_loss_per_s,config.damper_touch_s)
    if not all(math.isfinite(x) and x>=0 for x in values):
        raise ValueError('Parâmetros mecânicos devem ser finitos e >= 0')
    if not 0<=hold<=total or total<=0 or fs<8000:
        raise ValueError('Duração, sustentação ou amostragem inválida')
    p=note_params(midi)
    n=np.arange(1,min(75,int(18000/p.frequencia_hz)+1)+1,dtype=np.float64)
    f0=p.frequencia_hz
    fparts=f0*n*np.sqrt((1+p.inarmonicidade_b*n*n)/(1+p.inarmonicidade_b))
    keep=fparts<min(18000.,fs*.41)
    n=n[keep]; fparts=fparts[keep]
    if len(n)==0:
        raise ValueError('Nenhuma parcial audível')
    unison=p.cordas_por_nota
    detune=np.array([-0.48,0.,0.44] if unison==3 else
                    ([-0.3,0.3] if unison==2 else [0.]))
    freqs=fparts[None,:]*(2**(detune[:,None]/1200))
    omega=2*np.pi*freqs
    sigma=(.75+.008*(f0**.55)+.24*(freqs/1000)**1.2)
    wd=np.sqrt(np.maximum(omega*omega-sigma*sigma,1e-9))
    cosine=np.cos(wd/fs); sine=np.sin(wd/fs); decay=np.exp(-sigma/fs)
    hammer_shape=np.sin(np.pi*n*p.posicao_impacto_fracao)
    bridge_shape=(-1.)**(n+1)*(np.pi*n/p.comprimento_vibrante_m)*p.tensao_por_corda_n
    hvel=.45+(min(127,max(1,velocity))/127)**1.45*(2.6-.45)
    gamma=config.gamma_rad_1khz*(.65+.35*(fparts/1000)**.35)
    out,force=_impact_coupled(int(total*fs),unison,len(n),cosine,sine,decay,
                              omega*omega,wd,sigma,hammer_shape,
                              bridge_shape,p.densidade_linear_kg_m*p.comprimento_vibrante_m/2,
                              p.massa_martelo_kg,hvel,p.rigidez_feltro_k,
                              p.expoente_feltro_p,int(hold*fs),fs,
                              gamma,config.stiffness_fraction,
                              config.damper_loss_per_s,int(config.damper_touch_s*fs),pedal_down)
    return (out,force) if return_force else out


def render_note_coupled(midi:int,velocity:int=90,hold:float=1.2,
                        total:float=3.0,fs:int=SR,stereo=True,
                        config=None,pedal_down=False):
    bridge=string_bridge_coupled(midi,velocity,hold,total,fs,config,pedal_down)
    low=(midi-21)/87.
    signals=[]
    for side in range(2 if stereo else 1):
        board=fftconvolve(bridge,soundboard_impulse(fs,side),mode='full')[:len(bridge)]
        # Mesmo transdutor modal da V1: comparação preserva seu caráter.
        x=board*.006+bridge*.018
        x=sosfilt(butter(2,[32,13500],fs=fs,btype='bandpass',output='sos'),x)
        if stereo:
            pos=.6+.4*(low if side else 1-low)
            x*=pos
        signals.append(x)
    return np.stack(signals,axis=1).astype(np.float64) if stereo else signals[0]


def render_sequence_coupled(events,length=10.,fs=SR,stereo=True,
                            config=None,pedal_down=False,peak_normalize=True):
    """Eventos (segundos_início, MIDI, duração_tecla, velocidade)."""
    mix=np.zeros((int(fs*length),2) if stereo else int(fs*length),dtype=np.float64)
    for start,midi,hold,velocity in events:
        if start>=length: continue
        dur=min(length-start,max(hold+.85,2.6))
        voice=render_note_coupled(midi,velocity,hold,dur,fs,stereo,config,pedal_down)
        i=int(start*fs); j=min(i+len(voice),len(mix))
        mix[i:j]+=voice[:j-i]
    peak=np.max(abs(mix))
    if peak_normalize and peak>1e-10:
        mix*=.87/peak
    return mix.astype(np.float32)