import unittest
import numpy as np
from structural_passive_fit import structural_impedance,subspace,project,lift,select_rank,TRAIN,CHECK
from baffle_passive_fit import evaluate
class StructuralFitTest(unittest.TestCase):
    def test_congruence(self):
        rng=np.random.default_rng(2);B=rng.normal(size=(4,3))
        C=rng.normal(size=(3,4,4));C=C@C.transpose(0,2,1)
        cfg=dict(relax=[40.],osc=[120.],gamma=35.,ridge=0.)
        Z=evaluate(2j*np.pi*np.array([30.,100.,300.]),C,cfg)
        Q=structural_impedance(Z,B)
        np.testing.assert_allclose(Q,evaluate(2j*np.pi*np.array([30.,100.,300.]),structural_impedance(C,B),cfg))
        U=subspace(Q);np.testing.assert_allclose(lift(project(Q,U),U),Q,atol=1e-10)
        sel,_=select_rank(Q,U);self.assertEqual(sel['rank'],3)
        self.assertTrue(set(TRAIN).isdisjoint(CHECK))
if __name__=='__main__':unittest.main()
