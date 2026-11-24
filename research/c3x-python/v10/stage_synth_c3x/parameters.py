"""Parâmetros iniciais da escala C3X: geometria interna ESTIMADA.

Somente as dimensões externas e teclado são dados Yamaha confirmados.
Comprimentos, tensões, densidades, diâmetros, martelos são hipóteses
para experimentação, NÃO medidas do C3X.
"""
from dataclasses import dataclass, asdict
import csv
from pathlib import Path
import math
import numpy as np

YAMAHA_C3X = {"fabricante": "Yamaha", "modelo": "C3X", "teclas": 88,
              "comprimento_cm": 186, "largura_cm": 149, "altura_cm": 101,
              "massa_total_kg": 320}
STEEL_E_PA = 200e9
STEEL_RHO_KG_M3 = 7850.0

@dataclass(frozen=True)
class StringScale:
    midi: int
    nota: str
    frequencia_hz: float
    cordas_por_nota: int
    corda_enrolada: bool
    comprimento_vibrante_m: float
    tensao_por_corda_n: float
    diametro_nucleo_aco_mm: float
    densidade_linear_kg_m: float
    inarmonicidade_b: float
    massa_martelo_kg: float
    rigidez_feltro_k: float
    expoente_feltro_p: float
    posicao_impacto_fracao: float
    origem: str = "estimativa inicial; NAO medida do Yamaha C3X"

def _interp(n, points):
    keys = np.array(sorted(points), dtype=float)
    return float(np.interp(n, keys, [points[int(k)] for k in keys]))

def _interp_log(n, points):
    return math.exp(_interp(n, {k: math.log(v) for k, v in points.items()}))

def label_note(midi: int) -> str:
    names=("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return f"{names[midi%12]}{midi//12-1}"

def note_params(midi: int) -> StringScale:
    if not 21 <= midi <= 108:
        raise ValueError("MIDI permitido: 21 (A0) a 108 (C8)")
    f = 440.0 * 2**((midi-69)/12)
    # A região de mudança de ponte tem uma DESCONTINUIDADE que não deve
    # ser removida mediante uma interpolação única.
    if midi <= 46:
        L = _interp_log(midi, {21:1.36, 33:1.10, 45:0.86, 46:0.83})
    elif midi <= 49:
        L = _interp_log(midi, {47:1.03,49:0.985})
    else:
        L = _interp_log(midi, {50:0.963, 57:0.620, 60:0.545,
                              69:0.399, 81:0.208, 93:0.105, 108:0.050})
    wound = midi <= 49  # limite experimental; verificar no C3X real
    if midi <= 32:
        nstrings = 1
    elif midi <= 49:
        nstrings = 2
    else:
        nstrings = 3
    T = (_interp(midi, {21:1300, 32:1050, 46:675, 47:790,
                        49:760, 50:720, 69:687, 81:672,108:650}))
    d = (_interp(midi, {21:1.5,33:1.18,46:0.95,47:0.98,49:0.97,
                        50:1.125,69:0.95,81:0.9,108:0.78}))
    # μ necessário para que a corda de comprimento L e tensão T tenha f ideal.
    # Para graves enrolados inclui a contribuição de cobre indiretamente.
    mu = T / (4 * L * L * f * f)
    # Inarmonicidade da corda rígida idealizada usando o núcleo de aço.
    B = math.pi**3 * STEEL_E_PA * (d/1000)**4 / (64*T*L*L)
    # Altura e dureza dos martelos: hipóteses, não pesos Yamaha.
    mhammer = _interp(midi, {21:0.014, 45:0.012, 69:0.009,108:0.005})
    K = _interp_log(midi, {21:7e8, 49:1.5e10, 69:2e10,108:3e11})
    p = _interp(midi, {21:2.2, 69:2.8,108:3.5})
    xh = _interp(midi, {21:0.14, 69:0.125,108:0.105})
    return StringScale(midi,label_note(midi),f,nstrings,wound,L,T,d,mu,B,
                       mhammer,K,p,xh)

def save_scale_csv(path):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(asdict(note_params(21)).keys()),delimiter=";")
        w.writeheader()
        for n in range(21,109): w.writerow(asdict(note_params(n)))

if __name__=="__main__":
    save_scale_csv("dados/escala_88_notas_estimativa.csv")