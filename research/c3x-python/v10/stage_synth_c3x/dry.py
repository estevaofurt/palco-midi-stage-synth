"""STAGE SYNTH C3X V4 — saída instrumental dry (sem ambiência de sala).

Três domínios independentes:
  1. Excitação: martelo, cordas, ponte local, calculados pela V3.
  2. Corpo: resposta de campo próximo de curtíssima duração e tampo
     MODAL COMPARTILHADO por todas as notas; sem ecos de sala.
  3. Sala: NÃO implementada no renderizador do instrumento; eventual
     reverberação deve ser aplicada pelo usuário DEPOIS da saída dry.

Os modelos são estimativas; não constituem medição do Yamaha C3X.
O banco simpático recebe energia do tampo comum e a devolve a ele;
as cordas atacadas ainda usam a solução local V3 pré-renderizada.
"""
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence
import math
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from .feedback import (string_soundboard_feedback, BOARD_FREQ_HZ,
                       BOARD_MASS_KG, BOARD_DAMPING_S, BOARD_BRIDGE_SHAPE,
                       BOARD_RAD_LEFT, BOARD_RAD_RIGHT)
from .engine import soundboard_impulse, SR
from .tuning import tune_note
from .parameters import note_params
try:
    from numba import njit
except ImportError:
    def njit(fn): return fn

@dataclass(frozen=True)
class DryConfig:
    # Curta resposta estrutural para coloração do corpo; NÃO sala.
    body_window_ms:float=20.0
    body_decay_ms:float=18.0
    body_gain:float=0.00042
    body_highpass_hz:float=0.0  # apenas no ramo radiado do tampo; 0 desliga
    direct_gain:float=0.018
    board_mix:float=0.038
    sympathetic_mix:float=0.10
    # acoplamento modal estimado para cordas livres
    coupling_scale:float=1.0
    damper_loss_per_s:float=100.0
    # volumes relativos são calibrados a uma única excitação sintética A4,
    # não re-normalizados a cada música ou a cada pedal.
    profile:str='equal'

    def validate(self):
        vals=(self.body_window_ms,self.body_decay_ms,self.body_gain,self.body_highpass_hz,self.direct_gain,
              self.board_mix,self.sympathetic_mix,self.coupling_scale,self.damper_loss_per_s)
        if not all(np.isfinite(v) and v>=0 for v in vals):
            raise ValueError('Configuração dry inválida: valor negativo ou não finito')
        if not (1<=self.body_window_ms<=100 and self.body_decay_ms>0):
            raise ValueError('A janela do tampo deve estar entre 1 e 100 ms')
        if self.body_highpass_hz >= 3000:
            raise ValueError('Corte de frequência do corpo inválido')
        if self.profile not in ('equal','stretch_experimental'):
            raise ValueError('Perfil de afinação não reconhecido')
        return self

@lru_cache(maxsize=16)
def short_body_ir(fs:int=SR,side:int=0,window_ms:float=20.,decay_ms:float=18.):
    n=max(1,int(round(fs*window_ms/1000)))
    ir=soundboard_impulse(fs,side)[:n].copy()
    ir*=np.exp(-np.arange(n)/(fs*decay_ms/1000))
    # Janela suave evita truncamento com clique.
    taper=min(n, max(5,int(fs*.002)))
    ir[-taper:]*=np.linspace(1,0,taper)
    return ir

