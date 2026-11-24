"""STAGE SYNTH C3X V5A — cordas e tampo em UM integrador mecânico.

Os eventos tocados, 88 representantes simpáticos e 11 modos de tampo
compartilham o mesmo estado temporal. Forças do contato ponte/cordas são
iguais e opostas. O transdutor radiativo é um filtro modal matemático
DO INSTRUMENTO e não uma IR ou reverberação de sala.

IMPORTANTE: parâmetros internos ainda estimados, NÃO medidas Yamaha C3X.
Versão de pesquisa offline, NÃO otimizada para VST/tempo real.
"""
from dataclasses import dataclass
import math
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from .parameters import note_params
from .engine import SR
from .feedback import (BOARD_FREQ_HZ, BOARD_MASS_KG, BOARD_DAMPING_S,
                       BOARD_BRIDGE_SHAPE, BOARD_RAD_LEFT, BOARD_RAD_RIGHT)
from .harmonic_dry import modal_body_ir
from .tuning import tune_note
try:
    from numba import njit
except ImportError:
    def njit(fn): return fn

@dataclass(frozen=True)
class SharedMechanicsConfig:
    bridge_stiffness_N_m: float = 250.0
    bridge_damping_Ns_m: float = .018
    board_mass_scale: float = 1.0  # escalar massa modal efetiva; hipotese
    max_partials: int = 48
    sympathetic_partials: int = 3
    include_sympathetic: bool = True
    # Controles do instrumento; NÃO há opção de reverb neste motor.
    body_window_ms: float = 205.
    body_decay_ms: float = 190.
    body_gain: float = .0060
    direct_gain: float = .018
    board_gain: float = .02
    damper_loss_s: float = 90.
    tuning: str = 'equal'

    def validate(self):
        values=(self.bridge_stiffness_N_m,self.bridge_damping_Ns_m,
                self.body_window_ms,self.body_decay_ms,self.body_gain,
                self.direct_gain,self.board_gain,self.damper_loss_s,self.board_mass_scale)
        if not all(math.isfinite(x) and x>=0 for x in values):
            raise ValueError('Parâmetro de instrumento inválido')
        if not 0<=self.bridge_stiffness_N_m<=1000 or not 0<=self.bridge_damping_Ns_m<=.2 or not .05<=self.board_mass_scale<=5:
            raise ValueError('Acoplamento excessivo')
        if not 20<=self.body_window_ms<=250 or not 10<=self.body_decay_ms<=500:
            raise ValueError('Resposta modal inválida')
        if not 1<=self.max_partials<=75 or not 1<=self.sympathetic_partials<=8:
            raise ValueError('Resolução modal inválida')
        if self.tuning not in ('equal','stretch_experimental'):
            raise ValueError('Afinação inválida')
        return self


def shared_preset(name='equilibrado'):
    if name=='equilibrado':return SharedMechanicsConfig()
    if name=='aberto':return SharedMechanicsConfig(bridge_stiffness_N_m=190.,
        bridge_damping_Ns_m=.014,body_window_ms=225.,body_decay_ms=205.,
        body_gain=.0065,board_gain=.020)
    if name=='ressonante':return SharedMechanicsConfig(board_mass_scale=.18,
        bridge_stiffness_N_m=280.,bridge_damping_Ns_m=.018,
        body_window_ms=225.,body_decay_ms=205.,body_gain=.0064)
    raise ValueError('Preset inexistente')


