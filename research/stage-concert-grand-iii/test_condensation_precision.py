import os,json,unittest
from pathlib import Path
import numpy as np
from scipy.linalg import cholesky,lu_factor
from condensation_precision import response,extended_dynamic,refine
from string_structure import Wire,full_reference,response as prior
from structural_response import response as full_response
class PrecisionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads(Path(os.environ['G3_SCALE_REPORT']).read_text())['rows']
    def test_refinement(self):
        A=np.array([[1e10+1,-1e10],[-1e10,1e10+1.]])
        L=cholesky(A,lower=True);G=np.linalg.solve(L,np.linalg.solve(L,A).T).T
        rhs=np.array([[1.],[2.]])
        x=np.linalg.solve(A,rhs)+np.array([[1e-6],[-1e-6]])
        y,q=refine(A.astype(np.clongdouble),np.zeros(2),rhs,L,lu_factor(G),x)
        self.assertGreater(q['initial'],1e-3);self.assertLess(q['final'],1e-7)
        self.assertGreater(q['corrections'],0)
    def test_condensation_parity(self):
        M=np.diag([.02,.03]);K=np.array([[2e6,-1e6],[-1e6,2e6]]);D=np.diag([3.,5.])
        P=np.zeros((2,4));P[:,2:]=np.eye(2)
        wires=[Wire(self.rows[24],32,0,0,'a'),Wire(self.rows[24],32,0,0,'b'),Wire(self.rows[27],32,1,1,'c')]
        f=[30,65,110,130,150]
        y,s,_=response(M,K,D,P,wires,f);old,t,_=prior(M,K,D,P,wires,f)
        A,B,C,F=full_reference(M,K,D,P,wires);z,u,_=full_response(A,B,C,F,f,np.ones(4))
        self.assertTrue(s['gate'] and t['gate'] and u['gate'])
        np.testing.assert_allclose(y,z,rtol=1e-7,atol=1e-11)
        np.testing.assert_allclose(y,old,rtol=1e-7,atol=1e-11)
    def test_extended_matrix(self):
        M=np.array([[1.,.1],[.1,2.]]);K=np.array([[1e8,2.],[2.,4.]])
        D=np.eye(2);w=17.
        Z=extended_dynamic(M,K,D,w)
        self.assertEqual(Z.dtype,np.dtype(np.clongdouble))
        np.testing.assert_allclose(Z.astype(complex),K-w*w*M+1j*w*D)
if __name__=='__main__':unittest.main()
