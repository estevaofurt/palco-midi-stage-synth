import unittest
import numpy as np
from bem_strip_audit import audit_change,reliable,physical
class StripAuditTest(unittest.TestCase):
    def test_reliability_and_physical_separate(self):
        a=dict(heldoutResidual=.2,heldoutWorstColumn=.3,reciprocity=0.)
        P=np.eye(2,dtype=complex);C=P.copy();F=P.copy()
        self.assertTrue(reliable(audit_change(a,a,P,C,P,C)))
        self.assertFalse(physical(a,P,C,F)['physicalGate'])
        b=dict(a,heldoutResidual=.05)
        self.assertFalse(reliable(audit_change(a,b,P,C,P,C)))
        self.assertFalse(reliable(audit_change(a,a,P,C,1.03*P,C)))
        c=dict(a,heldoutResidual=.02,heldoutWorstColumn=.04)
        self.assertTrue(physical(c,P,C,F)['physicalGate'])
        H=np.diag([1.,-.001])
        self.assertFalse(physical(c,H,H,H)['physicalGate'])
if __name__=='__main__':unittest.main()
