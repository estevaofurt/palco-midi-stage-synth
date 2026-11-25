import unittest
import numpy as np
from scipy.special import j1
from numpy.polynomial.legendre import leggauss
from radiation_resistance import angular,surface,pressure,far_amplitude,hemisphere
class RadiationTest(unittest.TestCase):
    def test_hemisphere(self):
        d,w=hemisphere(12);self.assertAlmostEqual(sum(w),2*np.pi,places=12)
        np.testing.assert_allclose(np.linalg.norm(d,axis=1),1.,atol=1e-14)
    def test_piston(self):
        a=.12;rho=1.204;c=343.;z,w=leggauss(12);radius=a*(z+1)/2
        phi=np.arange(64)*2*np.pi/64
        xy=np.stack([radius[:,None]*np.cos(phi),radius[:,None]*np.sin(phi)],axis=-1).reshape(-1,2)
        weights=np.repeat(w*a/2*radius*2*np.pi/64,64);S=np.ones((len(xy),1));A=np.pi*a*a
        for f in (80.,500.,2000.):
            ka=2*np.pi*f*a/c;ref=rho*c*A*(1-j1(2*ka)/ka)
            self.assertLess(abs(angular(xy,weights,S,f,rho,c,24)[0,0]/ref-1),1e-8)
            self.assertLess(abs(surface(xy,weights,S,f,rho,c)[0,0]/ref-1),1e-8)
    def test_power_and_pressure(self):
        xy=np.array([[0.,0.],[.3,.1],[.4,.5]]);w=np.array([.03,.02,.04]);S=np.array([[1.,1.],[1.,-1.],[1.,.3]])
        f=500.;rho=1.204;c=343.;R=angular(xy,w,S,f,rho,c,24)
        np.testing.assert_allclose(R,surface(xy,w,S,f,rho,c),rtol=1e-12,atol=1e-12)
        d,weights=hemisphere(24);v=np.array([.3+.1j,-.2+.4j])
        p=far_amplitude(xy,w,S,d,f,rho,c)@v
        self.assertAlmostEqual(.5*float((v.conj()@R@v).real),float(weights@abs(p)**2)/(2*rho*c),places=12)
        near=pressure(xy,w,S,[[0,0,10000]],f,rho,c)[0]*10000*np.exp(1j*2*np.pi*f*10000/c)
        np.testing.assert_allclose(near,far_amplitude(xy,w,S,[[0,0,1]],f,rho,c)[0],rtol=1e-3,atol=1e-4)
    def test_invalid(self):
        with self.assertRaises(ValueError):angular([[0,0]],[-1.],[[1.]],80,1.2,343.,12)
        with self.assertRaises(ValueError):pressure([[0,0]],[1.],[[1.]],[[0,0,0]],80,1.2,343.)
if __name__=='__main__':unittest.main()
