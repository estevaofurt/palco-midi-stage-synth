import unittest
import numpy as np
from physical_joint_decay import configurations,reference,attack_metrics
class JointTest(unittest.TestCase):
    def test_grid(self):
        a=configurations();self.assertEqual(len(a),16);self.assertEqual(len(set(a)),16);self.assertEqual(a[0],(0.,1.))
    def test_reference(self):
        rms=np.array([[1.,2.,3.,4.,0.,0.],[2.,1.,4.,3.,0.,0.]])
        r=reference(rms,2)
        np.testing.assert_allclose(r,[2.,2.,np.sqrt(12.5),2.])
        x=attack_metrics(dict(mechanicalEnergyJ=.1,injectedJ=.2),rms,4.)
        self.assertEqual(x['mechanicalTransferFraction'],.5)
        self.assertEqual(x['first50msPlateRelative'],.5)
if __name__=='__main__':unittest.main()
