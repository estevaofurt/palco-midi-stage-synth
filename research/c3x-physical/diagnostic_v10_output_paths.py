"""Offline V10 output-path research: ablation only, NOT a model update.
No source samples or real C3X data are used. All outputs use one common gain.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import numpy as np
import soundfile as sf

# Assumes this file is adjacent to existing F1.4 tool after upload to GitHub.
from c4_v10_stem_ablation import reconstruct,partial_profile,estimate_onset,FS


def build_case(v10_root:Path,velocity:int=75):
    original,metadata=reconstruct(v10_root,velocity=velocity,fs=FS,verify=True)
    no_body=original['direct']+original['board']
    # The motor explicitly computes a modal output, but its real radiated pressure
    # is NOT known. Disabling it is a diagnostic, not a physics correction.
    o=estimate_onset(original['mix'],FS)
    peaks={}
    for name,x in [('v10_original',original['mix']),('direct_and_board_only_diagnostic',no_body)]:
        variant={**original,'mix':x}
        if name=='direct_and_board_only_diagnostic':
            variant['body']=np.zeros_like(original['body'])
        info=partial_profile(variant,fs=FS,onset=o)
        h4=info['attack_35_255ms'][3]['mix_relative_to_fundamental_db']
        h5=info['attack_35_255ms'][4]['mix_relative_to_fundamental_db']
        peaks[name]={'h4_db_rel_fundamental':h4,'h5_db_rel_fundamental':h5,
                     'h5_minus_h4_db':round(h5-h4,2)}
    return {'velocity':velocity,'waveforms':{'v10_original':original['mix'],
            'direct_and_board_only_diagnostic':no_body},'measures':peaks,
            'max_unmodified_V10_difference':metadata['baseline_max_abs_difference']}


def render_audio(v10_root:Path,outdir:Path,velocities=(75,115)):
    outdir.mkdir(parents=True,exist_ok=True)
    cases=[build_case(v10_root,v) for v in velocities]
    gain=.80/max(float(np.max(np.abs(x))) for c in cases for x in c['waveforms'].values())
    note_files=[]
    silence=np.zeros((int(.22*FS),2),np.float64)
    inter=[]
    for c in cases:
        for name,a in c['waveforms'].items():
            # One gain for every segment preserves differences in sound level.
            audio=a*gain
            if not np.isfinite(audio).all() or np.max(np.abs(audio))>.81:raise AssertionError('headroom')
            path=outdir/f"C4_MIDI{c['velocity']}_{name}.wav"
            sf.write(path,audio,FS,subtype='PCM_24')
            note_files.append(str(path.name))
            inter.extend([audio,silence])
    ab=np.vstack(inter[:-1]).astype(np.float64)
    # Separate psychoacoustic diagnostic: align sustain RMS within each pair.
    # This gain is NOT physically calibrated and must not be used to infer force,
    # acoustic pressure, energy transfer, or piano dynamics.
    tonal_segments=[]
    tonal_factors={}
    for case in cases:
        o=case['waveforms']['v10_original']
        d=case['waveforms']['direct_and_board_only_diagnostic']
        lo,hi=int(.12*FS),int(.62*FS)
        rms_o=math.sqrt(float(np.mean(o[lo:hi]**2)))
        rms_d=math.sqrt(float(np.mean(d[lo:hi]**2)))
        factor=rms_o/max(rms_d,1e-12)
        tonal_factors[str(case['velocity'])]=factor
        tonal_segments += [o,silence,d*factor,silence]
    tonal_master=.80/max(float(np.max(np.abs(x))) for x in tonal_segments if len(x))
    tonal_track=np.vstack(tonal_segments[:-1])*tonal_master
    if np.max(np.abs(tonal_track))>.800001: raise AssertionError('tonal headroom')
    tonal_name='C4_AB_V10_vs_sem_IR_modal_RMS_IGUALADO_DIAGNOSTICO.wav'
    sf.write(outdir/tonal_name,tonal_track,FS,subtype='PCM_24')
    wavname='C4_AB_V10_original_vs_sem_IR_modal_DIAGNOSTICO.wav'
    sf.write(outdir/wavname,ab,FS,subtype='PCM_24')
    info={'status':'OFFLINE ABLATION ONLY / not a physically calibrated alternative',
          'audio_sample_rate_hz':FS,'pcm':'stereo 24-bit','fixed_gain_all_versions':gain,
          'equalized_tonal_comparison':{'file':tonal_name,'rms_match_window_s':[.12,.62],
              'diagnostic_only_not_physical_evidence':True,'diagnostic_gain_factors':tonal_factors,
              'global_tonal_gain':tonal_master},
          'source':'Original V10 synthesis, no external samples, no room reverb',
          'v10_source_modified':False,
          'sequence':'MIDI75 original → MIDI75 diagnostic → MIDI115 original → MIDI115 diagnostic, separated by .22s silence',
          'differences_due_to_muting':"body=fftconvolve(source, modal_body_ir) branch muted. Direct+board original preserved.",
          'measurements':[{k:v for k,v in c.items() if k!='waveforms'} for c in cases],
          'wavs':note_files+[wavname,tonal_name]}
    (outdir/'F1_5_AUDICAO_DIAGNOSTICO.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
    return info


def main():
    p=argparse.ArgumentParser();p.add_argument('--v10-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    info=render_audio(args.v10_root,args.output)
    print(json.dumps({k:v for k,v in info.items() if k!='sequence'},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
