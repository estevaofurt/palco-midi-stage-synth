import unittest
import numpy as np
from neumann_regularized import candidates,fit
from exterior_neumann import audit
from rigid_scattering import sphere_points
class RegularizedTest(unittest.TestCase):
    def test_rank_and_tuning(self):
        # A nearly invisible direction fits perturbations in training, but
        # is visible at the independent tuning points.
        A=np.array([[1.,1.],[0.,1e-10],[1.,1.]])
        B=np.array([[1.],[1e-4],[1.]])
        At=np.array([[1.,1.],[0.,1.]])
        Bt=np.array([[1.],[.5]])
        q,r=candidates(A,B,np.ones(3),At,Bt,np.ones(2),(1e-4,1e-13))
        self.assertEqual(r['selected']['rank'],1)
        self.assertLess(r['selected']['tuning']['aggregate'],1e-8)
        self.assertLess(np.linalg.norm(q),1.)
    def test_sphere(self):
        a=.5;k=2*np.pi*80/343.;rho=1.204;c=343.
        src=.65*a*sphere_points(72)
        def nodes(n,phase):
            v=sphere_points(n,phase)
            return a*v,v,np.full(n,4*np.pi*a*a/n),np.ones((n,1))
        q,r=fit(nodes(216,.3),nodes(289,1.1),src,k)
        x,n,w,V=nodes(385,2.1)
        Z,P,rep=audit(x,n,w,V,src,q,k,[[1.,0.,0.]])
        expected=4*np.pi*a*a*1j*rho*c*k/(1/a+1j*k)
        self.assertTrue(rep['gate'],rep)
        self.assertLess(abs(Z[0,0]-expected)/abs(expected),.01)
if __name__=='__main__':unittest.main()
