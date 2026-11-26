import unittest
import numpy as np
from types import SimpleNamespace
from bridge_energy import energies,balance_step,step_block
from compiled_wire_midpoint import Compiled

class Ledger(unittest.TestCase):
    def test_net_work(self):
        a=np.array([1.,2.]);b=np.array([.7,2.2]);loss=np.array([.1,0.])
        w,e=balance_step(a,b,loss,.1,3.)
        np.testing.assert_allclose(w,[-.2,.2],atol=1e-14)
        self.assertLess(e,1e-14)
        with self.assertRaises(ValueError):balance_step(a,b,loss,.2,3.)
    def test_compiled_replay(self):
        # One normalized interior and one physical rear coordinate.
        w=SimpleNamespace(m=np.array([.1]),k=np.array([.2]),d=np.array([.01]),
            w2=np.array([100.]),gamma=np.array([.3]),M=np.array([[.5,.1],[.1,1.]]),
            K=np.array([[20.,.2],[.2,100.]]),D=np.array([[.1,.01],[.01,.3]]),
            P=np.array([.1,1.]),p=np.array([1.]),port=0)
        args=(np.array([400.]),np.array([[.2]]),np.zeros((1,1)),np.array([[.5]]),[w],48000,1)
        a,b=Compiled(*args),Compiled(*args)
        for m in (a,b):m.q[:]=.1;m.x[:]=.2;m.v[:]=.3;m.u[:]=.4
        initial=energies(a);E0=a.energy()
        self.assertAlmostEqual(initial.sum(),E0)
        acc,loss,total=step_block(a,127)
        F=np.zeros((127,1));O=F.copy();L=np.zeros((127,2));A=F.copy()
        b.process(F,O,L,A)
        np.testing.assert_array_equal(acc,A)
        for attr in ('q','v','x','u'):np.testing.assert_array_equal(getattr(a,attr),getattr(b,attr))
        self.assertAlmostEqual(total,L[:,1].sum())
        balance_step(initial,energies(a),loss,total,E0)
if __name__=='__main__':unittest.main()
