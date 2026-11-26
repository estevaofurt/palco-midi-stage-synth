import unittest
import numpy as np
from numpy.polynomial.legendre import leggauss
from trapezoidal_surface_audit import moments,delay_kernel,evaluate,RHO,C
from retarded_surface import delay_kernel as old_kernel
from acoustic_cq_surface import ProjectedLoad
class TrapSurfaceTest(unittest.TestCase):
    def test_moments(self):
        z=np.array([0j,.1+1j,10+20j,200+10j])
        t,w=leggauss(128);t=(t+1)/2;w=w/2
        expected=np.array([(w*t**j)@np.exp(-t[:,None]*z) for j in range(3)])
        np.testing.assert_allclose(moments(z),expected,rtol=1e-9,atol=1e-13)
    def test_old_low_band(self):
        s=2j*np.pi*150
        np.testing.assert_allclose(delay_kernel(3,.02,.03,s,16),old_kernel(3,.02,.03,s,16),rtol=1e-10)
    def test_limit(self):
        dx,dy=.02,.03
        B=np.ones((1,1,1))*dx*dy
        L=ProjectedLoad(B,dx,dy)
        Z=evaluate(L,1e8+0j,32)
        np.testing.assert_allclose(Z,[[RHO*C*dx*dy]],rtol=.002)
if __name__=='__main__':unittest.main()
