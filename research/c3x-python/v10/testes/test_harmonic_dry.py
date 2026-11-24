"""Testes de regressão V4.2. Executar: python -m unittest discover -s testes -v"""
import unittest
import numpy as np
from scipy.signal import welch
from stage_synth_c3x.harmonic_dry import (HarmonicDryConfig,harmonic_preset,
                                          modal_body_ir,render_sequence_harmonic)
from stage_synth_c3x.natural import render_sequence_natural
from stage_synth_c3x.engine import SR
from stage_synth_c3x.parameters import note_params


def harmonic_relative_db(x,midi,k):
    if x.ndim==2:x=x.mean(axis=1)
    seg=x[int(.07*SR):int(.65*SR)]
    nfft=2**18
    spectrum=np.abs(np.fft.rfft(seg*np.hanning(len(seg)),nfft))
    freq=np.fft.rfftfreq(nfft,1/SR)
    p=note_params(midi)
    def peak(h):
        f=h*p.frequencia_hz*np.sqrt((1+p.inarmonicidade_b*h*h)/(1+p.inarmonicidade_b))
        return np.max(spectrum[np.abs(freq-f)<10])
    return 20*np.log10(max(peak(k)/max(peak(1),1e-12),1e-15))

class TestHarmonicDryV42(unittest.TestCase):
    def test_validates_configs(self):
        for cfg in (HarmonicDryConfig(bridge_stiffness_N_m=-2),
                    HarmonicDryConfig(body_window_ms=500),
                    HarmonicDryConfig(bridge_damping_Ns_m=float('nan'))):
            with self.assertRaises(ValueError):cfg.validate()
        with self.assertRaises(ValueError):harmonic_preset('room')

    def test_ir_is_synthesized_limited_no_room(self):
        h=modal_body_ir(SR,0,170.,140.)
        self.assertEqual(len(h),int(.170*SR))
        self.assertEqual(h[-1],0.)
        self.assertTrue(np.isfinite(h).all())

    def test_no_sample_audio_reading_in_synthesis(self):
        import inspect
        import stage_synth_c3x.harmonic_dry as mod
        src=inspect.getsource(mod)
        self.assertNotIn('sf.read(',src)
        self.assertNotIn('librosa.load(',src)

    def test_harmonics_stronger_than_v41_a4(self):
        ev=[(0,69,.8,90)]
        old=render_sequence_natural(ev,1.15)
        new=render_sequence_harmonic(ev,1.15,config=harmonic_preset('aberto'))
        for partial in (5,7):
            with self.subTest(partial=partial):
                self.assertGreater(harmonic_relative_db(new,69,partial),
                                   harmonic_relative_db(old,69,partial)+6)

    def test_stems_sum_and_pedal_changes_sound(self):
        ev=[(0,69,.5,90)]
        a,st=render_sequence_harmonic(ev,1.1,return_stems=True)
        np.testing.assert_allclose(a,st['instrumento']+st['tampo_compartilhado']+st['simpaticas'],atol=4e-7,rtol=2e-5)
        b=render_sequence_harmonic(ev,1.1,pedal_down=True)
        self.assertGreater(np.max(np.abs(a-b)),1e-6)

    def test_determinism_and_peak(self):
        ev=[(.01,69,.5,88)]
        a=render_sequence_harmonic(ev,.95)
        b=render_sequence_harmonic(ev,.95)
        np.testing.assert_array_equal(a,b)
        self.assertLessEqual(np.abs(a).max(),.851)
        self.assertTrue(np.isfinite(a).all())

    def test_frequency_close_to_440_hz(self):
        a=render_sequence_harmonic([(0,69,.9,90)],1.1)
        seg=a[int(.25*SR):int(.85*SR)].mean(axis=1)
        fft=np.abs(np.fft.rfft(seg*np.hanning(len(seg)),2**19))
        f=np.fft.rfftfreq(2**19,1/SR)
        mask=(f>425)&(f<455)
        freq=f[mask][np.argmax(fft[mask])]
        self.assertLess(abs(1200*np.log2(freq/440)),1.)

if __name__=='__main__':unittest.main()
