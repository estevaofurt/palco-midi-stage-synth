"""STAGE SYNTH C3X V7 — pedais temporais e contato gradual dos abafadores.

Motor de pesquisa offline; SEM samples e SEM reverberação de sala.
A construção parte do banco V5, mas integra coordenadas ortogonais
verticais/horizontais com amortecimentos, rigidezes e mobilidades diferentes.
O acoplamento transversal é um par de forças iguais e opostas.

Os valores NÃO são medições internas de um Yamaha C3X.
"""
from dataclasses import dataclass, field
import math
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from .engine import SR
from .shared_mechanics import (_build_bank, shared_preset,
    SharedMechanicsConfig, render_sequence_shared)
from .harmonic_dry import modal_body_ir
from .feedback import BOARD_RAD_LEFT, BOARD_RAD_RIGHT
try:
    from numba import njit
except ImportError:
    def njit(f): return f

@dataclass(frozen=True)
class PolarizedConfig:
    base: SharedMechanicsConfig = field(default_factory=lambda: shared_preset('equilibrado'))
    # Adimensionais; k_cross = ratio * massa modal * omega^2.
    coupling_ratio: float = .00072
    horizontal_loss_ratio: float = .34
    horizontal_detune_cents: float = .48
    horizontal_bridge_fraction: float = .060
    horizontal_radiation_fraction: float = .080
    horizontal_hammer_fraction: float = 0.0
    horizontal_enabled: bool = True

    def validate(self):
        self.base.validate()
        params=(self.coupling_ratio,self.horizontal_loss_ratio,
            self.horizontal_detune_cents,self.horizontal_bridge_fraction,
            self.horizontal_radiation_fraction,self.horizontal_hammer_fraction)
        if not all(math.isfinite(float(v)) for v in params):
            raise ValueError('Parâmetro de polarização não finito')
        if not (0 <= self.coupling_ratio <= .004 and
                .08 <= self.horizontal_loss_ratio <= 1.0 and
                -2 <= self.horizontal_detune_cents <= 2 and
                0 <= self.horizontal_bridge_fraction <= .20 and
                0 <= self.horizontal_radiation_fraction <= .30 and
                0 <= self.horizontal_hammer_fraction <= .12):
            raise ValueError('Parâmetro de polarização fora do intervalo experimental')
        return self


def polarization_preset(name='natural'):
    if name=='natural':
        return PolarizedConfig()
    if name=='aberto':
        return PolarizedConfig(base=shared_preset('ressonante'),coupling_ratio=.00135,
            horizontal_loss_ratio=.22,horizontal_bridge_fraction=.085,
            horizontal_radiation_fraction=.13)
    if name=='conservador':
        return PolarizedConfig(coupling_ratio=.00042,
            horizontal_loss_ratio=.42,horizontal_bridge_fraction=.05,
            horizontal_radiation_fraction=.06)
    if name=='expressivo':
        return PolarizedConfig(coupling_ratio=.0012,
            horizontal_loss_ratio=.25,horizontal_bridge_fraction=.075,
            horizontal_radiation_fraction=.11)
    if name=='V5_exato':
        return PolarizedConfig(horizontal_enabled=False)
    raise ValueError('Preset desconhecido')


def _polar_bank(base_bank,fs,cfg):
    """Parâmetros do segundo plano; o primeiro permanece exatamente na V5."""
    count,w2,wd,sigma,cosine,sine,decay=base_bank[:7]
    ns,nm=w2.shape
    # Perturbação angular pequena, mesmo desvio nos modos de uma dada corda.
    hh_ratio=2.0**(cfg.horizontal_detune_cents/1200.)
    hw2=w2*hh_ratio**2
    hsigma=sigma*cfg.horizontal_loss_ratio
    hwd=np.sqrt(np.maximum(hw2-hsigma**2,1e-9))
    hcos=np.cos(hwd/fs)
    hsin=np.sin(hwd/fs)
    hdecay=np.exp(-hsigma/fs)
    # Evita acoplamento excessivo em parciais muito altos.
    cross=np.zeros((ns,nm),np.float64)
    for s in range(ns):
        if count[s]:
            jj=np.arange(1,count[s]+1,dtype=np.float64)
            cross[s,:count[s]]=cfg.coupling_ratio/np.sqrt(jj)
    return (hw2,hwd,hsigma,hcos,hsin,hdecay,cross)


