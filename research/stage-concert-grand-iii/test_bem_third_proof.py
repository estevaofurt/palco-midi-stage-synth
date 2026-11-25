import unittest
from bem_third_proof import require_refinement
class ThirdProofTest(unittest.TestCase):
    def test_provenance(self):
        base=dict(summary=dict(meshSha256='a'*64,densitySha256='b'*64))
        s=dict(gate=True,angleDeg=30.,frequencyHz=80.,diagnosticOnly=True,fixedDensity=True,sourceElements=628,
            sourceMeshSha256='a'*64,sourceDensitySha256='b'*64,solverApproved=False,radiationReady=False,
            convergence=dict(gate=True),againstArchivedAudit=dict(heldoutResidual=.001),
            candidateMeshes=[dict(elementBudget=850,file='third_strip_850.npz',geometryAudit=dict(gate=True))])
        doc=dict(scaleSha256='c'*64,summary=s)
        self.assertEqual(require_refinement(doc,base,30.,'c'*64,850)['elementBudget'],850)
        with self.assertRaises(ValueError):require_refinement(doc,base,30.,'c'*64,1050)
        s['sourceDensitySha256']='d'*64
        with self.assertRaises(ValueError):require_refinement(doc,base,30.,'c'*64,850)
if __name__=='__main__':unittest.main()
