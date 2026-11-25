import unittest
import numpy as np
from localized_edge_basis import LocalBasis
from edge_screen import EdgeBasis,operators
from rigid_screen import geometry
from lid_exterior import Panel,load
from screen_aperture import correction
from split_radiation import relative
class LocalTest(unittest.TestCase):
    def test_mass_gradient_prefix(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,.8],[0.,.8]])
        b=LocalBasis(poly,3);x,w=b.samples(48);V=b.evaluate(x)[0]
        np.testing.assert_allclose(V.T@(w[:,None]*V),np.eye(b.count),atol=1e-8,rtol=0)
        np.testing.assert_allclose(V[:,:b.n0],EdgeBasis(poly,3).evaluate(x)[0],atol=1e-8)
        q=np.array([[.13,.28],[.7,.5]]);v,dx,dy=b.evaluate(q);h=1e-6
        for d,g in [(np.array([h,0.]),dx),(np.array([0.,h]),dy)]:
            fd=(b.evaluate(q+d)[0]-b.evaluate(q-d)[0])/(2*h)
            self.assertLess(relative(fd,g),1e-6)
    def test_nested_solve_and_guards(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
        local,o,A,n=geometry(poly,0,0);b=LocalBasis(local,2,(.25,.08))
        panels=[Panel(np.array([[.2,.2,-.7],[.8,.2,-.7],[.8,.8,-.7],[.2,.8,-.7]]),n,1)]
        f=80.;k=2*np.pi*f/343.;W=operators(b,[k],10,18)[0]
        z0,_=load(panels,[f],10,18,16)[0]
        args=(b,W,o,A,n,panels,z0,f,2,12,12)
        z,Q,r=correction(*args,subspace=(b.prefix(1),b.count))
        self.assertTrue(np.isfinite(z).all())
        self.assertLess(r['powerRelative'],.01)
        with self.assertRaises(ValueError):correction(*args,subspace=(b.count,b.count))
if __name__=='__main__':unittest.main()
