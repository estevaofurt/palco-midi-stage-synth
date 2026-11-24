"""Motor acústico experimental sem nenhuma amostra de áudio.

Fonte sonora: acoplamento martelo não linear -> modos de corda rígida.
Saída: força na ponte -> mobilidade modal simplificada do tampo.

A resposta do tampo e a escala são estimativas e NÃO uma reconstrução
metrologicamente calibrada de um Yamaha C3X.
"""
from functools import lru_cache
import math
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from .parameters import note_params
try:
    from numba import njit
except ImportError:
    def njit(fn): return fn  # alternativa lenta sem numba

SR=48000

@njit
def _string_impact(nframes,nstrings,nmodes,cosine,sine,decay,omega2,omega_d,
                   damping,hammer_shape,bridge_shape,mass_modal,
                   hammer_mass,hammer_vel,hammer_K,hammer_p,
                   duration_frames,fs):
    # Cada uníssono recebe o martelo e vibra na sua própria frequência.
    q=np.zeros((nstrings,nmodes),dtype=np.float64)
    v=np.zeros((nstrings,nmodes),dtype=np.float64)
    out=np.zeros(nframes,dtype=np.float64)
    contact_forces=np.zeros(nframes,dtype=np.float64)
    z=0.0
    vz=hammer_vel
    started=False
    contact_over=False
    dt=1.0/fs
    for i in range(nframes):
        total_force=0.0
        forces=np.zeros(nstrings,dtype=np.float64)
        if not contact_over:
            for s in range(nstrings):
                u=0.0
                for k in range(nmodes):
                    u += q[s,k]*hammer_shape[k]
                compression=z-u
                if compression>0.0:
                    forces[s]=hammer_K*compression**hammer_p
                    total_force+=forces[s]
            if total_force>0.0:
                started=True
            elif started:
                contact_over=True # ação escapada: só um impacto
        contact_forces[i]=total_force
        for s in range(nstrings):
            for k in range(nmodes):
                # Força aproximadamente constante por amostra; solução
                # exata do oscilador linear amortecido em cada intervalo.
                drive = hammer_shape[k]*forces[s]/mass_modal
                qs = drive/omega2[s,k]
                Q = q[s,k]-qs
                V = v[s,k]
                c=cosine[s,k]; h=sine[s,k]; a=decay[s,k]
                q[s,k] = qs+a*(Q*c+(V+damping[s,k]*Q)*h/omega_d[s,k])
                v[s,k] = a*(V*c-(omega2[s,k]*Q+damping[s,k]*V)*h/omega_d[s,k])
        # Dinâmica livre do martelo (desacopla depois de perder contato).
        vz -= dt*total_force/hammer_mass
        z += dt*vz
        bridge = 0.0
        for s in range(nstrings):
            for k in range(nmodes):
                bridge += q[s,k]*bridge_shape[k]
        # A vibração da corda vai ao tampo enquanto sustentada; após
        # a tecla liberar, abafador simplificado reduz a energia.
        if i>duration_frames:
            bridge *= math.exp(-0.035*(i-duration_frames))
        out[i]=bridge
    return out,contact_forces

