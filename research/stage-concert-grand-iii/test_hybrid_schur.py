import unittest
import numpy as np
from scipy.sparse import csc_matrix
from hybrid_schur import solve_interface
from hybrid_cavity import build,response
from split_radiation import relative
class SchurTest(unittest.TestCase):
    def test_complex_indefinite_system(self):
        rng=np.random.default_rng(27);A=rng.normal(size=(20,20));W=A+A.T+1j*np.eye(20)
        D=rng.normal(size=(5,5));D=D+D.T;B=rng.normal(size=(20,3))+1j*rng.normal(size=(20,3))
        X,r=solve_interface(csc_matrix(W),D,B,block=2)
        W[:5,:5]+=D
        np.testing.assert_allclose(X,np.linalg.solve(W,B),atol=1e-12)
        self.assertLess(r['residual'],1e-12)
        self.assertLess(r['interfaceDenseMatrixBytes'],r['fullDenseMatrixBytes'])
        with self.assertRaises(ValueError):solve_interface(W,D,B)
    def test_layered_hybrid_equivalence(self):
        poly=np.array([[0.,0.],[1.,0.],[1.2,.7],[.7,1.5],[0.,1.]])
        field=lambda x:np.c_[np.ones(len(x)),x[:,0]]
        for layers in (1,4):
            m=build(poly,8,1,.24,55,field,10,wedge_layers=layers)
            for f in (30.,80.,150.,250.):
                Z,P,r=response(m,f,[[.3,.5,.12]],solver='dense')
                z,p,rr=response(m,f,[[.3,.5,.12]],solver='schur')
                self.assertTrue(r['gate'] and rr['gate'])
                self.assertLess(relative(Z,z),1e-9);self.assertLess(relative(P,p),1e-9)
if __name__=='__main__':unittest.main()
