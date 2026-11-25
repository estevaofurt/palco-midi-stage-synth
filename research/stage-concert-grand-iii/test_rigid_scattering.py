import unittest
import numpy as np
from rigid_scattering import green,normal_derivative,exact_sphere_scattered,sphere_points,benchmark
class ScatteringTest(unittest.TestCase):
    def test_derivative(self):
        x=np.array([[1.,.2,0.]]);n=np.array([[1.,0.,0.]]);y=np.array([[2.,1.,1.]])
        h=1e-6
        np.testing.assert_allclose(normal_derivative(x,n,y,2.),(green(x+h*n,y,2.)-green(x-h*n,y,2.))/(2*h),rtol=1e-8)
    def test_analytic_neumann(self):
        a=.55;k=2.;n=sphere_points(25);x=a*n;y=np.array([[1.2,.3,.2],[.1,-1.4,.3]])
        total=lambda v:green(v,y,k)+exact_sphere_scattered(v,y,k,a)
        h=1e-5
        der=(-3*total(x)+4*total(x+h*n)-total(x+2*h*n))/(2*h)
        self.assertLess(np.linalg.norm(der)/np.linalg.norm(normal_derivative(x,n,y,k)),1e-6)
        z=exact_sphere_scattered(y,y,k,a)
        np.testing.assert_allclose(z,z.T,atol=1e-12)
    def test_benchmark(self):
        y=np.array([[1.2,.3,.2],[.1,-1.4,.3],[-1.2,.1,.4]])
        x=np.array([[1.5,1.,.5],[-.6,1.4,.2]])
        _,_,q=benchmark(.55,2.,y,x,96)
        self.assertTrue(q['gate'],q)
if __name__=='__main__':unittest.main()
