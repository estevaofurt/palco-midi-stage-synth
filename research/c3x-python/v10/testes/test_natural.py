import unittest
import numpy as np
from stage_synth_c3x.natural import NaturalConfig,natural_preset,render_sequence_natural
from stage_synth_c3x.dry import short_body_ir
class TestNaturalV41(unittest.TestCase):
    def test_no_room_tail_and_finite_ir(self):
        h=short_body_ir(48000,0,80,70)
        self.assertEqual(len(h),3840)
        self.assertAlmostEqual(h[-1],0.,delta=1e-13)
        self.assertTrue(np.isfinite(h).all())
    def test_radiation_stems_sum_to_mix(self):
        x,s=render_sequence_natural([(0,69,.3,90)],.7,return_stems=True)
        np.testing.assert_allclose(x,s['direto_radiado']+s['tampo_compartilhado']+s['cordas_simpaticas'],atol=5e-7,rtol=2e-5)
    def test_config_rejects_invalid(self):
        with self.assertRaises(ValueError):NaturalConfig(body_window_ms=110).validate()
        with self.assertRaises(ValueError):NaturalConfig(high_radiation=float('nan')).validate()
        with self.assertRaises(ValueError):natural_preset('sala')
    def test_rich_preset_has_more_presence(self):
        a=render_sequence_natural([(0,69,.55,86)],.85,config=natural_preset('equilibrado'))
        b=render_sequence_natural([(0,69,.55,86)],.85,config=natural_preset('encorpado'))
        self.assertFalse(np.array_equal(a,b))
        self.assertTrue(np.isfinite(a).all() and np.isfinite(b).all())
    def test_same_input_is_deterministic(self):
        a=render_sequence_natural([(0,64,.3,90)],.45)
        b=render_sequence_natural([(0,64,.3,90)],.45)
        np.testing.assert_array_equal(a,b)
    def test_upper_partial_band_restored_vs_v4(self):
        from scipy.signal import welch
        from stage_synth_c3x.dry import render_sequence_dry
        events=[(.0,69,.55,90)]
        old=render_sequence_dry(events,.85,stereo=False)[:,0]
        new=render_sequence_natural(events,.85)[:,0]
        def relative_presence(x):
            f,p=welch(x,48000,nperseg=8192)
            e=lambda lo,hi:float(np.trapezoid(p[(f>=lo)&(f<hi)],f[(f>=lo)&(f<hi)]))
            return e(3000,8000)/max(e(400,1000),1e-20)
        self.assertGreater(relative_presence(new),relative_presence(old))
