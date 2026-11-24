"""Motor V3 experimental: cordas rigidamente modeladas + ponte/tampo dinâmico.

Este é um sistema REDUZIDO de massa/mola/amortecedor com feedback REAL.
Não equivale a uma malha 3D/FEM do Yamaha C3X. A radiação mantém parte
inteiramente sintética do transdutor original para comparar o timbre.
Sem arquivos de áudio usados como material de síntese.
"""
from dataclasses import dataclass
import math
import numpy as np
from scipy.signal import fftconvolve,butter,sosfilt
from .parameters import note_params
from .engine import SR,soundboard_impulse
from .tuning import tune_note
try:
    from numba import njit
except ImportError:
    def njit(fn): return fn

# Modos macroscópicos EXPERIMENTAIS. Frequências e massas não foram medidas
# em Yamaha C3X. Oito a doze modos também não modelam o tampo inteiro.
BOARD_FREQ_HZ=np.array([73.,102.,148.,216.,315.,465.,690.,1020.,1510.,2210.,3190.])
BOARD_MASS_KG=np.array([.70,.66,.63,.60,.56,.52,.49,.45,.43,.40,.38])
BOARD_DAMPING_S=np.array([4.0,4.4,4.8,5.2,5.7,6.3,7.1,8.4,10.0,12.5,16.0])
BOARD_BRIDGE_SHAPE=np.array([.68,-.51,.74,.39,-.58,.47,.35,-.41,.29,.23,-.18])
BOARD_RAD_LEFT=np.array([.69,-.40,.79,.28,-.52,.53,.31,-.32,.27,.16,-.12])
BOARD_RAD_RIGHT=np.array([.53,-.63,.55,.51,-.37,.32,.44,-.36,.22,.21,-.11])

@dataclass(frozen=True)
class FeedbackConfig:
    bridge_stiffness_N_m:float=2700.0
    bridge_damping_Ns_m:float=0.12
    contact_position:float=0.985
    damper_loss_s:float=85.0
    damper_touch_s:float=0.014
    board_blend:float=0.085  # comparação acústica, ganho não calibrado
    compensate_bridge_pitch:bool=True  # retensionamento contra carga da ponte

@njit
def _oscillators_step(q,v,omega2,wd,decay,cosine,sine,damping,drive):
    for s in range(len(q)):
        eq=drive[s]/omega2[s]
        Q=q[s]-eq; V=v[s]; h=sine[s]; c=cosine[s]; a=decay[s]
        q[s]=eq+a*(Q*c+(V+damping[s]*Q)*h/wd[s])
        v[s]=a*(V*c-(omega2[s]*Q+damping[s]*V)*h/wd[s])

