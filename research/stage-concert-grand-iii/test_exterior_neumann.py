import unittest
import numpy as np
from exterior_neumann import fit,audit
from rigid_scattering import sphere_points
from neumann_envelope import envelope,internal,geometry_audit
from split_radiation import relative
class ExteriorNeumannTest(unittest.TestCase):
    def test_uniform_sphere(self):
        a=.5;f=80.;c=343.;rho=1.204;k=2*np.pi*f/c
        src=.65*a*sphere_points(96)
        n=sphere_points(288,.3);x=a*n;w=np.full(len(x),4*np.pi*a*a/len(x))
        q,r=fit(x,n,w,np.ones((len(x),1)),src,k)
        n=sphere_points(385,1.1);x=a*n;w=np.full(len(x),4*np.pi*a*a/len(x))
        Z,P,r=audit(x,n,w,np.ones((len(x),1)),src,q,k,[[1.,0.,0.]])
        expected=4*np.pi*a*a*1j*rho*c*k/(1/a+1j*k)
        self.assertLess(abs(Z[0,0]-expected)/abs(expected),.01)
        self.assertTrue(r['gate'],r)
    def test_envelope_closure(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,.8],[0.,.8]])
        for angle in (30,55):
            s,p,c=envelope(poly,.24,angle,3,lambda x:np.ones((len(x),1)))
            r=geometry_audit(s,p,c);self.assertTrue(r['gate'],r)
            self.assertEqual(len(p),4)
            self.assertAlmostEqual(r['volume'],.8*(.24+.5*np.sin(np.deg2rad(angle))),places=10)
            self.assertTrue(np.isfinite(internal(s,p,c,2)).all())
if __name__=='__main__':unittest.main()
