import unittest
import numpy as np
from coupled_modal_midpoint import CoupledModal,probe
class CoupledTest(unittest.TestCase):
    def test_equivalence_energy(self):
        self.assertTrue(probe(12,8000,.06)['gate'])
    def test_zero_map(self):
        a=CoupledModal([1.],[100.],[0.],np.zeros((1,1)),np.ones((4,1,1)),[100.],5.,8000)
        w=0.
        for _ in range(100):v,ds,da=a.step(np.ones(1));w+=v;self.assertEqual(da,0.)
        self.assertAlmostEqual(w,a.energy(),places=12)
    def test_negative_mass(self):
        with self.assertRaises(ValueError):CoupledModal([-1.],[100.],[0.],np.ones((1,1)),np.ones((4,1,1)),[100.],5.,8000)
if __name__=='__main__':unittest.main()