def _build_bank(events,length,fs,cfg):
    """Arrays densos só para protótipo de pesquisa, nenhum material gravado."""
    valid=[]
    for ev in events:
        if len(ev)!=4:raise ValueError('Evento deve ser (inicio, MIDI, duracao, velocidade)')
        start,midi,hold,velocity=ev
        if not all(math.isfinite(float(a)) for a in ev):raise ValueError('Evento não finito')
        if not (0<=start and 0<=hold and 21<=midi<=108 and int(midi)==midi and 1<=velocity<=127):
            raise ValueError('Evento inválido')
        if start<length: valid.append((float(start),int(midi),float(hold),int(velocity)))
    valid.sort()
    nvoices=len(valid)
    # Cada martelo/ciclo de tecla pode excitar 1-3 cordas reais aproximadas.
    # As 88 cordas simpáticas são graus de liberdade FÍSICOS (3 parciais
    # por representante), não uma cauda de reverberação sintetizada à parte.
    played={ev[1] for ev in valid}
    strings=[]
    for eid,(start,midi,hold,velocity) in enumerate(valid):
        p=note_params(midi)
        for si in range(p.cordas_por_nota):strings.append((midi,eid,si,p.cordas_por_nota,False))
    if cfg.include_sympathetic:
        for midi in range(21,109):
            if midi not in played:strings.append((midi,-1,0,1,True))
    ns=len(strings); nm=cfg.max_partials
    omega2=np.ones((ns,nm));wd=np.ones((ns,nm));sigma=np.zeros((ns,nm))
    cosine=np.ones((ns,nm));sine=np.zeros((ns,nm));decay=np.ones((ns,nm))
    hshape=np.zeros((ns,nm));nearshape=np.zeros((ns,nm));bshape=np.zeros((ns,nm))
    mass=np.ones(ns);count=np.zeros(ns,np.int32);hammer_index=np.empty(ns,np.int32)
    syms=np.zeros(ns,np.bool_);midi_arr=np.zeros(ns,np.int32)
    bridge_phi=np.zeros((ns,len(BOARD_MASS_KG)))
    pan=np.zeros((ns,2))
    for s,(midi,eid,unison_id,nunison,is_sym) in enumerate(strings):
        p=note_params(midi); tune=tune_note(midi,cfg.tuning)
        f0=tune.target_hz
        detune=([-0.48,0,.44][unison_id] if nunison==3 else
                [-.3,.3][unison_id] if nunison==2 else 0.)
        f0*=2**(detune/1200)
        nmax=(cfg.sympathetic_partials if is_sym else cfg.max_partials)
        nn=np.arange(1,nmax+1,dtype=np.float64)
        freqs=f0*nn*np.sqrt((1+p.inarmonicidade_b*nn**2)/(1+p.inarmonicidade_b))
        keep=freqs<min(16000,fs*.43)
        nn=nn[keep];freqs=freqs[keep]
        count[s]=len(nn);mass[s]=p.densidade_linear_kg_m*p.comprimento_vibrante_m/2
        wm=2*np.pi*freqs
        sg=.75+.008*(f0**.55)+.24*(freqs/1000)**1.2
        wdm=np.sqrt(np.maximum(wm*wm-sg*sg,1e-9))
        qn=len(nn)
        omega2[s,:qn]=wm*wm;wd[s,:qn]=wdm;sigma[s,:qn]=sg
        cosine[s,:qn]=np.cos(wdm/fs);sine[s,:qn]=np.sin(wdm/fs)
        decay[s,:qn]=np.exp(-sg/fs)
        hshape[s,:qn]=np.sin(np.pi*nn*p.posicao_impacto_fracao)
        nearshape[s,:qn]=np.sin(np.pi*nn*.985)
        bshape[s,:qn]=(-1)**(nn+1)*np.pi*nn/p.comprimento_vibrante_m*p.tensao_por_corda_n
        hammer_index[s]=eid;syms[s]=is_sym;midi_arr[s]=midi
        # Ponto ponte varia entre grave e agudo; perfis modestos estimados,
        # sem pretensão de forma modal verdadeira do C3X.
        coord=(midi-21)/87.
        for j in range(len(BOARD_MASS_KG)):
            bridge_phi[s,j]=BOARD_BRIDGE_SHAPE[j]*(.86+.14*math.cos(math.pi*(j+1)*coord))
        pan[s]=(.6+.4*(1-coord),.6+.4*coord)
    starts=np.zeros(nvoices,np.int64);ends=np.zeros(nvoices,np.int64)
    m_h=np.zeros(nvoices);v_h=np.zeros(nvoices);k_h=np.zeros(nvoices);exp_h=np.zeros(nvoices)
    for e,(start,midi,hold,vel) in enumerate(valid):
        p=note_params(midi)
        starts[e]=round(start*fs);ends[e]=round((start+hold)*fs)
        m_h[e]=p.massa_martelo_kg
        v_h[e]=.45+(vel/127)**1.45*(2.6-.45)
        k_h[e]=p.rigidez_feltro_k;exp_h[e]=p.expoente_feltro_p
    board_w=2*np.pi*BOARD_FREQ_HZ
    board_wd=np.sqrt(board_w*board_w-BOARD_DAMPING_S*BOARD_DAMPING_S)
    return (count,omega2,wd,sigma,cosine,sine,decay,hshape,nearshape,
            bshape,mass,hammer_index,syms,pan,bridge_phi,
            starts,ends,m_h,v_h,k_h,exp_h,
            board_w*board_w,board_wd,np.cos(board_wd/fs),np.sin(board_wd/fs),
            np.exp(-BOARD_DAMPING_S/fs),BOARD_DAMPING_S.copy(),BOARD_MASS_KG*cfg.board_mass_scale)


