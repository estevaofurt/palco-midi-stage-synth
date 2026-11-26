import unittest
from unison_profiles import profiles_for_key,KEYS
from attack_flutter import variants
from nominal_unison import screen
class NominalTest(unittest.TestCase):
    def test_profiles(self):
        for key in KEYS:
            with self.subTest(key=key):
                profiles=profiles_for_key(key)
                self.assertEqual(len(profiles),6)
                approved=dict(variants(key))['nominal_structure']
                s=approved['spread']
                self.assertEqual(profiles[0][1],(0.,0.,s,0.))
                self.assertTrue(all(p[2]==s for _,p in profiles[:4]))
                self.assertTrue(all(len(p)==len(KEYS) and min(p)>=0 for _,p in profiles))
        with self.assertRaises(ValueError):profiles_for_key(61)
    def test_preservation(self):
        def row(r,t,m=1.):
            return dict(comparison=[dict(fundamentalCommonT60S=t,lateUpperEnergyPa2S=1.,upperDominanceWindowsCommon=0)],
                middle=[dict(middleEnergyAfter5s=m,middleWarningWindows=0)],pressureEnvelope=dict(fundamental=[dict(rippleRmsDb=r)]),attackComparison=dict(gate=True))
        self.assertTrue(screen(row(.55,15),row(.5,13))['candidateGate'])
        self.assertFalse(screen(row(.8,15),row(.5,13))['candidateGate'])
        self.assertFalse(screen(row(.5,10),row(.5,13))['candidateGate'])
        self.assertFalse(screen(row(.5,15,1.1),row(.5,13))['candidateGate'])
if __name__=='__main__':unittest.main()
