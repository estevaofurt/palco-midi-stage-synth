import unittest
import numpy as np
from compiled_modal_midpoint import CompiledBlock,proof
from coupled_modal_midpoint import synthetic
class CompiledTest(unittest.TestCase):
    def test_equivalence(self):
        self.assertTrue(proof(12,8000)['gate'])
    def test_partition(self):
        a=synthetic(12,8000,'lowrank');b=synthetic(12,8000,'lowrank')
        x=CompiledBlock(a);y=CompiledBlock(b)
        F=np.random.default_rng(42).normal(size=(257,12));L=np.empty((257,3));M=np.empty_like(L)
        x.process(F,L)
        for i in range(0,257,17):y.process(F[i:i+17],M[i:i+17])
        np.testing.assert_array_equal(L,M);np.testing.assert_array_equal(a.q,b.q);np.testing.assert_array_equal(a.v,b.v)
    def test_bad_block(self):
        a=CompiledBlock(synthetic(12,8000,'lowrank'))
        with self.assertRaises(ValueError):a.process(np.ones((2,11)),np.empty((2,3)))
if __name__=='__main__':unittest.main()
