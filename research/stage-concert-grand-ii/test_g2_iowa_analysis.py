import unittest
import numpy as np
from g2_iowa_analysis import adapt
from g2_c5_analysis import measure
class Iowa(unittest.TestCase):
    def test_mono(self):
        fs=44100;t=np.arange(fs*2)/fs
        x=(.1*np.sin(2*np.pi*261.625565*t)+.05*np.sin(2*np.pi*523.25113*t))[:,None]
        y=adapt(x,fs)
        self.assertEqual(y.shape,(96000,2))
        self.assertTrue(np.array_equal(y[:,0],y[:,1]))
        self.assertAlmostEqual(measure(y,48000,60)["windows"]["0.25-0.75"]["partial_band_relative_db"][1],-6.02,delta=.3)
    def test_reject(self):
        with self.assertRaises(ValueError):adapt(np.zeros((100,3)),44100)
if __name__=="__main__":unittest.main()
