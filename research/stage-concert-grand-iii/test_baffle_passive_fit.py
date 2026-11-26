import unittest
import numpy as np
from baffle_passive_fit import dictionary,evaluate,fit,audit
class PassiveFitTest(unittest.TestCase):
    def test_manufactured(self):
        cfg=dict(relax=[80.],osc=[],gamma=30.,ridge=1e-12)
        C=np.array([[[.003,.0002],[.0002,.005]],[[2.,.3],[.3,1.]]])
        freq=np.geomspace(10,1000,12);Y=evaluate(2j*np.pi*freq,C,cfg)
        X,opt=fit(freq,Y,cfg,maxiter=5000,tol=1e-8)
        self.assertTrue(opt['converged'])
        self.assertTrue(audit(X,cfg)['gate'])
        self.assertLess(np.linalg.norm(evaluate(2j*np.pi*freq,X,cfg)-Y)/np.linalg.norm(Y),1e-5)
    def test_dc_and_passivity(self):
        cfg=dict(relax=[40.,200.],osc=[120.],gamma=20.,ridge=1e-6)
        C=np.repeat(np.eye(3)[None,:,:],4,axis=0)
        self.assertTrue(audit(C,cfg)['gate'])
        with self.assertRaises(ValueError):dictionary([-1+1j],cfg)
    def test_nonpassive_input(self):
        cfg=dict(relax=[80.],osc=[],gamma=30.,ridge=1e-6)
        with self.assertRaises(ValueError):fit([30.,80.],-np.ones((2,1,1)),cfg)
if __name__=='__main__':unittest.main()
