import unittest
import numpy as np
from test_exterior_bem import sphere
from bem_p1_static_moments import fit
from bem_energy_marking import local_terms,score
class EnergyMarkingTest(unittest.TestCase):
    def test_score(self):
        r=np.array([4.,1.]);e=np.array([1.,9.])
        self.assertGreater(score([(r,e)],'residual')[0],score([(r,e)],'residual')[1])
        self.assertLess(score([(r,e)],'combined')[0],score([(r,e)],'combined')[1])
        np.testing.assert_allclose(score([(r,e)],'combined'),score([(r*10,e*.01)],'combined'))
    def test_local_work_closure(self):
        t=sphere(.5,1);k=2*np.pi*80/343.
        v=lambda x,o:np.c_[np.ones(len(x)),x[:,0]]
        q,_=fit(t,k,4,6,v)
        R,E,rep=local_terms(t,q,v,k,7)
        self.assertEqual(R.shape,(len(t),));self.assertEqual(E.shape,R.shape)
        self.assertTrue(np.isfinite(R).all() and np.isfinite(E).all())
        self.assertTrue(np.all(R>=0) and np.all(E>=0))
        self.assertLess(rep['localWorkClosure'],1e-10)
        self.assertGreaterEqual(rep['sumLocalWorkNorms']+1e-12,rep['globalWorkMismatch'])
if __name__=='__main__':unittest.main()
