import unittest
import numpy as np
from g2_c5_analysis import measure, onset
class Test(unittest.TestCase):
    def test_stereo_antiphase(self):
        fs=48000;t=np.arange(fs*2)/fs
        s=.1*np.sin(2*np.pi*261.625565*t)+.05*np.sin(2*np.pi*523.25113*t)
        y=np.column_stack([s,-s]); r=measure(y,fs,60)
        self.assertAlmostEqual(r["windows"]["0.25-0.75"]["partial_band_relative_db"][1],-6.02,delta=.3)
        self.assertTrue(all(np.isfinite(r["windows"]["0.25-0.75"]["band_power_pct"])))
    def test_silence(self):
        with self.assertRaises(ValueError):onset(np.zeros((48000,2)),48000)
    def test_onset(self):
        y=np.zeros((48000,2)); y[4800:]=.1
        self.assertEqual(onset(y,48000),4800)
if __name__=="__main__":unittest.main()
