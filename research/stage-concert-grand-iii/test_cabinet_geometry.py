import unittest
import numpy as np
from cabinet_geometry import geometry
class CabinetTest(unittest.TestCase):
    def setUp(self):
        self.poly=np.array([[0.,0.],[1.,0.],[1.,2.],[0.,2.]])
        self.layout=dict(capture=[dict(xyzM=[.2,.5,.17]),dict(xyzM=[.8,1.5,.17])],
          wires=[dict(bridgeXYZ_m=[.3,.5,.09],radiusM=.002)])
        self.cfg=dict(version='fixture',rimTopZ_m=.24,rimBottomZ_m=-.18,lidAnglesDeg=[0,30,55],limitations=[])
    def test_area_volume(self):
        q=geometry(self.poly,self.layout,self.cfg)
        self.assertAlmostEqual(q['summary']['sideWallAreaM2'],2.52)
        self.assertAlmostEqual(q['summary']['closedUpperPrismM3'],.48)
        self.assertAlmostEqual(q['summary']['lowerPrismInventoryM3'],.36)
        self.assertAlmostEqual(q['lidCases'][0]['uncoveredPlanAreaM2'],0.)
        self.assertAlmostEqual(q['lidCases'][1]['projectedAreaM2'],2*np.cos(np.pi/6))
    def test_rotation(self):
        q=geometry(self.poly,self.layout,self.cfg)
        for case in q['lidCases']:
            v=np.asarray(case['verticesXYZ_m'])
            np.testing.assert_allclose(np.linalg.norm(v-np.roll(v,-1,axis=0),axis=1),[1,2,1,2])
            self.assertAlmostEqual(min(v[:,2]),.24)
        self.assertTrue(q['lidCases'][0]['micUnderProjection'][1])
        self.assertFalse(q['lidCases'][-1]['micUnderProjection'][1])
    def test_no_reposition(self):
        q=geometry(self.poly,self.layout,self.cfg)
        self.assertEqual(q['microphonesXYZ_m'],[p['xyzM'] for p in self.layout['capture']])
        self.assertFalse(q['summary']['geometryReady']);self.assertFalse(q['summary']['acousticsReady'])
if __name__=='__main__':unittest.main()
