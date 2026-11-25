import unittest
import numpy as np
from dual_cavity_spatial_diagnostic import compare_spatial
class SpatialTest(unittest.TestCase):
    def test_physical_flow_gate(self):
        a=[(np.eye(2),np.eye(2),np.eye(2),np.eye(2),np.array([[1.],[1.]]))]
        b=[(np.eye(2),np.eye(2),np.eye(2),np.eye(2),np.array([[1.1],[1.]]))]
        r=compare_spatial([30.],a,b,[1,1],[.1,1.])
        self.assertFalse(r['gate'])
        self.assertGreater(r['maximum']['physicalVelocityRelative'],r['maximum']['flow'])
        self.assertEqual(len(r['frequencies'][0]['flowPanels']),2)
        self.assertTrue(compare_spatial([30.],a,a,[1,1],[.1,1.])['gate'])
        with self.assertRaises(ValueError):compare_spatial([30.,80.],a,b,[1,1],[.1,1.])
if __name__=='__main__':unittest.main()
