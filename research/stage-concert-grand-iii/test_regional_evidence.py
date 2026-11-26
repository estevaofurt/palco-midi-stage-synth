import unittest
from regional_evidence import crossing,compare,energy_summary,definitions
class RegionalTest(unittest.TestCase):
    def windows(self,n):
        return [dict(timeS=i,fundamentalRmsPa=1. if i<n else .0001) for i in range(40)]
    def test_censoring(self):
        a=crossing(self.windows(13),1.);b=crossing(self.windows(40),1.)
        self.assertEqual(a,dict(seconds=13,censored=False))
        self.assertTrue(compare(b,a)['extensionProven'])
        self.assertIsNone(compare(b,a)['deltaExactS'])
        self.assertFalse(compare(b,b)['extensionProven'])
        self.assertIsNone(compare(a,b)['deltaLowerBoundS'])
        self.assertFalse(compare(crossing(self.windows(14),1.),a)['extensionProven'])
        with self.assertRaises(ValueError):crossing(self.windows(13)[:-1],1.)
    def test_reference(self):
        self.assertEqual(definitions(48)['approved'],(0.,0.,0.,0.))
        self.assertEqual(definitions(60)['approved'],(0.,0.,1.,0.))
    def test_energy(self):
        r=dict(components=['board','k60-s1','k48-s1'],snapshots=[dict(timeS=40,energyFraction=[.1,.2,.1],lossFraction=[.2,.3,.1],netBridgeWorkFraction=[.1,-.2,.1])])
        self.assertAlmostEqual(energy_summary(r,60)['excitedGroupRemainingFraction'],.2)
        r['snapshots'][0]['lossFraction'][0]=.3
        with self.assertRaises(ValueError):energy_summary(r,60)
if __name__=='__main__':unittest.main()
