#!/usr/bin/env python3
"""F1: audit and estimate C4 partials from an isolated recorded WAV.

Not an instrument identifier. Never classify a recording as a Yamaha C3X
without external, instrument-specific provenance and commercial permissions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.optimize import least_squares
from scipy.signal import find_peaks
from scipy.fft import next_fast_len, rfft, rfftfreq

C4 = 261.6255653005986


def _hz_to_cent(a: float, b: float) -> float:
    return float(1200 * math.log2(a / b))


def _detect_onset(x: np.ndarray, fs: int) -> int:
    width = max(1, round(fs * .006))
    chunks = len(x) // width
    if chunks < 4:
        return 0
    rms = np.sqrt(np.mean(x[:chunks * width].reshape(chunks, width) ** 2, axis=1))
    maximum = float(np.max(rms))
    if maximum < 2e-6:
        return -1
    gate = maximum * .04
    for i in range(chunks - 2):
        if np.all(rms[i:i + 3] > gate):
            return i * width
    return int(np.argmax(rms) * width)


def _peaks_from_window(x: np.ndarray, fs: int, reference_hz: float) -> tuple[list[dict], dict]:
    N = len(x)
    nfft = next_fast_len(max(N * 4, 65536))
    window = np.hanning(N)
    amplitude = np.abs(rfft(x * window, n=nfft))
    hz = rfftfreq(nfft, 1 / fs)
    freq_step = fs / nfft
    detected = []
    detail = {}
    fundamental_band = amplitude[int(np.searchsorted(hz, .98*reference_hz)):int(np.searchsorted(hz, 1.02*reference_hz))]
    if len(fundamental_band) == 0:
        return detected, detail
    absolute_peak_cutoff = float(np.max(fundamental_band)) * (10 ** (-65 / 20))
    for k in range(1, 13):
        start = reference_hz * k * .978
        end = reference_hz * k * (1.072 if k > 1 else 1.022)
        left = int(np.searchsorted(hz, start))
        right = int(np.searchsorted(hz, end))
        if right - left < 8:
            continue
        band = amplitude[left:right]
        noise = float(np.median(band))
        peaks, _ = find_peaks(band, prominence=max(noise * 4, float(band.max()) * .005))
        if not len(peaks):
            peaks = np.array([int(band.argmax())])
        ranked = sorted((int(p) for p in peaks), key=lambda p: -band[p])
        first = ranked[0]
        if band[first] < max(absolute_peak_cutoff, 1e-9, noise * 6):
            continue

        def refine(p):
            j = left + p
            if 0 < j < len(amplitude) - 1:
                yy = np.log(np.maximum(amplitude[j - 1:j + 2], 1e-15))
                denom = float(yy[0] - 2 * yy[1] + yy[2])
                shift = float(.5 * (yy[0] - yy[2]) / denom) if abs(denom) > 1e-12 else 0.
                shift = max(-.5, min(.5, shift))
                return float((j + shift) * freq_step)
            return float(hz[j])

        freq = refine(first)
        detected.append({"n": k, "peak_hz": round(freq, 6),
                         "local_contrast_db": round(float(20 * np.log10(band[first] / max(noise, 1e-15))), 2)})
        if k == 4:
            pairs = []
            for p in ranked[1:]:
                other = refine(p)
                separation = abs(other - freq)
                if 1.5 * (fs / N) < separation < 7.5 and band[p] / band[first] > .15:
                    pairs.append({"first_hz": round(min(freq, other), 6),
                                  "second_hz": round(max(freq, other), 6),
                                  "separation_hz": round(separation, 6),
                                  "separation_cents": round(_hz_to_cent(max(freq, other), min(freq, other)), 4),
                                  "ratio_secondary_to_primary_db": round(float(20 * np.log10(band[p] / band[first])), 2)})
            detail = {"peak_pair_detected": bool(pairs),
                      "candidate": min(pairs, key=lambda q: abs(q["separation_cents"] - 3)) if pairs else None,
                      "note": "Dois picos NÃO provam duas cordas ou duas polarizações. Ausência de pico separado NÃO prova uníssono exato."}
    return detected, detail


def _estimate_decay(x: np.ndarray, fs: int, freq: float, onset: int, available_duration: float) -> dict:
    n = round(.18 * fs)
    hop = round(.09 * fs)
    begin = onset + round(.13 * fs)
    stop = min(len(x), onset + round(min(1.7, available_duration - .05) * fs))
    if stop - begin < 5 * hop + n:
        return {"status": "indeterminado", "reason": "janela curta"}
    window = np.hanning(n)
    phase = np.exp(-2j * np.pi * freq * (np.arange(n) / fs))
    times, logamps = [], []
    for pos in range(begin, stop - n + 1, hop):
        val = abs(np.dot(x[pos:pos + n] * window, phase))
        if val > 1e-12:
            times.append((pos - onset) / fs)
            logamps.append(float(np.log(val)))
    if len(times) < 6:
        return {"status": "indeterminado", "reason": "poucas janelas"}
    slope, intercept = np.polyfit(times, logamps, 1)
    fit = slope * np.array(times) + intercept
    total = float(np.sum((np.array(logamps) - np.mean(logamps)) ** 2))
    r2 = float(1 - np.sum((np.array(logamps) - fit) ** 2) / max(total, 1e-20))
    if slope >= 0:
        return {"status": "indeterminado", "reason": "crescimento de energia"}
    return {"status": "estimativa_espectral", "tau_seconds": round(float(-1 / slope), 4),
            "t60_seconds_extrapolated": round(float(-math.log(1000) / slope), 3),
            "linear_fit_r2": round(r2, 4),
            "warning": "T60 extrapolado de janela limitada; não mede diretamente cauda de 60 dB."}


def audit_wav(path: str | Path, *, reference_hz: float = C4, origin_class: str = "nao_verificada") -> dict:
    path = Path(path)
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    info = sf.info(path)
    pcm, fs = sf.read(path, dtype="float64", always_2d=True)
    duration = len(pcm) / fs
    if fs < 16000:
        raise ValueError("Taxa de amostragem insuficiente")
    if not np.all(np.isfinite(pcm)):
        raise ValueError("Amostras não finitas")
    peak = float(np.max(np.abs(pcm)))
    clip_frames = int(np.sum(np.any(abs(pcm) >= (1 - 2**-14), axis=1)))
    channel_rms = np.sqrt(np.mean(pcm ** 2, axis=0))
    selected_channel = int(np.argmax(channel_rms))
    x = pcm[:, selected_channel]
    onset = _detect_onset(x, fs)
    base = {"file":path.name,"sha256":sha,"origin_class":origin_class,
            "instrument_identity_verified":False,"commercial_rights_verified":False,
            "f1_c3x_measured":False, "sample_rate_hz":fs,"channels":pcm.shape[1],
            "subtype":info.subtype,"duration_seconds":round(duration,4),
            "peak":round(peak,6),"clip_frames":clip_frames,"channel_used":selected_channel,
            "reference_pitch_hz":reference_hz,
            "disclaimer":"Mede espectro do WAV fornecido; não valida modelo/piano, dados de força, identidade nem licença."}
    if duration < 2.0 or onset < 0 or (duration - onset/fs) < 2.0 or clip_frames > 0:
        base.update({"analysis_status":"insuficiente", "reason": "Curto/silencioso/clipping; não estimar parciais físicos."})
        return base
    offset = onset + int(.12 * fs)
    target = min(int(2.55 * fs), len(x) - offset)
    if target < int(1.9 * fs):
        base.update({"analysis_status":"insuficiente","reason":"Sem 1,9 s pós-ataque"})
        return base
    detected, doublet = _peaks_from_window(x[offset:offset + target], fs, reference_hz)
    base.update({"analysis_status":"estimativa_nao_homologada", "onset_seconds":round(onset/fs,5),
                 "spectral_window_seconds":round(target/fs,3),"partials":detected,"fourth_partial_doublet":doublet})
    if len(detected) < 5:
        base["fit"] = {"status":"inconclusivo","reason":"Menos de cinco parciais"}
        return base
    nn = np.array([e["n"] for e in detected], dtype=float)
    ff = np.array([e["peak_hz"] for e in detected], dtype=float)
    def residual(params):
        f0, B = params
        fitted = nn * f0 * np.sqrt((1 + B*nn**2) / (1 + B))
        return (fitted - ff) / nn
    res = least_squares(residual, x0=[reference_hz,.0005],bounds=([reference_hz*.978,0],[reference_hz*1.022,.004]),
                        loss="soft_l1",f_scale=.4,ftol=1e-12,xtol=1e-12,gtol=1e-12)
    f0,B=res.x
    estimated = nn*f0*np.sqrt((1+B*nn**2)/(1+B))
    cents=np.abs(1200*np.log2(ff/estimated))
    base["fit"]={"status":"ajuste_de_picos_nao_calibrado", "f1_hz":round(float(f0),6),
                 "f1_offset_cents_from_12tet":round(_hz_to_cent(f0,reference_hz),4),
                 "B_fit":round(float(B),9),"median_fit_residual_cents":round(float(np.median(cents)),3),
                 "detected_partial_count":len(detected),
                 "warning":"Modelo inarmônico simples; rigidez e impedância da ponte não identificáveis isoladamente."}
    base["decay_partial_1"]=_estimate_decay(x, fs, f0, onset, duration-onset/fs)
    return base


def main():
    ap=argparse.ArgumentParser(description="F1: auditor de WAV Dó4 isolado (pesquisa, sem homologação)")
    ap.add_argument('wav', type=Path)
    ap.add_argument('--saida',type=Path,required=True)
    ap.add_argument('--origem',choices=['sintetico_teste','v10_sintetizado','nao_verificada'],default='nao_verificada')
    args=ap.parse_args()
    output=audit_wav(args.wav,origin_class=args.origem)
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    args.saida.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"{output['analysis_status']}: {args.saida} | evidência C3X homologada: NÃO")

if __name__=='__main__':
    main()
