import unittest,copy
from verified_disjoint_archive import check_history
class VerifyTest(unittest.TestCase):
    def test_reused(self):
        old=dict(gate=True,changes={'00':0.})
        new=dict(priorGate=True,gate=True,finalOrder=48,history=[])
        check_history(old,new)
        with self.assertRaises(ValueError):check_history(old,dict(new,finalOrder=56))
    def test_recovered(self):
        old=dict(gate=False,changes={'00':1e-6})
        h=[dict(orders=[48,56],changes={'00':1e-9},polynomialRestriction=1e-10,gate=True),
           dict(orders=[56,64],changes={'00':1e-9},polynomialRestriction=1e-10,gate=True)]
        new=dict(priorGate=False,gate=True,finalOrder=64,history=h)
        check_history(old,new)
        for field,value in [('gate',False),('finalOrder',72),('history',h[:1])]:
            with self.assertRaises(ValueError):check_history(old,dict(new,**{field:value}))
        bad=copy.deepcopy(new);bad['history'][1]['changes']['00']=float('nan')
        with self.assertRaises(ValueError):check_history(old,bad)
        bad=copy.deepcopy(new);bad['history'][1]['changes']['00']=1e-5
        with self.assertRaises(ValueError):check_history(old,bad)
if __name__=='__main__':unittest.main()
