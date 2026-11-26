import unittest
import numpy as np
from types import SimpleNamespace
from frozen_regional_loss import components,contract
class FrozenRegionalTest(unittest.TestCase):
    def test_partition(self):
        a=SimpleNamespace(A=np.eye(2),d0=np.array([1.,2.]),ds=np.ones((2,1)),di=np.zeros((2,1)),h=.1)
        G=np.stack([np.eye(2),2*np.eye(2),3*np.eye(2)])
        v=np.array([1.,2.]);u=np.array([[3.],[4.]])
        np.testing.assert_allclose(components(a,G,v,u,5.,np.array([True,False])),[.5,1.,1.5,1.,2.4,.5])
    def test_gate(self):
        with self.assertRaises(ValueError):contract(dict(gate=False),dict(gate=True))
if __name__=='__main__':unittest.main()