@njit
def _shared_core(force, pedal, played_mask, freq, masses, phi_note, k_contact,
                 c_contact, sigma_note, omega_note, damper_loss, board_omega, board_masses,
                 board_sigma, b_shape, b_left, b_right, fs):
    """Osciladores lineares acoplados por forças iguais e opostas.

    'force' é força de ponte (não áudio reverberado); pedal é vetor bool.
    Retorna velocidades do tampo (L,R) e das cordas simpáticas. As
    oscilações simpáticas são atenuadas quando os abafadores encostam.
    """
    nframes=len(force);ns=len(freq);nb=len(board_omega)
    q=np.zeros(ns);v=np.zeros(ns)
    b=np.zeros(nb);bv=np.zeros(nb)
    out_l=np.zeros(nframes);out_r=np.zeros(nframes)
    out_sym=np.zeros(nframes)
    dt=1.0/fs
    # Propagadores analíticos dos osciladores com força constante por amostra.
    bc=np.empty(nb);bs=np.empty(nb);bd=np.empty(nb);bwd=np.empty(nb)
    for j in range(nb):
        w=board_omega[j];d=board_sigma[j]
        bwd[j]=math.sqrt(max(w*w-d*d,1e-12))
        bc[j]=math.cos(bwd[j]*dt);bs[j]=math.sin(bwd[j]*dt)
        bd[j]=math.exp(-d*dt)
    sc=np.empty(ns);ss=np.empty(ns);sd=np.empty(ns);swd=np.empty(ns)
    for j in range(ns):
        w=omega_note[j];d=sigma_note[j]
        swd[j]=math.sqrt(max(w*w-d*d,1e-12))
        sc[j]=math.cos(swd[j]*dt);ss[j]=math.sin(swd[j]*dt)
        sd[j]=math.exp(-d*dt)
    for i in range(nframes):
        xb=0.;vb=0.
        for j in range(nb):
            xb+=b_shape[j]*b[j]
            vb+=b_shape[j]*bv[j]
        reaction=0.;sym_vel=0.
        for s in range(ns):
            fc=0.
            if k_contact[s]>0.0:
                # Sintonia simpática: mesma força de mola em direção oposta.
                delta=q[s]-phi_note[s]*xb
                dv=v[s]-phi_note[s]*vb
                fc= -k_contact[s]*delta-c_contact[s]*dv
            reaction-=phi_note[s]*fc
            drive=fc/masses[s]
            w2=omega_note[s]*omega_note[s]
            eq=drive/w2;Q=q[s]-eq;V=v[s]
            a=sd[s];h=ss[s];c=sc[s];d=sigma_note[s];w=swd[s]
            next_q=eq+a*(Q*c+(V+d*Q)*h/w)
            next_v=a*(V*c-(w2*Q+d*V)*h/w)
            # Pedal elevado = abafadores nas cordas não tocadas.
            # Atacadas não entram no banco de simpatia (played_mask).
            if (not pedal[i]) and (not played_mask[s]):
                damp=math.exp(-damper_loss*dt)
                next_q*=damp;next_v*=damp
            q[s]=next_q;v[s]=next_v
            sym_vel+=phi_note[s]*next_v
        for j in range(nb):
            w2=board_omega[j]*board_omega[j]
            drive=b_shape[j]*(force[i]+reaction)/board_masses[j]
            eq=drive/w2;Q=b[j]-eq;V=bv[j]
            a=bd[j];h=bs[j];c=bc[j];d=board_sigma[j];w=bwd[j]
            b[j]=eq+a*(Q*c+(V+d*Q)*h/w)
            bv[j]=a*(V*c-(w2*Q+d*V)*h/w)
        l=0.;r=0.
        for j in range(nb):
            l+=b_left[j]*bv[j]
            r+=b_right[j]*bv[j]
        out_l[i]=l;out_r[i]=r;out_sym[i]=sym_vel
    return out_l,out_r,out_sym

def _sympathetic_setup(profile,fs,coupling_scale,played_midis):
    # Até duas parciais de cada uma das 88 notas, sem qualquer amostra.
    freqs=[];masses=[];phases=[];klist=[];clist=[];sigmas=[];played=[]
    for midi in range(21,109):
        p=note_params(midi)
        base=tune_note(midi,profile).target_hz
        for harmonic in (1,2):
            f=base*harmonic*math.sqrt((1+p.inarmonicidade_b*harmonic**2)/(1+p.inarmonicidade_b))
            if f>=.44*fs:continue
            mass=p.densidade_linear_kg_m*p.comprimento_vibrante_m/2
            spatial=(.65+.35*math.sin((midi-20)/87*math.pi))*(1. if harmonic==1 else .55)
            k=0.0 if midi in played_midis else min(65.0, mass*(2*math.pi*f)**2*.00018)*coupling_scale
            c=0.0 if midi in played_midis else 0.002*coupling_scale
            freqs.append(f);masses.append(mass);phases.append(spatial)
            klist.append(k);clist.append(c);sigmas.append(1.8+.8*(f/1000)**.65)
            played.append(midi in played_midis)
    return tuple(np.asarray(t,dtype=d) for t,d in zip((freqs,masses,phases,klist,clist,sigmas,played),
                                                        (float,float,float,float,float,float,bool)))

def shared_soundboard(bridge_force:np.ndarray,fs:int=SR,pedal_down:bool=False,
                      played_midis=(),profile='equal',coupling_scale=1.0,
                      damper_loss_per_s=100.0):
    bridge_force=np.asarray(bridge_force,dtype=np.float64)
    if bridge_force.ndim!=1:raise ValueError('Força da ponte deve ser mono')
    if not np.isfinite(bridge_force).all():raise ValueError('Força da ponte não finita')
    f,mass,phi,k,c,sigma,played=_sympathetic_setup(profile,fs,coupling_scale,set(played_midis))
    pedal=np.full(len(bridge_force),bool(pedal_down))
    return _shared_core(bridge_force,pedal,played,f,mass,phi,k,c,sigma,
                        2*np.pi*f,float(damper_loss_per_s),2*np.pi*BOARD_FREQ_HZ,BOARD_MASS_KG,
                        BOARD_DAMPING_S,BOARD_BRIDGE_SHAPE,BOARD_RAD_LEFT,
                        BOARD_RAD_RIGHT,float(fs))

