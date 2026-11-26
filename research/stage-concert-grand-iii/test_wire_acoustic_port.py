import unittest
import numpy as np
from types import SimpleNamespace
from wire_acoustic_port import compare
class WireAcousticTest(unittest.TestCase):
    def test_dense_replay(self):
        M=np.array([[.5,.1,.03],[.1,1.,0.],[.03,0.,1.]])
        K=np.diag([100.,1000.,4000.]);D=.4*M+.001*K
        w=SimpleNamespace(M=M,K=K,D=D,P=np.array([.2,1.,.4]),port=0,U=np.eye(2),
            m=M[1:,0],k=K[1:,0],d=D[1:,0],w2=np.diag(K)[1:],gamma=np.diag(D)[1:],p=np.array([1.,.4]))
        for wet in (False,True):
            r=compare(np.array([200.,500.]),np.eye(2),np.zeros((2,1)),np.array([[.8,.2]]),[w],48000,2,128,wet)
            self.assertTrue(r['gate'],r)
            if wet:self.assertGreater(r['acousticWorkJ'],0.)
if __name__=='__main__':unittest.main()
