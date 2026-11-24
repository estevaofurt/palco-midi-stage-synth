"""STAGE SYNTH C3X V10 - motor dry V9 com ação continua experimental.

Nao usa samples nem convolucao de resposta impulsiva de uma SALA.
A IR modal herdada da V8 faz parte da radiacao aproximada do instrumento.
"""
import math
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from .engine import SR
from .optimized_coeff import (polarization_preset, _polar_bank,
    DamperConfig, _pedal_events_to_arrays)
from .action_engine import _integrate_v9_shared, _build_v9_bank, render_sequence_v9_action
from .continuous_action import schedule_continuous_action, ContinuousActionConfig
from .harmonic_dry import modal_body_ir


def render_sequence_v10_action(events=(), length=10., fs=SR, config=None,
     pedal_events=None, pedal_initial=0., damper_config=None,
     action_config=None, action_mode='double', keyframes=None,
     normalize=True, return_diagnostics=False, bypass_continuous=False):
    """Renderiza mecanica de teclas com o mesmo motor vibratorio da V9.

    Keyframes (t, midi, profundidade, velocidade) permitem meio-retorno.
    O modo bypass_continuous preserva a saída V9 para testes A/B.
    """
    if bypass_continuous:
        if keyframes is not None:
            raise ValueError('Bypass V9 requer eventos MIDI, nao keyframes')
        return render_sequence_v9_action(events, length, fs, config=config,
            pedal_events=pedal_events, pedal_initial=pedal_initial,
            damper_config=damper_config, normalize=normalize,
            action_mode=action_mode, return_diagnostics=return_diagnostics)
    cfg=(config or polarization_preset('natural')).validate()
    mech=(damper_config or DamperConfig()).validate()
    act=(action_config or ContinuousActionConfig()).validate()
    if not (math.isfinite(length) and 0<length<=60 and isinstance(fs,(int,float)) and fs>=16000):
        raise ValueError('Duracao ou frequencia de amostragem invalida')
    if not (math.isfinite(pedal_initial) and 0<=pedal_initial<=1):
        raise ValueError('Pedal inicial invalido')
    scheduled,actions=schedule_continuous_action(events,length,keyframes,act,action_mode)
    size=round(length*fs)
    if not scheduled:
        silence=np.zeros((size,2),dtype=np.float32)
        return (silence,actions) if return_diagnostics else silence
    frames,positions=_pedal_events_to_arrays(pedal_events,length,fs)
    # O banco vibra na mesma equacao da V9; apenas a entrada da acao mudou.
    bank,indices,counts=_build_v9_bank(scheduled,length,fs,cfg,bypass_action=True)
    bank=list(bank)
    # A V9 converte velocidade do martelo em valores MIDI inteiros.
    # A V10 mantem a velocidade calculada, evitando quantizacao no impacto.
    v_h=bank[18].copy(); k_h=bank[19].copy()
    for i,strike in enumerate(actions['action_events']):
        speed=strike['hammer_speed_m_s']
        v_h[i]=speed
        # Hipotese: rigidez efetiva do feltro depende da velocidade de contato.
        k_h[i]*=(max(speed,.01)/1.4)**act.felt_rate_exponent
    bank[18]=v_h; bank[19]=k_h
    hb=_polar_bank(tuple(bank),fs,cfg)
    a_down=-math.expm1(-1./(fs*mech.pedal_raise_ms*.001))
    a_up=-math.expm1(-1./(fs*mech.pedal_release_ms*.001))
    a_contact=-math.expm1(-1./(fs*mech.damper_touch_ms*.001))
    a_lift=-math.expm1(-1./(fs*mech.damper_lift_ms*.001))
    srl,srr,bl,br,sym_en,pol_en,pedal_trace,_=_integrate_v9_shared(
        size,float(fs),float(pedal_initial),frames,positions,
        a_down,a_up,a_contact,a_lift,mech.partial_contact_exponent,
        cfg.base.bridge_stiffness_N_m,cfg.base.bridge_damping_Ns_m,
        cfg.base.damper_loss_s,*bank,*hb,cfg.horizontal_bridge_fraction,
        cfg.horizontal_radiation_fraction,cfg.horizontal_hammer_fraction,indices,counts)
    source=np.column_stack((srl,srr)); modal=np.column_stack((bl,br))
    body=np.column_stack([fftconvolve(source[:,ch],
        modal_body_ir(fs,ch,cfg.base.body_window_ms,cfg.base.body_decay_ms),
        mode='full')[:len(source)] for ch in range(2)])
    direct=cfg.base.direct_gain*source
    body*=cfg.base.body_gain;modal*=cfg.base.board_gain*2e3
    sos=butter(2,[30.,min(13200.,fs*.44)],fs=fs,btype='bandpass',output='sos')
    mix=sosfilt(sos,direct,axis=0)+sosfilt(sos,body,axis=0)+sosfilt(sos,modal,axis=0)
    peak=float(np.max(np.abs(mix)))
    gain=.84/peak if normalize and peak>1e-12 else 1.
    mix=(mix*gain).astype(np.float32)
    if return_diagnostics:
        actions.update({'pedal_final':float(pedal_trace[-1]),
           'sympathetic_energy':float(np.sum(sym_en)/fs),
           'horizontal_vertical_energy_ratio':float(pol_en[1]/max(pol_en[0],1e-30))})
        return mix,actions
    return mix
