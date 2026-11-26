import unittest
from types import SimpleNamespace
import numpy as np
from cq_bridge_sensitivity import solve
class BridgeSensitivityTest(unittest.TestCase):
    def test_energy(self):
        a=SimpleNamespace(ks=np.array([[100.]]),ds=np.array([[2.]]),ki=np.zeros((1,1)),di=np.zeros((1,1)),
            mi=np.zeros((1,1)),Kb=np.array([[200.]]),Db=np.array([[3.]]),Mb=np.eye(1),A=np.zeros((1,1)),
            P=np.ones((1,1)),F=np.zeros((1,1,1)),d0=np.zeros(1))
        r=solve(a,np.array([[[1.]],[[1.]],[[1.]]]),np.array([[2.+0j]]),2.,np.ones(1),np.array([True]))
        self.assertAlmostEqual(r['lossFractions']['air'],.4)
        self.assertAlmostEqual(r['lossFractions']['bridges'],.2)
        self.assertLess(r['powerRelativeError'],1e-12)
if __name__=='__main__':unittest.main()
