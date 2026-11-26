import unittest
from loss_attribution import aggregate,TIMES
class AttributionTest(unittest.TestCase):
    def row(self):
        initial=[.2]+[.08]*10
        snapshots=[]
        for t in TIMES:
            l=[v*t/80 for v in initial];e=[x-y for x,y in zip(initial,l)]
            snapshots.append(dict(timeS=t,energyFraction=e,lossFraction=l,netBridgeWorkFraction=[0.]*11,
                positiveWindowNetFraction=[0.]*11,negativeWindowNetFraction=[0.]*11))
        return dict(components=['board','k45-s1','k45-s2','k48-s1','k48-s2','k60-s1','k60-s2','k60-s3','k64-s1','k64-s2','k64-s3'],
            initialEnergyFraction=initial,initialEnergyJ=1.,variant='approved',speed=3.,snapshots=snapshots)
    def test_aggregate(self):
        r=aggregate(self.row(),60)
        self.assertAlmostEqual(r['samples'][-1]['groups']['struckWires']['lossFraction'],.12)
        self.assertAlmostEqual(r['samples'][-1]['groups']['board']['energyFraction'],.1)
    def test_reject_bad_balance(self):
        r=self.row();r['snapshots'][-1]['lossFraction'][0]+=.01
        with self.assertRaises(ValueError):aggregate(r,60)
if __name__=='__main__':unittest.main()
