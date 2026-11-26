import unittest
from new_frequency_validation import NEW,FREQ,require_basis
from fixed_355_validation import METRICS
class NewTest(unittest.TestCase):
    def test_grid(self):
        self.assertFalse(set(NEW)&set(FREQ))
        self.assertEqual(len(NEW),3)
    def test_basis(self):
        s=dict(gate=True,angleDeg=30.,diagnosticOnly=True,rank=24,modes=168,referenceModes=385,trainingMesh=[40,160,24],
            validationMesh=[50,200,32],fixedBasis=True,trainedOnFine=False,independentUpperMeshValidated=True,
            continuousFrequencyValidated=False,timeDomainReady=False,modalConvergenceCertified=False,radiationReady=False,
            maximum={k:{m:.01 for m in METRICS} for k in ('coarseModal','fineModal','fullSpatial','reducedSpatial','combined')})
        d=dict(summary=s,scaleSha256='x',frequenciesHz=FREQ)
        require_basis(d,30.,'x')
        s['trainedOnFine']=True
        with self.assertRaises(ValueError):require_basis(d,30.,'x')
if __name__=='__main__':unittest.main()