# Ganhos experimentais fixos serão determinados por uma nota A4 sintetizada
# uma só vez e reaplicados a todas as músicas do mesmo fs e configuração.
@lru_cache(maxsize=16)
def _calibration(fs,profile,coupling_scale):
    force=string_soundboard_feedback(69,90,.65,.85,fs,profile)[0]
    l,r,s=shared_soundboard(force,fs,True,(69,),profile,coupling_scale)
    start=int(.04*fs);end=int(.75*fs)
    rms=lambda x:float(np.sqrt(np.mean(x[start:end]**2)+1e-25))
    return rms(force),max(rms((l+r)*.5),1e-12),max(rms(s),1e-12)

def render_sequence_dry(events:Sequence,length=10.,fs:int=SR,
                 config:DryConfig|None=None,pedal_down:bool=False,
                 stereo=True,normalize=True,return_stems=False):
    """Eventos: (segundos_inicio, midi, duração_tecla, velocity).

    Room FX = ZERO. A única convolução é um modelo curto do corpo do
    próprio piano, com duração limitada (padrão 20 ms).
    """
    config=(config or DryConfig()).validate()
    if fs<8000 or length<=0 or not math.isfinite(length):
        raise ValueError('Parâmetros de renderização inválidos')
    nframes=int(round(fs*length));total=np.zeros(nframes,dtype=np.float64)
    left=np.zeros(nframes,dtype=np.float64);right=np.zeros(nframes,dtype=np.float64)
    played_midis=set()
    for start,midi,hold,vel in events:
        if start<0 or hold<0 or not 21<=midi<=108 or not 1<=vel<=127:
            raise ValueError('Evento musical inválido')
        if start>=length:continue
        played_midis.add(midi)
        dur=min(length-start,max(hold+.85,2.6))
        # A V3 mantém o ataque validado e a compensação de afinação.
        force=string_soundboard_feedback(midi,vel,min(hold,dur),dur,fs,
                      config.profile,pedal_down=pedal_down)[0]
        i=int(round(start*fs));j=min(i+len(force),nframes)
        x=force[:j-i];total[i:j]+=x
        pan=(midi-21)/87
        left[i:j]+=x*(.6+.4*(1-pan))
        right[i:j]+=x*(.6+.4*pan)
    nch=2 if stereo else 1
    main=np.zeros((nframes,nch))
    for side in range(nch):
        source=left if side==0 and stereo else right if stereo else total
        ir=short_body_ir(fs,side,config.body_window_ms,config.body_decay_ms)
        body=fftconvolve(source,ir,mode='full')[:nframes]
        if config.body_highpass_hz > 0:
            body=sosfilt(butter(2,config.body_highpass_hz,fs=fs,btype='highpass',output='sos'),body)
        main[:,side]=config.direct_gain*source+config.body_gain*body
    shared_l,shared_r,sym=shared_soundboard(total,fs,pedal_down,played_midis,
                                            config.profile,config.coupling_scale,config.damper_loss_per_s)
    fref,bref,sref=_calibration(fs,config.profile,config.coupling_scale)
    # Ajustes fixos em vez de normalizar o pedal a cada música.
    board_gain=config.board_mix*config.direct_gain*fref/bref
    sym_gain=config.sympathetic_mix*config.direct_gain*fref/sref
    board=np.column_stack((shared_l,shared_r)) if stereo else ((shared_l+shared_r)*.5)[:,None]
    sympathetic=np.column_stack((sym,sym)) if stereo else sym[:,None]
    board*=board_gain
    sympathetic*=sym_gain
    sos=butter(2,[30.,min(13200.,fs*.44)],btype='bandpass',fs=fs,output='sos')
    main=sosfilt(sos,main,axis=0)
    board=sosfilt(sos,board,axis=0)
    sympathetic=sosfilt(sos,sympathetic,axis=0)
    mix=main+board+sympathetic
    # A/B recebe um ganho de saída, nunca reverberação.
    peak=float(np.max(np.abs(mix))) if len(mix) else 0.
    gain=(.85/peak if normalize and peak>1e-12 else 1.0)
    mix*=gain
    if return_stems:
        return mix.astype(np.float32),{
            'direto_e_corpo':(main*gain).astype(np.float32),
            'tampo_compartilhado':(board*gain).astype(np.float32),
            'cordas_simpaticas':(sympathetic*gain).astype(np.float32),
            'ganho_de_saida':gain
        }
    return mix.astype(np.float32)