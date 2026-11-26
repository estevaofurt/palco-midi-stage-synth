import unittest
import numpy as np
from disjoint_extended_edge_block import extended_block,rel
from disjoint_extended_scalar_control import scalar_integral
class BlockTest(unittest.TestCase):
    def test_scalar_and_reverse(self):
        rng=np.random.default_rng(17)
        x=rng.random((9,3));y=rng.random((12,3))+2
        A=rng.normal(size=(9,3));B=rng.normal(size=(12,4));k=.7
        X=extended_block(x,A,y,B,k,3)
        for i in range(3):
            for j in range(4):
                self.assertAlmostEqual(float(X[i,j]),float(scalar_integral(x,A[:,i],y,B[:,j],k,2)),places=12)
        self.assertLess(rel(X,extended_block(y,B,x,A,k,5).T),1e-12)
    def test_coincident(self):
        x=np.zeros((1,3))
        with self.assertRaises(ValueError):extended_block(x,[[1]],x,[[1]],1.)
if __name__=='__main__':unittest.main()
