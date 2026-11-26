import unittest
import numpy as np
from response_weighted_fit import weight,states
from structural_passive_fit import project,lift
class WeightTest(unittest.TestCase):
    def test_congruence(self):
        G=np.array([[2.,.4],[.4,1.]])
        X=np.array([[[1.,.2],[.2,.5]],[[2.,.3],[.3,1.]]])
        for strength in (0.,3.,15.):
            T,I=weight(G,strength)
            Y=lift(project(X,T),I)
            np.testing.assert_allclose(Y,X,atol=1e-12)
            self.assertGreaterEqual(np.linalg.eigvalsh(Y).min(),0.)
    def test_state(self):
        md=dict(M=np.eye(2),K=np.diag([100.,200.]),D=np.eye(2),P=np.eye(2))
        Z=.2*np.eye(2);f=3.;w=2*np.pi*f
        np.testing.assert_allclose(states(md,[],[],Z,f),1j*w*np.linalg.inv(md['K']-w*w*md['M']+1j*w*(md['D']+Z)))
if __name__=='__main__':unittest.main()
