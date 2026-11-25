import unittest,json
from pathlib import Path
import numpy as np
from bridge_board_interface import plate,assemble,mobility
ROOT=Path(__file__).parent
class InterfaceTest(unittest.TestCase):
    def setUp(self):
        self.cfg=json.loads((ROOT/'board_interface_hypothesis.json').read_text());self.bcfg=json.loads((ROOT/'bridge_hypothesis.json').read_text())
        self.layout={'boardEnvelope':{'x':[0.,1.4],'y':[0.,1.6]}}
        self.centers={s:dict(xyz=np.array([[.3,.4+j*.4,0],[.6,.5+j*.4,0],[.9,.6+j*.4,0]]),keys=[1,2,3]) for j,s in enumerate(('bass','treble'))}
    def test_plate(self):
        M,K,S=plate(self.layout['boardEnvelope'],self.cfg['plate'],5)
        self.assertTrue(np.all(M>0));self.assertTrue(np.all(K>0))
        self.assertLess(np.max(abs(S([0.,.4]))),1e-14)
    def test_joint_work(self):
        M,K,J,D,P,maps,nb=assemble(self.centers,self.layout,self.cfg,self.bcfg,2,5,6)
        x=np.sin(np.arange(len(M)))*1e-5
        v=np.cos(np.arange(len(M)))*1e-3
        expected=sum(self.cfg['joint']['stiffnessNperM2']*float(w@((R@x)*(R@v))) for R,w in maps)
        self.assertAlmostEqual(float(v@J@x),expected,places=12)
        self.assertGreater(np.linalg.eigvalsh(M)[0],0.)
        self.assertGreaterEqual(np.linalg.eigvalsh(J)[0],-1e-7)
        self.assertGreater(np.linalg.eigvalsh(K+J)[0],0.)
    def test_cross_mobility(self):
        M,K,J,D,P,_,_=assemble(self.centers,self.layout,self.cfg,self.bcfg,2,5,6)
        Y,_,_=mobility(M,K+J,D,P,[100.,200.,500.])
        Z,_,_=mobility(M,K,D,P,[100.,200.,500.])
        self.assertGreater(np.max(abs(Y[:,0,2])),1e-10)
        self.assertLess(np.max(abs(Z[:,0,2])),1e-14)
        self.assertGreater(np.max(abs(Y[:,0,4])),1e-10)
if __name__=='__main__':unittest.main()
