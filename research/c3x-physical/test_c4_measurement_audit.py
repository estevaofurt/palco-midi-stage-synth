from __future__ import annotations
import importlib.util
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('f1audit',ROOT/'c4_measurement_audit.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
FS=48000
F0=mod.C4


def signal(duration=3.9, f0=F0, B=0.00045, decay=0.75, doublet_cents=0, channel_mode='mono'):
    t=np.arange(round(duration*FS))/FS
    wave=np.zeros_like(t)
    for k in range(1,11):
        fk=k*f0*np.sqrt((1+B*k*k)/(1+B))
        amp=.4/k**1.25
        wave+=amp*np.sin(2*np.pi*fk*t)*np.exp(-decay*t)
        if k==4 and doublet_cents:
            wave+=.75*amp*np.sin(2*np.pi*fk*2**(doublet_cents/1200)*t)*np.exp(-decay*t)
    wave*=np.minimum(1,t*60)
    wave*=.62/max(np.max(abs(wave)),1e-12)
    if channel_mode=='anti': return np.stack([wave,-wave],axis=1)
    return wave

class TestF1Medidor(unittest.TestCase):
    def setUp(self): self.temp=tempfile.TemporaryDirectory()
    def tearDown(self): self.temp.cleanup()
    def save(self,wave,rate=FS):
        path=Path(self.temp.name)/'teste.wav'
        sf.write(path,wave,rate,subtype='PCM_24')
        return path

    def test_fundamental_and_B_ground_truth(self):
        res=mod.audit_wav(self.save(signal(B=.00045)))
        self.assertEqual(res['analysis_status'],'estimativa_nao_homologada')
        self.assertAlmostEqual(res['fit']['f1_hz'],F0,delta=.2)
        self.assertAlmostEqual(res['fit']['B_fit'],.00045,delta=.00007)
        self.assertGreaterEqual(res['fit']['detected_partial_count'],8)
        self.assertLess(res['fit']['median_fit_residual_cents'],1)
        self.assertFalse(res['f1_c3x_measured'])

    def test_fourth_partial_split_3_cents(self):
        res=mod.audit_wav(self.save(signal(duration=4.6,doublet_cents=3)))
        info=res['fourth_partial_doublet']
        self.assertTrue(info['peak_pair_detected'],info)
        self.assertAlmostEqual(info['candidate']['separation_cents'],3,delta=.9)

    def test_no_forced_doublet_when_single(self):
        res=mod.audit_wav(self.save(signal()))
        self.assertFalse(res['fourth_partial_doublet']['peak_pair_detected'],res['fourth_partial_doublet'])

    def test_stereo_out_of_phase_does_not_cancel(self):
        res=mod.audit_wav(self.save(signal(channel_mode='anti')))
        self.assertAlmostEqual(res['fit']['f1_hz'],F0,delta=.2)
        self.assertEqual(res['channels'],2)

    def test_short_file_rejected(self):
        res=mod.audit_wav(self.save(signal(duration=1.0)))
        self.assertEqual(res['analysis_status'],'insuficiente')
        self.assertNotIn('fit',res)

    def test_clipping_rejected(self):
        y=signal()
        y[:1000]=1.
        res=mod.audit_wav(self.save(y))
        self.assertEqual(res['analysis_status'],'insuficiente')
        self.assertGreater(res['clip_frames'],0)

    def test_hash_stable_and_source_not_proven(self):
        path=self.save(signal())
        a=mod.audit_wav(path,origin_class='sintetico_teste')
        b=mod.audit_wav(path,origin_class='sintetico_teste')
        self.assertEqual(a['sha256'],b['sha256'])
        self.assertFalse(a['instrument_identity_verified'])
        self.assertFalse(a['commercial_rights_verified'])

    def test_44100_sample_rate_ground_truth(self):
        from scipy.signal import resample_poly
        y=resample_poly(signal(duration=3.8),147,160)
        res=mod.audit_wav(self.save(y,44100))
        self.assertEqual(res['sample_rate_hz'],44100)
        self.assertAlmostEqual(res['fit']['f1_hz'],F0,delta=.2)
        self.assertAlmostEqual(res['fit']['B_fit'],.00045,delta=.00008)
        self.assertFalse(any(k['n'] > 10 for k in res['partials']), 'Parciais ausentes não devem virar picos por vazamento do FFT')

    def test_decay_estimate(self):
        res=mod.audit_wav(self.save(signal(decay=.75)))
        d=res['decay_partial_1']
        self.assertEqual(d['status'],'estimativa_espectral')
        self.assertAlmostEqual(d['tau_seconds'],1/.75,delta=.28)

if __name__=='__main__': unittest.main()
