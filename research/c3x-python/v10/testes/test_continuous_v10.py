"""Testes da ação contínua V10, além das regressões V9/V8."""
import unittest
import inspect
import numpy as np
from stage_synth_c3x.continuous_action import (ContinuousActionConfig,
    schedule_continuous_action)
from stage_synth_c3x.continuous_engine import render_sequence_v10_action
from stage_synth_c3x.action_engine import render_sequence_v9_action

KEYFRAMES=[(.02,69,1.,90),(.12,69,.45,0),(.16,69,1.,99),
           (.26,69,.45,0),(.30,69,1.,105),(.40,69,0.,0)]

class ScheduleV10Tests(unittest.TestCase):
    def test_config_invalid(self):
        for c in (ContinuousActionConfig(double_reset_fraction=.95),
                  ContinuousActionConfig(simulation_hz=10),
                  ContinuousActionConfig(key_dip_mm=float('nan'))):
            with self.assertRaises(ValueError):c.validate()

    def test_invalid_commands(self):
        for cs in [[(-.1,69,.1,90)],[(0,110,.1,90)],[(0,69,-.1,90)],[(0,69,.1,200)]]:
            with self.assertRaises(ValueError):schedule_continuous_action(cs,1.)
        with self.assertRaises(ValueError):schedule_continuous_action([],1.,keyframes=[(0,69,1.1,80)])

    def test_normal_note_strikes_once(self):
        ev,info=schedule_continuous_action([(.05,69,.2,85)],.7)
        self.assertEqual(len(ev),1)
        self.assertGreater(ev[0][0],.05)
        self.assertEqual(info['blocked_count'],0)

    def test_shallow_press_does_not_trigger_hammer(self):
        ev,diag=schedule_continuous_action([],1.,keyframes=[(.1,69,.5,90),(.3,69,0.,0)])
        self.assertEqual(ev,[])
        self.assertEqual(diag['strike_count'],0)

    def test_partial_key_release_enables_double_repetition(self):
        d,diag=schedule_continuous_action([],1.,keyframes=KEYFRAMES,mode='double')
        s,_=schedule_continuous_action([],1.,keyframes=KEYFRAMES,mode='single')
        self.assertEqual(len(d),3)
        self.assertEqual(len(s),1)
        self.assertEqual(diag['unique_key_count'],1)

    def test_no_restrike_if_key_does_not_release(self):
        keys=[(.02,69,1.,93),(.15,69,.70,0),(.19,69,1.,110),(.3,69,0.,0)]
        s,diag=schedule_continuous_action([],1.,keyframes=keys)
        self.assertEqual(len(s),1)
        self.assertGreaterEqual(diag['blocked_count'],1)

    def test_higher_velocity_faster_and_harder(self):
        slow,_=schedule_continuous_action([(.05,69,.3,35)],1.)
        fast,_=schedule_continuous_action([(.05,69,.3,113)],1.)
        self.assertGreater(slow[0][0],fast[0][0])
        self.assertLess(slow[0][3],fast[0][3])

    def test_deterministic(self):
        e=[(.04,60,.22,80),(.26,60,.21,100)]
        self.assertEqual(schedule_continuous_action(e,1.),schedule_continuous_action(e,1.))

    def test_rearm_threshold_mode_difference(self):
        cfg=ContinuousActionConfig(double_reset_fraction=.54,single_reset_fraction=.13)
        d,_=schedule_continuous_action([],1.,keyframes=KEYFRAMES,mode='double',config=cfg)
        s,_=schedule_continuous_action([],1.,keyframes=KEYFRAMES,mode='single',config=cfg)
        self.assertEqual(len(d)-len(s),2)

    def test_trace_retained(self):
        _,diag=schedule_continuous_action([(.02,69,.3,80)],.55,include_trajectories=True)
        pos=diag['key_trajectories'][69]
        self.assertGreater(len(pos),40)
        self.assertLessEqual(max(x[1] for x in pos),1.)

class AudioV10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.event=[(.02,69,.34,91)]
        cls.v10,cls.diag=render_sequence_v10_action(cls.event,.68,fs=24000,
             normalize=False,return_diagnostics=True)

    def test_finite_nonzero_and_stereo(self):
        self.assertEqual(self.v10.shape,(round(.68*24000),2))
        self.assertTrue(np.isfinite(self.v10).all())
        self.assertGreater(float(np.max(abs(self.v10))),1e-5)

    def test_v9_bypass_exact(self):
        e=[(.02,60,.21,80),(.06,64,.22,85),(.10,67,.20,90)]
        a=render_sequence_v10_action(e,.48,fs=24000,
               bypass_continuous=True,normalize=False)
        b=render_sequence_v9_action(e,.48,fs=24000,normalize=False)
        np.testing.assert_array_equal(a,b)

    def test_keyframe_repeated_strikes_sound(self):
        sound,diag=render_sequence_v10_action([], .54,fs=24000,
            keyframes=KEYFRAMES,return_diagnostics=True,normalize=False)
        self.assertEqual(diag['strike_count'],3)
        self.assertTrue(np.isfinite(sound).all())
        self.assertGreater(float(np.linalg.norm(sound)),.01)

    def test_keyframe_shallow_is_silent(self):
        snd=render_sequence_v10_action([], .5,fs=24000,
            keyframes=[(.01,69,.5,80),(.25,69,0.,0)])
        self.assertEqual(int(np.count_nonzero(snd)),0)

    def test_dynamics(self):
        arr=[]
        for v in (25,60,100):
            snd=render_sequence_v10_action([(.02,69,.43,v)],.65,fs=24000,
                 normalize=False)
            arr.append(float(np.linalg.norm(snd)))
        self.assertTrue(all(b>a for a,b in zip(arr,arr[1:])))

    def test_dry_no_samples(self):
        import stage_synth_c3x.continuous_engine as m
        src=inspect.getsource(m)
        for token in ('sf.read(', 'librosa.load(', 'room_ir(', 'convolve_room'):
            self.assertNotIn(token,src)

    def test_pedal_still_sustains(self):
        e=[(.04,69,.16,96)]
        a=render_sequence_v10_action(e,.8,fs=24000,normalize=False)
        b=render_sequence_v10_action(e,.8,fs=24000,normalize=False,pedal_initial=1.)
        self.assertGreater(np.linalg.norm(b[13000:]),np.linalg.norm(a[13000:]))

if __name__=='__main__':unittest.main()