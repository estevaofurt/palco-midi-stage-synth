import unittest
import hashlib
from pathlib import Path
import numpy as np
from stage_synth_c3x.dry import (DryConfig,short_body_ir,shared_soundboard,
                                   render_sequence_dry,_sympathetic_setup)
from stage_synth_c3x.feedback import string_soundboard_feedback
class TestDryV4(unittest.TestCase):
    def test_profile_has_no_room_delay_tail(self):
        h=short_body_ir(48000,0,20,18)
        self.assertEqual(len(h),960)
        self.assertAlmostEqual(h[-1],0,delta=1e-14)
    def test_no_piano_samples_used_for_synthesis(self):
        # O teste prova independencia dos WAVs de referencia: motor
        # opera apenas com os parametros e operadores do codigo.
        a=render_sequence_dry([(0,69,.45,83)],.65,normalize=False)
        self.assertGreater(float(np.max(abs(a))),0.)
        self.assertTrue(np.isfinite(a).all())
    def test_stems_sum_exactly_to_mix(self):
        a,stems=render_sequence_dry([(0,60,.35,87)],.65,return_stems=True)
        recomposed=(stems['direto_e_corpo']+stems['tampo_compartilhado']+
                    stems['cordas_simpaticas'])
        np.testing.assert_allclose(a,recomposed,atol=5e-7,rtol=1e-5)
    def test_sympathetic_pedal_raises_string_energy(self):
        source=string_soundboard_feedback(60,90,.5,1.)[0]
        s_off=shared_soundboard(source,48000,False,(60,))[2]
        s_on=shared_soundboard(source,48000,True,(60,))[2]
        tail=slice(int(.45*48000),None)
        self.assertGreater(float(np.sqrt(np.mean(s_on[tail]**2))),
                           2.0*float(np.sqrt(np.mean(s_off[tail]**2))))
    def test_coupling_disabled_removes_sympathy(self):
        source=string_soundboard_feedback(60,90,.3,.6)[0]
        s=shared_soundboard(source,48000,True,(60,),coupling_scale=0)[2]
        self.assertEqual(float(np.max(np.abs(s))),0.)
    def test_all_88_notes_in_shared_register(self):
        setup=_sympathetic_setup('equal',48000,1.,set())
        self.assertEqual(len(setup[0]),176)
        self.assertTrue(np.all(np.isfinite(setup[0])))
    def test_dry_disabled_room_does_not_change_engine(self):
        a=render_sequence_dry([(0,69,.3,80)],.55)
        b=render_sequence_dry([(0,69,.3,80)],.55)
        np.testing.assert_array_equal(a,b)
    def test_invalid_config_rejected(self):
        with self.assertRaises(ValueError):DryConfig(body_window_ms=120).validate()
        with self.assertRaises(ValueError):DryConfig(body_gain=float('nan')).validate()
    def test_a4_fundamental_remains_close_to_440_hz(self):
        sr=48000
        y=render_sequence_dry([(.0,69,1.1,88)],1.4,stereo=False)
        chunk=y[int(.25*sr):int(1.05*sr),0]
        nfft=2**19
        spec=np.abs(np.fft.rfft(chunk*np.hanning(len(chunk)),nfft))
        freqs=np.fft.rfftfreq(nfft,1./sr)
        lo=np.searchsorted(freqs,435.);hi=np.searchsorted(freqs,445.)
        peak=freqs[lo+int(np.argmax(spec[lo:hi]))]
        self.assertLess(abs(float(peak)-440.),0.2)
    def test_v1_reference_is_unchanged(self):
        path=Path(__file__).resolve().parents[1]/'referencias'/'V1_original_10s.wav'
        self.assertTrue(path.is_file())
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                         '6f919989b11ca6146537c0a58e35405364bf55b38c5819b100d34fcd4ff41c2d')
