import unittest
import numpy as np
from high_modal_surface_audit import compare_smooth,require_angular
class SurfaceTest(unittest.TestCase):
    def test_fixed_flow(self):
        R=np.eye(2);P=np.array([[1.,2.]])
        F=np.array([[1j],[2.]])
        self.assertEqual(max(compare_smooth((R,P),(R,P),F).values()),0.)
        rr=compare_smooth((R,P),(2*R,2*P),F)
        np.testing.assert_allclose(list(rr.values()),.5)
    def test_guard(self):
        with self.assertRaises(ValueError):require_angular({},30,'a'*64)
if __name__=='__main__':unittest.main()
