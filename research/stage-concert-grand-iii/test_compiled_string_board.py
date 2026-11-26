import unittest
import numpy as np
from compiled_string_board import StringBlock,fixture,proof,timing
class CompiledStringTest(unittest.TestCase):
    def test_reference(self):
        self.assertTrue(proof(4,3,12,5,8000,.04,17)['gate'])
    def test_partition(self):
        a=fixture(4,3,12,5,8000);b=fixture(4,3,12,5,8000);x=StringBlock(a);y=StringBlock(b)
        F=np.zeros((129,12));S=np.random.default_rng(5).normal(size=(129,12));L=np.empty((129,4));M=np.empty_like(L)
        x.process(F,S,L)
        for i in range(0,129,17):y.process(F[i:i+17],S[i:i+17],M[i:i+17])
        np.testing.assert_array_equal(L,M);np.testing.assert_array_equal(a.q,b.q);np.testing.assert_array_equal(a.b.v,b.b.v)
    def test_invalid(self):
        a=StringBlock(fixture(4,3,12,5,8000))
        with self.assertRaises(ValueError):a.process(np.zeros((2,12)),np.zeros((2,11)),np.empty((2,4)))
    def test_timing_energy(self):
        self.assertTrue(timing(4,3,12,5,8000,16,4)['gate'])
if __name__=='__main__':unittest.main()
