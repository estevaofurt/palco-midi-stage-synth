import unittest
import numpy as np
from closed_cavity import assemble,response as closed
from vented_cavity import aperture,response,exterior
class VentTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[.3,0.],[.3,.2],[0.,.2]])
        self.q=assemble(self.poly,6,12,.24,lambda xy:np.ones((len(xy),1)))
    def test_exact_aperture_area(self):
        ap,A,C=aperture(self.q,self.poly,.17)
        self.assertAlmostEqual(A,.13*.2);self.assertAlmostEqual(sum(C),1.)
        self.assertEqual(np.count_nonzero(C[:-len(self.q['xy'])]),0)
    def test_matched_duct(self):
        ap,A,C=aperture(self.q,self.poly,0.)
        r=self.q['rho'];c=self.q['c']
        for s in (10+10j,2j*np.pi*100,20+2j*np.pi*200):
            z,p,U,m=response(self.q,C,s,[[.15,.1,.1]],r*c/A)
            self.assertLess(abs(z[0,0]/(r*c*A)-1),.005);self.assertTrue(m['gate'])
    def test_closed_limit_and_radiation(self):
        ap,A,C=aperture(self.q,self.poly,.17);s=2j*np.pi*100
        z,p,_=closed(self.q,s,[[.15,.1,.1]])
        v,o,U,m=response(self.q,C,s,[[.15,.1,.1]],1e15)
        np.testing.assert_allclose(v,z,rtol=1e-8);self.assertTrue(m['gate'])
        e=exterior(ap,A,s,self.q['rho'],self.q['c'],12,20);self.assertGreater(e.real,0)
        v,o,U,m=response(self.q,C,s,[[.15,.1,.1]],e)
        self.assertGreater(m['exteriorPowerTrace'],0);self.assertTrue(m['gate'])
    def test_active_rejected(self):
        _,_,C=aperture(self.q,self.poly,.17)
        with self.assertRaises(ValueError):response(self.q,C,10+10j,[[.15,.1,.1]],-1.)
if __name__=='__main__':unittest.main()
