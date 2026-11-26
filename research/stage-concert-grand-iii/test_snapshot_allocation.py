import unittest
from snapshot_allocation import configurations,choose,common_report
from fixed_355_validation import METRICS
from dual_cavity_spatial_diagnostic import FREQ

class AllocationTest(unittest.TestCase):
    def evidence(self,angle):
        rows=[]
        for c in configurations():
            ok=c[-1]==24 and (c[0]==24 if angle==30 else c[1]==24)
            rows.append(dict(counts=list(c),totalModes=sum(c),gate=ok,maximum={m:.01 if ok else .1 for m in METRICS}))
        return dict(summary=dict(gate=True,angleDeg=angle,diagnosticOnly=True,referenceModes=385,leaveOneFrequencyOut=True,
            trainedOnFine=False,exhaustiveAllocations=128,retrospectiveSelection=True,timeDomainReady=False,radiationReady=False,selected=choose(rows)),
            cases=rows,scaleSha256='x',frequenciesHz=FREQ)
    def test_common(self):
        a,b=self.evidence(30),self.evidence(55)
        r=common_report(a,b,'x')['summary']['commonSelection']
        self.assertEqual(r['counts'],[24,24,16,16,16,16,24])
        self.assertEqual(r['totalModes'],136)
    def test_corrupt(self):
        a,b=self.evidence(30),self.evidence(55)
        a['cases'][0]['gate']=True
        with self.assertRaises(ValueError):common_report(a,b,'x')
    def test_inventory(self):
        a,b=self.evidence(30),self.evidence(55)
        a['cases'].pop()
        with self.assertRaises(ValueError):common_report(a,b,'x')
if __name__=='__main__':unittest.main()
