import unittest
import numpy as np
from spectral_tail_audit import analyze,new_cases
class TailTest(unittest.TestCase):
    def test_harmonic_takeover(self):
        rate=8000;t=np.arange(12*rate)/rate;f=440*2**(-9/12)
        x=np.sin(2*np.pi*f*t)*np.exp(-t)+.05*np.sin(2*np.pi*1838*t)*np.exp(-t/10)
        a=analyze(np.stack([x,x],axis=1),rate,60)
        self.assertTrue(a['upperDominanceDetected'])
        self.assertLess(a['channels'][0]['windows'][0]['fraction1838'],.03)
        self.assertGreater(a['channels'][0]['windows'][7]['fraction1838'],.9)
        self.assertEqual(a['channels'][0]['windows'][7]['dominantHz'],1838.)
    def test_cases(self):
        self.assertEqual(len(new_cases('held_no_pedal')),4)
        self.assertEqual(len(new_cases('45')),4)
if __name__=='__main__':unittest.main()
