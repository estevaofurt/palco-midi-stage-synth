import unittest,copy
from fixed_355_validation import require_common,require_fine,valid_metrics,COUNTS,METRICS,FREQ
class FixedTest(unittest.TestCase):
    def test_metrics(self):
        m={k:.05 for k in METRICS}
        self.assertTrue(valid_metrics(m))
        for v in (float('nan'),float('inf'),-.1,.050001,True):
            self.assertFalse(valid_metrics(dict(m,flow=v)))
        self.assertFalse(valid_metrics({'flow':0.}))
    def test_common(self):
        d=dict(scaleSha256='x',frequenciesHz=FREQ,summary=dict(gate=True,diagnosticOnly=True,angles=[30,55],retrospectiveSelection=True,modalConvergenceCertified=False,radiationReady=False,commonSelection=dict(counts=list(COUNTS),totalModes=355,gate=True,maximum={k:.03 for k in METRICS})))
        require_common(d,'x')
        with self.assertRaises(ValueError):require_common(d,'y')
        d['summary']['commonSelection']['counts'][0]=45
        with self.assertRaises(ValueError):require_common(d,'x')
    def test_fine(self):
        d=dict(scaleSha256='x',frequenciesHz=FREQ,geometry=dict(gate=True),cases=[dict(frequencyHz=f,upper=dict(gate=True),coupled=dict(gate=True)) for f in FREQ],summary=dict(gate=True,angleDeg=30,diagnosticOnly=True,upperConfig=[50,200,32],baselineConfig=[40,160,24],modes=385,lowerFixed=True,exteriorFixed=True,modalConvergenceCertified=False,fullCabinetReady=False,radiationReady=False,minimumCapture=.99,combinedUpperRefinementGate=True,comparison={k:.01 for k in METRICS}))
        require_fine(d,30,'x')
        for key,value in [('combinedUpperRefinementGate',False),('radiationReady',True),('minimumCapture',.94)]:
            q=copy.deepcopy(d);q['summary'][key]=value
            with self.assertRaises(ValueError):require_fine(q,30,'x')
        d['cases'].pop()
        with self.assertRaises(ValueError):require_fine(d,30,'x')
if __name__=='__main__':unittest.main()
