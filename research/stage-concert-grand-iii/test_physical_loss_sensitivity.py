import unittest
import numpy as np
from scipy.linalg import solve
from physical_loss_sensitivity import prepare,simulate,crossings,configurations
class LossTest(unittest.TestCase):
    def test_partitions(self):
        M=np.array([[2.,.2],[.2,1.]])
        K=np.array([[1000.,10.],[10.,400.]])
        G=np.stack([.1*M,.2*M,.0001*K,np.array([[.2,.1],[.1,.1]])])
        O=np.eye(2);h=1/48000;n=193;D=G.sum(axis=0)
        T,J,Lk,Lm,_=prepare(M,K,G,O,h,n)
        q=np.array([.01,.02]);v=np.array([.1,-.2]);y=np.r_[Lk.T@q,Lm.T@v];loss=np.zeros(6)
        for _ in range(n):
            m=solve(2*M/h+D+h*K/2,2*M@v/h-K@q,assume_a='pos')
            q+=h*m;v=2*m-v
            loss+=h*np.r_[np.einsum('i,kij,j->k',m,G,m),(O.T@m)**2]
        np.testing.assert_allclose(T@y,np.r_[Lk.T@q,Lm.T@v],rtol=1e-10,atol=1e-12)
        np.testing.assert_allclose(np.einsum('i,kij,j->k',y,J,y),loss,rtol=1e-9,atol=1e-14)
    def test_common_reference(self):
        self.assertEqual(crossings(np.array([.1,.01,.001]),1.)['-20']['lastWindowEndS'],.05)
        self.assertEqual(len(configurations(1.)),7)
        self.assertEqual(len(configurations(.5)),1)
if __name__=='__main__':unittest.main()
