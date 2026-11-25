import unittest
import numpy as np
from lid_exterior import Panel,load
from split_radiation import relative
class AngularLoadTest(unittest.TestCase):
    def test_complete_load(self):
        a=np.array([[0.,0.,0.],[1.,0.,0.],[.5,.7,0.]])
        p=Panel(a,np.array([0.,0.,1.]),6)
        q=Panel(a+[0.,0.,.8],np.array([0.,0.,1.]),10)
        old=load([p,q],[30.,150.,300.],12,24,20,pair_block=32,self_block=8)
        new=load([p,q],[30.,150.,300.],12,24,20,pair_block=32,self_block=8,angular_local=True)
        for (Z,r),(W,s) in zip(old,new):
            self.assertLess(relative(Z,W),1e-12)
            np.testing.assert_array_equal(Z.imag,W.imag)
            self.assertEqual(r['gate'],s['gate'])
            self.assertLess(abs(r['gramVsSurface']-s['gramVsSurface']),1e-12)
        with self.assertRaises(ValueError):load([p],[30.],12,24,20,angular_local=1)
if __name__=='__main__':unittest.main()
