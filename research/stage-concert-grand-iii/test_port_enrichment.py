import unittest
import numpy as np
from scipy.linalg import eigh
from port_enrichment import enrich
from modal_string_radiation import response,truncate
class EnrichmentTest(unittest.TestCase):
    def test_compliance(self):
        M=np.eye(8);K=np.diag(np.geomspace(1e4,1e9,8));D=2*M;F=np.ones((8,1));U=np.eye(8)
        q=enrich(M,K,D,F,U,F,2,(4,6),shiftHz=0.)
        s=q['sizes'][1];V=q['U'][:,:s];a=np.linalg.solve(q['K'][:s,:s],q['P'][:s])
        np.testing.assert_allclose(V@a,np.linalg.solve(K,F),rtol=1e-9,atol=1e-14)
        self.assertEqual(q['residualVectorRank'],1)
    def test_congruence(self):
        rng=np.random.default_rng(7);A=rng.normal(size=(12,12));M=A.T@A+np.eye(12)
        B=rng.normal(size=(12,12));K=1e5*(B.T@B+np.eye(12));D=.3*M+.00001*K
        F=rng.normal(size=(12,3));w,U=eigh(K,M);q=enrich(M,K,D,F,U,F,4,(8,12))
        self.assertEqual(q['sizes'][-1],12)
        f=80.;y,_,s=response(q,[],[],np.zeros((12,12)),np.zeros((2,12)),f)
        omega=2*np.pi*f;ref=1j*omega*F.T@np.linalg.solve(K-omega**2*M+1j*omega*D,F)
        np.testing.assert_allclose(y,ref,rtol=1e-9,atol=1e-12);self.assertTrue(s['gate'])
    def test_rank(self):
        M=np.eye(6);K=np.diag(np.arange(1,7)*1e5);D=M;F=np.eye(6)[:,[0,0]]
        q=enrich(M,K,D,F,np.eye(6),F,2,(4,6))
        self.assertEqual(q['residualVectorRank'],0);self.assertEqual(q['sizes'][-1],6)
if __name__=='__main__':unittest.main()
