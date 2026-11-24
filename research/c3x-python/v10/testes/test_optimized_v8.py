"""Regressões do integrador V8: timbre, fases, envelope e pedais.

Comparações de waveform são entre dois motores matemáticos, não há samples no motor.
"""
import inspect
import unittest
import numpy as np
from stage_synth_c3x.pedals import render_sequence_pedals
from stage_synth_c3x.optimized import render_sequence_v8
from stage_synth_c3x.optimized_coeff import render_sequence_v8_coeff
from stage_synth_c3x.engine import SR
from testes.test_harmonic_dry import harmonic_relative_db

class TestV8Optimization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ev=[(.02,48,.47,69),(.18,55,.65,86),(.26,60,.64,108)]
        cls.pedal=[(.11,1.),(.68,.42),(.9,0.)]
        cls.v7=render_sequence_pedals(cls.ev,1.18,normalize=False,pedal_events=cls.pedal)
        cls.v8=render_sequence_v8(cls.ev,1.18,normalize=False,pedal_events=cls.pedal)
        cls.fast=render_sequence_v8_coeff(cls.ev,1.18,normalize=False,pedal_events=cls.pedal)

    def test_v8_strict_exact_v7(self):
        np.testing.assert_array_equal(self.v7,self.v8)

    def test_v8_coeff_negligible_numeric_difference(self):
        b=self.v7.astype(float);n=self.fast.astype(float)
        rel=np.linalg.norm(b-n)/max(np.linalg.norm(b),1e-15)
        self.assertLess(rel,1e-7)
        self.assertTrue(np.isfinite(n).all())

    def test_no_pedal_same_output(self):
        ev=[(0.,69,.6,95)]
        a=render_sequence_pedals(ev,1.0,normalize=False)
        b=render_sequence_v8_coeff(ev,1.0,normalize=False)
        self.assertLess(np.linalg.norm(a.astype(float)-b.astype(float))/np.linalg.norm(a),1e-7)

    def test_half_pedal_matches_v7(self):
        ev=[(0.,69,.25,84)]
        for p in (0.,.5,1.):
            with self.subTest(position=p):
                a=render_sequence_pedals(ev,.85,pedal_initial=p,normalize=False)
                b=render_sequence_v8_coeff(ev,.85,pedal_initial=p,normalize=False)
                self.assertLess(np.max(np.abs(a-b)),1e-5)

    def test_long_tail_stable(self):
        x=render_sequence_v8_coeff([(0.,69,.16,102)],2.,pedal_initial=1.,normalize=False)
        self.assertTrue(np.isfinite(x).all())
        self.assertGreater(float(np.sqrt(np.mean(x[-3000:].astype(float)**2))),0.)

    def test_kinematic_diagnostics_identical(self):
        a,da=render_sequence_pedals(self.ev,1.18,pedal_events=self.pedal,return_diagnostics=True)
        b,db=render_sequence_v8_coeff(self.ev,1.18,pedal_events=self.pedal,return_diagnostics=True)
        for key in ('pedal_final','abafador_final','energia_simpaticas','horizontal_vertical_energy_ratio'):
            self.assertAlmostEqual(da[key],db[key],delta=max(1e-9,abs(da[key])*1e-7))

    def test_stems_recompose_audio(self):
        x,st=render_sequence_v8_coeff([(0,69,.8,90)],1.,return_stems=True)
        self.assertLessEqual(np.max(abs(x)),.85)
        np.testing.assert_allclose(x,st['direto']+st['corpo']+st['tampo'],atol=3e-6)

    def test_harmonics_a4_unchanged(self):
        ev=[(0,69,.9,90)]
        a=render_sequence_pedals(ev,1.05)
        b=render_sequence_v8_coeff(ev,1.05)
        for k in (2,3,4,5,6,7,8):
            with self.subTest(partial=k):
                self.assertLess(abs(harmonic_relative_db(a,69,k)-harmonic_relative_db(b,69,k)),.02)

    def test_bass_treble_same_waveform(self):
        for midi in (33,57,81,96):
            with self.subTest(midi=midi):
                ev=[(0,midi,.48,91)]
                a=render_sequence_pedals(ev,.8,normalize=False)
                b=render_sequence_v8_coeff(ev,.8,normalize=False)
                e=np.linalg.norm(a.astype(float)-b.astype(float))/max(np.linalg.norm(a),1e-15)
                self.assertLess(e,1e-7)

    def test_dynamic_increases_unormalized_amplitude(self):
        ev=lambda v:[(0.,69,.5,v)]
        rms=[]
        for v in (20,50,80,110):
            x=render_sequence_v8_coeff(ev(v),.7,normalize=False)
            rms.append(np.sqrt(np.mean(x[1000:14000].astype(float)**2)))
        self.assertTrue(all(a<b for a,b in zip(rms,rms[1:])),rms)

    def test_deterministic(self):
        b=render_sequence_v8_coeff(self.ev,1.18,normalize=False,pedal_events=self.pedal)
        np.testing.assert_array_equal(self.fast,b)

    def test_no_recordings_or_reverb_in_v8_engine(self):
        import stage_synth_c3x.optimized_coeff as mod
        s=inspect.getsource(mod)
        self.assertNotIn('sf.read(',s)
        self.assertNotIn('librosa.load(',s)
        self.assertNotIn('room_ir(',s)

if __name__=='__main__':unittest.main()
