import unittest
import numpy as np
from aperture_modes import FluxBasis
from inclined_lid import build
from lid_exterior import ports,load
from ribbed_plate import quadrature
class QuinticTest(unittest.TestCase):
    def test_nested_orthonormal_basis(self):
        poly=np.array([[0.,0.],[1.,0.],[1.1,.6],[.6,1.],[0.,.8]])
        xy,w=quadrature(poly,12);b=FluxBasis(poly,21);S=b(xy)
        np.testing.assert_allclose(S.T@(w[:,None]*S),np.eye(21)/b.area,atol=1e-8)
        np.testing.assert_allclose(w@S,np.r_[1.,np.zeros(20)],atol=1e-9)
        for n in (1,3,6,10,15):
            np.testing.assert_allclose(S[:,:n],FluxBasis(poly,n)(xy),atol=1e-8)
    def test_3d_ports(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,2.],[0.,2.]])
        m,C,q=build(poly,4,2,.24,55,lambda x:np.ones((len(x),1)))
        p,V=ports(m,C,q,21)
        np.testing.assert_allclose(V[:,::21],C,atol=1e-10)
        np.testing.assert_allclose(V.sum(0),np.tile(np.r_[1.,np.zeros(20)],3),atol=1e-9)
        Z,rep=load(p,[50.],8,14,12)[0]
        self.assertEqual(Z.shape,(63,63))
        self.assertLess(rep['gramVsSurface'],1e-8)
        self.assertGreaterEqual(rep['passivityMinRelative'],-1e-10)
if __name__=='__main__':unittest.main()
