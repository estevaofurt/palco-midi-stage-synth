import unittest
import numpy as np
from disjoint_enriched_refinement import scales
from enriched_reactive_diagnostic import block_changes
class DisjointTest(unittest.TestCase):
    def test_small_subblock_is_not_hidden(self):
        a=np.ones((2,56,56));b=a.copy()
        a[:,55,55]=2e-12;b[:,55,55]=1e-12
        c=block_changes(a,b);s=scales(a,b)
        self.assertLess(c['whole'],1e-8)
        self.assertAlmostEqual(c['11'],1.)
        self.assertLess(s['11']['maximumDifferenceFraction'],1e-8)
    def test_no_extra_modes_on_lower_port(self):
        a=np.ones((2,56,55))
        self.assertEqual(set(scales(a,a)),{'00','10'})
if __name__=='__main__':unittest.main()
