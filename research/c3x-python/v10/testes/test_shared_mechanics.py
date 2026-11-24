"""Regressão V5A. Não substitui testes perceptuais nem medições de um C3X."""
import inspect
import math
import unittest
from dataclasses import replace
import numpy as np
from stage_synth_c3x.shared_mechanics import (_build_bank,SharedMechanicsConfig,
    shared_preset,render_sequence_shared)
from stage_synth_c3x.harmonic_dry import harmonic_preset,render_sequence_harmonic
from testes.test_harmonic_dry import harmonic_relative_db

class TestSharedMechanicsV5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.event=[(0.,69,.7,90)]
        cls.v5,cls.stems=render_sequence_shared(cls.event,1.05,return_stems=True)

    def test_default_dry_and_no_audio_input(self):
        import stage_synth_c3x.shared_mechanics as m
        txt=inspect.getsource(m)
        for bad in ('sf.read(', 'librosa.load(', 'room_ir', 'convolve_reverb'):
            self.assertNotIn(bad,txt)
        self.assertFalse(hasattr(SharedMechanicsConfig,'reverb'))

    def test_88_sympathetic_note_registers(self):
        bank=_build_bank(self.event,1.05,48000,shared_preset())
        n_sym=int(np.count_nonzero(bank[12]))
        # A4 é tocada (3 cordas); outras 87 notas têm representante simpático.
        self.assertEqual(n_sym,87)
        self.assertEqual(len(bank[0]),90)

    def test_stems_add_to_final_mix(self):
        v=self.stems
        np.testing.assert_allclose(self.v5,v['direto']+v['corpo']+v['tampo'],atol=3e-6,rtol=2e-5)

    def test_numeric_finite_peak_and_nonzero(self):
        self.assertEqual(self.v5.shape,(round(48000*1.05),2))
        self.assertTrue(np.isfinite(self.v5).all())
        self.assertGreater(float(np.std(self.v5)),1e-5)
        self.assertLessEqual(float(abs(self.v5).max()),.841)

    def test_frequency_a4(self):
        x=self.v5[12000:42000].mean(axis=1)
        nfft=2**19
        S=np.abs(np.fft.rfft(x*np.hanning(len(x)),nfft))
        f=np.fft.rfftfreq(nfft,1/48000)
        inds=np.where((f>435)&(f<445))[0]
        peak=f[inds[np.argmax(S[inds])]]
        self.assertLess(abs(1200*math.log2(peak/440.)),.6)

    def test_harmonics_do_not_collapse(self):
        v4=render_sequence_harmonic(self.event,1.05,config=harmonic_preset('aberto'))
        for k in (5,7):
            self.assertGreater(harmonic_relative_db(self.v5,69,k),
                               harmonic_relative_db(v4,69,k)-4.)

    def test_pedal_exposes_sympathetic_energy(self):
        _,a=render_sequence_shared(self.event,.9,return_diagnostics=True,pedal_down=False)
        _,b=render_sequence_shared(self.event,.9,return_diagnostics=True,pedal_down=True)
        self.assertGreater(b['energia_simpaticas'],10*a['energia_simpaticas'])

    def test_global_coupling_changes_polyphony(self):
        events=[(0.,60,.6,86),(0.,67,.6,90)]
        together=render_sequence_shared(events,.85,normalize=False,pedal_down=True)
        a=render_sequence_shared(events[:1],.85,normalize=False,pedal_down=True)
        b=render_sequence_shared(events[1:],.85,normalize=False,pedal_down=True)
        # Soma de modelos INDEPENDENTES não é a mesma solução do sistema global.
        diff=float(np.sqrt(np.mean((together-a-b)**2)))
        norm=float(np.sqrt(np.mean(together**2)))
        self.assertGreater(diff/norm,1e-7)

    def test_detuned_preset_and_validation(self):
        for cfg in [SharedMechanicsConfig(board_mass_scale=0),
                    SharedMechanicsConfig(bridge_damping_Ns_m=float('nan')),
                    SharedMechanicsConfig(max_partials=0),
                    SharedMechanicsConfig(body_window_ms=500)]:
            with self.assertRaises(ValueError):cfg.validate()
        self.assertTrue(shared_preset('ressonante').validate())
        with self.assertRaises(ValueError):shared_preset('reverb')
        with self.assertRaises(ValueError):render_sequence_shared([(0,69,.4,0)],.7)

    def test_stable_repeated(self):
        x=render_sequence_shared(self.event,1.05)
        np.testing.assert_array_equal(x,self.v5)

    def test_true_removal_of_sympathetic_bank(self):
        bank=_build_bank(self.event,1.05,48000,replace(shared_preset(),include_sympathetic=False))
        self.assertEqual(len(bank[0]),3)
        self.assertEqual(int(np.count_nonzero(bank[12])),0)

if __name__=='__main__':unittest.main()
