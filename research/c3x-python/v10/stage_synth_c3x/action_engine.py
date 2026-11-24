"""STAGE SYNTH C3X V9 — cordas reutilizadas em repetição da mesma nota.

A mecânica grand aproximada está em action.py. A resposta sonora preserva
integralmente os filtros/acoplamentos da V8, sem samples nem reverb de sala.
Os parâmetros NÃO são especificações verificadas de um Yamaha C3X.
"""
import math
import numpy as np
from scipy.signal import butter,sosfilt,fftconvolve
from numba import njit
from .engine import SR
from .feedback import BOARD_RAD_LEFT,BOARD_RAD_RIGHT
from .parameters import note_params
from .shared_mechanics import _build_bank
from .optimized_coeff import (polarization_preset,_polar_bank,
    DamperConfig,_pedal_events_to_arrays)
from .harmonic_dry import modal_body_ir
from .action import schedule_grand_action,GrandActionConfig,_hammer_speed

@njit
def _integrate_v9_shared(nframes,fs,initial_pedal,event_frames,event_values,
        alpha_down,alpha_up,contact_rise,contact_fall,contact_power,
        k_contact,c_contact,damper_loss,
        count,omega2,wd,sigma,cosine,sine,decay,hshape,nearshape,
        bshape,mass,hammer_index,syms,pan,bridge_phi,
        starts,ends,m_h,v_h,k_h,exp_h,
        board_omega2,board_wd,board_cos,board_sin,board_decay,board_sigma,board_mass,
        hw2,hwd,hsigma,hcos,hsin,hdecay,cross,hbrid,hrad,hhammer,
        strike_string_index,strike_string_count):
    ns=len(count);nv=len(starts);nb=len(board_omega2)
    nm=count.max() if ns else 1
    q=np.zeros((ns,nm));v=np.zeros_like(q) # vertical
    qh=np.zeros_like(q);vh=np.zeros_like(q) # horizontal
    b=np.zeros(nb);bv=np.zeros(nb)
    z=np.zeros(nv);vz=v_h.copy();started=np.zeros(nv,np.bool_);escaped=np.zeros(nv,np.bool_)
    force_h=np.zeros(ns);force_c=np.zeros(ns);force_ch=np.zeros(ns)
    # V8: matrizes fixas alocadas apenas uma vez, sem alterar equacoes.
    board_force=np.zeros(nb)
    event_force=np.zeros(nv)
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
    # V8 coefficient cache: transicao exata (oscilador linear de rigidez e perda
    # constantes durante a amostra), fatorada UMA vez por nota/mode.
    invw2=np.empty_like(omega2); a_q=np.empty_like(omega2);a_v=np.empty_like(omega2)
    b_q=np.empty_like(omega2);b_v=np.empty_like(omega2);kick_coeff=np.empty_like(omega2)
    hinvw2=np.empty_like(hw2);ha_q=np.empty_like(hw2);ha_v=np.empty_like(hw2)
    hb_q=np.empty_like(hw2);hb_v=np.empty_like(hw2)
    for s in range(ns):
        for j in range(nm):
            invw2[s,j]=1./omega2[s,j]
            sv=sine[s,j]/wd[s,j]
            a_q[s,j]=decay[s,j]*(cosine[s,j]+sigma[s,j]*sv)
            a_v[s,j]=decay[s,j]*sv
            b_q[s,j]=-decay[s,j]*omega2[s,j]*sv
            b_v[s,j]=decay[s,j]*(cosine[s,j]-sigma[s,j]*sv)
            kick_coeff[s,j]=.5*dt*omega2[s,j]*cross[s,j]
            hinvw2[s,j]=1./hw2[s,j]
            sh=hsin[s,j]/hwd[s,j]
            ha_q[s,j]=hdecay[s,j]*(hcos[s,j]+hsigma[s,j]*sh)
            ha_v[s,j]=hdecay[s,j]*sh
            hb_q[s,j]=-hdecay[s,j]*hw2[s,j]*sh
            hb_v[s,j]=hdecay[s,j]*(hcos[s,j]-hsigma[s,j]*sh)
    binv=np.empty(nb);ba_q=np.empty(nb);ba_v=np.empty(nb);bb_q=np.empty(nb);bb_v=np.empty(nb)
    for j in range(nb):
        binv[j]=1./board_omega2[j]
        sbr=board_sin[j]/board_wd[j]
        ba_q[j]=board_decay[j]*(board_cos[j]+board_sigma[j]*sbr)
        ba_v[j]=board_decay[j]*sbr
        bb_q[j]=-board_decay[j]*board_omega2[j]*sbr
        bb_v[j]=board_decay[j]*(board_cos[j]-board_sigma[j]*sbr)
    # A primeira tecla precisa liberar progressivamente o abafador ANTES do
    # ataque; a V8 já associava o evento à corda desde t=0.
    hammer_index[:] = -1
    for e in range(nv):
        for k in range(strike_string_count[e]):
            sid=strike_string_index[e,k]
            if hammer_index[sid]<0:hammer_index[sid]=e
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
        # Repetições reutilizam as MESMAS cordas; troca apenas o martelo ativo.
        # O abafador se afasta um pouco antes do golpe, mesmo na primeira nota.
        for e in range(nv):
            if i==max(0,starts[e]-anticipation_frames):
                for k in range(strike_string_count[e]):
                    hammer_index[strike_string_index[e,k]]=e
            if i==starts[e]:
                for k in range(strike_string_count[e]):
                    sid=strike_string_index[e,k]
                    hammer_index[sid]=e
                    if starts[e]==0:damper_contact[sid]=0.
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
        # V8: acumula a mesma forca de cada martelo em um unico percurso,
        # evitando varrer todas as cordas novamente para cada evento.
        event_force[:] = 0.
        for s in range(ns):
            eid=hammer_index[s]
            if eid>=0:
                if escaped[eid]:force_h[s]=0.
                event_force[eid]+=force_h[s]
        board_force[:] = 0.
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
                # Kick-oscillate-kick de Strang: a troca elástica conserva
                # energia na ausência de perdas e evita instabilidade explícita
                # nos parciais próximos a Nyquist.
                kick=kick_coeff[s,j]*(qh[s,j]-q[s,j])
                v[s,j]+=kick
                vh[s,j]-=kick
                dv=(hshape[s,j]*force_h[s]+nearshape[s,j]*force_c[s])/mass[s]
                dh=(hhammer*hshape[s,j]*force_h[s]+nearshape[s,j]*force_ch[s])/mass[s]
                eq=dv*invw2[s,j]
                Q=q[s,j]-eq;V=v[s,j]
                q[s,j]=(eq+a_q[s,j]*Q+a_v[s,j]*V)*df
                v[s,j]=(b_q[s,j]*Q+b_v[s,j]*V)*df
                eqh=dh*hinvw2[s,j]
                Qh=qh[s,j]-eqh;Vh=vh[s,j]
                qh[s,j]=(eqh+ha_q[s,j]*Qh+ha_v[s,j]*Vh)*df
                vh[s,j]=(hb_q[s,j]*Qh+hb_v[s,j]*Vh)*df
                kick=kick_coeff[s,j]*(qh[s,j]-q[s,j])
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
            eq=drive*binv[j];Q=b[j]-eq;V=bv[j]
            b[j]=eq+ba_q[j]*Q+ba_v[j]*V
            bv[j]=bb_q[j]*Q+bb_v[j]*V
        for e in range(nv):
            if i>=starts[e] and not escaped[e]:
                vz[e]-=dt*event_force[e]/m_h[e]
                z[e]+=dt*vz[e]
        for j in range(nb):
            modal_l[i]+=bv[j]*BOARD_RAD_LEFT[j]
            modal_r[i]+=bv[j]*BOARD_RAD_RIGHT[j]
        srcl[i]=l;srcr[i]=r;sym_en[i]=se
    return srcl,srcr,modal_l,modal_r,sym_en,pol_en,pedal_trace,release_trace






