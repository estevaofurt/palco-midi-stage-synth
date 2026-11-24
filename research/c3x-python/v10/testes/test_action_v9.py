"""Validação V9: ação, repetição e regressão acústica V8."""
import unittest
import numpy as np
from stage_synth_c3x.action import (GrandActionConfig,schedule_grand_action,
                                    _hammer_speed)
from stage_synth_c3x.action_engine import (_build_v9_bank,
                                           render_sequence_v9_action)
from stage_synth_c3x.optimized_coeff import (render_sequence_v8_coeff,
                                             polarization_preset)


class ActionUnitTests(unittest.TestCase):
    def test_invalid_mechanical_constants(self):
        with self.assertRaises(ValueError):GrandActionConfig(let_off_gap_mm=-.1).validate()
        with self.assertRaises(ValueError):GrandActionConfig(felt_rate_exponent=.5).validate()

    def test_bad_events(self):
        for ev in [(-.1,69,.1,80),(0.,200,.1,80),(0.,69,-1,80),(0.,69,.1,0)]:
            with self.subTest(ev=ev),self.assertRaises(ValueError):
                schedule_grand_action([ev],1.)

    def test_key_velocity_order(self):
        vel=[];onset=[]
        for v in [20,50,80,110]:
            ev,_=schedule_grand_action([(0.,69,.2,v)],1.)
            vel.append(_hammer_speed(ev[0][3]))
            onset.append(ev[0][0])
        self.assertEqual(vel,sorted(vel))
        self.assertEqual(onset,sorted(onset,reverse=True))

    def test_repetition_double_faster_than_single(self):
        ev=[(0.,69,.08,80),(.085,69,.06,88)]
        d,detail_d=schedule_grand_action(ev,.5,mode='double')
        s,detail_s=schedule_grand_action(ev,.5,mode='single')
        self.assertLess(d[1][0],s[1][0])
        self.assertGreater(detail_s[1]['rearm_wait_ms'],detail_d[1]['rearm_wait_ms'])

    def test_bypass_exact_events(self):
        src=[(0.,69,.1,100),(.14,69,.1,90)]
        ev,_=schedule_grand_action(src,.6,bypass=True)
        self.assertEqual(ev,src)

    def test_action_is_deterministic(self):
        ev=[(0.,64,.1,80),(.15,64,.1,80)]
        self.assertEqual(schedule_grand_action(ev,1.),schedule_grand_action(ev,1.))

    def test_speed_preservation(self):
        for v in [1,40,80,127]:
            a,_=schedule_grand_action([(0,69,.4,v)],1.)
            self.assertGreaterEqual(a[0][3],1)
            self.assertLessEqual(a[0][3],127)


class PhysicsV9Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=[(0.,69,.2,78),(.31,69,.2,96),(.62,69,.2,110)]
        cls.a,cls.da=render_sequence_v9_action(cls.e,1.05,fs=24000,
            return_diagnostics=True,normalize=False)

    def test_repetition_reuses_physical_strings(self):
        sch,_=schedule_grand_action(self.e,1.05)
        bank,indices,counts=_build_v9_bank(sch,1.05,24000,polarization_preset())
        self.assertEqual(len(np.unique(indices[indices>=0])),3)
        self.assertTrue(np.all(indices[0]==indices[1]))
        self.assertTrue(np.all(indices[1]==indices[2]))
        self.assertEqual(self.da['unique_key_count'],1)
        self.assertEqual(self.da['strike_count'],3)

    def test_repeated_strikes_finite(self):
        self.assertTrue(np.isfinite(self.a).all())
        self.assertGreater(np.max(abs(self.a)),.001)

    def test_bypass_matches_v8_single(self):
        for pitch in (48,69,86):
            with self.subTest(pitch=pitch):
                ev=[(.01,pitch,.28,92)]
                a=render_sequence_v9_action(ev,.46,fs=24000,
                                             normalize=False,bypass_action=True)
                b=render_sequence_v8_coeff(ev,.46,fs=24000,normalize=False)
                np.testing.assert_array_equal(a,b)

    def test_bypass_matches_v8_chord(self):
        ev=[(0.,60,.4,80),(.02,64,.4,87),(.04,67,.4,92)]
        a=render_sequence_v9_action(ev,.75,fs=24000,normalize=False,bypass_action=True,
                                      pedal_initial=.4)
        b=render_sequence_v8_coeff(ev,.75,fs=24000,normalize=False,pedal_initial=.4)
        np.testing.assert_array_equal(a,b)

    def test_double_and_single_change_repetition_timing(self):
        ev=[(0.,69,.07,88),(.075,69,.12,92)]
        a,d=render_sequence_v9_action(ev,.50,fs=24000,action_mode='double',
                                      normalize=False,return_diagnostics=True)
        b,e=render_sequence_v9_action(ev,.50,fs=24000,action_mode='single',
                                      normalize=False,return_diagnostics=True)
        self.assertLess(d['action_events'][1]['strike_at_s'],e['action_events'][1]['strike_at_s'])
        self.assertGreater(np.linalg.norm(a-b),0.)

    def test_pedal_changes_sustain(self):
        ev=[(0.,69,.2,90)]
        dry=render_sequence_v9_action(ev,.85,fs=24000,normalize=False)
        pedal=render_sequence_v9_action(ev,.85,fs=24000,normalize=False,pedal_initial=1.)
        self.assertGreater(np.linalg.norm(pedal[15000:]),np.linalg.norm(dry[15000:]))

    def test_no_ambient_effects_or_samples(self):
        import inspect,stage_synth_c3x.action_engine as module
        source=inspect.getsource(module)
        self.assertNotIn('sf.read(',source)
        self.assertNotIn('room_ir(',source)
        self.assertNotIn('librosa.load(',source)


if __name__=='__main__':unittest.main()
