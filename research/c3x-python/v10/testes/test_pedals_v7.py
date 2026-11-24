"""Regressões de contato gradual, pedal contínuo e motor dry V7."""
import unittest
import inspect
import numpy as np
from stage_synth_c3x.pedals import (DamperConfig, render_sequence_pedals,
                                      _pedal_events_to_arrays)

SR=48000

def rms(x, t0, t1):
    seg=np.asarray(x)[int(t0*SR):int(t1*SR)]
    return float(np.sqrt(np.mean(seg.astype(np.float64)**2)))

class TestDamperMechanicsV7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.event=[(0.,69,.27,86)]
        cls.off=render_sequence_pedals(cls.event,1.2,normalize=False)
        cls.mid=render_sequence_pedals(cls.event,1.2,pedal_initial=.5,normalize=False)
        cls.on=render_sequence_pedals(cls.event,1.2,pedal_initial=1.,normalize=False)

    def test_pedal_scale_continuous_effect(self):
        a,b,c=[rms(x,.73,1.) for x in (self.off,self.mid,self.on)]
        self.assertLess(a,b)
        self.assertLess(b,c)
        self.assertGreater(b,a*10.)

    def test_release_is_not_instantaneous(self):
        # A cauda permanece por um intervalo curto após key-off.
        x=self.off
        before=rms(x,.242,.268)
        just_after=rms(x,.278,.300)
        late=rms(x,.7,.8)
        self.assertGreater(just_after,late)
        self.assertGreater(just_after,before*.08)

    def test_pedal_down_after_attack_changes_tail(self):
        x=render_sequence_pedals(self.event,1.2,pedal_events=[(.13,1.)],normalize=False)
        self.assertGreater(rms(x,.7,.9),rms(self.off,.7,.9)*1.4)

    def test_pedal_up_after_release_damps_tail(self):
        x=render_sequence_pedals(self.event,1.2,pedal_initial=1.,
                                  pedal_events=[(.6,0.)],normalize=False)
        self.assertLess(rms(x,.95,1.1),rms(self.on,.95,1.1)*.6)

    def test_causal_event_future_does_not_change_past(self):
        x=render_sequence_pedals(self.event,1.2,pedal_events=[(.8,1.)],normalize=False)
        np.testing.assert_allclose(self.off[:int(.65*SR)],x[:int(.65*SR)],rtol=1e-5,atol=2e-10)

    def test_determinism(self):
        again=render_sequence_pedals(self.event,1.2,pedal_initial=.5,normalize=False)
        np.testing.assert_array_equal(self.mid,again)

    def test_stems_and_finite(self):
        x,st=render_sequence_pedals(self.event,1.1,return_stems=True)
        self.assertTrue(np.isfinite(x).all())
        self.assertEqual(x.shape,(52800,2))
        self.assertLessEqual(abs(x).max(),.841)
        np.testing.assert_allclose(x,st['direto']+st['corpo']+st['tampo'],atol=4e-6)

    def test_pedal_diagnostics(self):
        _,d=render_sequence_pedals(self.event,1.0,pedal_events=[(.1,1.),(.7,0.)],return_diagnostics=True)
        self.assertLess(d['pedal_final'],.01)
        self.assertGreater(d['abafador_final'],.90)
        self.assertGreater(float(np.max(d['pedal_trace_100hz'])),.99)

    def test_midi_cc64_conversion(self):
        from stage_synth_c3x.pedals import cc64_to_pedal_events
        self.assertEqual(cc64_to_pedal_events([(0,0),(.5,64),(1.,127)]),
                         [(0.,0.),(.5,64/127.),(1.,1.)])
        with self.assertRaises(ValueError):cc64_to_pedal_events([(.5,200)])
        with self.assertRaises(ValueError):cc64_to_pedal_events([(.5,64),(.2,80)])

    def test_input_validation(self):
        for p in [-.1,1.1,float('nan')]:
            with self.assertRaises(ValueError):render_sequence_pedals(self.event,.6,pedal_initial=p)
        for evs in [[(0.1,-.1)],[(.6,1.),(.3,0.)],[(.2,float('nan'))],[(.3,.5,.6)]]:
            with self.assertRaises(ValueError):render_sequence_pedals(self.event,.7,pedal_events=evs)
        for d in (DamperConfig(pedal_raise_ms=0),DamperConfig(partial_contact_exponent=7)):
            with self.assertRaises(ValueError):d.validate()

    def test_no_sample_or_reverb_code(self):
        import stage_synth_c3x.pedals as m
        s=inspect.getsource(m)
        self.assertNotIn('sf.read(',s)
        self.assertNotIn('librosa.load(',s)
        self.assertNotIn('reverb(',s)
        self.assertNotIn('room_ir(',s)

if __name__=='__main__':unittest.main()