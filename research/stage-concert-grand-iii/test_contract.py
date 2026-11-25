import copy,json,unittest
from pathlib import Path
from validate_contract import validate
class ContractTest(unittest.TestCase):
    def setUp(self):self.c=json.loads(Path(__file__).with_name('contrato.json').read_text())
    def bad(self,mutate):
        mutate(self.c)
        with self.assertRaises(ValueError):validate(self.c)
    def test_valid(self):self.assertFalse(validate(self.c)['listeningEligible'])
    def test_unknown(self):self.bad(lambda c:c['reference']['capture']['hammerSpeedMps'].update(value=1.))
    def test_datum(self):self.bad(lambda c:c['reference']['capture']['heightAboveStringsM'].update(value=1.))
    def test_holdout(self):self.bad(lambda c:c['reference'].update(holdoutOpened=True))
    def test_phase_order(self):self.bad(lambda c:c['phases'][2].update(status='passed',evidence=[{'commit':'fixture','report':'fixture'}]))
    def test_missing_evidence(self):self.bad(lambda c:c['phases'][0].update(status='passed',evidence=[]))
    def test_listening(self):self.bad(lambda c:c['phases'][10].update(status='implemented'))
    def test_samples(self):self.bad(lambda c:c['requirements'].update(externalAudioInEngine=True))
    def test_unlock_synthetic(self):
        for p in self.c['phases'][:10]:p.update(status='passed',evidence=[{'commit':'synthetic','report':'synthetic'}])
        self.assertTrue(validate(self.c)['listeningEligible'])
if __name__=='__main__':unittest.main()
