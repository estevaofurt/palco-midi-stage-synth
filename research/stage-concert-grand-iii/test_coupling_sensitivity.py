import unittest
import numpy as np
from coupling_sensitivity import prepare,compare_sensitivity
from dual_cavity_reference import couple
class SensitivityTest(unittest.TestCase):
    def fixture(self,perturb=0.):
        Zu=np.array([[4.,1.,.2],[1.,3.,.1],[.2,.1,2.]])+np.diag([0.,perturb,0.])
        Zl=np.array([[3.,.4],[.4,1.5]])
        Ze=np.eye(3)*.2;Ze[0,1]=Ze[1,0]=.03
        return Zu,Zl,Ze
    def test_identity_and_operator_only(self):
        a=self.fixture();b=self.fixture(.2)
        def get(x):
            u,l,e=x
            p=prepare(u,l,e,1,[2,1],[.1,2.])
            y,p1,p2,p3,F,r=couple(u,np.eye(3),l,np.eye(2),e,np.eye(3),1,reference_kind='common-free-space-monopole')
            return p,F
        x,f=get(a);y,g=get(b)
        q=compare_sensitivity(x,y,f,g)
        self.assertAlmostEqual(q['physicalFlowChange'],q['impedanceContribution'],places=12)
        self.assertAlmostEqual(q['excitationContribution'],0.)
        self.assertLess(q['decompositionClosure'],1e-12)
        self.assertGreaterEqual(q['upperBound']+1e-12,q['physicalFlowChange'])
        self.assertEqual(compare_sensitivity(x,x,f,f)['physicalFlowChange'],0.)
    def test_excitation_only(self):
        u,l,e=self.fixture();x=prepare(u,l,e,1,[2,1],[.1,2.])
        u=u.copy();u[0,1]+=0.1;u[1,0]+=0.1
        y=prepare(u,l,e,1,[2,1],[.1,2.])
        f=np.linalg.solve(x['A'],x['B'])*x['scale'][:,None]
        g=np.linalg.solve(y['A'],y['B'])*y['scale'][:,None]
        q=compare_sensitivity(x,y,f,g)
        self.assertAlmostEqual(q['physicalFlowChange'],q['excitationContribution'],places=12)
        self.assertEqual(q['impedanceContribution'],0.)
    def test_geometry_validation(self):
        u,l,e=self.fixture()
        with self.assertRaises(ValueError):prepare(u,l,e,1,[2,1],[0.,1.])
        with self.assertRaises(ValueError):prepare(u,l,e,1,[2,2],[1.,1.])
if __name__=='__main__':unittest.main()
