import unittest
import numpy as np
from scipy.special import j1,struve
from scipy.integrate import quad
from radiation_impedance import impedance,audit,retarded_pressure
from radiation_resistance import pressure,surface
from ribbed_plate import quadrature
def uniform(x,p):return np.ones((len(x),1))
class ImpedanceTest(unittest.TestCase):
    def test_disk_reference(self):
        # Independent exact overlap-area convolution for circular piston.
        a=.12;rho=1.204;c=343.;A=np.pi*a*a
        def overlap(r):return 2*a*a*np.arccos(r/(2*a))-.5*r*np.sqrt(max(0.,4*a*a-r*r))
        for f in (80,500,2000):
            w=2*np.pi*f;k=w/c
            z=rho*1j*w*complex(quad(lambda r:overlap(r)*np.cos(k*r),0,2*a,epsabs=1e-12,epsrel=1e-12)[0],-quad(lambda r:overlap(r)*np.sin(k*r),0,2*a,epsabs=1e-12,epsrel=1e-12)[0])
            ref=rho*c*A*(1-j1(2*k*a)/(k*a)+1j*struve(1,2*k*a)/(k*a))
            self.assertLess(abs(z/ref-1),1e-8)
    def test_polygon_resistance(self):
        p=np.array([[0.,0.],[.3,0.],[.3,.2],[0.,.2]]);rho=1.204;c=343.;f=500.
        xy,w=quadrature(p,16);S=uniform(xy,p)
        Z=impedance(p,uniform,2j*np.pi*f,rho,c,20,24)
        R=surface(xy,w,S,f,rho,c)
        np.testing.assert_allclose(Z.real,R,rtol=1e-8)
        self.assertGreater(Z.imag[0,0],0)
    def test_laplace_and_reciprocity(self):
        p=np.array([[0.,0.],[.3,0.],[.3,.2],[0.,.2]])
        def fields(x,p):return np.c_[np.ones(len(x)),x[:,0],x[:,1]]
        Z=impedance(p,fields,100+500j,1.204,343.,24,28);a=audit(Z)
        self.assertLess(a['reciprocity'],1e-4);self.assertGreater(a['passivityMinRelative'],-1e-10)
    def test_retarded_observation(self):
        p=np.array([[0.,0.],[.3,0.],[.3,.2],[0.,.2]])
        xy,w=quadrature(p,12);S=uniform(xy,p);pts=[[.1,.1,.17],[.2,.1,1.]]
        f=500.;omega=2*np.pi*f;t=.02
        q=retarded_pressure(xy,w,S,pts,t,lambda x:(1j*omega*np.exp(1j*omega*x))[...,None],1.204,343.)
        np.testing.assert_allclose(q,pressure(xy,w,S,pts,f,1.204,343.)[:,0]*np.exp(1j*omega*t),rtol=1e-12)
        q=retarded_pressure(xy,w,S,pts,0.,lambda x:np.maximum(x,0)[...,None],1.204,343.)
        np.testing.assert_array_equal(q,0.)
if __name__=='__main__':unittest.main()
