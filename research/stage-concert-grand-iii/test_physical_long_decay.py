import unittest
import numpy as np
from scipy.linalg import solve
from physical_long_decay import propagator,block_power,thresholds
class LongDecayTest(unittest.TestCase):
    def test_exact_block(self):
        M=np.array([[2.,.2],[.2,1.]])
        K=np.array([[1000.,10.],[10.,400.]])
        Q=np.array([[.2,.1],[.1,.1]]);D=.1*M+Q
        O=np.array([[1.,.4],[.2,1.]])
        h=1/48000;n=193
        A,B,Lk,Lm,audit=propagator(M,K,D,Q,O,h,n)
        q=np.array([.01,.02]);v=np.array([.1,-.2])
        y=np.r_[Lk.T@q,Lm.T@v];g=np.zeros(4)
        for _ in range(n):
            m=solve(2*M/h+D+h*K/2,2*M@v/h-K@q,assume_a='pos')
            q+=h*m;v=2*m-v
            g+=h*np.r_[m@D@m,m@Q@m,(O.T@m)**2]
        np.testing.assert_allclose(A@y,np.r_[Lk.T@q,Lm.T@v],rtol=1e-10,atol=1e-12)
        np.testing.assert_allclose(np.einsum('i,kij,j->k',y,B,y),g,rtol=1e-9,atol=1e-14)
    def test_threshold_censor(self):
        _,x=thresholds([1.,.01,.001],.05)
        self.assertFalse(x['-20']['rightCensored'])
        self.assertTrue(x['-60']['rightCensored'])
if __name__=='__main__':unittest.main()
