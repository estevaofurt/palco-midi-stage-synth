import unittest
import numpy as np
from passive_board_fit import dictionary,fit,evaluate,audit,psd
class FitTest(unittest.TestCase):
    def test_known(self):
        f=np.array([30.,50.,80.,120.,200.,300.]);centers=np.array([80.,180.])
        C=np.array([np.eye(2)*.1,np.eye(2)*.001,np.eye(2)*100.,np.array([[20.,5.],[5.,10.]]),np.eye(2)*50])
        Z=evaluate(2j*np.pi*f,C,centers)
        out,r=fit(f,Z,centers,iterations=8000)
        self.assertTrue(audit(out,centers)['gate'])
        self.assertLess(np.linalg.norm(evaluate(2j*np.pi*f,out,centers)-Z)/np.linalg.norm(Z),.005)
    def test_psd(self):
        X=psd(np.array([[[1.,2.],[2.,1.]]]))
        self.assertGreaterEqual(np.linalg.eigvalsh(X[0]).min(),-1e-12)
    def test_invalid(self):
        with self.assertRaises(ValueError):dictionary([0j])
        with self.assertRaises(ValueError):fit([1.,2.],-np.ones((2,1,1)))
if __name__=='__main__':unittest.main()
