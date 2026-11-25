import unittest
import numpy as np
from inclined_lid import build
from lid_exterior import load,pressure,ports
from port_coordinates import audit,same_coordinates
from aperture_modes import response
from split_radiation import relative
class PortCoordinatesTest(unittest.TestCase):
    def test_basis_and_mesh_independence(self):
        poly=np.array([[0.,0.],[1.,0.],[1.3,.7],[1.,1.8],[0.,2.]])
        field=lambda x:np.c_[np.ones(len(x)),x[:,0]]
        m,C,r=build(poly,4,2,.24,55,field)
        a,b,Co,Cn,T,rep=audit(m,C,r,21)
        self.assertTrue(rep['gate'],rep)
        m2,C2,r2=build(poly,8,3,.24,55,field)
        c,_=ports(m2,C2,r2,21,canonical=True)
        self.assertTrue(same_coordinates(b,c)['gate'])
    def test_physical_invariance(self):
        poly=np.array([[0.,0.],[1.,0.],[1.,2.],[0.,2.]])
        m,C,r=build(poly,6,3,.24,30,lambda x:np.c_[np.ones(len(x)),x[:,0]])
        a,b,Co,Cn,T,rep=audit(m,C,r,3);self.assertTrue(rep['gate'],rep)
        Z,rr=load(a,[80.],12,22,20)[0]
        Zn=T.T@Z@T
        p=[[.3,.6,.12]]
        y,pr,U,ro=response(m,Co,2j*np.pi*80,p,Z)
        yn,pn,Un,rn=response(m,Cn,2j*np.pi*80,p,Zn)
        self.assertTrue(ro['gate'] and rn['gate'])
        np.testing.assert_allclose(y,yn,rtol=1e-8,atol=1e-8)
        np.testing.assert_allclose(pr,pn,rtol=1e-8,atol=1e-8)
        np.testing.assert_allclose(U,T@Un,rtol=1e-8,atol=1e-8)
        q=load(b,[80.],12,22,20)[0][0]
        self.assertLess(relative(q,Zn),.01)
        self.assertLess(relative(pressure(a,U,[[3.,3.,2.]],80,12),pressure(b,Un,[[3.,3.,2.]],80,12)),.001)
if __name__=='__main__':unittest.main()