def _string_force(midi:int,velocity:int=90,hold:float=1.3,total:float=3.0,fs:int=SR,return_force:bool=False):
    p=note_params(midi)
    # frequência inarmônica e perda dependente da frequência
    max_partials=min(75, int(18000/p.frequencia_hz)+1)
    n=np.arange(1,max_partials+1,dtype=np.float64)
    f0=p.frequencia_hz
    fparts=f0*n*np.sqrt((1+p.inarmonicidade_b*n*n)/(1+p.inarmonicidade_b))
    keep=fparts<min(18000.0,fs*.41)
    n=n[keep]; fparts=fparts[keep]
    nm=len(n)
    unison=p.cordas_por_nota
    detune=np.array([-0.48,0.0,0.44] if unison==3 else ([-0.3,0.3] if unison==2 else [0.0]))
    # Pequenas diferenças de afinação permitem batimentos entre cordas.
    fmult=2**(detune/1200)
    freqs=fparts[None,:]*fmult[:,None]
    omega=2*np.pi*freqs
    sigma=(.75+.008*(f0**.55)+.24*(freqs/1000)**1.2)
    wd=np.sqrt(np.maximum(omega*omega-sigma*sigma,1e-9))
    cosine=np.cos(wd/fs); sine=np.sin(wd/fs); decay=np.exp(-sigma/fs)
    pos=p.posicao_impacto_fracao
    hammer_shape=np.sin(np.pi*n*pos)
    # reação vertical aproximada no ponto de fixação da ponte
    bridge_shape=(-1.0)**(n+1) * (np.pi*n/p.comprimento_vibrante_m)*p.tensao_por_corda_n
    # baixa resposta de modos com nós de martelo, sem espectro imposto
    vmin=.45; vmax=2.6
    hvel=vmin+(min(127,max(1,velocity))/127)**1.45*(vmax-vmin)
    nframes=int(total*fs)
    signal,forces=_string_impact(nframes,unison,nm,cosine,sine,decay,
                          omega*omega,wd,sigma,hammer_shape,
                          bridge_shape,p.densidade_linear_kg_m*p.comprimento_vibrante_m/2,
                          p.massa_martelo_kg,hvel,p.rigidez_feltro_k,p.expoente_feltro_p,
                          int(hold*fs),fs)
    return (signal,forces) if return_force else signal

@lru_cache(maxsize=8)
def soundboard_impulse(fs=SR,channel=0):
    """Resposta modal sintética para placa de madeira; dados ainda não medidos."""
    n=int(.25*fs)
    t=np.arange(n)/fs
    h=np.zeros(n)
    # Múltiplos modos não-harmônicos, fixos e reprodutíveis.
    rng=np.random.default_rng(20261123)
    f_modes=np.geomspace(65,10000,100)
    f_modes=f_modes*(1+rng.uniform(-.016,.016,size=len(f_modes)))
    strengths=rng.uniform(.40,1.0,len(f_modes))
    # Duas posições no tampo: forças acopladas diferentemente em cada lado.
    if channel==0:
        strengths *= (.6+.4*np.cos(np.arange(len(f_modes))*1.32)**2)
    else:
        strengths *= (.6+.4*np.sin(np.arange(len(f_modes))*1.09)**2)
    for ix,f in enumerate(f_modes):
        loss=4.0+1.1*(f/1000)**.75
        # Velocidade/radiação relativa: grandes modos irradiam mais até
        # determinada faixa; depois perdem eficiência.
        a=strengths[ix]*(f/1000)**.24/(1+(f/5500)**1.4)
        h+=a*np.exp(-loss*t)*np.sin(2*np.pi*f*t)
    # impulsos de passagem do sinal na ponte e radiação aproximada
    h/=max(np.max(abs(h)),1e-12)
    return h

def render_note(midi:int,velocity=90,hold=1.2,total=3.0,fs=SR,stereo=True):
    bridge=_string_force(midi,velocity,hold,total,fs)
    low=float(midi-21)/87
    signals=[]
    for side in range(2 if stereo else 1):
        board=fftconvolve(bridge,soundboard_impulse(fs,side),mode="full")[:len(bridge)]
        # Decomposição na forma de uma transferência modal finita.
        x=board*.006+bridge*.018
        x=sosfilt(butter(2,[32,13500],fs=fs,btype="bandpass",output="sos"),x)
        if stereo:
            pos=.6+.4*(low if side else 1-low)
            x*=pos
        signals.append(x)
    return np.stack(signals,axis=1).astype(np.float64) if stereo else signals[0]

def render_sequence(events,length=10.0,fs=SR,stereo=True):
    """Eventos como (inicio_em_segundos, midi, duração_tecla, velocidade)."""
    mix=np.zeros((int(fs*length),2),dtype=np.float64) if stereo else np.zeros(int(fs*length),dtype=np.float64)
    for start,midi,hold,velocity in events:
        if start>=length: continue
        dur=min(length-start,max(hold+.85,2.6))
        voice=render_note(midi,velocity,hold,dur,fs,stereo)
        i=int(start*fs); j=min(i+len(voice),len(mix))
        mix[i:j]+=voice[:j-i]
    # Único ganho global: preserva dinâmica relativa entre as notas.
    peak=np.max(abs(mix))
    if peak>1e-10:
        mix*=.87/peak
    return mix.astype(np.float32)
