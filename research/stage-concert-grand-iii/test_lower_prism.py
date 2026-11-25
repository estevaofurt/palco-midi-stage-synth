import unittest
import numpy as np
from lower_prism import build,response
from recess_envelope import build as envelope
from bem_envelope import triangulate
class LowerPrismTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
        self.field=lambda x:np.ones((len(x),1))
    def test_uniform_exact(self):
        m=build(self.poly,8,.18,self.field,1)
        for s in (2j*np.pi*80,5+2j*np.pi*80):
            Z,P,r=response(m,s,[[.5,.5,-.09]])
            a=s/343.;h=.18
            exact=1.204*s/a*np.array([[1/np.tanh(a*h),1/np.sinh(a*h)],[1/np.sinh(a*h),1/np.tanh(a*h)]])
            np.testing.assert_allclose(Z,exact,rtol=1e-8,atol=1e-8)
            np.testing.assert_allclose(P,1.204*s*np.full((1,2),np.cosh(a*h/2)/(a*np.sinh(a*h))),rtol=1e-8,atol=1e-8)
            self.assertTrue(r['gate'])
    def test_recess_geometry(self):
        for angle in (30,55):
            s,p,c,r=envelope(self.poly,.24,-.18,angle,3,self.field,6)
            self.assertTrue(r['gate']);self.assertAlmostEqual(r['lowerVolume'],.18)
            self.assertEqual(s[-1]['kind'],'lower-mouth');self.assertEqual(p[-1].basis.count,6)
            self.assertTrue(all(v['kind']!='board' for v in s))
            t,l,g=triangulate(s,1);self.assertTrue(g['gate']);self.assertAlmostEqual(g['volume'],r['volume'])
if __name__=='__main__':unittest.main()
