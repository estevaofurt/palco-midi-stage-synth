import unittest
import numpy as np
from edge_screen import EdgeBasis,operators
from rigid_screen import geometry,coupling
from lid_exterior import Panel,load
from screen_aperture import interaction,screen_samples,correction,observe
class CouplingTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[1.,0.],[1.,1.],[0.,1.]])
        self.local,self.o,self.A,self.n=geometry(self.poly,0,0)
        self.b=EdgeBasis(self.local,3)
    def test_point_source_parity(self):
        x,S=screen_samples(self.b,self.o,self.A,16)
        y=np.array([[.3,.4,.6],[.7,.5,-.8]])
        np.testing.assert_allclose(interaction(x,S,y,np.eye(2),self.n,2.),coupling(self.b,self.o,self.A,self.n,y,2.,16),atol=1e-12)
    def test_distributed_source(self):
        xyz=np.array([[.2,.2,-.7],[.8,.2,-.7],[.8,.8,-.7],[.2,.8,-.7]])
        p=[Panel(xyz,np.array([0.,0.,1.]),3)]
        f=80.;k=2*np.pi*f/343.;W=operators(self.b,[k],12,22)[0]
        Z0,_=load(p,[f],12,22,20)[0]
        Z,Q,rep=correction(self.b,W,self.o,self.A,self.n,p,Z0,f,2,16,16)
        self.assertLess(rep['powerRelative'],.01,rep)
        self.assertGreater(rep['correctionRelative'],0)
        self.assertGreaterEqual(rep['passivityMinRelative'],-1e-8,rep)
        self.assertTrue(np.isfinite(observe(self.b,Q,self.o,self.A,self.n,p,np.eye(3),[[.5,.5,1.]],f,16)).all())
if __name__=='__main__':unittest.main()
