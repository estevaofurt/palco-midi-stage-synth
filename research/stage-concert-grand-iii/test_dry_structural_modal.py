import unittest
import numpy as np
from dry_structural_modal import projection,mobility,compare,patch_projection
from spline_plate import LocalBasis
class DryModalTest(unittest.TestCase):
    def test_projection(self):
        x=np.linspace(-1,1,31);F=np.column_stack((np.ones(31),x))
        C=np.array([[1.,2.],[3.,4.]])
        A,r=projection(F,F@C,np.ones(31))
        np.testing.assert_allclose(A,C,atol=1e-12);self.assertLess(r['maximumModeResidual'],1e-12)
    def test_unrepresented_field(self):
        x=np.linspace(-1,1,31);F=np.ones((31,1))
        _,r=projection(F,x[:,None],np.ones(31))
        self.assertGreater(r['maximumModeResidual'],.99)
    def test_knot_aligned(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
        b=LocalBasis(poly,3,False)
        def field(xy):
            x,y=xy.T
            return np.column_stack((1+2*x-3*y+x*y, np.maximum(x-1/3,0)**3))
        A,r=patch_projection(b,field,poly,8)
        B,s=patch_projection(b,field,poly,12)
        np.testing.assert_allclose(A,B,atol=1e-12)
        self.assertAlmostEqual(r['quadratureAreaM2'],1.,places=12)
        self.assertAlmostEqual(r['capturedEnergyByMode'][0],1.,places=12)
        self.assertGreater(r['maximumModeResidual'],.01)
    def test_damping(self):
        k=np.array([100.,300.]);D=np.array([[2.,1.],[1.,3.]]);P=np.eye(2);f=[1.,2.,3.]
        ref=mobility(k,D,P,f);r=compare(f,k,D,P,ref)
        self.assertEqual(r['maximumReferenceRelative'],0.)
        self.assertGreater(r['maximumDiagonalRelative'],.05)
if __name__=='__main__':unittest.main()
