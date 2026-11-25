import unittest,json
from pathlib import Path
import numpy as np
from board_contour import hull,properties,margins,clip_line,build
ROOT=Path(__file__).parent
class ContourTest(unittest.TestCase):
    def test_square(self):
        p=hull([[0,0],[1,0],[1,1],[0,1],[.5,.5]])
        a,c,l=properties(p);self.assertAlmostEqual(a,1.);self.assertAlmostEqual(l,4.);np.testing.assert_allclose(c,[.5,.5])
        np.testing.assert_allclose(margins(p,[[.5,.5],[1.2,.5]]),[.5,-.2])
    def test_clip(self):
        p=hull([[0,0],[1,0],[1,1],[0,1]])
        self.assertEqual(clip_line(p,np.array([.5,0]),np.array([0,1])),(0.,1.))
        self.assertIsNone(clip_line(p,np.array([2.,0]),np.array([0,1])))
    def test_inventory(self):
        nodes=[dict(wireId=str(i),footProjectionXYZ_m=[.5+i*.001,.5,0.]) for i in range(226)]
        l=dict(boardEnvelope=dict(x=[0,1.4],y=[0,1.6]),bridgeAttachmentNodes=dict(bass=nodes[:43],treble=nodes[43:]),frame={})
        cfg=json.loads((ROOT/'board_contour_hypothesis.json').read_text());m=json.loads((ROOT/'board_interface_hypothesis.json').read_text())
        z=build(l,cfg,m);self.assertEqual(z['summary']['attachmentCount'],226);self.assertEqual(len(z['ribs']),12)
        self.assertFalse(z['summary']['boardReady']);self.assertGreaterEqual(z['summary']['minAttachmentMarginM'],.008-1e-12)
        l['bridgeAttachmentNodes']['bass'][0]['footProjectionXYZ_m']=[0.,.5,0.]
        with self.assertRaises(ValueError):build(l,cfg,m)
if __name__=='__main__':unittest.main()
