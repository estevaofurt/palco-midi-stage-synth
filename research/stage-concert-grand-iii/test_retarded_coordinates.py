import unittest
import numpy as np
from retarded_coordinates import align
class CoordinateTest(unittest.TestCase):
    def test_signed_permutation(self):
        R=dict(physicalLift=np.array([[1.,2.],[3.,4.],[2.,-1.]]),stiffness=np.array([2.,3.]),damping=np.diag([.1,.2]),ports=np.eye(2),wirePorts=np.eye(2),regionalDamping=np.array([np.diag([.1,.2])]))
        Q=np.array([[0.,-1.],[1.,0.]])
        L=dict(physicalLift=R['physicalLift']@Q,stiffness=np.diag(Q.T@np.diag(R['stiffness'])@Q),damping=Q.T@R['damping']@Q,ports=Q.T@R['ports'],wirePorts=R['wirePorts']@Q,regionalDamping=np.array([Q.T@R['regionalDamping'][0]@Q]))
        q,e=align(L,R);np.testing.assert_allclose(q,Q,atol=1e-12)
        L['stiffness']+=1.
        with self.assertRaises(ValueError):align(L,R)
if __name__=='__main__':unittest.main()
