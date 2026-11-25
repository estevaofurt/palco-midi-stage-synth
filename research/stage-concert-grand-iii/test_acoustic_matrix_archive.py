import unittest,tempfile,hashlib
from pathlib import Path
import numpy as np
from acoustic_matrix_archive import read_npz,replay_full,modal_replay,validate_manifest
from dual_cavity_reference import couple
class ArchiveTest(unittest.TestCase):
    def test_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'test.npz'
            np.savez(p,frequencies=[30.],Z=np.eye(2)[None])
            entry=dict(file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertEqual(read_npz(root,entry,{'Z':(1,2,2)},[30.])['Z'].shape,(1,2,2))
            for invalid in [dict(entry,sha256='0'*64),dict(entry,file='../test.npz')]:
                with self.assertRaises(ValueError):read_npz(root,invalid,{'Z':(1,2,2)},[30.])
            with self.assertRaises(ValueError):read_npz(root,entry,{'Z':(1,3,3)},[30.])
            with self.assertRaises(ValueError):read_npz(root,entry,{'Z':(1,2,2)},[80.])
    def test_replay_and_projection(self):
        rng=np.random.default_rng(20)
        def make(n):
            a=rng.normal(size=(n,n));return a.T@a+np.eye(n)
        Zu=make(5);Zl=make(3);Ze=make(6);mat=(Zu,np.eye(5),Zl,np.eye(3),Ze,np.eye(6))
        Y,p1,p2,p3,F,r=couple(*mat,1,reference_kind='common-free-space-monopole')
        full,d=replay_full(*mat,Y,F,1)
        self.assertLess(max(d.values()),1e-12)
        with self.assertRaises(ValueError):replay_full(*mat,Y*2,F,1)
        out,rr=modal_replay(mat,np.eye(4)[:,:2],np.eye(2)[:,:1],1,[4,2],[1.,2.],full)
        self.assertTrue(rr['coupled']['gate']);self.assertGreater(rr['flow']['omittedRelative'],0.)
        self.assertLess(rr['pressureDefect']['resolvedRelative'],1e-10)
    def test_manifest_scope(self):
        s=dict(gate=False,angleDeg=30,maximumModes=252,exteriorFixed=True,lowerFixed=True,
            directionalSpatialOnly=True,commonFreeSpaceMonopolesOnly=True,fullCabinetReady=False,radiationReady=False,
            modalConvergenceCertified=False,quadratureConvergenceCertified=False)
        row=dict(planarN=40,boundaryN=40,wedgeLayers=1,gate=True,
            reports=[dict(frequencyHz=30.,**{k:dict(gate=True) for k in ('upper','lower','exterior','coupled')})])
        d=dict(summary=s,scaleSha256='a'*64,frequenciesHz=[30.],cases=[row])
        self.assertEqual(validate_manifest(d,30,'a'*64,[30.],[(40,40,1)]),[row])
        d['cases']=[]
        with self.assertRaises(ValueError):validate_manifest(d,30,'a'*64,[30.],[(40,40,1)])
if __name__=='__main__':unittest.main()