def _build_v9_bank(scheduled,length,fs,config,action_config=None,bypass_action=False):
    # Uma única escala física por nota distinta, preservando ressonância e
    # energia das cordas entre golpes sucessivos.
    unique_by_midi={}
    for ev in scheduled:
        unique_by_midi.setdefault(ev[1],ev)
    unique=sorted(unique_by_midi.values(),key=lambda e:(e[0],e[1]))
    bank=list(_build_bank(unique,length,fs,config.base))
    sid_by_midi={};sid=0
    for _,midi,_,_ in unique:
        count=note_params(midi).cordas_por_nota
        sid_by_midi[midi]=list(range(sid,sid+count));sid+=count
    action_cfg=(action_config or GrandActionConfig()).validate()
    nv=len(scheduled)
    starts=np.zeros(nv,np.int64);ends=np.zeros(nv,np.int64)
    m_h=np.zeros(nv);v_h=np.zeros(nv);k_h=np.zeros(nv);exp_h=np.zeros(nv)
    strike_index=np.full((nv,3),-1,np.int64)
    strike_count=np.zeros(nv,np.int64)
    for e,(start,midi,hold,vel) in enumerate(scheduled):
        p=note_params(midi)
        starts[e]=round(start*fs);ends[e]=round((start+hold)*fs)
        m_h[e]=p.massa_martelo_kg
        v_h[e]=_hammer_speed(vel)
        rate=1. if bypass_action else (_hammer_speed(vel)/1.4)**action_cfg.felt_rate_exponent
        k_h[e]=p.rigidez_feltro_k*rate;exp_h[e]=p.expoente_feltro_p
        ids=sid_by_midi[midi]
        strike_index[e,:len(ids)]=ids;strike_count[e]=len(ids)
    bank[11]=np.full(len(bank[11]),-1,dtype=np.int32)
    bank[15:21]=[starts,ends,m_h,v_h,k_h,exp_h]
    return tuple(bank),strike_index,strike_count


