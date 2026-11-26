import unittest
import numpy as np
from physical_cq_offline import PackedLoad,packed_weights,transfer
from retarded_surface import impedance
from acoustic_cq_surface import cq
class PackedTest(unittest.TestCase):
    def test_packed(self):
        B=np.random.default_rng(1).normal(size=(3,3,3))
        L=PackedLoad(B,.02,.03);s=np.array([1j*1000,100+200j])
        np.testing.assert_allclose(L.expand(L.evaluate(s)),np.stack([impedance(B,.02,.03,v) for v in s]),rtol=1e-10,atol=1e-10)
        w,e=packed_weights(L,48000,64)
        expected,_=cq(lambda s:impedance(B,.02,.03,s),48000,64)
        np.testing.assert_allclose(L.expand(w),expected,rtol=1e-6,atol=1e-6)
        np.testing.assert_allclose(L.expand(transfer(w,[100,200],48000)),np.einsum('ft,tij->fij',np.exp(-2j*np.pi*np.array([100,200])[:,None]/48000)**np.arange(64),expected),rtol=1e-8,atol=1e-6)
if __name__=='__main__':unittest.main()
