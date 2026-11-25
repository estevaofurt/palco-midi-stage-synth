import unittest,math
from felt_law import Felt,potential,secant,energy,force,relax,step
class FeltTest(unittest.TestCase):
    def setUp(self):self.f=Felt(1.4e9,.6e9,1000.,1.,2.5)
    def test_unilateral(self):
        self.assertEqual(force(-.001,.0001,self.f),0.)
        self.assertEqual(secant(-.001,-.0001,1e9,2.5),0.)
    def test_gradient(self):
        for a,b in ((-.0001,.0005),(.0005,.0007),(.001,.001+1e-13)):
            q=secant(a,b,1e9,2.5)
            self.assertGreaterEqual(q,0)
            self.assertAlmostEqual(q*(b-a),potential(b,1e9,2.5)-potential(a,1e9,2.5),places=12)
    def test_hold(self):
        q,l,r=relax(.001,0.,1e-5,self.f)
        self.assertGreater(q,0.);self.assertGreater(l,0.);self.assertLess(abs(r),1e-12)
        self.assertLess(force(.001,q,self.f),force(.001,0,self.f))
    def test_free_recovery(self):
        q,l,r=relax(-.001,.0002,1e-5,self.f)
        self.assertAlmostEqual(q,.0002*(1-.005)/(1+.005),places=14)
        self.assertLess(abs(r),1e-12);self.assertGreater(l,0.)
    def test_passive_step(self):
        q=step(-.0001,.0004,0.,1e-5,self.f)
        self.assertLess(abs(q['residualJ']),1e-12);self.assertGreater(q['lossJ'],0)
    def test_invalid(self):
        with self.assertRaises(ValueError):relax(.001,0.,.003,self.f)
        with self.assertRaises(ValueError):Felt(1,-1,1,1,2)
if __name__=='__main__':unittest.main()
