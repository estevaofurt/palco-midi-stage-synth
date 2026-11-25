import unittest
import numpy as np
from high_modal_allocation import degree_energy,select_next,require_archive
class AllocationTest(unittest.TestCase):
    def test_physical_energy(self):
        F=np.zeros((110,2),complex);F[54,0]=2j;F[55,1]=2
        E=degree_energy(F,[1.,4.])
        self.assertAlmostEqual(E[0,9],.8);self.assertAlmostEqual(E[1,0],.2);self.assertAlmostEqual(E.sum(),1.)
        with self.assertRaises(ValueError):degree_energy(F,[1.,0.])
    def test_selection(self):
        f=lambda v:dict(maximum=dict(physicalVelocityRelative=v,impedance=.01))
        a=(((55,45),f(.2)),((45,55),f(.1)))
        self.assertEqual(select_next((45,45),a)[0],(45,55))
        with self.assertRaises(ValueError):select_next((45,45),[((55,55),f(.1))])
    def test_archive_guard(self):
        with self.assertRaises(ValueError):require_archive({},30,'a'*64)
if __name__=='__main__':unittest.main()
