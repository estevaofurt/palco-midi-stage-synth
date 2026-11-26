import unittest
import numpy as np
from dry_damping_midpoint import DryBlock,block_damping,proof,screen,require_grid
class DampingTest(unittest.TestCase):
    def setUp(self):
        self.k=(2*np.pi*np.linspace(30,400,8))**2
        self.D=4*np.eye(8)+np.ones((8,8));self.P=np.random.default_rng(4).normal(size=(8,4))
    def test_grid_roundoff(self):
        f=np.geomspace(30,500,32);require_grid(np.nextafter(f,np.inf))
        f[10]*=1.000001
        with self.assertRaises(ValueError):require_grid(f)
    def test_reference(self):
        for b in (1,4,8):self.assertTrue(proof(self.k,self.D,self.P,8000,b)['gate'])
    def test_psd(self):
        self.assertGreater(np.linalg.eigvalsh(block_damping(self.D,4)).min(),0)
        with self.assertRaises(ValueError):DryBlock(self.k,-self.D,self.P,8000,4)
    def test_partition(self):
        a=DryBlock(self.k,self.D,self.P,8000,4);b=DryBlock(self.k,self.D,self.P,8000,4)
        F=np.ones((129,4));O=np.empty_like(F);L=np.empty((129,2));X=np.empty_like(O);Y=np.empty_like(L)
        a.process(F,O,L)
        for i in range(0,len(F),17):b.process(F[i:i+17],X[i:i+17],Y[i:i+17])
        np.testing.assert_array_equal(O,X);np.testing.assert_array_equal(L,Y)
if __name__=='__main__':unittest.main()
