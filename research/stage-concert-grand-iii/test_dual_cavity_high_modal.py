import unittest
from dual_cavity_high_modal_diagnostic import require_screen
class HighModalGuardTest(unittest.TestCase):
    def test_screen(self):
        doc=dict(scaleSha256='a'*64,summary=dict(angleDeg=30,gate=True,diagnosticOnly=True,screeningMinimumEnergy=.95),
            cases=[dict(boundaryN=160,wedgeLayers=24,minimumCapture={'55':.951})],
            lower=[dict(planarN=72,degrees={'55':dict(minimumCapturedEnergy=.999)})])
        self.assertEqual(require_screen(doc,30,'a'*64),(.951,.999))
        with self.assertRaises(ValueError):require_screen(doc,55,'a'*64)
        doc['cases'][0]['minimumCapture']['55']=.94
        with self.assertRaises(ValueError):require_screen(doc,30,'a'*64)
if __name__=='__main__':unittest.main()
