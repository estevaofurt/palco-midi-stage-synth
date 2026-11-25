import unittest,math
import numpy as np
from test_exterior_bem import sphere
from bem_oversampled import TRAIN,AUDIT,WEIGHTS,fit,audit,audit_targets
from bem_linear import COL,CHECK,targets,fit as collocate
class OversampledTest(unittest.TestCase):
    def test_independent_degree_four_rule(self):
        for x in AUDIT:
            self.assertFalse(any(np.allclose(x,y) for y in np.vstack([TRAIN,CHECK])))
        for i in range(5):
            for j in range(5-i):
                for k in range(5-i-j):
                    exact=2*math.factorial(i)*math.factorial(j)*math.factorial(k)/math.factorial(i+j+k+2)
                    self.assertAlmostEqual(WEIGHTS@(AUDIT[:,0]**i*AUDIT[:,1]**j*AUDIT[:,2]**k),exact,places=13)
    def test_sphere(self):
        t=sphere(.5,1);k=2*np.pi*80/343.
        q,r=fit(t,np.ones((len(t)*len(TRAIN),1)),k,6)
        self.assertEqual(r['rank'],3*len(t))
        self.assertLess(r['normalEquationResidual'],1e-10)
        Z,P,rr=audit(t,q,np.ones((len(t)*len(AUDIT),1)),k,[[1.,0.,0.]],8)
        exact=4*np.pi*.5**2*1j*1.204*343*k/(2+1j*k)
        self.assertLess(abs(Z[0,0]-exact)/abs(exact),.25)
        self.assertLess(rr['powerRelative'],.15)
if __name__=='__main__':unittest.main()
