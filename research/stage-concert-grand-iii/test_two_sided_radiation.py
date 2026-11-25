import unittest
import numpy as np
from two_sided_radiation import combine,fixture
class TwoSidedTest(unittest.TestCase):
    def test_mirror_load_doubles_not_cancels(self):
        z=np.array([[2+3j,.2j],[.2j,3+4j]]);I=np.eye(2)
        q,parts,r=combine(z,z,I,-I)
        np.testing.assert_allclose(q,2*z)
        self.assertTrue(r['gate'])
        V,r=fixture(I,1e5*I,.4*I,q,parts,60.)
        self.assertTrue(r['gate'],r)
        self.assertAlmostEqual(r['powerFractions']['upper'],r['powerFractions']['lower'])
        self.assertAlmostEqual(sum(r['powerFractions'].values()),1.)
    def test_distinct_maps(self):
        u=np.array([[1.,2.]]);l=np.array([[-2.,1.]])
        z,_,r=combine(np.array([[2+1j]]),np.array([[3+2j]]),u,l)
        np.testing.assert_allclose(z,(2+1j)*u.T@u+(3+2j)*l.T@l)
        self.assertTrue(r['gate'])
    def test_reject_active_and_nonreciprocal(self):
        I=np.eye(2)
        for z in (-I,np.array([[1.,.2],[0.,1.]])):
            with self.assertRaises(ValueError):combine(I,z,I,I)
if __name__=='__main__':unittest.main()
