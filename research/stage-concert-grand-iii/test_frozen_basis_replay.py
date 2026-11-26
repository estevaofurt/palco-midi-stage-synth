import unittest
import numpy as np
from frozen_basis_replay import benchmark,require_120,CFG
from fixed_355_validation import METRICS
from dual_cavity_spatial_diagnostic import FREQ
class ReplayTest(unittest.TestCase):
    def test_benchmark(self):
        A=np.eye(5,dtype=complex)*2;B=np.ones((5,4));T=np.eye(5)[:,:3]
        r=benchmark(A,B,T,3);self.assertEqual(r['modes'],3);self.assertGreater(r['medianMs'],0)
    def test_basis(self):
        s=dict(gate=True,angleDeg=30.,diagnosticOnly=True,rankDistribution=CFG,modes=120,referenceModes=385,
            trainingMesh=[40,160,24],validationMesh=[50,200,32],fixedBasis=True,trainedOnFine=False,independentUpperMeshValidated=True,
            continuousFrequencyValidated=False,timeDomainReady=False,modalConvergenceCertified=False,radiationReady=False,
            maximum={k:{m:.01 for m in METRICS} for k in ('coarseModal','fineModal','fullSpatial','reducedSpatial','combined')})
        d=dict(summary=s,scaleSha256='x',frequenciesHz=FREQ)
        require_120(d,30.,'x')
        s['rankDistribution']=[24]*7
        with self.assertRaises(ValueError):require_120(d,30.,'x')
if __name__=='__main__':unittest.main()
