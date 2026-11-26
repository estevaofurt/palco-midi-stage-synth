import unittest,itertools
from graded_reference_audit import configurations,choose,require_graded
from graded_common_allocation import common
class AuditTest(unittest.TestCase):
    def test_allocation(self):
        cfg=list(itertools.chain.from_iterable(configurations(k) for k in range(8)))
        self.assertEqual(len(set(cfg)),128)
        def rows(required):
            return [dict(counts=list(c),maximum=dict(physicalVelocityRelative=.03 if all(c[i]==55 for i in required) else .1),gate=all(c[i]==55 for i in required)) for c in cfg]
        a,b=rows([0,1]),rows([1,2])
        best,rr=common(a,b);self.assertEqual(best['totalModes'],345);self.assertEqual(best['counts'][:3],[55,55,55])
        with self.assertRaises(ValueError):common(a[:-1],b)
        with self.assertRaises(ValueError):require_graded({},30,'a'*64)
if __name__=='__main__':unittest.main()
