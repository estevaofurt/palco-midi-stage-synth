import unittest
import numpy as np
from compiled_variable_damper import VariableBlock,proof,fixture
class CompiledDamperTest(unittest.TestCase):
    def test_dense(self):
        self.assertTrue(proof(4,2,12,5,8000,.07,17)['gate'])
    def test_partition(self):
        a=fixture(4,2,12,5,8000);b=fixture(4,2,12,5,8000);mapping=np.repeat(np.arange(4),2)
        x=VariableBlock(a,mapping,160*a.ms);y=VariableBlock(b,mapping,160*b.ms)
        F=np.zeros((129,12));S=np.ones((129,8));D=np.random.default_rng(2).random((129,4));L=np.empty((129,5));M=np.empty_like(L)
        x.process(F,S,D,L)
        for i in range(0,129,17):y.process(F[i:i+17],S[i:i+17],D[i:i+17],M[i:i+17])
        np.testing.assert_array_equal(L,M);np.testing.assert_array_equal(a.q,b.q)
    def test_invalid(self):
        a=fixture(4,2,12,5,8000);x=VariableBlock(a,np.repeat(np.arange(4),2),160*a.ms)
        with self.assertRaises(ValueError):x.process(np.zeros((2,12)),np.zeros((2,8)),np.ones((2,4))*2,np.zeros((2,5)))
if __name__=='__main__':unittest.main()
