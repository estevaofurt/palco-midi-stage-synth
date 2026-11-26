import unittest
import numpy as np
from acoustic_cq_surface import ProjectedLoad,cq,passivity
from retarded_surface import impedance
class ProjectedTest(unittest.TestCase):
    def test_correlation(self):
        B=np.random.default_rng(5).normal(size=(3,3,2))
        L=ProjectedLoad(B,.02,.03)
        for s in (2j*np.pi*150,1000+2000j):
            np.testing.assert_allclose(L(s),impedance(B,.02,.03,s),rtol=1e-11,atol=1e-8)
    def test_cq(self):
        w,e=cq(lambda s:np.array([[s]]),48000,128)
        np.testing.assert_allclose(w[:3,0,0],[72000.,-96000.,24000.],rtol=1e-10)
        self.assertLess(e,1e-10)
    def test_dc_scale(self):
        z=np.array([[[1e-12]],[[1.]],[[2.]]])
        self.assertEqual(passivity(z)['minimumLocalNonDC'],1.)
if __name__=='__main__':unittest.main()