@njit
def _global_integrator(nframes,fs,pedal,k_contact,c_contact,damper_loss,
        count,omega2,wd,sigma,cosine,sine,decay,hshape,nearshape,
        bshape,mass,hammer_index,syms,pan,bridge_phi,
        starts,ends,m_h,v_h,k_h,exp_h,
        board_omega2,board_wd,board_cos,board_sin,board_decay,board_sigma,board_mass):
    ns=len(count);nv=len(starts);nb=len(board_omega2)
    q=np.zeros((ns,count.max() if ns else 1));v=np.zeros_like(q)
    b=np.zeros(nb);bv=np.zeros(nb)
    z=np.zeros(nv);vz=v_h.copy();started=np.zeros(nv,np.bool_);escaped=np.zeros(nv,np.bool_)
    force_h=np.zeros(ns);force_c=np.zeros(ns)
    srcl=np.zeros(nframes);srcr=np.zeros(nframes)
    modal_l=np.zeros(nframes);modal_r=np.zeros(nframes)
    sym_en=np.zeros(nframes)
    dt=1/fs
    for i in range(nframes):
        # 1. Martelos dos eventos ativos; cada martelo excita seu uníssono.
        for s in range(ns):
            eid=hammer_index[s];force_h[s]=0.
            if eid>=0 and i>=starts[eid] and not escaped[eid]:
                u=0.
                for j in range(count[s]):u+=q[s,j]*hshape[s,j]
                d=z[eid]-u
                if d>0.:
                    force_h[s]=k_h[eid]*d**exp_h[eid]
                    started[eid]=True
        # Encerrar após primeiro contato completo.
        for e in range(nv):
            if i>=starts[e] and started[e]:
                touching=False
                for s in range(ns):
                    if hammer_index[s]==e and force_h[s]>0.:touching=True
                if not touching:escaped[e]=True
        for s in range(ns):
            eid=hammer_index[s]
            if eid>=0 and escaped[eid]:force_h[s]=0.
        # 2. Uma ponte dinâmica compartilhada pelas cordas.
        board_force=np.zeros(nb)
        for s in range(ns):
            xb=0.;vb=0.
            for j in range(nb):
                xb+=bridge_phi[s,j]*b[j]
                vb+=bridge_phi[s,j]*bv[j]
            xs=0.;vs=0.
            for j in range(count[s]):
                xs+=nearshape[s,j]*q[s,j]
                vs+=nearshape[s,j]*v[s,j]
            f=-k_contact*(xs-xb)-c_contact*(vs-vb)
            force_c[s]=f
            for j in range(nb):
                board_force[j]-=f*bridge_phi[s,j]
        # 3. Corda e tampo recebem forças iguais/opostas.
        l=0.;r=0.;se=0.
        for s in range(ns):
            eid=hammer_index[s]
            if eid>=0:
                released=(i>=ends[eid] and not pedal)
            else:
                released=not pedal
            df=math.exp(-damper_loss*dt) if released else 1.
            for j in range(count[s]):
                drive=(hshape[s,j]*force_h[s]+nearshape[s,j]*force_c[s])/mass[s]
                eq=drive/omega2[s,j];Q=q[s,j]-eq;V=v[s,j]
                c=cosine[s,j];h=sine[s,j];a=decay[s,j];sig=sigma[s,j]
                q[s,j]=(eq+a*(Q*c+(V+sig*Q)*h/wd[s,j]))*df
                v[s,j]=(a*(V*c-(omega2[s,j]*Q+sig*V)*h/wd[s,j]))*df
                if syms[s]:se+=v[s,j]*v[s,j]
            if not syms[s]:
                bs=0.
                for j in range(count[s]):bs+=q[s,j]*bshape[s,j]
                l+=bs*pan[s,0];r+=bs*pan[s,1]
        for j in range(nb):
            drive=board_force[j]/board_mass[j]
            eq=drive/board_omega2[j];Q=b[j]-eq;V=bv[j]
            c=board_cos[j];h=board_sin[j];a=board_decay[j];sig=board_sigma[j]
            b[j]=eq+a*(Q*c+(V+sig*Q)*h/board_wd[j])
            bv[j]=a*(V*c-(board_omega2[j]*Q+sig*V)*h/board_wd[j])
        # Hammer does not keep pushing if it escapes; event-specific mass.
        for e in range(nv):
            if i>=starts[e] and not escaped[e]:
                total=0.
                for s in range(ns):
                    if hammer_index[s]==e:total+=force_h[s]
                vz[e]-=dt*total/m_h[e]
                z[e]+=dt*vz[e]
        for j in range(nb):
            modal_l[i]+=bv[j]*BOARD_RAD_LEFT[j]
            modal_r[i]+=bv[j]*BOARD_RAD_RIGHT[j]
        srcl[i]=l;srcr[i]=r;sym_en[i]=se
    return srcl,srcr,modal_l,modal_r,sym_en


