import unittest
import numpy as np
from wire_port_enrichment import enrich_basis,model,comparison
class WirePortTest(unittest.TestCase):
    def test_preserve(self):
        T=np.eye(8)[:,:3];S=np.random.default_rng(4).normal(size=(8,10))
        V=enrich_basis(T,S,4)
        self.assertEqual(V.shape,(8,7))
        np.testing.assert_array_equal(V[:,:3],T)
        np.testing.assert_allclose(V.T@V,np.eye(7),atol=1e-12)
    def test_congruence_transfer(self):
        from dry_structural_modal import mobility
        M=np.eye(6);K=np.diag(np.arange(1.,7.));D=np.eye(6)+np.ones((6,6));P=np.eye(6)[:,:2]
        R,_=np.linalg.qr(np.random.default_rng(31).normal(size=(6,6)))
        m,V,e=model(M,K,D,P,R)
        np.testing.assert_allclose(mobility(np.diag(m['K']),m['D'],m['P'],[1.,2.]),mobility(np.diag(K),D,P,[1.,2.]),rtol=1e-10,atol=1e-12)
    def test_model(self):
        M=np.eye(6);K=np.diag(np.arange(1.,7.));D=np.eye(6)+np.ones((6,6));P=np.eye(6)[:,:2]
        m,V,e=model(M,K,D,P,np.eye(6)[:,:4])
        np.testing.assert_allclose(V.T@M@V,np.eye(4),atol=1e-12)
        self.assertGreater(np.linalg.eigvalsh(m['D']).min(),0)
        self.assertEqual(comparison(np.ones((2,2)),np.ones((2,2)))['maximum'],0.)
if __name__=='__main__':unittest.main()
