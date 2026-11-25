import json,unittest
from pathlib import Path
import numpy as np
from spatial_layout import segment_distance_xy,build
class LayoutTest(unittest.TestCase):
    def test_crossing(self):
        v=lambda x:np.array(x,dtype=float)
        self.assertEqual(segment_distance_xy(v([0,0]),v([1,1]),v([0,1]),v([1,0])),(0.,True))
    def test_parallel(self):
        v=lambda x:np.array(x,dtype=float)
        d,hit=segment_distance_xy(v([0,0]),v([1,0]),v([0,2]),v([1,2]))
        self.assertAlmostEqual(d,2.);self.assertFalse(hit)
    def test_endpoints(self):
        v=lambda x:np.array(x,dtype=float)
        d,hit=segment_distance_xy(v([0,0]),v([1,0]),v([2,0]),v([3,0]))
        self.assertAlmostEqual(d,1.);self.assertFalse(hit)
    def test_layout(self):
        scale=json.loads(Path('/tmp/g3-geometry/scale_geometry.json').read_text());cfg=json.loads(Path(__file__).with_name('layout_hypothesis.json').read_text())
        r=build(scale,cfg);self.assertEqual(r['summary']['locatedPorts'],678)
        self.assertFalse(r['summary']['geometryReady'])
        self.assertTrue(all(w['rearNonSpeakingLengthM'] is None for w in r['wires']))
        self.assertTrue(all(abs(m['heightAboveAnchorM']-.12)<1e-12 for m in r['capture']))
    def test_reject_collisions(self):
        scale=json.loads(Path('/tmp/g3-geometry/scale_geometry.json').read_text());cfg=json.loads(Path(__file__).with_name('layout_hypothesis.json').read_text())
        cfg['layout']['bassHeightM']=cfg['layout']['trebleHeightM']
        with self.assertRaises(AssertionError):build(scale,cfg)
if __name__=='__main__':unittest.main()