def render_sequence_shared(events,length=10.,fs=SR,config=None,pedal_down=False,
                           normalize=True,return_stems=False,return_diagnostics=False):
    cfg=(config or shared_preset()).validate()
    if not (math.isfinite(length) and 0<length<=60 and fs>=16000):
        raise ValueError('Áudio inválido')
    events=list(events)
    bank=_build_bank(events,length,fs,cfg)
    if not events or not any(e[0]<length for e in events):
        zero=np.zeros((round(length*fs),2),np.float32)
        if return_stems:return zero,{'direto':zero.copy(),'corpo':zero.copy(),'tampo':zero.copy(),'ganho':1.}
        if return_diagnostics:return zero,{'energia_simpaticas':0.,'ponte_rms':0.}
        return zero
    srcl,srcr,bl,br,sym_en=_global_integrator(round(fs*length),float(fs),
       bool(pedal_down),cfg.bridge_stiffness_N_m,cfg.bridge_damping_Ns_m,
       cfg.damper_loss_s,*bank)
    source=np.stack((srcl,srcr),axis=1)
    modal=np.stack((bl,br),axis=1)
    # Diferentemente da V4.2, não há gerador separado de cordas simpáticas.
    # Elas realimentam o MESMO estado do tampo, e daí as notas tocadas.
    # O IR abaixo é apenas radiação modal do tampo, matematicamente gerada.
    body=np.column_stack([fftconvolve(source[:,ch],
                modal_body_ir(fs,ch,cfg.body_window_ms,cfg.body_decay_ms),
                mode='full')[:len(source)] for ch in range(2)])
    instrument=cfg.direct_gain*source
    body*=cfg.body_gain
    # A escala de radiação do modo dinâmico é experimental.
    # Referência RMS baseada em A4 fixo: não depende da música nem de samples.
    modal*=cfg.board_gain*2.0e3
    filt=butter(2,[30.,min(13200.,fs*.44)],fs=fs,btype='bandpass',output='sos')
    instrument=sosfilt(filt,instrument,axis=0)
    body=sosfilt(filt,body,axis=0)
    modal=sosfilt(filt,modal,axis=0)
    mix=instrument+body+modal
    peak=float(np.max(np.abs(mix)))
    gain=.84/peak if normalize and peak>1e-12 else 1.
    mix=(mix*gain).astype(np.float32)
    if return_stems:
        return mix,{'direto':(instrument*gain).astype(np.float32),
                    'corpo':(body*gain).astype(np.float32),
                    'tampo':(modal*gain).astype(np.float32),
                    'ganho':gain}
    if return_diagnostics:
        return mix,{'energia_simpaticas':float(np.sum(sym_en)/fs),
                    'ponte_rms':float(np.sqrt(np.mean(modal**2)))}
    return mix