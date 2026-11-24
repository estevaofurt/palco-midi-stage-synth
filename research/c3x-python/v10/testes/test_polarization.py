"""Testes de regressão e estabilidade da modelagem V6."""
import math
import unittest
import inspect
from dataclasses import replace
import numpy as np
from stage_synth_c3x.polarization import (
  PolarizedConfig,polarization_preset,render_sequence_polarized)
from stage_synth_c3x.shared_mechanics import render_sequence_shared
from testes.test_harmonic_dry import harmonic_relative_db

class TestPolarizationV6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.event=[(0.,69,.8,90)]
        cls.v6,cls.stems=render_sequence_polarized(cls.event,1.1,return_stems=True)

    def test_dry_no_sample_input(self):
        import stage_synth_c3x.polarization as p
        src=inspect.getsource(p)
        for banned in ('sf.read(', 'librosa.load(', 'room_ir', 'convolve_reverb'):
            self.assertNotIn(banned,src)
        self.assertFalse(hasattr(PolarizedConfig,'reverb'))

    def test_preset_validation(self):
        for bad in [PolarizedConfig(coupling_ratio=-.01),
                    PolarizedConfig(horizontal_bridge_fraction=1),
                    PolarizedConfig(horizontal_loss_ratio=0),
                    PolarizedConfig(horizontal_detune_cents=float('nan'))]:
            with self.assertRaises(ValueError):bad.validate()
        with self.assertRaises(ValueError):polarization_preset('room')

    def test_disabled_identical_v5(self):
        a=render_sequence_polarized(self.event,1.1,config=polarization_preset('V5_exato'))
        b=render_sequence_shared(self.event,1.1)
        np.testing.assert_array_equal(a,b)

    def test_nonzero_horizontal_motion(self):
        _,info=render_sequence_polarized([(0,69,1.3,88)],1.5,
                   return_diagnostics=True)
        self.assertGreater(info['horizontal_vertical_energy_ratio'],0.001)
        self.assertTrue(math.isfinite(info['horizontal_vertical_energy_ratio']))

    def test_output_finite_clipped_and_stereo(self):
        self.assertEqual(self.v6.shape,(52800,2))
        self.assertTrue(np.isfinite(self.v6).all())
        self.assertLessEqual(np.max(abs(self.v6)),.841)
        self.assertGreater(np.std(self.v6),1e-4)

    def test_stems_sum(self):
        s=self.stems
        np.testing.assert_allclose(self.v6,s['direto']+s['corpo']+s['tampo'],atol=3e-6,rtol=2e-5)

    def test_late_note_stability(self):
        x=render_sequence_polarized([(0.,69,4.4,90)],4.8,normalize=False)
        self.assertTrue(np.isfinite(x).all())
        # Detecta especificamente a instabilidade que surgiu no primeiro integrador.
        a=np.sqrt(np.mean(x[int(.1*48000):int(.4*48000)]**2))
        b=np.sqrt(np.mean(x[int(3.4*48000):int(3.7*48000)]**2))
        self.assertLess(b,a*.7)

    def test_harmonics_v5_preserved_a4(self):
        v5=render_sequence_shared(self.event,1.1)
        for k in (3,4,5,7):
            self.assertGreater(harmonic_relative_db(self.v6,69,k),
                               harmonic_relative_db(v5,69,k)-3.0)

    def test_pedal_and_damper(self):
        x=render_sequence_polarized([(0.,60,.35,94)],1.5,pedal_down=False)
        y=render_sequence_polarized([(0.,60,.35,94)],1.5,pedal_down=True)
        rms=lambda a:np.sqrt(np.mean(a[int(.95*48000):int(1.3*48000)]**2))
        self.assertGreater(rms(y),rms(x)*1.5)

    def test_determinism(self):
        again=render_sequence_polarized(self.event,1.1)
        np.testing.assert_array_equal(again,self.v6)

    def test_distinct_horizontal_effect(self):
        x=render_sequence_polarized(self.event,1.1)
        y=render_sequence_shared(self.event,1.1)
        self.assertGreater(np.max(abs(x-y)),1e-4)

    def test_invalid_events(self):
        with self.assertRaises(ValueError):
            render_sequence_polarized([(0.,69,1.,0)],1.1)

if __name__=='__main__': unittest.main()