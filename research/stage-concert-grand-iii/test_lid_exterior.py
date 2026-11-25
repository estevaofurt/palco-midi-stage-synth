import unittest
import numpy as np
from inclined_lid import build
from lid_exterior import ports,load,pressure
from aperture_modes import response
class ExteriorTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[1.,0.],[1.,2.],[0.,2.]])
        self.m,self.C,self.q=build(self.poly,4,2,.24,30,lambda x:np.c_[np.ones(len(x)),x[:,0]])
    def test_modes_and_scalar_parity(self):
        p,C=ports(self.m,self.C,self.q,3)
        self.assertEqual(C.shape[1],9)
        np.testing.assert_allclose(C[:,::3],self.C,atol=1e-10)
        np.testing.assert_allclose(C.sum(0),np.tile([1.,0.,0.],3),atol=1e-10)
    def test_radiation_low_frequency(self):
        p,C=ports(self.m,self.C,self.q,1)
        Z,q=load(p,[.01],6,10,8)[0]
        expected=self.m['rho']*(2*np.pi*.01)**2/(4*np.pi*self.m['c'])
        np.testing.assert_allclose(Z.real/expected,np.ones((3,3)),atol=1e-6)
        self.assertLess(q['gramVsSurface'],1e-8)
    def test_reciprocal_coupling(self):
        p,C=ports(self.m,self.C,self.q,3)
        Z,q=load(p,[80.],8,14,12)[0]
        self.assertLess(q['gramVsSurface'],1e-8)
        self.assertGreater(np.linalg.norm(Z[:3,3:]),0)
        z,pr,U,rep=response(self.m,C,2j*np.pi*80,[[.3,.6,.12]],Z)
        self.assertTrue(rep['gate'])
        self.assertTrue(np.isfinite(pressure(p,U,[[3.,3.,2.]],80,8)).all())
if __name__=='__main__':unittest.main()
