import unittest,copy
from fixed_snapshot_transfer import require_snapshot
from snapshot_reduction import RANKS
from dual_cavity_spatial_diagnostic import FREQ
from fixed_355_validation import METRICS
class TransferTest(unittest.TestCase):
    def evidence(self):
        rows=[]
        for k in RANKS:
            gate=k>=24
            rows.append(dict(rankLimit=k,maximumModes=k*7,gate=gate,comparison=dict(gate=gate,maximum={m:.01 if gate else .1 for m in METRICS}),
                folds=[dict(heldOutHz=f,trainingHz=[x for x in FREQ if x!=f],counts=[k]*7) for f in FREQ]))
        s=dict(gate=True,angleDeg=55.,diagnosticOnly=True,referenceModes=385,leaveOneFrequencyOut=True,reductionGate=True,
            independentGeometryValidated=False,continuousFrequencyValidated=False,timeDomainReady=False,
            modalConvergenceCertified=False,radiationReady=False,provisionalRank=24,provisionalModes=168)
        return dict(summary=s,cases=rows,scaleSha256='x',frequenciesHz=FREQ)
    def test_selection(self):
        d=self.evidence();self.assertEqual(require_snapshot(d,55.,'x'),24)
        d['summary']['provisionalRank']=32
        with self.assertRaises(ValueError):require_snapshot(d,55.,'x')
    def test_no_leakage(self):
        d=self.evidence();d['cases'][0]['folds'][0]['trainingHz']=FREQ
        with self.assertRaises(ValueError):require_snapshot(d,55.,'x')
    def test_no_approval(self):
        d=self.evidence();d['cases'][-2]['comparison']['maximum']['flow']=.08
        with self.assertRaises(ValueError):require_snapshot(d,55.,'x')
if __name__=='__main__':unittest.main()
