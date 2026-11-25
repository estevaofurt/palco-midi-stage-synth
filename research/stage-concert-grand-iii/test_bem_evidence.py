import unittest
from bem_evidence import summarize,METRICS
class EvidenceTest(unittest.TestCase):
    def setUp(self):
        self.m=dict(key='p1',run=1,role='solver',audit='audit',family='six-point')
        self.job=dict(status='completed',conclusion='success')
        self.freq=[30,80,150]
        self.doc=dict(summary=dict(gate=True,angleDeg=30),scaleSha256='a'*64,cases=[dict(elements=64,gate=True,
            reports=[dict(frequencyHz=f,audit=dict(**{k:.001 for k in METRICS},passivityMinRelative=0.)) for f in self.freq])])
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
    def test_passivity_and_scope(self):
        from copy import deepcopy
        for key,value in [('passivityMinRelative',-1e-4),('passivityMinRelative',None)]:
            x=deepcopy(self.doc);x['cases'][0]['reports'][0]['audit'][key]=value
            self.assertFalse(summarize(self.m,30,self.job,x,self.freq)['solverApproved'])
        x=deepcopy(self.doc);x['summary']['diagnosticOnly']=True
        self.assertFalse(summarize(self.m,30,self.job,x,self.freq)['solverApproved'])
        x=deepcopy(self.doc);x['scaleSha256']='z'*64
        self.assertFalse(summarize(self.m,30,self.job,x,self.freq)['solverApproved'])
    def test_policy_selection_and_diagnostic_gate(self):
        self.m.update(role='diagnostic',select=dict(policy='red',step=2))
        self.doc['cases'][0].update(policy='red',step=2)
        self.doc['cases'].append(dict(policy='strip',step=2,elements=90,reports=[]))
        row=summarize(self.m,30,self.job,self.doc,self.freq)
        self.assertEqual(row['elements'],64)
        self.assertTrue(row['diagnosticApproved']);self.assertFalse(row['solverApproved'])
        row=summarize(self.m,30,dict(status='in_progress'),self.doc,self.freq)
        self.assertFalse(row['diagnosticApproved'])
        self.doc['summary']['gate']=False
        row=summarize(self.m,30,self.job,self.doc,self.freq)
        self.assertEqual(row['state'],'diagnostic-fail')
    def test_frequency_specific_diagnostic(self):
        self.m.update(role='diagnostic',select=dict(outerOrder=8,innerOrder=10))
        self.doc['summary'].update(frequencyHz=80,diagnosticOnly=True,physicalGate=False)
        self.doc['cases']=[dict(elements=446,frequencyHz=80,outerOrder=8,innerOrder=10,
            audit=dict(**{k:.001 for k in METRICS},physicalGate=False,passivityMinRelative=-.001))]
        r=summarize(self.m,30,self.job,self.doc,self.freq,80)
        self.assertTrue(r['diagnosticApproved']);self.assertFalse(r['physicalGate'])
        self.assertFalse(r['solverApproved']);self.assertEqual(r['frequencyHz'],80)
        self.assertFalse(summarize(self.m,30,self.job,self.doc,self.freq,150)['diagnosticApproved'])
        self.assertEqual(summarize(self.m,30,dict(status='in_progress'),None,self.freq,80)['state'],'pending-artifact')
        self.doc['cases'][0]['frequencyHz']=30
        self.assertFalse(summarize(self.m,30,self.job,self.doc,self.freq,80)['diagnosticApproved'])
    def test_no_physical_gate_inference(self):
        self.m['role']='diagnostic'
        self.doc['cases'][0]['gate']=True
        self.assertIsNone(summarize(self.m,30,self.job,self.doc,self.freq)['physicalGate'])
if __name__=='__main__':unittest.main()
