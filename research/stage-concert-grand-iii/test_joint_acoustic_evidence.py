import unittest
from joint_acoustic_evidence import delta,joint,FACTORS

def ep(n):return dict(lastWindowEndS=n,rightCensored=n==40)
def fixture(speed,passes):
    rows=[]
    for f in FACTORS:
        a=f in passes
        rows.append(dict(speed=speed,bridgeFactor=f,wet=True,seconds=5,fundamentalRatioToDry=[[1.,1.]]*5,
            vsDryNominal=dict(attackScreeningGate=a),attackScreeningGate=a,lateWindowAtLeastDry=True,attackBalance=0.,tailBalance=0.))
    return dict(summary=dict(gate=True,diagnosticOnly=True,cases=3,speed=speed,seconds=5,rate=48000,
        bridgeFactors=list(FACTORS),otherDampingNominal=True,noOutputEQ=True,selectedParameters=None,
        physicalFeedbackAccepted=False,audibleSustainMeasured=False,eligibleForLongTest=list(passes)),cases=rows)
class JointTest(unittest.TestCase):
    def test_censoring(self):
        self.assertEqual(delta(ep(30),ep(20))['exactDifferenceS'],10)
        r=delta(ep(40),ep(30));self.assertEqual(r['lowerBoundS'],10);self.assertIsNone(r['exactDifferenceS'])
        self.assertEqual(delta(ep(30),ep(40))['upperBoundS'],-10)
        self.assertIsNone(delta(ep(40),ep(40))['lowerBoundS'])
    def test_both_speeds(self):
        r=joint({.3:fixture(.3,{.75,.5}),3.:fixture(3.,{.5,.25})})
        self.assertEqual([x['bridgeFactor'] for x in r if x['eligibleForLongTest']],[.5])
    def test_gate_mismatch(self):
        a=fixture(.3,{.75});a['cases'][0]['lateWindowAtLeastDry']=False
        with self.assertRaises(ValueError):joint({.3:a,3.:fixture(3.,{.75})})
if __name__=='__main__':unittest.main()
