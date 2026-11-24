#!/usr/bin/env python3
"""F1.12: descriptive, uncertainty-aware C5 C4 stereo/temporal study.

Only externally verified C5 original FLACs in an ephemeral runner. This is
NOT C3X physics metrology, transfer-function identification or calibrated DSP.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.fft import rfft, next_fast_len
from scipy.signal.windows import hann

# Empirical guards: these are analysis assumptions, not piano measurements.
WINDOWS = {
    "attack": ([.025, .035, .045], [.18, .22, .26]),
    "body": ([.23, .26, .29], [.38, .44, .50]),
    "tail": ([.85, .90, .95], [.40, .50, .60]),
}
CHANNELS = ("L", "R", "mono")
HARMONICS = (4, 5)


def harmonic_frequency(f1: float, B: float, partial: int) -> float:
    if not 200 < f1 < 400 or not 0 <= B < .012 or partial < 1:
        raise ValueError("invalid C4 frequency, B or partial")
    return f1 * partial * math.sqrt((1 + B * partial**2) / (1 + B))


def verify_input(y: np.ndarray, fs: int) -> np.ndarray:
    y = np.asarray(y)
    if fs != 48000 or y.ndim != 2 or y.shape[1] != 2 or y.shape[0] < fs * 2:
        raise ValueError("expected >=2 seconds original stereo 48kHz")
    if not np.isfinite(y).all():
        raise ValueError("non-finite audio")
    return y.astype(np.float64, copy=False)


def partial_measure(x: np.ndarray, fs: int, start_s: float, duration_s: float,
                    expected_hz: float, guard_hz: float = 8.0) -> dict:
    """Read only a narrow *physically predicted* harmonic band (no sidebands)."""
    a = round(start_s*fs); n = round(duration_s*fs)
    if a < 0 or n < 2048 or a+n > len(x):
        raise ValueError("window outside available original signal")
    if not 100 < expected_hz < fs/2-guard_hz or not 2 <= guard_hz <= 15:
        raise ValueError("invalid physical band")
    window = hann(n, sym=False)
    nfft = next_fast_len(8*n)
    spectrum = np.abs(rfft(x[a:a+n]*window, nfft))/max(float(window.sum()), 1.0)
    freq_step = fs / nfft
    k0 = max(1, math.ceil((expected_hz-guard_hz)/freq_step))
    k1 = min(len(spectrum)-2, math.floor((expected_hz+guard_hz)/freq_step))
    if k0 > k1: raise ValueError("empty spectral band")
    k = k0 + int(np.argmax(spectrum[k0:k1+1]))
    # Quadratic log-magnitude interpolation; this is a frequency estimate, not
    # calibrated pressure. Recording room/mic spectral coloration remains.
    s = np.log(np.maximum(spectrum[k-1:k+2], 1e-20))
    denom = float(s[0]-2*s[1]+s[2])
    offset = float(np.clip(.5*(s[0]-s[2])/denom, -.5, .5)) if abs(denom)>1e-12 else 0.
    peak = float(spectrum[k])
    # Local 30-50Hz neighborhood outside physical +/-8Hz band as a conservative
    # sideband/noise proxy. Not a formal sound-pressure or SNR measurement.
    noise_bins = np.r_[max(1,round((expected_hz-50)/freq_step)):max(1,round((expected_hz-15)/freq_step)),
                       min(len(spectrum),round((expected_hz+15)/freq_step)):min(len(spectrum),round((expected_hz+50)/freq_step))]
    floor = float(np.median(spectrum[noise_bins])) if len(noise_bins) else 0.
    contrast = 20*math.log10(max(peak,1e-15)/max(floor,1e-15))
    return {"amplitude": peak, "peak_hz": round((k+offset)*freq_step,3),
            "contrast_db": round(contrast,2),
            "frequency_offset_hz": round((k+offset)*freq_step-expected_hz,3)}


def summarize(seq: list[float]) -> dict:
    if not seq: return {"valid": 0}
    z = np.asarray(seq, dtype=float)
    return {"valid": len(seq), "median_db": round(float(np.median(z)),2),
            "min_db":round(float(z.min()),2), "max_db":round(float(z.max()),2),
            "p10_db":round(float(np.percentile(z,10)),2),
            "p90_db":round(float(np.percentile(z,90)),2)}


def analyze_stereo(y: np.ndarray, fs: int, f1: float, B: float, onset_s: float) -> dict:
    y = verify_input(y, fs)
    if not 0 <= onset_s <= 1: raise ValueError("invalid onset")
    sources={"L":y[:,0], "R":y[:,1], "mono": y.mean(axis=1)}
    f4=harmonic_frequency(f1,B,4)
    f5=harmonic_frequency(f1,B,5)
    outputs={}
    for stage,(starts,durations) in WINDOWS.items():
        cells={c:[] for c in CHANNELS}
        for start in starts:
            for dur in durations:
                for ch,signal in sources.items():
                    h4=partial_measure(signal,fs,onset_s+start,dur,f4)
                    h5=partial_measure(signal,fs,onset_s+start,dur,f5)
                    db=20*math.log10(max(h5["amplitude"],1e-15)/max(h4["amplitude"],1e-15))
                    # Require both peaks to rise above a repeatable local floor.
                    reliable=(h4["contrast_db"]>=6 and h5["contrast_db"]>=6)
                    cells[ch].append({"start_s":start,"duration_s":dur,
                         "h4_freq_hz":h4["peak_hz"],"h5_freq_hz":h5["peak_hz"],
                         "h4_contrast_db":h4["contrast_db"],"h5_contrast_db":h5["contrast_db"],
                         "h5_minus_h4_db":round(db,2),"reliable":bool(reliable)})
        outputs[stage]={}
        for ch, data in cells.items():
            good=[z["h5_minus_h4_db"] for z in data if z["reliable"]]
            outputs[stage][ch]={"summary":summarize(good),"total_windows":len(data),
                                "rejected_windows":len(data)-len(good),"windows":data}
        # Descriptive impact of processing: channel averaging != physical power sum.
        lm=outputs[stage]["L"]["summary"].get("median_db")
        rm=outputs[stage]["R"]["summary"].get("median_db")
        mm=outputs[stage]["mono"]["summary"].get("median_db")
        outputs[stage]["channel_spread_median_db"]=round(abs(lm-rm),2) if lm is not None and rm is not None else None
        outputs[stage]["mono_bias_vs_mean_channel_medians_db"]=round(mm-(lm+rm)/2,2) if None not in (lm,rm,mm) else None
    return {"note":"C5 Dó4; NOT Yamaha C3X", "channels":list(CHANNELS),
            "anchors":{"f1_hz":f1,"B_fit":B,"f4_pred_hz":round(f4,3),"f5_pred_hz":round(f5,3)},
            "spectrum_method":"periodic Hann + zero-pad x8, H4/H5 peak within +/-8 Hz of physically predicted frequency; reject contrast <6dB",
            "temporal_windows":"3 start times x 3 durations at attack/body/tail; percentile range is SENSITIVITY, not statistical confidence interval",
            "stages":outputs,"source_recording_licenses":"CC BY 3.0; Alexander Holm"}


def analyze_files(source_dir: Path, previous_metrics_path:Path, output:Path):
    from c5_c4_analysis import SOURCES,sha256_file,onset_sample
    import soundfile as sf
    old=json.loads(previous_metrics_path.read_text(encoding="utf-8"))
    result={"schema":"c3x-f1-12-c5-stereo-spectral-robustness-v1", "physical_c3x_f1_status":"PENDENTE",
            "real_instrument":"Yamaha C5, Salamander Grand Piano; NOT Yamaha C3X",
            "source_recording_in_synth":False,"original_audio_committed":False,
            "c5_v10_velocity_matched":False,
            "limitations":["Estimates describe recorded microphone signals, not unique causal hammer/string/bridge transfer",
                           "Window percentiles describe sensitivity to chosen intervals, not statistical confidence limits",
                           "C5 is not Yamaha C3X; velocity layers not impact-speed calibrated",
                           "No surface velocities, bridge force, microphone calibration or position-specific C3X measurements"],
            "layers":{}}
    for layer,meta in SOURCES.items():
        path=source_dir/meta["file"]
        if path.stat().st_size!=meta["size_bytes"] or sha256_file(path)!=meta["sha256"]:
            raise ValueError("Unverified sample bytes: " + layer)
        audio,fs=sf.read(path,always_2d=True,dtype="float64")
        previous=old["layers"][layer]
        oldfit=previous["inharmonicity_estimate"]
        fit=analyze_stereo(audio,fs,oldfit["fundamental_fit_hz"],oldfit["B_fit"],onset_sample(audio,fs)/fs)
        result["layers"][layer]={"source_sha256":meta["sha256"], "source_original_bytes":meta["size_bytes"],**fit}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("F1_12_VERIFIED_C5_LAYERS",len(result["layers"]),flush=True)
    for layer,data in result["layers"].items():
        for stage in ("attack","body","tail"):
            s=data["stages"][stage]
            print("F1_12_SPECTRAL_ROBUSTNESS",json.dumps({"layer":layer,"stage":stage,
                  "L":s["L"]["summary"],"R":s["R"]["summary"],"mono":s["mono"]["summary"],
                  "channel_spread":s["channel_spread_median_db"],
                  "mono_bias":s["mono_bias_vs_mean_channel_medians_db"]},sort_keys=True),flush=True)
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--previous-metrics",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    analyze_files(a.source_dir,a.previous_metrics,a.output)

if __name__=="__main__":main()
