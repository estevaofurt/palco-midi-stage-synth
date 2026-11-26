import unittest
from fine_mode_loss import incremental
def row(mid,up,t,peak=1.,mw=0,uw=0,gate=True):
    return dict(comparison=[dict(channel=1,lateUpperEnergyPa2S=up,fundamentalCommonT60S=t,
        fundamentalPeakRelative=peak,upperDominanceWindowsCommon=uw)],
        middle=[dict(middleEnergyAfter5s=mid,targetEnergyAfter1s={'791':mid},middleWarningWindows=mw)],
        screening=dict(candidateGate=gate))
class FineLossTest(unittest.TestCase):
    def test_improvement(self):
        b=row(1.,1.,36)
        self.assertTrue(incremental(row(.7,.5,35),b)['incrementalGate'])
        self.assertFalse(incremental(row(1.1,.5,35),b)['incrementalGate'])
        self.assertFalse(incremental(row(.7,.5,34),b)['incrementalGate'])
        self.assertFalse(incremental(row(.7,.5,35,gate=False),b)['incrementalGate'])
    def test_reference_is_not_candidate(self):
        b=row(1.,1.,36)
        self.assertFalse(incremental(b,b)['incrementalGate'])
if __name__=='__main__':unittest.main()
