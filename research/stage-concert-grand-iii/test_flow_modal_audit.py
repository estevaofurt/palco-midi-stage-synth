import unittest
import numpy as np
from flow_modal_audit import audit_flow,pressure_defect
class FlowTest(unittest.TestCase):
    def test_area_and_omission(self):
        T=np.eye(4)[:,[0,2]];high=np.array([[1.],[2.],[3.],[4.]])
        low=np.array([[2.],[0.],[3.],[0.]])
        r=audit_flow(low,high,T,[2,2],[1.,4.])
        self.assertAlmostEqual(r['physicalVelocityRelative'],np.sqrt(9/11.25))
        self.assertAlmostEqual(r['resolvedRelative'],np.sqrt(1/11.25))
        self.assertAlmostEqual(r['omittedRelative'],np.sqrt(8/11.25))
        self.assertLess(r['orthogonalClosure'],1e-12)
        self.assertAlmostEqual(sum(p['errorEnergyFraction'] for p in r['panels']),1.)
        with self.assertRaises(ValueError):audit_flow(high,high,T,[2,2],[1.,4.])
    def test_pressure_defect(self):
        Z=np.array([[2.,1.,2.],[1.,3.,0.],[2.,0.,4.]])
        Ze=np.eye(4);T=np.eye(4)[:,[0,2]]
        F=np.array([[.25],[0.],[-.25],[0.]])
        r=pressure_defect(Z,Z,Ze,F,T,1)
        self.assertLess(r['resolvedRelative'],1e-14)
        self.assertGreater(r['omittedRelative'],0.)
if __name__=='__main__':unittest.main()
