import unittest,json,math
from pathlib import Path
import numpy as np
from scipy.linalg import eigh
from moving_termination import matrices,basis,Boundary
from scale_hypothesis import build
ROOT=Path(__file__).parent
class TerminationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=build(json.loads((ROOT/'scale_hypothesis.json').read_text()))['rows']
    def test_mass_integral(self):
        r=self.rows[39];L=r['lengthM'];mu=r['linearDensityKgM'];M,K,P=matrices(r,32,.005,1e6)
        n=np.arange(1,33);expected=-mu*np.sqrt(2/L)*L*(-1.)**n/(n*np.pi)
        np.testing.assert_allclose(M[0,1:],expected,atol=1e-15)
        self.assertAlmostEqual(M[0,0],.005+mu*L/3,places=14)
        self.assertGreater(np.linalg.eigvalsh(M)[0],0.)
    def test_static(self):
        r=self.rows[39];M,K,P=matrices(r,32,.005,1e6)
        a=P.T@np.linalg.solve(K,P)
        self.assertAlmostEqual(a[1,1],1/(1e6+r['tensionPerStringN']/r['lengthM']),places=14)
        self.assertAlmostEqual(a[0,1],a[1,0],places=14)
    def test_fixed_limit(self):
        r=self.rows[39];M,K,P=matrices(r,32,.005,1e6)
        f=np.sqrt(eigh(K[1:,1:],M[1:,1:],eigvals_only=True)[0])/(2*np.pi)
        self.assertAlmostEqual(f,r['nominalHz'],places=7)
    def test_work(self):
        r=self.rows[39];w,P=basis(r,128,24000,.005,1e6);t=Boundary(w,P,192000,5.)
        for i in range(400):
            E=t.energy();z=t.step([.1*math.sin(i*.02),.05*math.cos(i*.04)])
            self.assertLess(abs(t.energy()-E-z['work']+z['loss']),1e-12)
            self.assertLess(z['damperResidualN'],1e-10)
        self.assertGreater(t.loss,0.)
    def test_lossless(self):
        t=Boundary(np.array([100.,10000.]),np.array([[1.,.2],[.3,1.]]),96000,0.)
        t.step([1.,0.]);E=t.energy()
        for _ in range(100):t.step([0.,0.])
        self.assertAlmostEqual(t.energy(),E,places=14);self.assertEqual(t.loss,0.)
    def test_domain(self):
        with self.assertRaises(ValueError):matrices(self.rows[39],32,-1.,1e6)
if __name__=='__main__':unittest.main()
