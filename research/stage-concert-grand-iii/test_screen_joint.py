import unittest
import numpy as np
from edge_screen import EdgeBasis,operators
from rigid_screen import geometry
from lid_exterior import Panel,load
from screen_aperture import correction
from shared_edge_quadrature import assemble
class JointScreenTest(unittest.TestCase):
    def test_separated_parity_and_shape_guard(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
        local,o,A,n=geometry(poly,0,0);b=EdgeBasis(local,3)
        xyz=np.array([[.2,.2,-.7],[.8,.2,-.7],[.8,.8,-.7],[.2,.8,-.7]])
        panels=[Panel(xyz,np.array([0.,0.,1.]),3)]
        f=80.;k=2*np.pi*f/343.;W=operators(b,[k],12,22)[0]
        Z0,_=load(panels,[f],12,22,20)[0]
        B,rep=assemble(b,o,A,n,panels,[k],16,True)
        self.assertEqual(rep['sharedPairs'],0)
        args=(b,W,o,A,n,panels,Z0,f,2,16,16)
        z,q,r=correction(*args)
        zj,qj,rj=correction(*args,interaction_block=B[0])
        np.testing.assert_allclose(z,zj,rtol=1e-5,atol=1e-7)
        self.assertLess(rj['powerRelative'],.01,rj)
        with self.assertRaises(ValueError):correction(*args,interaction_block=np.zeros((1,1)))
if __name__=='__main__':unittest.main()
