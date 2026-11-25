import unittest
import numpy as np
from scipy.linalg import block_diag
from lid_exterior import Panel,load,pressure
from nested_acoustic_ports import embedding,reduced_panels,project,coupled_projection
from dual_cavity_reference import couple
class NestedPortTest(unittest.TestCase):
    def setUp(self):
        a=np.array([[0.,0.,0.],[1.,0.,0.],[1.,.7,0.],[0.,1.,0.]])
        self.high=[Panel(a,np.array([0.,0.,1.]),21),Panel(a+[0.,0.,-.3],np.array([0.,0.,-1.]),21)]
    def test_all_nested_degrees_and_orientation(self):
        for n in (1,3,6,10,15,21):
            low=reduced_panels(self.high,[n,n]);T,r=embedding(self.high,low)
            self.assertEqual(T.shape,(42,2*n));self.assertTrue(r['gate'])
        with self.assertRaises(ValueError):embedding(self.high,self.high[::-1])
    def test_independent_load_projection(self):
        high=reduced_panels(self.high,[6,6]);low=reduced_panels(high,[3,3]);T,_=embedding(high,low)
        (Zh,rh),=load(high,[80.],12,22,24);(Zl,rl),=load(low,[80.],12,22,24)
        Ph=pressure(high,np.eye(12),[[2.,0.,.5]],80.,12)
        Pl=pressure(low,np.eye(6),[[2.,0.,.5]],80.,12)
        Z,P=project(Zh,Ph,T)
        np.testing.assert_allclose(Z,Zl,rtol=1e-8,atol=1e-8)
        np.testing.assert_allclose(P,Pl,rtol=1e-8,atol=1e-8)
    def test_coupled_projection(self):
        low=reduced_panels(self.high,[6,10]);Tu,_=embedding(self.high[:1],low[:1]);Tl,_=embedding(self.high[1:],low[1:])
        rng=np.random.default_rng(12);nb=2
        def matrix(n):
            A=rng.normal(size=(n,n));return A.T@A+np.eye(n)+1j*np.eye(n)
        Zu,Zl,Ze=matrix(23),matrix(23),matrix(42)
        Pu,Pl,Pe=np.eye(23),np.eye(23),np.eye(42)
        Y,pu,pl,pf,F,r=coupled_projection(Zu,Pu,Zl,Pl,Ze,Pe,Tu,Tl,nb)
        U,L,T=block_diag(np.eye(nb),Tu),block_diag(np.eye(nb),Tl),block_diag(Tu,Tl)
        z,p1,p2,p3,f,rr=couple(U.T@Zu@U,Pu@U,L.T@Zl@L,Pl@L,T.T@Ze@T,Pe@T,nb,reference_kind='common-free-space-monopole')
        np.testing.assert_allclose(Y,z,atol=1e-10);np.testing.assert_allclose(F,T@f,atol=1e-10)
        self.assertTrue(r['gate']);self.assertFalse(r['radiationReady'])
    def test_prior_reference_guard(self):
        from dual_cavity_modal_diagnostic import prerequisite
        from copy import deepcopy
        f=[30.,80.,150.,200.,250.,300.]
        metrics=dict.fromkeys(('impedance','upperPressure','lowerPressure','exteriorPressure','flow'),.01)
        doc=dict(scaleSha256='a'*64,frequenciesHz=f,
            summary=dict(gate=True,angleDeg=30,commonFreeSpaceMonopolesOnly=True,
                upperApertureModes=36,lowerMouthModes=10,boardFields=4,
                radiationReady=False,fullCabinetReady=False,
                meshConvergence=metrics.copy(),quadratureConvergence=metrics.copy()),
            cases=[dict(gate=True,reports=[dict(frequencyHz=x) for x in f]) for _ in range(4)])
        prerequisite(doc,30,'a'*64)
        for key,value in [('gate',False),('radiationReady',True),('lowerMouthModes',21),('meshConvergence',{})]:
            invalid=deepcopy(doc);invalid['summary'][key]=value
            with self.assertRaises(ValueError):prerequisite(invalid,30,'a'*64)
        with self.assertRaises(ValueError):prerequisite(doc,55,'a'*64)
        with self.assertRaises(ValueError):prerequisite(doc,30,'b'*64)
        invalid=deepcopy(doc);invalid['cases'][0]['reports'].pop()
        with self.assertRaises(ValueError):prerequisite(invalid,30,'a'*64)
if __name__=='__main__':unittest.main()
