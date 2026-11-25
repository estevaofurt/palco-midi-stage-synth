import unittest
import numpy as np
from structural_response import response
class ResponseTest(unittest.TestCase):
    def test_scalar(self):
        M=np.array([[2.]]);K=np.array([[1e5]]);D=np.array([[3.]])
        f=np.array([10.,20.,35.]);w=2*np.pi*f
        Y,s,_=response(M,K,D,np.ones((1,1)),f,[1.])
        np.testing.assert_allclose(Y[:,0,0],1j*w/(1e5-2*w*w+3j*w),rtol=1e-12)
        self.assertTrue(s['gate'])
    def test_congruence(self):
        M=np.array([[2.,.2],[.2,1.]])
        K=np.array([[10000.,-2000.],[-2000.,8000.]])
        D=np.array([[3.,.2],[.2,4.]])
        P=np.eye(2);S=np.diag([1e-5,1e5])
        x,s,_=response(M,K,D,P,[10,20,30],[1.,1.])
        y,t,_=response(S@M@S,S@K@S,S@D@S,S@P,[10,20,30],[1.,1.])
        np.testing.assert_allclose(x,y,rtol=1e-12,atol=1e-14);self.assertTrue(s['gate'] and t['gate'])
    def test_power(self):
        rng=np.random.default_rng(43);A=rng.normal(size=(8,8));B=rng.normal(size=(8,8));C=rng.normal(size=(8,8))
        M=A.T@A+np.eye(8);K=1e4*(B.T@B+np.eye(8));D=C.T@C;P=rng.normal(size=(8,3))
        x,s,_=response(M,K,D,P,[30,100,150],[1.,.02,1.])
        y,t,_=response(M,K,D,P,[30,100,150],[1.,.02,1.],'direct')
        np.testing.assert_allclose(x,y,rtol=1e-11,atol=1e-14);self.assertTrue(s['gate'] and t['gate'])
    def test_active_damping_detected(self):
        _,s,_=response(np.eye(2),1e6*np.eye(2),-np.eye(2),np.eye(2),[20,40],[1.,1.])
        self.assertFalse(s['gate']);self.assertLess(s['passivityMinRelative'],0)
if __name__=='__main__':unittest.main()
