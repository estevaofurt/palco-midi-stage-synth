import unittest
import numpy as np
from coupled_hammer_contact import make,midpoint,probe
class HammerTest(unittest.TestCase):
    def test_compliance(self):
        a=make(48000,1.,4,'schur');b=make(48000,1.,4,'dense')
        self.assertAlmostEqual(a.compliance,b.compliance,places=14)
        _,v=midpoint(a.a,a.Fb,a.port,True)
        self.assertGreater(a.port@v,0.)
    def test_free_prediction(self):
        a=make(48000,1.,4,'schur');b=a.a
        b.q[:]=1e-5;b.v[:]=.01
        vb,vs=midpoint(b,a.Fb,a.port)
        oldb=b.b.v.copy();olds=b.v.copy();b.step(a.Fb,a.port)
        np.testing.assert_allclose((b.b.v+oldb)/2,vb,atol=1e-12)
        np.testing.assert_allclose((b.v+olds)/2,vs,atol=1e-12)
    def test_impact(self):
        self.assertTrue(probe(48000,1.,4)['gate'])
if __name__=='__main__':unittest.main()
