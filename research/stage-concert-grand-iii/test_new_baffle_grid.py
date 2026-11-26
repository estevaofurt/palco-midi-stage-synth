import unittest
import numpy as np
from new_baffle_grid import check_grid,coordinate_audit,DEVELOPMENT,RESERVED,EXTENSION
class GridTest(unittest.TestCase):
    def test_split(self):
        check_grid()
        self.assertEqual((len(DEVELOPMENT),len(RESERVED),len(EXTENSION)),(8,7,4))
    def test_coordinate_guard(self):
        keys=('stiffness','damping','ports','wirePorts','physicalLift','regionalDamping')
        a={k:np.eye(3) for k in keys}
        self.assertEqual(max(coordinate_audit(a,a).values()),0.)
        b=dict(a,physicalLift=-np.eye(3))
        with self.assertRaises(ValueError):coordinate_audit(a,b)
if __name__=='__main__':unittest.main()
