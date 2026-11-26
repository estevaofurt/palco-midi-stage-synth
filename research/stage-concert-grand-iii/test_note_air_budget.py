import unittest
import numpy as np
from note_air_budget import power_budget,one,wire_displacement
from types import SimpleNamespace
from string_structure import Wire
class NoteAirTest(unittest.TestCase):
    def test_budget(self):
        d=power_budget(10.,2.,3.,[4.,1.])
        self.assertAlmostEqual(d['airFraction'],.3)
        self.assertAlmostEqual(sum(d['wireFractions']),.5)
        with self.assertRaises(ValueError):power_budget(10.,2.,3.,[4.])
        with self.assertRaises(ValueError):power_budget(10.,2.,-1.,[9.])
    def test_wire_coordinate_recovery(self):
        w=SimpleNamespace(U=np.array([[2.,0.],[0.,3.]]))
        w.recover=Wire.recover.__get__(w)
        q=wire_displacement(w,1.,2.,np.array([.1,.2]),np.array([.5,.6]))
        np.testing.assert_allclose(q,[1.,1.8,3.])
    def test_single_board(self):
        md=dict(M=np.eye(1),K=np.array([[100.]]),D=np.array([[2.]]),P=np.ones((1,1)))
        a=one(md,np.empty((0,1)),[],np.array([[3.+1j]]),np.ones((1,1)),2.,0)
        self.assertAlmostEqual(a['wet']['airFraction'],.6)
        self.assertAlmostEqual(a['dry']['airFraction'],0.)
        self.assertAlmostEqual(a['wet']['structureFraction'],.4)
if __name__=='__main__':unittest.main()
