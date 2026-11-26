import unittest
import numpy as np
from regularized_board_fit import candidates,solve_fit,centers_for,require_dense
from passive_board_fit import evaluate,audit
class RegularizedTest(unittest.TestCase):
    def test_complexity(self):
        self.assertEqual(len(candidates(6)),4)
        self.assertEqual(len(candidates(12)),12)
        self.assertTrue(all(k+3<=10 for k,_,_ in candidates(6)))
    def test_known_passive(self):
        f=np.linspace(30.,300.,30);cfg=(5,5.,1e-4);c=centers_for(5)
        C=np.array([np.eye(2)*.1,np.eye(2)*.001,np.eye(2)*100]+[np.eye(2)*5]*5)
        Z=evaluate(2j*np.pi*f,C,c,5.)
        out,opt=solve_fit(f,Z,cfg)
        self.assertTrue(audit(out,c,5.)['gate'])
        self.assertLess(np.linalg.norm(evaluate(2j*np.pi*f,out,c,5.)-Z)/np.linalg.norm(Z),.01)
    def test_bad_evidence(self):
        with self.assertRaises(ValueError):require_dense({},30.,'x')
    def test_nonpassive(self):
        with self.assertRaises(ValueError):solve_fit([30.,50.],-np.ones((2,1,1)),(5,5.,1e-4))
if __name__=='__main__':unittest.main()
