import unittest
import numpy as np
from passive_midpoint import MidpointLoad,energy_probe,harmonic_probe
class MidpointTest(unittest.TestCase):
    def test_energy(self):
        C=np.array([np.eye(2)*.2,np.eye(2)*.03,np.eye(2)*40.,[[2.,1.],[1.,2.]]])
        self.assertTrue(energy_probe(C,[80.],10.,8000)['gate'])
    def test_harmonic(self):
        C=np.array([np.eye(2)*.2,np.eye(2)*.001,np.eye(2)*40.,[[20.,10.],[10.,20.]]])
        self.assertTrue(harmonic_probe(C,[80.],10.,8000,70.)['gate'])
    def test_negative(self):
        C=np.array([np.eye(2),-np.eye(2),np.eye(2),np.eye(2)])
        with self.assertRaises(ValueError):MidpointLoad(C,[80.],10.,8000)
    def test_zero(self):
        a=MidpointLoad(np.zeros((4,2,2)),[80.],10.,8000)
        f,w,l=a.step(np.ones(2));np.testing.assert_array_equal(f,np.zeros(2))
        self.assertEqual((w,l,a.storage()),(0.,0.,0.))
if __name__=='__main__':unittest.main()
