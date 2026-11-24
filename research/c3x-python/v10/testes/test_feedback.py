import unittest
import numpy as np
from stage_synth_c3x.feedback import (FeedbackConfig,string_soundboard_feedback,
    render_note_feedback,render_sequence_feedback)
class TestFeedback(unittest.TestCase):
    def test_board_reacts_only_when_mechanically_coupled(self):
        on=string_soundboard_feedback(69,90,0.4,0.65)
        off=string_soundboard_feedback(69,90,0.4,0.65,config=FeedbackConfig(
            bridge_stiffness_N_m=0,bridge_damping_Ns_m=0))
        self.assertEqual(float(np.max(np.abs(off[1]))),0.)
        self.assertGreater(float(np.max(np.abs(on[1]))),1e-12)
        self.assertGreater(float(np.max(np.abs(on[0]-off[0]))),1e-10)
    def test_88_notes_stable(self):
        for n in range(21,109):
            traces=string_soundboard_feedback(n,83,0.03,0.06)
            self.assertTrue(all(np.isfinite(x).all() for x in traces),(n,'not finite'))
            self.assertGreater(float(np.max(np.abs(traces[0]))),0,n)
    def test_midi_velocity_affects_energy(self):
        soft=render_note_feedback(69,45,.3,.5,stereo=False)
        strong=render_note_feedback(69,110,.3,.5,stereo=False)
        self.assertGreater(np.sqrt(np.mean(strong**2)),np.sqrt(np.mean(soft**2)))
    def test_damper(self):
        a=string_soundboard_feedback(69,90,.19,.5,pedal_down=False)[0]
        b=string_soundboard_feedback(69,90,.19,.5,pedal_down=True)[0]
        self.assertLess(np.sqrt(np.mean(a[int(.35*48000):]**2)),
                        .1*np.sqrt(np.mean(b[int(.35*48000):]**2)))
    def test_loaded_pitch_correction_a4(self):
        # Ponto de validação: frequência medida nos modos de corda,
        # não a frequência escrita em uma tabela de parâmetros.
        import math
        from scipy.signal import find_peaks
        def pitch(config):
            sr=48000
            x=string_soundboard_feedback(69,90,.9,.9,config=config)[0]
            chunk=x[int(.13*sr):int(.85*sr)]
            nfft=2**19
            spectrum=np.abs(np.fft.rfft(chunk*np.hanning(len(chunk)),nfft))
            f=np.fft.rfftfreq(nfft,1/sr)
            lo=np.searchsorted(f,435);hi=np.searchsorted(f,445)
            k=np.argmax(spectrum[lo:hi])+lo
            y=np.log(np.maximum(spectrum[k-1:k+2],1e-300))
            step=.5*(y[0]-y[2])/(y[0]-2*y[1]+y[2])
            return (k+step)*sr/nfft
        corrected=pitch(FeedbackConfig(compensate_bridge_pitch=True))
        uncorrected=pitch(FeedbackConfig(compensate_bridge_pitch=False))
        self.assertLess(abs(1200*math.log2(corrected/440)),.2)
        self.assertGreater(abs(1200*math.log2(uncorrected/440)),.35)

    def test_render_modes_and_checks(self):
        x=render_sequence_feedback([(0,69,.3,80)],.6,stereo=True)
        self.assertEqual(x.shape,(28800,2))
        self.assertLess(float(np.max(np.abs(x))),.90)
        y=render_note_feedback(69,90,.3,.6,stereo=False,radiation='board_only')
        self.assertTrue(np.isfinite(y).all())
        with self.assertRaises(ValueError):render_note_feedback(69,radiation='invalid')
