import unittest
import numpy as np
from retarded_impedance import kernel,impedance,delay_matrix,fold,RHO
from surface_reactive_fft import average_kernel
class RetardedTest(unittest.TestCase):
    def test_fold(self):
        c=np.arange(36).reshape(6,6);a=fold(c,3)
        self.assertEqual(a[0,0],c[0,0])
        self.assertEqual(a[1,2],c[1,2]+c[5,2]+c[1,4]+c[5,4])
    def test_static(self):
        rng=np.random.default_rng(11);B=rng.normal(size=(4,4,3));K,err=kernel(B,.04,.06,48000,8)
        A=average_kernel(4,.04,.06,0.,8);out=np.zeros((3,3))
        for i in range(4):
            for j in range(4):
                for u in range(4):
                    for v in range(4):out+=A[abs(i-u),abs(j-v)]*np.outer(B[i,j],B[u,v])
        np.testing.assert_allclose(K.sum(axis=0),RHO/(2*np.pi)*out,rtol=1e-12,atol=1e-12)
        self.assertLess(err,1e-12)
        self.assertFalse(np.any(impedance(K,[0.],48000)))
        np.testing.assert_allclose(K,K.transpose(0,2,1))
if __name__=='__main__':unittest.main()
