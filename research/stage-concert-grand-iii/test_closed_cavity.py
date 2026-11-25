import unittest
import numpy as np
from closed_cavity import assemble,response
class CavityTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[.3,0.],[.3,.2],[0.,.2]])
        self.field=lambda xy:np.ones((len(xy),1))
    def test_uniform_piston(self):
        q=assemble(self.poly,6,12,.24,self.field)
        for s in (10+0j,2j*np.pi*100,20+2j*np.pi*200):
            z,p,a=response(q,s,[[.15,.1,.1]])
            ref=q['rho']*q['c']*q['area']/np.tanh(s*.24/q['c'])
            self.assertLess(abs(z[0,0]/ref-1),.005);self.assertTrue(a['gate'])
    def test_positive_real(self):
        field=lambda xy:np.c_[np.ones(len(xy)),xy[:,0],xy[:,1]]
        q=assemble(self.poly,5,4,.24,field)
        for s in (5+2j*np.pi*300,15+2j*np.pi*500):
            _,_,a=response(q,s,[[.15,.1,.1]]);self.assertTrue(a['gate'])
    def test_volume_and_outside(self):
        q=assemble(self.poly,4,2,.24,self.field)
        self.assertAlmostEqual(q['volume'],.3*.2*.24)
        with self.assertRaises(ValueError):response(q,10+10j,[[.5,.1,.1]])
if __name__=='__main__':unittest.main()
