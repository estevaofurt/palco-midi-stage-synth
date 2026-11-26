import unittest
import numpy as np
from residual_poles import pole_data
class PoleTest(unittest.TestCase):
    def test_single_oscillator(self):
        r=48000;w=2*np.pi*1800;d=2.
        p,z,U,V,om,e=pole_data(np.eye(1),np.array([[w*w]]),np.array([[d]]),r)
        expected=-1+1j*np.sqrt(w*w-1)
        self.assertLess(abs(p[0]-expected)/w,1e-12)
        self.assertLess(abs(z[0]-(1+expected/(2*r))/(1-expected/(2*r))),1e-12)
        self.assertLess(e,1e-10)
        self.assertLess(abs(z[0]),1.)
if __name__=='__main__':unittest.main()
