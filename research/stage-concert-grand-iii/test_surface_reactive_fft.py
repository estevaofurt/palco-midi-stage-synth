import unittest
import numpy as np
from surface_reactive_fft import average_kernel,reactive,cell_integrals
class ReactiveFFTTest(unittest.TestCase):
    def test_constant_rectangle(self):
        # Exact cell averages are additive under uniform subdivision.
        # No artificial diagonal distance is introduced.
        a=reactive(np.ones((1,1,1)),1.,1.,150.,16)
        b=reactive(np.ones((8,8,1))/64,1/8,1/8,150.,16)
        np.testing.assert_allclose(a,b,rtol=1e-8,atol=1e-10)
    def test_kernel_order(self):
        a=average_kernel(8,.2,.3,2.,8);b=average_kernel(8,.2,.3,2.,12)
        np.testing.assert_allclose(a,b,rtol=1e-6,atol=1e-9)
    def test_cut_cells(self):
        poly=np.array([[0.,0.],[1.,0.],[0.,1.]])
        B,dx,dy,area=cell_integrals(poly,lambda x:np.ones((len(x),1)),8)
        self.assertAlmostEqual(area,.5,places=12)
        self.assertAlmostEqual(B.sum(),.5,places=12)
    def test_signed_fields(self):
        B=np.random.default_rng(4).normal(size=(8,8,3))
        X=reactive(B,.1,.2,150.,8)
        np.testing.assert_allclose(X,X.T,rtol=1e-10,atol=1e-10)
if __name__=='__main__':unittest.main()