@njit
def _evolve_string_board(nframes,ns,nm,fs,omega2,wd,sigma,cosine,sine,decay,
      hammer_shape,bridge_shape,mass_modal,hmass,hvel,hK,hp,
      hold_frames,damper_touch_frames,damper_loss,pedal,
      near_shape,k_contact,c_contact,
      board_omega2,board_wd,board_sigma,board_cos,board_sin,board_decay,
      board_mass,board_bridge_shape,board_rad_l,board_rad_r):
    q=np.zeros((ns,nm),dtype=np.float64);v=np.zeros((ns,nm),dtype=np.float64)
    nb=len(board_mass); b=np.zeros(nb); bv=np.zeros(nb)
    bridge_trace=np.zeros(nframes); board_l=np.zeros(nframes);board_r=np.zeros(nframes)
    hammer_forces=np.zeros(nframes); contact_forces=np.zeros(nframes)
    fhammer=np.zeros(ns);fcontact=np.zeros(ns)
    z=0.0;vz=hvel;touched=False;escaped=False;dt=1/fs
    for i in range(nframes):
        total_h=0.0
        if not escaped:
            for s in range(ns):
                uh=0.0
                for mode in range(nm): uh+=q[s,mode]*hammer_shape[mode]
                delta=z-uh
                fhammer[s]=hK*delta**hp if delta>0 else 0.0
                total_h+=fhammer[s]
            if total_h>0: touched=True
            elif touched: escaped=True
        else:
            for s in range(ns):fhammer[s]=0.0
        hammer_forces[i]=total_h
        xb=0.0;vb=0.0
        for j in range(nb):
            xb+=board_bridge_shape[j]*b[j]
            vb+=board_bridge_shape[j]*bv[j]
        total_c=0.0
        for s in range(ns):
            xs=0.0;vs=0.0
            for mode in range(nm):
                xs+=near_shape[mode]*q[s,mode]
                vs+=near_shape[mode]*v[s,mode]
            # Igual e oposta: gradiente do mesmo potencial + dissipação.
            fcontact[s]=-k_contact*(xs-xb)-c_contact*(vs-vb)
            total_c+=fcontact[s]
        contact_forces[i]=total_c
        factor=1.0
        if not pedal and i>=hold_frames:
            ramp=min(1.,(i-hold_frames+1)/max(1,damper_touch_frames))
            factor=math.exp(-damper_loss*ramp*dt)
        for s in range(ns):
            for mode in range(nm):
                drive=(hammer_shape[mode]*fhammer[s]+near_shape[mode]*fcontact[s])/mass_modal
                eq=drive/omega2[s,mode]
                Q=q[s,mode]-eq;V=v[s,mode];cc=cosine[s,mode]
                hh=sine[s,mode];aa=decay[s,mode]
                q[s,mode]=(eq+aa*(Q*cc+(V+sigma[s,mode]*Q)*hh/wd[s,mode]))*factor
                v[s,mode]=(aa*(V*cc-(omega2[s,mode]*Q+sigma[s,mode]*V)*hh/wd[s,mode]))*factor
        # Ação e reação: cada força da corda sobre o bloco ponte/tampo.
        for j in range(nb):
            drive=-total_c*board_bridge_shape[j]/board_mass[j]
            eq=drive/board_omega2[j];Q=b[j]-eq;V=bv[j]
            cc=board_cos[j];hh=board_sin[j];aa=board_decay[j]
            b[j]=eq+aa*(Q*cc+(V+board_sigma[j]*Q)*hh/board_wd[j])
            bv[j]=aa*(V*cc-(board_omega2[j]*Q+board_sigma[j]*V)*hh/board_wd[j])
        vz-=dt*total_h/hmass;z+=dt*vz
        bridge=0.0
        for s in range(ns):
            for mode in range(nm):bridge+=q[s,mode]*bridge_shape[mode]
        bridge_trace[i]=bridge
        l=0.0;r=0.0
        for j in range(nb):
            l+=board_rad_l[j]*bv[j]
            r+=board_rad_r[j]*bv[j]
        board_l[i]=l;board_r[i]=r
    return bridge_trace,board_l,board_r,hammer_forces,contact_forces


def string_soundboard_feedback(midi:int,velocity:int=90,hold:float=1.3,
      total:float=3.0,fs:int=SR,profile:str='equal',config:FeedbackConfig|None=None,
      pedal_down:bool=False,diagnostics:bool=False):
    config=FeedbackConfig() if config is None else config
    if not 21<=midi<=108 or not 1<=velocity<=127:
        raise ValueError('Nota ou velocidade MIDI inválida')
    if not 0<=hold<=total or total<=0 or fs<8000:
        raise ValueError('Durações e frequência de amostragem inválidas')
    checks=(config.bridge_stiffness_N_m,config.bridge_damping_Ns_m,
            config.damper_loss_s,config.damper_touch_s,config.board_blend)
    if not all(math.isfinite(x) and x>=0 for x in checks):
        raise ValueError('Parâmetros de acoplamento inválidos')
    if not 0<config.contact_position<1 or config.board_blend>1:
        raise ValueError('Posição de contato ou mistura inválida')
    p=note_params(midi);tune=tune_note(midi,profile)
    # A ponte tem rigidez: ao conectar uma corda de frequência alvo, o modo
    # passa a vibrar um pouco mais agudo. Compensamos isso pela TENSÃO,
    # sem transpor nem pós-processar o áudio. Aproximação de 1ª ordem.
    mass_modal=p.densidade_linear_kg_m*p.comprimento_vibrante_m/2
    load_sqr=config.bridge_stiffness_N_m*(math.sin(math.pi*config.contact_position)**2)/mass_modal
    target_omega2=(2*math.pi*tune.target_hz)**2
    base_omega2=target_omega2-load_sqr if config.compensate_bridge_pitch else target_omega2
    if base_omega2<=0:
        raise ValueError('Ponte rígida demais para a nota')
    base_f=math.sqrt(base_omega2)/(2*math.pi)
    tension_ratio=(base_f/p.frequencia_hz)**2-p.inarmonicidade_b
    if tension_ratio<=0:raise ValueError('Tensão fisicamente inválida')
    effective_tension=p.tensao_por_corda_n*tension_ratio
    effective_B=p.inarmonicidade_b/tension_ratio
    n=np.arange(1,min(75,int(18000/tune.target_hz)+1)+1,dtype=np.float64)
    fparts=n*base_f*np.sqrt((1+effective_B*n*n)/(1+effective_B))
    keep=fparts<min(18000.,fs*.41); n=n[keep];fparts=fparts[keep]
    ns=p.cordas_por_nota
    detune=np.array([-0.48,0.,0.44] if ns==3 else [-.3,.3] if ns==2 else [0.])
    freqs=fparts[None,:]*2**(detune[:,None]/1200)
    omega=2*np.pi*freqs
    sigma=.75+.008*(tune.target_hz**.55)+.24*(freqs/1000)**1.2
    wd=np.sqrt(np.maximum(omega*omega-sigma*sigma,1e-9))
    cosine=np.cos(wd/fs);sine=np.sin(wd/fs);decay=np.exp(-sigma/fs)
    hshape=np.sin(np.pi*n*p.posicao_impacto_fracao)
    near=np.sin(np.pi*n*config.contact_position)
    bridge=(-1.)**(n+1)*np.pi*n/p.comprimento_vibrante_m*effective_tension
    board_omega=2*np.pi*BOARD_FREQ_HZ
    board_wd=np.sqrt(board_omega**2-BOARD_DAMPING_S**2)
    hvel=.45+(velocity/127)**1.45*(2.6-.45)
    result=_evolve_string_board(int(total*fs),ns,len(n),float(fs),
        omega*omega,wd,sigma,cosine,sine,decay,hshape,bridge,
        p.densidade_linear_kg_m*p.comprimento_vibrante_m/2,
        p.massa_martelo_kg,hvel,p.rigidez_feltro_k,p.expoente_feltro_p,
        int(hold*fs),max(1,int(config.damper_touch_s*fs)),
        config.damper_loss_s,pedal_down,near,
        config.bridge_stiffness_N_m,config.bridge_damping_Ns_m,
        board_omega**2,board_wd,BOARD_DAMPING_S,
        np.cos(board_wd/fs),np.sin(board_wd/fs),np.exp(-BOARD_DAMPING_S/fs),
        BOARD_MASS_KG,BOARD_BRIDGE_SHAPE,BOARD_RAD_LEFT,BOARD_RAD_RIGHT)
    return result if diagnostics else result[:3]


