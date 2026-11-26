import unittest
from unison_profiles import PROFILES,KEYS
from nominal_unison import screen
class NominalTest(unittest.TestCase):
    def test_profiles(self):
        self.assertEqual(len(PROFILES),6)
        self.assertEqual(PROFILES[0][1],(0.,0.,1.,0.))
        self.assertTrue(all(len(p)==len(KEYS) and min(p)>=0 for _,p in PROFILES))
    def test_preservation(self):
        def row(r,t,m=1.):
            return dict(comparison=[dict(fundamentalCommonT60S=t,lateUpperEnergyPa2S=1.,upperDominanceWindowsCommon=0)],
                middle=[dict(middleEnergyAfter5s=m,middleWarningWindows=0)],pressureEnvelope=dict(fundamental=[dict(rippleRmsDb=r)]),attackComparison=dict(gate=True))
        self.assertTrue(screen(row(.55,15),row(.5,13))['candidateGate'])
        self.assertFalse(screen(row(.8,15),row(.5,13))['candidateGate'])
        self.assertFalse(screen(row(.5,10),row(.5,13))['candidateGate'])
        self.assertFalse(screen(row(.5,15,1.1),row(.5,13))['candidateGate'])
if __name__=='__main__':unittest.main()
