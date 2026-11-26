import unittest
import numpy as np
from scipy.fft import rfft2
from retarded_load import delay_table,folded_correlation,build,transfer,RHO
from surface_reactive_fft import average_kernel
class RetardedTest(unittest.TestCase):
    def test_singular(self):
        T=delay_table(3,.03,.04,48000,8)
        f=100.
        np.testing.assert_allclose(np.asarray(T.sum(axis=0)).ravel(),average_kernel(3,.03,.04,0.,8).ravel(),rtol=1e-12)
        z=np.exp(-2j*np.pi*f/48000)**np.arange(T.shape[0])
        np.testing.assert_allclose((z@T).real,average_kernel(3,.03,.04,2*np.pi*f/343.,8).ravel(),rtol=3e-5)
    def test_folded(self):
        a=np.arange(9.).reshape(3,3);b=a[::-1].copy()
        c=folded_correlation(rfft2(a,s=(6,6)),rfft2(b,s=(6,6)),3).reshape(3,3)
        ref=np.zeros_like(c)
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    for l in range(3):ref[abs(i-k),abs(j-l)]+=a[i,j]*b[k,l]
        np.testing.assert_allclose(c,ref,atol=1e-12)
    def test_dc_and_reciprocity(self):
        B=np.arange(18.).reshape(3,3,2)/100
        K=build(B,.03,.04,(48000,))[0]
        np.testing.assert_array_equal(K,K.transpose(0,2,1))
        self.assertFalse(np.any(transfer(K,[0.],48000,True)))
if __name__=='__main__':unittest.main()
