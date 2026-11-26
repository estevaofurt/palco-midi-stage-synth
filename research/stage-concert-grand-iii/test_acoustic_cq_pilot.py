import unittest
import numpy as np
from acoustic_cq_pilot import symbol,coefficients,transfer,convolve,power_check
class CQTest(unittest.TestCase):
    def test_symbol(self):
        z=np.exp(2j*np.pi*np.arange(1024)/1024)
        self.assertGreaterEqual(symbol(z,48000).real.min(),-1e-9)
        self.assertEqual(symbol(1,48000),0)
        with self.assertRaises(ValueError):symbol(1.01,48000)
    def test_inertance(self):
        W,err=coefficients(lambda s:np.array([[2*s]]),48000,128,.98)
        np.testing.assert_allclose(W[:3,0,0],[144000.,-192000.,48000.],rtol=1e-12)
        self.assertLess(np.linalg.norm(W[3:])/np.linalg.norm(W),1e-12)
        self.assertLess(err,1e-12)
        v=np.ones((10,1));y=convolve(W,v)
        np.testing.assert_allclose(y[:3,0],[144000.,-48000.,0.],atol=1e-8)
    def test_relaxation(self):
        rate=48000.;f=np.array([0.,50.,500.,5000.]);load=lambda s:np.array([[s/(s+2*np.pi*500)]])
        W,_=coefficients(load,rate,512,.98)
        z=np.exp(-2j*np.pi*f/rate)
        ref=np.stack([load(s) for s in symbol(z,rate)])
        np.testing.assert_allclose(transfer(W,f,rate),ref,atol=1e-9,rtol=1e-9)
        self.assertGreaterEqual(min(power_check(v) for v in ref),-1e-12)
if __name__=='__main__':unittest.main()
