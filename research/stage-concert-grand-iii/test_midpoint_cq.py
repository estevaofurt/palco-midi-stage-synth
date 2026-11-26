import unittest
import numpy as np
from midpoint_cq import symbol,simulate
class MidpointCQTest(unittest.TestCase):
    def test_symbol(self):
        z=.999*np.exp(2j*np.pi*np.arange(1024)/1024)
        self.assertGreater(symbol(z,48000).real.min(),0.)
        with self.assertRaises(ValueError):symbol(-1,48000)
    def test_coupling(self):
        r=simulate(48000,512,256)
        self.assertTrue(r['screeningGate'],r)
if __name__=='__main__':unittest.main()
