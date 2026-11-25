import unittest,math,json
from pathlib import Path
import numpy as np
from wound_modes import mass_matrix,modes,solve,cents
from scale_hypothesis import build
class WoundModesTests(unittest.TestCase):
    def test_uniform(self):
        L=.8;mu=.009;EI=.015;T=650;n=np.arange(1,9)
        M=mass_matrix(L,mu,0,0,L,32)
        expected=np.sqrt((T*(n*np.pi/L)**2+EI*(n*np.pi/L)**4)/mu)/(2*np.pi)
        np.testing.assert_allclose(modes(M,L,EI,T),expected,rtol=1e-9)
    def test_full_winding(self):
        np.testing.assert_allclose(mass_matrix(1,.01,.03,0,1,32),.04*np.eye(32),atol=1e-15)
    def test_mass_bounds(self):
        M=mass_matrix(1,.01,.03,.05,.95,64)
        v=np.linalg.eigvalsh(M);self.assertGreaterEqual(v[0],.01-1e-12);self.assertLessEqual(v[-1],.04+1e-12)
        self.assertAlmostEqual(M[0,1],0.,places=14)
    def test_integral(self):
        x=np.linspace(.08,.85,100001);p=np.sin(np.pi*x);q=np.sin(3*np.pi*x)
        M=mass_matrix(1,.01,.03,.08,.85,16)
        self.assertAlmostEqual(M[0,2],.06*np.trapezoid(p*q,x),places=10)
    def test_retune(self):
        c=json.loads(Path(__file__).with_name('scale_hypothesis.json').read_text());r=build(c)['rows'][0]
        a=solve(r,64,c['wrappedFraction'],c['screen'])
        self.assertLess(abs(cents(a['corrected'][0],r['nominalHz'])),1e-4)
        self.assertGreater(abs(cents(a['original'][0],r['nominalHz'])),.1)
    def test_invalid(self):
        with self.assertRaises(ValueError):mass_matrix(1,.01,.03,-.1,.9,16)
if __name__=='__main__':unittest.main()
