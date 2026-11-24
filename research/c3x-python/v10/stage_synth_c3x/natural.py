"""V4.1 — radiação instrumental natural, sem reverberação de sala.

Este módulo não mistura WAVs, IRs medidos ou samples. Preserva o martelo,
a corda e o tampo compartilhado da V4. Amplia apenas a resposta modal
SINTÉTICA DO INSTRUMENTO e modela sua eficiência radiativa em frequência.

A difusão de sala, ecos, crossfeed de paredes, early-reflections e reverb
não estão presentes; o resultado permanece uma estimativa, não um C3X medido.
"""
from dataclasses import dataclass
import numpy as np
from scipy.signal import butter, sosfilt
from .dry import DryConfig, render_sequence_dry
from .engine import SR


@dataclass(frozen=True)
class NaturalConfig:
    body_window_ms: float = 80.0
    body_decay_ms: float = 70.0
    body_gain: float = .00190
    body_highpass_hz: float = 250.0
    # Interpretação como ganho aproximado da eficiência radiativa com frequência.
    # Os estágios só realçam parciais EXISTENTES, não criam novas frequências.
    mid_radiation: float = .30
    high_radiation: float = .95
    board_mix: float = .038
    sympathetic_mix: float = .10
    profile: str = 'equal'

    def validate(self):
        vals = (self.body_window_ms,self.body_decay_ms,self.body_gain,self.body_highpass_hz,
                self.mid_radiation,self.high_radiation,self.board_mix,
                self.sympathetic_mix)
        if not all(np.isfinite(x) and x >= 0 for x in vals):
            raise ValueError('Configuração de radiação inválida')
        if not 1 <= self.body_window_ms <= 100:
            raise ValueError('Janela modal instrumental excede 100 ms')
        if self.body_highpass_hz >= 3000:
            raise ValueError('Corte do corpo inválido')
        if self.mid_radiation > 2.5 or self.high_radiation > 4:
            raise ValueError('Ganho de radiação fora do intervalo seguro')
        if self.profile not in ('equal','stretch_experimental'):
            raise ValueError('Perfil de afinação inválido')
        return self


def natural_preset(name='equilibrado'):
    presets = {
        'equilibrado': NaturalConfig(),
        'encorpado': NaturalConfig(body_window_ms=90.,body_decay_ms=80.,
                     body_gain=.00255,mid_radiation=.42,high_radiation=1.55),
    }
    if name not in presets:raise ValueError('Preset inválido')
    return presets[name]


def _radiation_filter(audio, fs, config):
    # Resposta de radiação dependente de frequência da placa, como função
    # de transferência aproximada. NÃO é um EQ aplicado a samples.
    low_high = min(1300., .19*fs)
    high_high = min(2900., .31*fs)
    mid = sosfilt(butter(2,low_high,fs=fs,btype='highpass',output='sos'),audio,axis=0)
    high = sosfilt(butter(2,high_high,fs=fs,btype='highpass',output='sos'),audio,axis=0)
    return audio + config.mid_radiation*mid + config.high_radiation*high


def render_sequence_natural(events,length=10.,fs=SR,config=None,pedal_down=False,
                            normalize=True,return_stems=False):
    cfg=(config if config is not None else NaturalConfig()).validate()
    dry_config=DryConfig(body_window_ms=cfg.body_window_ms,
             body_decay_ms=cfg.body_decay_ms,body_gain=cfg.body_gain,
             body_highpass_hz=cfg.body_highpass_hz,
             direct_gain=.018,board_mix=cfg.board_mix,
             sympathetic_mix=cfg.sympathetic_mix,profile=cfg.profile)
    # Obtém cada ramo antes de qualquer normalização. Exatamente o mesmo
    # martelo/corda/afinação da V4: só muda a transferência de radiação.
    _,stems=render_sequence_dry(events,length,fs=fs,config=dry_config,
                    pedal_down=pedal_down,normalize=False,return_stems=True)
    direct=stems['direto_e_corpo'].astype(np.float64)
    board=stems['tampo_compartilhado'].astype(np.float64)
    sym=stems['cordas_simpaticas'].astype(np.float64)
    radiated=_radiation_filter(direct,fs,cfg)
    mix=radiated + board + sym
    peak=float(np.max(np.abs(mix))) if mix.size else 0.
    gain=.85/peak if normalize and peak>1e-12 else 1.
    mix=(mix*gain).astype(np.float32)
    if return_stems:
        return mix,dict(direto_radiado=(radiated*gain).astype(np.float32),
                   tampo_compartilhado=(board*gain).astype(np.float32),
                   cordas_simpaticas=(sym*gain).astype(np.float32),
                   ganho_de_saida=gain)
    return mix