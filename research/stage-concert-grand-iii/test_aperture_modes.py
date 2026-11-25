import unittest
import numpy as np
from closed_cavity import assemble
from vented_cavity import aperture,response as scalar
from aperture_modes import aperture_modes,response,exterior
from ribbed_plate import quadrature
class ApertureTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[.3,0.],[.3,.2],[0.,.2]])
        self.q=assemble(self.poly,6,4,.24,lambda xy:np.c_[np.ones(len(xy)),xy[:,0]])
        self.points=[[.15,.1,.1]]
    def test_nested_flux_basis(self):
        ap,b,C=aperture_modes(self.q,self.poly,.12,6)
        _,a,F=aperture_modes(self.q,self.poly,.12,1)
        np.testing.assert_allclose(C[:,:1],F,atol=1e-12)
        xy,w=quadrature(ap,8);S=b(xy)
        np.testing.assert_allclose(b.area*S.T@(w[:,None]*S),np.eye(6),atol=1e-12)
        np.testing.assert_allclose(C.sum(0),[1,0,0,0,0,0],atol=1e-12)
    def test_scalar_parity(self):
        ap,A,C=aperture(self.q,self.poly,.12);_,_,D=aperture_modes(self.q,self.poly,.12,1)
        z=1000+200j;s=2j*np.pi*100
        x,p,u,t=scalar(self.q,C,s,self.points,z)
        y,q,v,r=response(self.q,D,s,self.points,np.array([[z]]))
        np.testing.assert_allclose(x,y,rtol=1e-11);np.testing.assert_allclose(p,q,rtol=1e-11)
        np.testing.assert_allclose(u,v[0],rtol=1e-11);self.assertTrue(t['gate'] and r['gate'])
    def test_passive_exterior(self):
        ap,b,C=aperture_modes(self.q,self.poly,.12,3)
        Z,r=exterior(ap,b,[100.],12,20,16,self.q['rho'],self.q['c'])[0]
        self.assertTrue(r['gate'])
        _,_,_,m=response(self.q,C,2j*np.pi*100,self.points,Z)
        self.assertTrue(m['gate']);self.assertGreater(m['exteriorPowerTrace'],0)
        with self.assertRaises(ValueError):response(self.q,C,2j*np.pi*100,self.points,-np.eye(3))
if __name__=='__main__':unittest.main()
