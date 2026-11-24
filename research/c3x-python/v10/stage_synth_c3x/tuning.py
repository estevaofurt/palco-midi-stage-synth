"""Auditoria e afinação hipotética baseada em inarmonicidade, NÃO Yamaha medida.

Todas as escolhas são explicitamente reversíveis. O valor B é uma estimativa
pré-existente; nenhuma curva representa a regulagem de fábrica de um C3X.
"""
from dataclasses import dataclass
import math
import numpy as np
from .parameters import note_params

ANCHOR_MIDI = (21, 33, 45, 57, 69, 81, 93, 105)


def octave_match_cents(lower: int, partial_pair: tuple[int, int]) -> float:
    """Desvio necessário para igualar parciais de uma oitava, em cents.

    Ex.: 4:2 significa 4ª parcial da nota grave ~ 2ª da nota aguda.
    """
    lower_partial, upper_partial = partial_pair
    if lower_partial != 2 * upper_partial:
        raise ValueError('A relação deve corresponder a uma oitava (2k:k)')
    b0 = note_params(lower).inarmonicidade_b
    b1 = note_params(lower+12).inarmonicidade_b
    ratio = math.sqrt((1+b0*lower_partial**2)/(1+b0))
    ratio /= math.sqrt((1+b1*upper_partial**2)/(1+b1))
    return 1200.0 * math.log2(ratio)


def anchor_stretch_cents() -> dict[int,float]:
    """Curva estimada suavizada por interpolação de oitavas e ancorada em A4.

    Grave: 6:3 (abaixo de A3); médio: 4:2 (A3–A5); agudo: 2:1.
    Escolhas heurísticas, NÃO medidas. Aplicamos variação por intervalos
    para evitar compensações arbitrárias nota a nota.
    """
    p = {69:0.0}
    for lo in (57, 45, 33, 21):
        pair = (4,2) if lo==57 else (6,3)
        p[lo]=p[lo+12]-octave_match_cents(lo, pair)
    for lo in (69,81,93):
        pair=(4,2) if lo==69 else (2,1)
        p[lo+12]=p[lo]+octave_match_cents(lo, pair)
    return p


def tuning_cents(midi:int, profile:str='equal')->float:
    if not 21<=midi<=108: raise ValueError('Nota MIDI fora do piano de 88 teclas')
    if profile=='equal': return 0.0
    if profile!='stretch_experimental':
        raise ValueError('Perfil desconhecido: escolha equal ou stretch_experimental')
    anchors=anchor_stretch_cents()
    # No trecho C8, extrapolação limitada da oitava A6–A7.
    if midi>105:
        slope=(anchors[105]-anchors[93])/12
        return anchors[105]+(midi-105)*slope
    return float(np.interp(midi, sorted(anchors), [anchors[k] for k in sorted(anchors)]))

@dataclass(frozen=True)
class TunedString:
    midi:int
    profile:str
    target_hz:float
    cents:float
    tension_newton:float
    inharmonicity_b:float
    ideal_fundamental_hz:float


def tune_note(midi:int, profile:str='equal')->TunedString:
    """Consistência T, μ, L e B: f1 = 1/(2L) sqrt(T/μ) sqrt(1+B).

    Mantém núcleo, comprimento e massa linear da V1. Corrige apenas a tensão
    para alcançar a frequência-alvo física, com EI constante (T*B).
    A escala original μ é estimada para a corda perfeitamente flexível.
    """
    p=note_params(midi)
    cents=tuning_cents(midi,profile)
    r=2.0**(cents/1200.0)
    tension_ratio=r*r-p.inarmonicidade_b
    if tension_ratio<=0: raise ValueError('Inarmonicidade incompatível com afinação')
    t=p.tensao_por_corda_n*tension_ratio
    b=p.inarmonicidade_b/tension_ratio
    ideal=1.0/(2*p.comprimento_vibrante_m)*math.sqrt(t/p.densidade_linear_kg_m)
    f1=ideal*math.sqrt(1+b)
    target=p.frequencia_hz*r
    if not math.isclose(f1,target,rel_tol=1e-10):
        raise ArithmeticError('Inconsistência na afinação física')
    return TunedString(midi,profile,target,cents,t,b,ideal)


def note_partials(midi:int,profile:str='equal',nmax:int=40):
    q=tune_note(midi,profile)
    n=np.arange(1,nmax+1)
    return n*q.target_hz*np.sqrt((1+q.inharmonicity_b*n*n)/(1+q.inharmonicity_b))
