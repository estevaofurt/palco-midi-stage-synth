import unittest
import numpy as np
from continuous_bridge import build,segment,response
class BeamTest(unittest.TestCase):
    def test_element(self):
        L=.2;m,k,f=segment(L,.5,50.,1e5);rigid=np.array([1.,0.,1.,0.]);linear=np.array([0.,1.,L,1.])
        self.assertAlmostEqual(float(rigid@m@rigid),.5*L)
        self.assertLess(np.linalg.norm(k@rigid),1e-8);self.assertLess(np.linalg.norm(k@linear),1e-8)
        self.assertAlmostEqual(float(rigid@f@rigid),1e5*L)
    def test_cantilever(self):
        L=.5;rho=660;E=10e9;w=.025;h=.022
        a=build([[0,0,0],[L,0,0]],4,rho,E,w,h,0.)
        K=a['K'][2:,2:];F=np.zeros(len(K));F[-2]=1.
        x=np.linalg.solve(K,F);EI=E*w*h**3/12
        self.assertAlmostEqual(x[-2]/(L**3/(3*EI)),1.,places=10)
        self.assertAlmostEqual(x[-1]/(L**2/(2*EI)),1.,places=10)
    def test_mass_and_ports(self):
        a=build([[0,0,0],[.1,.02,0],[.2,.03,0]],2,660,1e10,.025,.022,2e6)
        q=np.zeros(len(a['M']));q[::2]=1
        self.assertAlmostEqual(float(q@a['M']@q),a['massKg'],places=12)
        self.assertEqual(a['attachmentDofs'].tolist(),[0,4,8])
        z=response(a,[0,1,2],[100,500,2000],30,1e-5)
        self.assertGreater(abs(z['Y'][1,0,4]),0.);self.assertLess(z['reciprocity'],1e-10)
        self.assertGreaterEqual(z['passivityMinRelative'],-1e-10)
if __name__=='__main__':unittest.main()
