import unittest
from bem_evidence import summarize,METRICS
class EvidenceTest(unittest.TestCase):
    def setUp(self):
        self.m=dict(key='p1',run=1,role='solver',audit='audit',family='six-point')
        self.job=dict(status='completed',conclusion='success')
        self.freq=[30,80,150]
        self.doc=dict(summary=dict(gate=True,angleDeg=30),scaleSha256='a'*64,cases=[dict(elements=64,
            reports=[dict(frequencyHz=f,audit={k:.001 for k in METRICS}) for f in self.freq])])
    def test_pass_requires_complete_evidence(self):
        self.assertTrue(summarize(self.m,30,self.job,self.doc,self.freq)['solverApproved'])
        self.assertFalse(summarize(self.m,30,dict(status='in_progress'),self.doc,self.freq)['solverApproved'])
        self.assertFalse(summarize(self.m,55,self.job,self.doc,self.freq)['solverApproved'])
        self.assertFalse(summarize(self.m,30,self.job,None,self.freq)['solverApproved'])
        self.doc['cases'][0]['reports'][0]['audit']['powerRelative']=.02
        self.assertEqual(summarize(self.m,30,self.job,self.doc,self.freq)['state'],'inconsistent-pass')
    def test_partial_and_diagnostic(self):
        self.doc.pop('summary')
        self.assertEqual(summarize(self.m,30,self.job,self.doc,self.freq)['state'],'partial')
        self.m['role']='diagnostic';self.doc['summary']=dict(gate=True,angleDeg=30)
        self.assertFalse(summarize(self.m,30,self.job,self.doc,self.freq)['solverApproved'])
    def test_adaptive_reference_not_final(self):
        self.m['rowKind']='adaptive';self.doc['cases'][0]['kind']='adaptive'
        self.doc['cases'].append(dict(kind='uniformReference',elements=1024,reports=[]))
        self.assertEqual(summarize(self.m,30,self.job,self.doc,self.freq)['elements'],64)
if __name__=='__main__':unittest.main()
