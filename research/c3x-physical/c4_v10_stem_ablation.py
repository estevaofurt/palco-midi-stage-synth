#!/usr/bin/env python3
"""F1 research: inspect baseline V10 direct/body/board stems with identical, unmodified physics.

No Yamaha C3X physical parameter is inferred, no commercial recordings are distributed,
and no sound-engine code or configuration is changed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import math
import sys
import numpy as np
from scipy.fft import rfft, rfftfreq, next_fast_len
from scipy.signal import butter, sosfilt, fftconvolve

FS=48000
LENGTH=1.8
EVENT_START=.025
HOLD=1.74
STEM_NAMES=('direct','body','board')
WINDOWS={
    'attack_35_255ms':(.035,.22),
    'body_260_700ms':(.26,.44),
    'tail_900_1400ms':(.90,.50),
}


def get_baseline(v10_root:Path):
    p=str(v10_root.resolve())
    if p not in sys.path:sys.path.insert(0,p)
    from stage_synth_c3x.optimized_coeff import (polarization_preset,_polar_bank,
        DamperConfig,_pedal_events_to_arrays)
    from stage_synth_c3x.action_engine import _integrate_v9_shared,_build_v9_bank
    from stage_synth_c3x.continuous_action import (schedule_continuous_action,
        ContinuousActionConfig)
    from stage_synth_c3x.continuous_engine import render_sequence_v10_action
    from stage_synth_c3x.harmonic_dry import modal_body_ir
    from stage_synth_c3x.parameters import note_params
    return locals()


def reconstruct(v10_root:Path, velocity:int=75, fs:int=FS, length:float=LENGTH,
                verify:bool=True):
    """Recover signal paths without touching the V10 synthesizer or its physical parameters."""
    if velocity not in (25,75,115):raise ValueError('Only canonical research velocities supported')
    if fs not in (44100,48000):raise ValueError('Research protocol limited to 44.1/48 kHz')
    if not .5 <= length <= 2.0:raise ValueError('Invalid length')
    e=get_baseline(v10_root)
    cfg=e['polarization_preset']('natural').validate()
    damp=e['DamperConfig']().validate()
    action=e['ContinuousActionConfig']().validate()
    events=[(EVENT_START,60,min(HOLD,length-.05),velocity)]
    sched,trace=e['schedule_continuous_action'](events,length,None,action,'double')
    if len(sched)!=1 or len(trace['action_events'])!=1:
        raise RuntimeError('Expected one physical collision for C4')
    n=round(length*fs)
    frames,positions=e['_pedal_events_to_arrays'](None,length,fs)
    bank,indices,counts=e['_build_v9_bank'](sched,length,fs,cfg,bypass_action=True)
    bank=list(bank)
    vh=bank[18].copy();kh=bank[19].copy()
    for i,strike in enumerate(trace['action_events']):
        speed=strike['hammer_speed_m_s']
        vh[i]=speed
        kh[i]*=(max(speed,.01)/1.4)**action.felt_rate_exponent
    bank[18]=vh;bank[19]=kh
    polarized=e['_polar_bank'](tuple(bank),fs,cfg)
    down=-math.expm1(-1./(fs*damp.pedal_raise_ms*.001))
    up=-math.expm1(-1./(fs*damp.pedal_release_ms*.001))
    contact=-math.expm1(-1./(fs*damp.damper_touch_ms*.001))
    lift=-math.expm1(-1./(fs*damp.damper_lift_ms*.001))
    a,b,bl,br,sym,pol,pedal,release=e['_integrate_v9_shared'](
        n,float(fs),0.,frames,positions,down,up,contact,lift,
        damp.partial_contact_exponent,cfg.base.bridge_stiffness_N_m,
        cfg.base.bridge_damping_Ns_m,cfg.base.damper_loss_s,
        *bank,*polarized,cfg.horizontal_bridge_fraction,
        cfg.horizontal_radiation_fraction,cfg.horizontal_hammer_fraction,
        indices,counts)
    source=np.column_stack((a,b));modal=np.column_stack((bl,br))
    body=np.column_stack([fftconvolve(source[:,ch],
        e['modal_body_ir'](fs,ch,cfg.base.body_window_ms,cfg.base.body_decay_ms),
        mode='full')[:n] for ch in (0,1)])
    raw={
        'direct':cfg.base.direct_gain*source,
        'body':cfg.base.body_gain*body,
        'board':cfg.base.board_gain*2e3*modal,
    }
    sos=butter(2,[30.,min(13200.,fs*.44)],fs=fs,btype='bandpass',output='sos')
    stems={name:sosfilt(sos,signal,axis=0) for name,signal in raw.items()}
    stems['mix']=sum(stems.values())
    diff=None
    if verify:
        original=e['render_sequence_v10_action'](events,length=length,fs=fs,normalize=False)
        diff=float(np.max(np.abs(stems['mix']-original)))
        if diff>2e-6:raise AssertionError(f'V10 reconstruction mismatch: {diff}')
    return stems,{'midi_velocity':velocity,'onset_impact_s':trace['action_events'][0]['impact_s'],
                  'baseline_max_abs_difference':diff,
                  'base_B_estimated':e['note_params'](60).inarmonicidade_b,
                  'stems_no_normalization':True,'c5_sample_not_used':True}


def estimate_onset(x,fs):
    # Same method as the C5-vs-V10 measurement. Kept here to make the research tool independent.
    mono=x.mean(axis=1)
    width=max(64,int(fs*.005));n=len(mono)//width
    rms=np.sqrt(np.mean(mono[:n*width].reshape(n,width)**2,axis=1))
    peak=float(np.max(rms));thresh=max(peak*.03,2e-5)
    if peak < thresh:return 0
    for j in range(n-1):
        if rms[j]>=thresh and rms[j+1]>=thresh:
            return max(0,(j-1)*width)
    return int(np.argmax(rms)*width)


def partial_profile(stems, fs=FS, onset=None, f0=261.6255653005986, B=.000528449):
    if onset is None:onset=estimate_onset(stems['mix'],fs)
    results={}
    for win,(t,duration) in WINDOWS.items():
        a=onset+round(t*fs);n=round(duration*fs)
        if a+n>len(stems['mix']):continue
        nfft=next_fast_len(n*8)
        winfunc=np.hanning(n)
        spec={k:rfft(y[a:a+n].mean(axis=1)*winfunc,nfft) for k,y in stems.items()}
        hz=rfftfreq(nfft,1/fs)
        parts=[]
        for k in range(1,9):
            expected=f0*k*math.sqrt((1+B*k*k)/(1+B))
            lo=np.searchsorted(hz,expected*.993)
            hi=np.searchsorted(hz,expected*1.007)
            if not (0<lo<hi<len(hz)):
                raise ValueError('Insufficient sample support')
            selected=lo+int(np.argmax(np.abs(spec['mix'][lo:hi])))
            a_complex={s:spec[s][selected] for s in spec}
            mix_amp=abs(a_complex['mix'])
            sum_amp=sum(abs(a_complex[s]) for s in STEM_NAMES)
            if abs(sum(a_complex[s] for s in STEM_NAMES)-a_complex['mix']) > (1e-9*max(mix_amp,1.) + 1e-12):
                raise AssertionError('Complex partial stem sums do not reconstruct the mix')
            phase_loss=20*math.log10(max(mix_amp,1e-100)/max(sum_amp,1e-100))
            rel={s:20*math.log10(max(abs(a_complex[s]),1e-100)/max(mix_amp,1e-100)) for s in STEM_NAMES}
            parts.append({'partial':k,'peak_hz':round(float(hz[selected]),3),
               'sum_of_magnitudes_vs_mix_db':round(float(-phase_loss),3),
               'phase_cancellation_db':round(float(phase_loss),3),
               'component_vs_mix_db':{s:round(float(rel[s]),3) for s in STEM_NAMES},
               'component_relative_phase_deg':{s:round(float(np.angle(a_complex[s]/a_complex['mix'],deg=True)),2) if mix_amp>1e-100 else None for s in STEM_NAMES},
               'direct_vs_body_phase_deg':round(float(np.angle(a_complex['direct']/a_complex['body'],deg=True)),2) if abs(a_complex['body'])>1e-100 else None,
               'mix_complex_amplitude':float(mix_amp),
               'direct_complex_amplitude':float(abs(a_complex['direct']))})
        first=parts[0]['mix_complex_amplitude']
        for p in parts:
            p['mix_relative_to_fundamental_db']=round(20*math.log10(max(p['mix_complex_amplitude'],1e-100)/max(first,1e-100)),2)
            p['component_relative_to_its_fundamental_db']={name:round(
                p['mix_relative_to_fundamental_db']
                +p['component_vs_mix_db'][name]-parts[0]['component_vs_mix_db'][name],2)
                for name in STEM_NAMES}
        results[win]=parts
    return results


def to_summary(stems,metadata,fs=FS):
    from stage_synth_c3x.parameters import note_params
    p=note_params(60)
    onset=estimate_onset(stems['mix'],fs)
    profiles=partial_profile(stems,fs,onset, p.frequencia_hz,p.inarmonicidade_b)
    return {'velocity':metadata['midi_velocity'],'impact_s':metadata['onset_impact_s'],
            'detected_onset_s':round(onset/fs,5),'baseline_max_abs_difference':metadata['baseline_max_abs_difference'],
            'windows':profiles,
            'stems_rms':{name:float(np.sqrt(np.mean(a*a))) for name,a in stems.items()},
            'not_c3x_measurement':True,'c5_audio_used_as_input':False}



def original_body_transfer(v10_root:Path,fs:int=FS):
    """Independent, LTI frequency-response check of the *synthetic* output-body IR.

    This does NOT measure real Yamaha C5/C3X board radiation. The mechanical board
    output is a distinct third route and not included in the transfer ratio.
    """
    e=get_baseline(v10_root)
    cfg=e['polarization_preset']('natural').base
    p=e['note_params'](60)
    result={}
    for k in range(1,9):
        hz=p.frequencia_hz*k*math.sqrt((1+p.inarmonicidade_b*k*k)/(1+p.inarmonicidade_b))
        channel=[]
        for ch in (0,1):
            ir=e['modal_body_ir'](fs,ch,cfg.body_window_ms,cfg.body_decay_ms)
            h=np.dot(ir,np.exp(-2j*np.pi*hz*np.arange(len(ir))/fs))
            complex_gain=cfg.direct_gain+cfg.body_gain*h
            channel.append({'route':('left','right')[ch],
                 'combined_body_plus_direct_vs_direct_only_db':round(float(20*np.log10(abs(complex_gain)/cfg.direct_gain)),3),
                 'body_vs_direct_phase_deg':round(float(np.angle(h,deg=True)),2),
                 'body_vs_direct_magnitude':round(float(abs(cfg.body_gain*h)/cfg.direct_gain),4)})
        result[str(k)]={'predicted_partial_hz':round(hz,4),'channels':channel}
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--v10-root',type=Path,required=True)
    ap.add_argument('--c5-metrics',type=Path)
    ap.add_argument('--prior-v10-profiles',type=Path,help='Old broad-peak reference for identifying H5 sideband confusions')
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    ans={'schema':'stage-c3x-f1-v10-output-stem-ablation-v1',
         'protocol':'Original V10 reproduced without modifying any source file; no samples as synthesis input',
         'reference_instrument':'Yamaha C5 recorded by Alexander Holm (not C3X)',
         'c5_reference_hashes':{'v1':'ca44d2e906110ebc2f67ae4c233e84cbbf0e657fe53e1c6724e4f31409478f11',
                                'v8':'36fb0535a1f21fe1dfc367c361dedda73710144e8c4940b40e97e6e5f8a3c694',
                                'v16':'e2944a0d1b31ea0ff8eb82b20ae2108027f111d96fb680c6e36d01f40582c252'},
         'sample_rate_hz':FS,'length_seconds':LENGTH,
         'C3X_F1_status':'PENDENTE','V10_default_unchanged':True,'cases':{},
         'synthetic_body_IR_transfer':original_body_transfer(args.v10_root)}
    for layer,vel in [('v1',25),('v8',75),('v16',115)]:
        stems,meta=reconstruct(args.v10_root,vel,FS,LENGTH,verify=True)
        ans['cases'][layer]=to_summary(stems,meta,FS)
    if args.c5_metrics:
        x=json.loads(args.c5_metrics.read_text(encoding='utf-8'))
        ans['c5_C4_numeric_source_license']=x.get('license')
        ans['c5_C4_original_sha_verified']=all('verified_sha256' in x['layers'][k] for k in ['v1','v8','v16'])
        ans['c5_C4_numeric_only']={k:{'f1_fit':x['layers'][k]['inharmonicity_estimate']['fundamental_fit_hz'],
             'B_fit':x['layers'][k]['inharmonicity_estimate']['B_fit'],
             'reference_attack_h4_rel_db':next((p['relative_db'] for p in x['layers'][k]['spectral_windows']['attack_35_255ms'] if p['n']==4),None),
             'reference_attack_h5_rel_db':next((p['relative_db'] for p in x['layers'][k]['spectral_windows']['attack_35_255ms'] if p['n']==5),None)} for k in ['v1','v8','v16']}
    # Anchored comparison corrects a previous broad-band peak selector which mistook a
    # 1291 Hz sideband for the *actual* fifth harmonic at ~1317 Hz on V10 attacks.
    ans['corrected_h5_attack_reference_minus_v10_db']={}
    for layer,case in ans['cases'].items():
        if layer in ans.get('c5_C4_numeric_only',{}):
            ref=ans['c5_C4_numeric_only'][layer]
            v10p=case['windows']['attack_35_255ms'][4]
            ans['corrected_h5_attack_reference_minus_v10_db'][layer]=round(
                ref['reference_attack_h5_rel_db']-v10p['mix_relative_to_fundamental_db'],2)
    if args.prior_v10_profiles:
        prior=json.loads(args.prior_v10_profiles.read_text(encoding='utf-8'))
        ans['previous_broad_peak_algorithm_issue']={}
        for layer in ['v1','v8','v16']:
            old=next(p for p in prior['layers'][layer]['spectral_windows']['attack_35_255ms'] if p['n']==5)
            new=ans['cases'][layer]['windows']['attack_35_255ms'][4]
            ans['previous_broad_peak_algorithm_issue'][layer]={
                'old_frequency_hz':old['freq_hz'],
                'old_reported_h5_relative_db':old['relative_db'],
                'new_physically_anchored_h5_frequency_hz':new['peak_hz'],
                'new_h5_relative_db':new['mix_relative_to_fundamental_db'],
                'old_minus_new_db':round(old['relative_db']-new['mix_relative_to_fundamental_db'],2),
                'diagnosis':'Previous attack detector chose a ~1291Hz sideband outside the predicted V10 5th harmonic (~1317Hz).'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(ans,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    for layer,case in ans['cases'].items():
        for win in ['attack_35_255ms','body_260_700ms']:
            fourth=case['windows'][win][3];fifth=case['windows'][win][4]
            print(layer,win, 'h4',fourth['mix_relative_to_fundamental_db'],
                  'h5',fifth['mix_relative_to_fundamental_db'],
                  'h5_cancellation_db',fifth['phase_cancellation_db'],
                  'h4_body_vs_mix_db',fourth['component_vs_mix_db']['body'])


if __name__=='__main__':main()
