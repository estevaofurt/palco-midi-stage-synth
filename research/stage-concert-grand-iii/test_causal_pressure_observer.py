import unittest
import numpy as np
from causal_pressure_observer import build_kernel,delay_weights,stream_proof,harmonic_proof,Observer
class PressureTest(unittest.TestCase):
    def test_lagrange(self):
        for n in (1,3):
            x=np.linspace(0.,.999,101);nodes,w=delay_weights(x,n)
            for j in range(n+1):np.testing.assert_allclose(w@nodes.astype(float)**j,x**j,atol=1e-14)
    def test_point_quadrature(self):
        xy=np.array([[0.,0.],[.1,.2]]);w=np.array([.2,.1]);S=np.array([[1.,.2],[.4,1.]])
        mic=np.array([[0.,0.,.5],[.2,0.,1.5]])
        for rate in (48000,96000):
            K,s,d=build_kernel(xy,w,S,mic,rate,3)
            self.assertTrue(stream_proof(K,rate,s)['gate'])
            self.assertLess(max(v['velocityRelative'] for v in harmonic_proof(K,rate,xy,w,S,mic,[30.,500.])),.005)
            self.assertEqual(Observer(K,rate).process(np.zeros((0,2))).shape,(0,2))
if __name__=='__main__':unittest.main()