def render_sequence_v9_action(events,length=10.,fs=SR,config=None,
        pedal_events=None,pedal_initial=0.,damper_config=None,
        action_config=None,action_mode='double',bypass_action=False,
        normalize=True,return_diagnostics=False):
    """Motor V9; uma corda física por uníssono, mesmo sob repetição rápida.

    Não simula toda a geometria da ação: converte pressões em colisões físicas
    com atraso e rearmamento estimados, sem simplificar o impacto do feltro.
    """
    cfg=(config or polarization_preset('natural')).validate()
    mech=(damper_config or DamperConfig()).validate()
    if not (math.isfinite(length) and 0<length<=60 and fs>=16000):
        raise ValueError('Duração ou amostragem inválida')
    if not math.isfinite(pedal_initial) or not 0<=pedal_initial<=1:
        raise ValueError('Posição inicial do pedal inválida')
    scheduled,actions=schedule_grand_action(events,length,action_config,
                                             mode=action_mode,bypass=bypass_action)
    size=round(length*fs)
    if not scheduled:
        zero=np.zeros((size,2),np.float32)
        return (zero,{'action_events':actions,'unique_key_count':0}) if return_diagnostics else zero
    frames,positions=_pedal_events_to_arrays(pedal_events,length,fs)
    bank,indices,counts=_build_v9_bank(scheduled,length,fs,cfg,action_config,bypass_action)
    hb=_polar_bank(bank,fs,cfg)
    a_down=-math.expm1(-1./(fs*mech.pedal_raise_ms*.001))
    a_up=-math.expm1(-1./(fs*mech.pedal_release_ms*.001))
    a_contact=-math.expm1(-1./(fs*mech.damper_touch_ms*.001))
    a_lift=-math.expm1(-1./(fs*mech.damper_lift_ms*.001))
    srl,srr,bl,br,sym_en,pol_en,pedal_trace,damper_trace=_integrate_v9_shared(
        size,float(fs),float(pedal_initial),frames,positions,
        a_down,a_up,a_contact,a_lift,mech.partial_contact_exponent,
        cfg.base.bridge_stiffness_N_m,cfg.base.bridge_damping_Ns_m,
        cfg.base.damper_loss_s,*bank,*hb,cfg.horizontal_bridge_fraction,
        cfg.horizontal_radiation_fraction,cfg.horizontal_hammer_fraction,
        indices,counts)
    source=np.column_stack((srl,srr));modal=np.column_stack((bl,br))
    body=np.column_stack([fftconvolve(source[:,ch],
         modal_body_ir(fs,ch,cfg.base.body_window_ms,cfg.base.body_decay_ms),
         mode='full')[:len(source)] for ch in range(2)])
    direct=cfg.base.direct_gain*source
    body*=cfg.base.body_gain;modal*=cfg.base.board_gain*2e3
    sos=butter(2,[30.,min(13200.,fs*.44)],fs=fs,btype='bandpass',output='sos')
    direct=sosfilt(sos,direct,axis=0)
    body=sosfilt(sos,body,axis=0)
    modal=sosfilt(sos,modal,axis=0)
    mix=direct+body+modal
    peak=float(np.max(np.abs(mix)))
    gain=.84/peak if normalize and peak>1e-12 else 1.
    mix=(mix*gain).astype(np.float32)
    if return_diagnostics:
        return mix,{'action_events':actions,
                    'unique_key_count':len({e[1] for e in scheduled}),
                    'strike_count':len(scheduled),
                    'pedal_final':float(pedal_trace[-1]),
                    'sympathetic_energy':float(np.sum(sym_en)/fs),
                    'horizontal_vertical_energy_ratio':float(pol_en[1]/max(pol_en[0],1e-30))}
    return mix