@njit
def _integrate_pedals(nframes,fs,initial_pedal,event_frames,event_values,
        alpha_down,alpha_up,contact_rise,contact_fall,contact_power,
        k_contact,c_contact,damper_loss,
        count,omega2,wd,sigma,cosine,sine,decay,hshape,nearshape,
        bshape,mass,hammer_index,syms,pan,bridge_phi,
        starts,ends,m_h,v_h,k_h,exp_h,
        board_omega2,board_wd,board_cos,board_sin,board_decay,board_sigma,board_mass,
        hw2,hwd,hsigma,hcos,hsin,hdecay,cross,hbrid,hrad,hhammer):
    ns=len(count);nv=len(starts);nb=len(board_omega2)
    nm=count.max() if ns else 1
    q=np.zeros((ns,nm));v=np.zeros_like(q) # vertical
    qh=np.zeros_like(q);vh=np.zeros_like(q) # horizontal
    b=np.zeros(nb);bv=np.zeros(nb)
    z=np.zeros(nv);vz=v_h.copy();started=np.zeros(nv,np.bool_);escaped=np.zeros(nv,np.bool_)
    force_h=np.zeros(ns);force_c=np.zeros(ns);force_ch=np.zeros(ns)
    srcl=np.zeros(nframes);srcr=np.zeros(nframes)
    modal_l=np.zeros(nframes);modal_r=np.zeros(nframes)
    sym_en=np.zeros(nframes)
    # Diagnóstico: energia cinética modal aproximada, não calibração absoluta.
    pol_en=np.zeros(2)
    dt=1/fs
    pedal_actual=initial_pedal
    pedal_target=initial_pedal
    event_ptr=0
    pedal_trace=np.zeros(nframes)
    damper_contact=np.full(ns,(1.-initial_pedal)**contact_power)
    # O abafador da nota já atacada deve estar erguido na colisão com o martelo.
    # Para ataques futuros, inicia-se a retirada um pouco antes do impacto.
    anticipation_frames=int(.018*fs)
    for s in range(ns):
        eid=hammer_index[s]
        if eid>=0 and starts[eid]==0:damper_contact[s]=0.
    release_trace=np.zeros(nframes)
    for i in range(nframes):
        while event_ptr<len(event_frames) and i>=event_frames[event_ptr]:
            pedal_target=event_values[event_ptr]
            event_ptr+=1
        # Curso mecânico gradual do pedal: alfa calculado a partir de tau.
        alpha=alpha_down if pedal_target>pedal_actual else alpha_up
        pedal_actual+=alpha*(pedal_target-pedal_actual)
        pedal_trace[i]=pedal_actual
        # Abafador pode tocar parcialmente uma corda já liberada pela tecla.
        contact_target=(1.-pedal_actual)**contact_power
        # Impacto do martelo na polarização principal, preservando V5.
        for s in range(ns):
            eid=hammer_index[s];force_h[s]=0.
            if eid>=0 and i>=starts[eid] and not escaped[eid]:
                u=0.
                for j in range(count[s]):u+=q[s,j]*hshape[s,j]
                d=z[eid]-u
                if d>0.:
                    force_h[s]=k_h[eid]*d**exp_h[eid]
                    started[eid]=True
        for e in range(nv):
            if i>=starts[e] and started[e]:
                touching=False
                for s in range(ns):
                    if hammer_index[s]==e and force_h[s]>0.:touching=True
                if not touching:escaped[e]=True
        for s in range(ns):
            eid=hammer_index[s]
            if eid>=0 and escaped[eid]:force_h[s]=0.
        board_force=np.zeros(nb)
        for s in range(ns):
            xb=0.;vb=0.
            for j in range(nb):
                xb+=bridge_phi[s,j]*b[j];vb+=bridge_phi[s,j]*bv[j]
            xs=0.;vs=0.;xh=0.;vsh=0.
            for j in range(count[s]):
                shp=nearshape[s,j]
                xs+=shp*q[s,j];vs+=shp*v[s,j]
                xh+=shp*qh[s,j];vsh+=shp*vh[s,j]
            f=-k_contact*(xs-xb)-c_contact*(vs-vb)
            fh=-hbrid*(k_contact*(xh-xb)+c_contact*(vsh-vb))
            force_c[s]=f;force_ch[s]=fh
            for j in range(nb):
                board_force[j]-=(f+fh)*bridge_phi[s,j]
        l=0.;r=0.;se=0.
        for s in range(ns):
            eid=hammer_index[s]
            key_held=(eid>=0 and i>=starts[eid]-anticipation_frames and i<ends[eid])
            damper_target=0. if key_held else contact_target
            tau_alpha=contact_rise if damper_target>damper_contact[s] else contact_fall
            damper_contact[s]+=tau_alpha*(damper_target-damper_contact[s])
            df=math.exp(-damper_loss*dt*damper_contact[s])
            if s==0:release_trace[i]=damper_contact[s]
            bs=0.;bsh=0.
            for j in range(count[s]):
                cp=omega2[s,j]*cross[s,j]
                # Kick-oscillate-kick de Strang: a troca elástica conserva
                # energia na ausência de perdas e evita instabilidade explícita
                # nos parciais próximos a Nyquist.
                kick=.5*dt*cp*(qh[s,j]-q[s,j])
                v[s,j]+=kick
                vh[s,j]-=kick
                dv=(hshape[s,j]*force_h[s]+nearshape[s,j]*force_c[s])/mass[s]
                dh=(hhammer*hshape[s,j]*force_h[s]+nearshape[s,j]*force_ch[s])/mass[s]
                eq=dv/omega2[s,j]
                Q=q[s,j]-eq;V=v[s,j]
                c=cosine[s,j];h=sine[s,j];a=decay[s,j];sg=sigma[s,j]
                q[s,j]=(eq+a*(Q*c+(V+sg*Q)*h/wd[s,j]))*df
                v[s,j]=a*(V*c-(omega2[s,j]*Q+sg*V)*h/wd[s,j])*df
                eqh=dh/hw2[s,j]
                Qh=qh[s,j]-eqh;Vh=vh[s,j]
                hc=hcos[s,j];hs=hsin[s,j];ha=hdecay[s,j];hsg=hsigma[s,j]
                qh[s,j]=(eqh+ha*(Qh*hc+(Vh+hsg*Qh)*hs/hwd[s,j]))*df
                vh[s,j]=ha*(Vh*hc-(hw2[s,j]*Qh+hsg*Vh)*hs/hwd[s,j])*df
                kick=.5*dt*cp*(qh[s,j]-q[s,j])
                v[s,j]+=kick
                vh[s,j]-=kick
                if syms[s]:se+=v[s,j]*v[s,j]+vh[s,j]*vh[s,j]
                else:
                    bs+=q[s,j]*bshape[s,j]
                    bsh+=qh[s,j]*bshape[s,j]
                    if i%48==0:
                        pol_en[0]+=mass[s]*v[s,j]*v[s,j]
                        pol_en[1]+=mass[s]*vh[s,j]*vh[s,j]
            if not syms[s]:
                l+=(bs+hrad*bsh)*pan[s,0]
                r+=(bs+hrad*bsh)*pan[s,1]
        for j in range(nb):
            drive=board_force[j]/board_mass[j]
            eq=drive/board_omega2[j];Q=b[j]-eq;V=bv[j]
            c=board_cos[j];h=board_sin[j];a=board_decay[j];sig=board_sigma[j]
            b[j]=eq+a*(Q*c+(V+sig*Q)*h/board_wd[j])
            bv[j]=a*(V*c-(board_omega2[j]*Q+sig*V)*h/board_wd[j])
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
    return srcl,srcr,modal_l,modal_r,sym_en,pol_en,pedal_trace,release_trace




