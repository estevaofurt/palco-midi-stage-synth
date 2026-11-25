import unittest
import numpy as np
from screen_residual_energy import audit,metric,norm
class EnergyResidualTest(unittest.TestCase):
    def test_static_galerkin_identity(self):
        W=np.array([[4.,1.,.2],[1.,3.,.4],[.2,.4,2.]])
        B=np.array([[1.,2.],[3.,1.],[2.,1.]])
        Q=np.zeros_like(B);Q[:2]=np.linalg.solve(W[:2,:2],B[:2])
        r=audit(W,B,Q,W)
        self.assertAlmostEqual(r['dualStaticRelative'],r['enrichedSolutionRelative'],places=12)
        self.assertLess(r['staticIdentityRelative'],1e-12)
        self.assertLess(r['enrichedResidual'],1e-12)
    def test_invariance_under_basis_scaling(self):
        W0=np.array([[3.,.2],[.2,2.]])
        W=W0+1j*np.eye(2);B=np.array([[1.],[2.]])
        Q=np.array([[.5+.1j],[0.]])
        T=np.diag([.001,100.])
        r=audit(W,B,Q,W0);s=audit(T.T@W@T,T.T@B,np.linalg.solve(T,Q),T.T@W0@T)
        for k in ('dualStaticRelative','enrichedSolutionRelative'):
            self.assertAlmostEqual(r[k],s[k],places=11)
    def test_active_static_guard(self):
        with self.assertRaises(np.linalg.LinAlgError):metric(-np.eye(2))
if __name__=='__main__':unittest.main()
