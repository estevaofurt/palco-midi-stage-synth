import unittest,json,os
from pathlib import Path
import numpy as np
from scale_hypothesis import build
from string_ports import element,assemble,PortString
from moving_termination import matrices
from duplex_string import Duplex
from duplex_diagnostic import ZERO,LOSS
from termination_diagnostic import LOAD
ROOT=Path(__file__).parent
class PortTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=json.loads(Path(os.environ['G3_SCALE_REPORT']).read_text())['rows']
    def test_fixed_front_parity(self):
        for key in (21,60,108):
            r=self.rows[key-21];M,K,P=element(r,32)
            A,B,C=matrices(r,32,.005,1e6);A[0,0]-=.005;B[0,0]-=1e6
            np.testing.assert_allclose(M[1:,1:],A,atol=1e-14)
            np.testing.assert_allclose(K[1:,1:],B,atol=1e-9)
            np.testing.assert_allclose(P[1:],C[:,0],atol=1e-14)
    def test_translation_and_mass(self):
        for key in (21,60):
            r=self.rows[key-21];M,K,P=element(r,32);x=np.r_[1.,1.,np.zeros(32)]
            self.assertAlmostEqual(float(x@M@x),r['linearDensityKgM']*r['lengthM'],places=12)
            self.assertAlmostEqual(float(x@K@x),0.,places=12)
            self.assertAlmostEqual(float(P@x),1.)
    def test_removable_load(self):
        r=self.rows[39];z=dict(massKg=0.,stiffnessNm=0.,dampingNsm=0.)
        M,K,P,parts,supports,labels=assemble(r,32,.1,.25,z,None)
        self.assertEqual(labels,['hammer','front','rear']);self.assertEqual(len(parts),3)
        self.assertGreater(np.linalg.eigvalsh(M)[0],0.)
        self.assertAlmostEqual(M[0,0],r['linearDensityKgM']*r['lengthM']*1.1/3,places=12)
    def test_rear_parity(self):
        r=self.rows[39];load=dict(LOAD,dampingNsm=0.)
        a=PortString(r,64,24000,192000,0.,.25,None,load,ZERO);b=Duplex(r,64,24000,192000,load,.25,ZERO)
        for f in np.sin(np.arange(300)*.04):
            a.step([f,0]);b.step([f,0]);np.testing.assert_allclose(a.position(),b.position(),atol=1e-12,rtol=1e-8)
    def test_energy_and_reciprocity(self):
        r=self.rows[39];front=dict(massKg=.02,stiffnessNm=1e8,dampingNsm=20.)
        a=PortString(r,64,24000,192000,.1,.25,front,LOAD,LOSS);b=PortString(r,64,24000,192000,.1,.25,front,LOAD,LOSS);work=0.
        for f in np.sin(np.arange(1500)*.04):
            work+=a.step([f,0,0]);b.step([0,f,0])
            self.assertLess(abs(a.energy()+a.loss-work),1e-12)
            self.assertAlmostEqual(a.position()[1],b.position()[0],places=13)
        self.assertGreater(a.partition()['frontDuplex'],0.)
        self.assertGreater(a.losses['frontSupport'],0.)
if __name__=='__main__':unittest.main()