@dataclass(frozen=True)
class DamperConfig:
    """Parâmetros mecânicos EXPERIMENTAIS; não medidos no Yamaha C3X."""
    pedal_raise_ms: float = 16.0
    pedal_release_ms: float = 30.0
    damper_touch_ms: float = 24.0
    damper_lift_ms: float = 14.0
    partial_contact_exponent: float = 4.2

    def validate(self):
        vals=(self.pedal_raise_ms,self.pedal_release_ms,self.damper_touch_ms,
              self.damper_lift_ms,self.partial_contact_exponent)
        if any(not math.isfinite(v) for v in vals):
            raise ValueError('Parâmetro de abafador não finito')
        if any(not (1. <= x <= 160.) for x in vals[:4]):
            raise ValueError('Tempo de abafador fora da faixa experimental')
        if not (.5 <= self.partial_contact_exponent <= 6.):
            raise ValueError('Expoente de contato fora da faixa experimental')
        return self


def _pedal_events_to_arrays(events,length,fs):
    """Eventos (segundos, posição de 0 a 1). Discretização sample-exact."""
    if events is None:
        return np.empty(0,dtype=np.int64),np.empty(0,dtype=np.float64)
    try:events=list(events)
    except TypeError as exc:raise ValueError('Eventos de pedal inválidos') from exc
    frames=[]; values=[]; previous=-1.
    for ev in events:
        if len(ev)!=2:raise ValueError('Cada pedal deve ser (segundos, posição)')
        t,p=(float(ev[0]),float(ev[1]))
        if not (math.isfinite(t) and math.isfinite(p) and
                0.<=t<=length and 0.<=p<=1. and t>previous):
            raise ValueError('Evento de pedal inválido ou fora de ordem')
        frames.append(round(t*fs));values.append(p);previous=t
    return np.asarray(frames,dtype=np.int64),np.asarray(values,dtype=np.float64)


