import unittest
import numpy as np
from retarded_surface import delay_kernel,impedance,audit,C,RHO
from surface_reactive_fft import average_kernel
class RetardedSurfaceTest(unittest.TestCase):
    def test_reactive(self):
        f=150.;K=delay_kernel(3,.02,.03,2j*np.pi*f,12)
        np.testing.assert_allclose(K.real,average_kernel(3,.02,.03,2*np.pi*f/C,12),rtol=1e-12,atol=1e-12)
        self.assertTrue(np.all(K.imag<0))
    def test_fft(self):
        rng=np.random.default_rng(4);B=rng.normal(size=(3,3,2));s=2j*np.pi*150
        K=delay_kernel(3,.02,.03,s);ids=np.array([(i,j) for i in range(3) for j in range(3)])
        d=abs(ids[:,None]-ids[None,:]);M=K[d[:,:,0],d[:,:,1]];F=B.reshape(9,2)
        Z=impedance(B,.02,.03,s)
        np.testing.assert_allclose(Z,RHO*s/(2*np.pi)*F.T@M@F,rtol=1e-12,atol=1e-10)
        self.assertTrue(audit(Z)['gate'])
    def test_dc_and_domain(self):
        B=np.ones((1,1,1));np.testing.assert_array_equal(impedance(B,.02,.03,0j),np.zeros((1,1)))
        with self.assertRaises(ValueError):delay_kernel(1,.02,.03,-1+0j)
if __name__=='__main__':unittest.main()
