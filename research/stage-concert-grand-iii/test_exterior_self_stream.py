import unittest
import numpy as np
from lid_exterior import Panel,self_react,load
from exterior_self_stream import self_react_blocked
from split_radiation import relative
class SelfStreamTest(unittest.TestCase):
    def test_raw_integral_equivalence(self):
        k=2*np.pi*np.array([30.,80.,150.,300.])/343.
        polys=[np.array([[0.,0.,0.],[1.,0.,0.],[.3,.7,0.]]),
               np.array([[0.,0.,0.],[1.,0.,0.],[.8,.7,0.],[0.,.8,0.]])]
        for x in polys:
            for count in (1,6,21,36):
                p=Panel(x,np.array([0.,0.,1.]),count);s=p.samples(5)
                ref=self_react(p,s,k,9)
                for block in (1,4,13,256):
                    q=self_react_blocked(p,s,k,9,block=block)
                    self.assertLess(relative(q,ref),1e-11)
                    self.assertLess(abs(relative(q,q.transpose(0,2,1))-relative(ref,ref.transpose(0,2,1))),1e-11)
        with self.assertRaises(ValueError):self_react_blocked(p,s,k,9,block=0)
    def test_high_order_and_complete_load(self):
        x=np.array([[0.,0.,0.],[1.,0.,0.],[1.,.7,0.],[0.,.8,0.]])
        p=Panel(x,np.array([0.,0.,1.]),36);s=p.samples(10);k=2*np.pi*np.array([30.,300.])/343.
        r=self_react(p,s,k,18);q=self_react_blocked(p,s,k,18,block=8)
        self.assertLess(relative(r,q),1e-11)
        pp=[Panel(x,np.array([0.,0.,1.]),6),Panel(x+[0,0,.5],np.array([0.,0.,1.]),6)]
        a=load(pp,[30.,150.],8,14,16)
        b=load(pp,[30.,150.],8,14,16,pair_block=32,self_block=8)
        for (z,r),(q,s) in zip(a,b):
            self.assertLess(relative(z,q),1e-11)
            for key in ('gramVsSurface','reactiveAsymmetry','passivityMinRelative','reciprocity'):
                self.assertAlmostEqual(r[key],s[key],places=11)
            self.assertEqual(r['gate'],s['gate'])
if __name__=='__main__':unittest.main()