def render_note_feedback(midi:int,velocity:int=90,hold:float=1.2,
      total:float=3.0,fs:int=SR,stereo:bool=True,profile:str='equal',
      config:FeedbackConfig|None=None,pedal_down:bool=False,
      radiation:str='hybrid'):
    """Radiação 'hybrid' preserva grande parte do transdutor da V1.

    'board_only' emite exclusivamente as velocidades dos modos dinâmicos;
    a normalização é de teste, não uma calibração de potência acústica.
    """
    config=FeedbackConfig() if config is None else config
    bridge,vl,vr=string_soundboard_feedback(midi,velocity,hold,total,fs,
         profile,config,pedal_down)
    if radiation not in ('hybrid','board_only'):
        raise ValueError('Radiação deve ser hybrid ou board_only')
    signals=[];pos=(midi-21)/87.
    for side in range(2 if stereo else 1):
        board=vl if side==0 else vr
        if radiation=='hybrid':
            legacy=fftconvolve(bridge,soundboard_impulse(fs,side),mode='full')[:len(bridge)]*.006+bridge*.018
            # Escala EXPERIMENTAL da saída radiativa modal, por nota.
            # Não é medida de pressão/mobilidade acústica do Yamaha.
            r0=np.sqrt(np.mean(legacy*legacy))
            r1=np.sqrt(np.mean(board*board))
            x=(1-config.board_blend)*legacy+(config.board_blend*r0/max(r1,1e-15))*board
        else:
            x=board.copy()
        x=sosfilt(butter(2,[32,min(13500.,fs*.44)],fs=fs,btype='bandpass',output='sos'),x)
        if stereo:x*=(.6+.4*(pos if side else 1-pos))
        signals.append(x)
    return np.stack(signals,axis=1) if stereo else signals[0]


def render_sequence_feedback(events,length:float=10.,fs:int=SR,stereo:bool=True,
        profile:str='equal',config:FeedbackConfig|None=None,pedal_down=False,
        radiation:str='hybrid',peak_normalize=True):
    mix=np.zeros((int(fs*length),2) if stereo else int(fs*length))
    for start,midi,hold,velocity in events:
        if start>=length:continue
        duration=min(length-start,max(hold+.85,2.6))
        voice=render_note_feedback(midi,velocity,hold,duration,fs,stereo,profile,
             config,pedal_down,radiation)
        i=int(start*fs);j=min(i+len(voice),len(mix))
        mix[i:j]+=voice[:j-i]
    peak=np.max(np.abs(mix))
    if peak_normalize and peak>1e-10: mix*=.87/peak
    return mix.astype(np.float32)
