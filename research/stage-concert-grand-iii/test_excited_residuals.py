import unittest
import numpy as np
from excited_residuals import basis,coefficients,pressure_coefficients,pressure_window
class ExcitedTest(unittest.TestCase):
    def test_replay(self):
        rate=48000;M=np.eye(1);K=np.array([[(2*np.pi*669)**2]]);D=np.array([[2.]])
        U,w,p,z,V,e=basis(M,K,D,rate)
        q=np.array([.0001]);v=np.array([.1]);c,err=coefficients(M,U,w,V,q,v)
        kernel=np.array([[[.4],[.6]]]);H=pressure_coefficients(U,V,z,c,kernel,rate)
        a=np.block([[np.zeros((1,1)),np.eye(1)],[-K,-D]])
        T=np.linalg.solve(np.eye(2)-a/(2*rate),np.eye(2)+a/(2*rate))
        x=np.r_[q,v];acc=[]
        for i in range(200):
            nxt=T@x;acc.append((nxt[1]-x[1])*rate);x=nxt
        expected=np.convolve(acc,[.4,.6])[:200]
        got,imag=pressure_window(z,H,20,180,rate)
        np.testing.assert_allclose(got[:,0],expected[20:],rtol=1e-8,atol=1e-8)
        self.assertLess(imag,1e-10)
if __name__=='__main__':unittest.main()
