import unittest
import numpy as np
from stage_synth_c3x import note_params,render_note,render_sequence

class TestPhysicalModel(unittest.TestCase):
    def test_88_keys(self):
        p=[note_params(n) for n in range(21,109)]
        self.assertEqual(len(p),88)
        self.assertEqual(p[0].nota,'A0')
        self.assertEqual(p[-1].nota,'C8')
        self.assertTrue(all(q.comprimento_vibrante_m>0 for q in p))
        self.assertTrue(all(q.inarmonicidade_b>0 for q in p))
        self.assertTrue(all('NAO medida' in q.origem for q in p))
    def test_a4_frequency(self):
        self.assertAlmostEqual(note_params(69).frequencia_hz,440.0,places=6)
    def test_no_clipping_sequence(self):
        y=render_sequence([(0,69,.3,60),(.15,72,.3,100)],1.2,stereo=False)
        self.assertTrue(np.isfinite(y).all())
        self.assertLess(np.max(abs(y)),.90)
        self.assertGreater(np.max(abs(y)),.01)
    def test_velocity_changes_waveform(self):
        quiet=render_note(69,40,.5,.8,stereo=False)
        loud=render_note(69,115,.5,.8,stereo=False)
        self.assertGreater(np.max(abs(loud)),np.max(abs(quiet)))
        self.assertGreater(np.sqrt(np.mean(loud*loud)),np.sqrt(np.mean(quiet*quiet)))

if __name__=='__main__':unittest.main()
