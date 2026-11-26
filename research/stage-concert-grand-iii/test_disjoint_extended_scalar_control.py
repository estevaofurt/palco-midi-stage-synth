import unittest
import numpy as np
from disjoint_extended_scalar_control import scalar_integral
class ExtendedTest(unittest.TestCase):
    def test_single_pair(self):
        x=np.array([[0.,0.,0.]]);y=np.array([[2.,0.,0.]])
        v=scalar_integral(x,[3.],y,[4.],.5)
        self.assertAlmostEqual(float(v),6*np.cos(1),places=13)
    def test_reverse(self):
        x=np.array([[0.,0.,0.],[1.,0.,0.]])
        y=np.array([[0.,2.,0.],[1.,3.,0.],[2.,2.,0.]])
        a=np.array([2.,-1.]);b=np.array([3.,-2.,1.])
        v=scalar_integral(x,a,y,b,.7,1);w=scalar_integral(y,b,x,a,.7,2)
        self.assertAlmostEqual(float(v),float(w),places=13)
    def test_coincident(self):
        x=np.zeros((1,3))
        with self.assertRaises(ValueError):scalar_integral(x,[1.],x,[1.],1.)
if __name__=='__main__':unittest.main()
