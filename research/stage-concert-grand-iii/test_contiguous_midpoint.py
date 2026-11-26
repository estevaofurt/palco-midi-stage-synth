import unittest
import numpy as np
from contiguous_midpoint import ContiguousBlock,stress_model,proof,timing
class LayoutTest(unittest.TestCase):
    def test_dense(self):
        self.assertTrue(proof(12,39,8000,17,.06)['gate'])
    def test_partition(self):
        a=stress_model(12,39,8000);b=stress_model(12,39,8000)
        x=ContiguousBlock(a);y=ContiguousBlock(b)
        F=np.random.default_rng(9).normal(size=(129,12));L=np.empty((129,3));M=np.empty_like(L)
        x.process(F,L)
        for i in range(0,129,19):y.process(F[i:i+19],M[i:i+19])
        np.testing.assert_array_equal(L,M);np.testing.assert_array_equal(a.q,b.q)
    def test_timing(self):
        r=timing(16,5,8000,16,3)
        self.assertEqual(len(r['timings']),2)
if __name__=='__main__':unittest.main()
