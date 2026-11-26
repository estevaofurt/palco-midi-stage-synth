import unittest
import numpy as np
from exterior_pair_stream import pair_integrals
from disjoint_fixed_node_arithmetic import compensated_reactive
class ArithmeticTest(unittest.TestCase):
    def test_same_kernel(self):
        rng=np.random.default_rng(8);x=rng.random((11,3));y=rng.random((13,3))+2
        A=rng.normal(size=(11,4));B=rng.normal(size=(13,3));k=np.array([.5,2.])
        _,expected,_=pair_integrals(x,A,y,B,k,mutual=True,block=3)
        for block in (1,3,7):
            np.testing.assert_allclose(compensated_reactive(x,A,y,B,k,block),expected,rtol=1e-12,atol=1e-12)
        np.testing.assert_allclose(compensated_reactive(y,B,x,A,k,4).transpose(0,2,1),expected,rtol=1e-12,atol=1e-12)
    def test_coincident(self):
        x=np.zeros((1,3))
        with self.assertRaises(ValueError):compensated_reactive(x,np.ones((1,1)),x,np.ones((1,1)),np.array([1.]))
if __name__=='__main__':unittest.main()
