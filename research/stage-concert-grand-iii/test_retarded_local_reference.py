import unittest
import numpy as np
from unittest.mock import patch
from retarded_local_reference import local_group
class LocalReferenceTest(unittest.TestCase):
    def test_external_comparison(self):
        Z=np.eye(2,dtype=complex);H=np.ones((1,2),complex);Y=np.eye(2,dtype=complex);O=np.ones((1,2),complex)
        archived=dict(mobility=Y[None,None],observation=O[None,None])
        with patch('retarded_local_reference.kernel',return_value=(Z,H,dict(gate=True))),patch('retarded_local_reference.response',return_value=(Y,O,dict(gate=True))):
            d,a=local_group([100.],None,None,None,np.eye(2),None,[(None,None)],archived)
            self.assertEqual(a[0]['externalMaximum'],0.)
            np.testing.assert_array_equal(d['mobility'],archived['mobility'])
        with patch('retarded_local_reference.kernel',return_value=(Z,H,dict(gate=False))):
            with self.assertRaises(ValueError):local_group([100.],None,None,None,np.eye(2),None,[(None,None)],archived)
if __name__=='__main__':unittest.main()
