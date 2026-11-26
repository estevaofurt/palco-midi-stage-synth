import unittest
import numpy as np
from physical_acoustic_long import validate_coordinates,thresholds,RATE
from spectral_tail_audit import analyze
class PhysicalLongTest(unittest.TestCase):
    def test_basis(self):
        x=np.eye(3)
        self.assertEqual(validate_coordinates(dict(x=x),dict(x=x))['x'],0.)
        with self.assertRaises(ValueError):validate_coordinates(dict(x=x),dict(x=-x))
    def test_censored(self):
        t=np.arange(10*RATE)/RATE;y=np.sin(2*np.pi*261.63*t)[:,None]*np.array([[1.,.5]])
        r=thresholds(y,analyze(y,RATE,60))
        self.assertTrue(r['common'][0]['fundamental']['-60']['rightCensored'])
if __name__=='__main__':unittest.main()