def render_sequence_pedals(events,length=10.,fs=SR,config=None,
                           pedal_events=None,pedal_initial=0.,damper_config=None,
                           normalize=True,return_stems=False,return_diagnostics=False):
    """Motor V7 sem samples nem reverb de sala. Pedal em posições contínuas.

    pedal_events: [(tempo_segundos, posição_0_a_1), ...]. A posição varia
    com uma constante de tempo mecânica (raise/release); não salta instantaneamente.
    """
    cfg=(config or polarization_preset('natural')).validate()
    mech=(damper_config or DamperConfig()).validate()
    if not (math.isfinite(length) and 0 < length<=60 and fs>=16000):
        raise ValueError('Duração ou amostragem inválida')
    if not math.isfinite(pedal_initial) or not 0<=pedal_initial<=1:
        raise ValueError('Posição inicial inválida')
    frames,positions=_pedal_events_to_arrays(pedal_events,length,fs)
    events=list(events)
    if not cfg.horizontal_enabled:
        raise ValueError('Use render_sequence_polarized para modo V5 exato')
    bank=_build_bank(events,length,fs,cfg.base)
    size=round(fs*length)
    if not events or not any(ev[0]<length for ev in events):
        zero=np.zeros((size,2),np.float32)
        if return_stems:return zero,{'direto':zero.copy(),'corpo':zero.copy(),'tampo':zero.copy(),'ganho':1.}
        if return_diagnostics:return zero,{'pedal_final':float(pedal_initial),'abafador_final':1.,'energia_simpaticas':0.}
        return zero
    hb=_polar_bank(bank,fs,cfg)
    a_down=-math.expm1(-1./(fs*mech.pedal_raise_ms*.001))
    a_up=-math.expm1(-1./(fs*mech.pedal_release_ms*.001))
    a_contact=-math.expm1(-1./(fs*mech.damper_touch_ms*.001))
    a_lift=-math.expm1(-1./(fs*mech.damper_lift_ms*.001))
    srl,srr,bl,br,sym_en,pol_en,pedal_trace,damper_trace=_integrate_pedals(
        size,float(fs),float(pedal_initial),frames,positions,
        a_down,a_up,a_contact,a_lift,mech.partial_contact_exponent,
        cfg.base.bridge_stiffness_N_m,cfg.base.bridge_damping_Ns_m,
        cfg.base.damper_loss_s,*bank,*hb,cfg.horizontal_bridge_fraction,
        cfg.horizontal_radiation_fraction,cfg.horizontal_hammer_fraction)
    source=np.column_stack((srl,srr))
    modal=np.column_stack((bl,br))
    body=np.column_stack([fftconvolve(source[:,ch],
         modal_body_ir(fs,ch,cfg.base.body_window_ms,cfg.base.body_decay_ms),
         mode='full')[:len(source)] for ch in range(2)])
    direct=cfg.base.direct_gain*source
    body*=cfg.base.body_gain
    modal*=cfg.base.board_gain*2e3
    sos=butter(2,[30.,min(13200.,fs*.44)],fs=fs,btype='bandpass',output='sos')
    direct=sosfilt(sos,direct,axis=0)
    body=sosfilt(sos,body,axis=0)
    modal=sosfilt(sos,modal,axis=0)
    mix=direct+body+modal
    peak=float(np.max(np.abs(mix)))
    gain=.84/peak if normalize and peak>1e-12 else 1.
    mix=(mix*gain).astype(np.float32)
    if return_stems:
        return mix,{'direto':(direct*gain).astype(np.float32),
                    'corpo':(body*gain).astype(np.float32),
                    'tampo':(modal*gain).astype(np.float32),'ganho':gain}
    if return_diagnostics:
        return mix,{'pedal_final':float(pedal_trace[-1]),
                    'abafador_final':float(damper_trace[-1]),
                    'pedal_trace_100hz':pedal_trace[::max(1,fs//100)].astype(np.float32),
                    'abafador_trace_100hz':damper_trace[::max(1,fs//100)].astype(np.float32),
                    'energia_simpaticas':float(np.sum(sym_en)/fs),
                    'horizontal_vertical_energy_ratio':float(pol_en[1]/max(pol_en[0],1e-30))}
    return mix


def cc64_to_pedal_events(cc64_events):
    """Converte eventos MIDI CC64 (tempo em segundos, valor 0..127) em posição 0..1.

    Não importa biblioteca MIDI nem carrega arquivos; apenas converte valores.
    """
    result=[]
    last=-1.
    for t,value in cc64_events:
        if not (isinstance(value,(int,np.integer)) and 0<=int(value)<=127):
            raise ValueError('Valor MIDI CC64 deve ser inteiro entre 0 e 127')
        tf=float(t)
        if not math.isfinite(tf) or tf<0 or tf<=last:
            raise ValueError('Tempo MIDI CC64 inválido ou fora de ordem')
        result.append((tf,float(value)/127.))
        last=tf
    return result