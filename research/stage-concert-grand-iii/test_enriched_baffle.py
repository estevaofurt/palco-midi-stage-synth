import unittest
import numpy as np
from enriched_baffle import resistance,harmonic
from radiation_resistance import angular,surface
from ribbed_plate import quadrature
class EnrichedBaffleTest(unittest.TestCase):
    def test_gram(self):
        xy,w=quadrature(np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]]),8)
        S=np.column_stack([np.ones(len(xy)),xy[:,0]-.5])
        R,a=resistance(xy,w,S,150.,16)
        np.testing.assert_allclose(R,angular(xy,w,S,150.,1.204,343.,16),rtol=1e-10,atol=1e-12)
        np.testing.assert_allclose(R,surface(xy,w,S,150.,1.204,343.),rtol=1e-8,atol=1e-10)
        self.assertGreaterEqual(a['passivityMinRelative'],-1e-10)
    def test_power(self):
        k=np.array([100.,200.]);D=np.eye(2);P=np.eye(2);A=np.array([[1.,.3],[.2,1.]])
        Y,O,a=harmonic(k,D,P,A,np.eye(2),np.eye(2),10.)
        self.assertLess(a['powerRelative'],1e-10)
        self.assertTrue(0<a['airFraction']<1)
if __name__=='__main__':unittest.main()
