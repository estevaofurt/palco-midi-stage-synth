"""Tests of the real 500 ms verification utilities, using non-physical I/O fixtures.
These are not acoustic or mechanical simulation results.
"""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import verify_prefix_250ms as prefix
import verify_restart_500ms as restart

class PrefixTests(unittest.TestCase):
    def test_canonical_header_and_payload(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            # Test both supported NPY header formats and representative ranks.
            for version in ((1,0),(2,0)):
                for shape in ((192000,), (192000,2), (192000,1,2)):
                    with self.subTest(version=version,shape=shape):
                        src=root/'long.npy';old=root/'old.npy'
                        a=np.lib.format.open_memmap(src,mode='w+',dtype=np.float64,shape=shape,version=version)
                        a[:]=np.arange(a.size,dtype=np.float64).reshape(shape)
                        a.flush()
                        b=np.lib.format.open_memmap(old,mode='w+',dtype=np.float64,shape=(96000,*shape[1:]),version=version)
                        b[:]=a[:96000];b.flush()
                        expected=restart.digest(old)
                        self.assertEqual(prefix.sha_prefix(src),expected)
                        a[100000]+=1;a.flush()
                        self.assertEqual(prefix.sha_prefix(src),expected)
                        a[95999]+=1;a.flush()
                        self.assertNotEqual(prefix.sha_prefix(src),expected)
                        del a,b
    def test_reject_wrong_sample_count(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'short.npy';np.save(p,np.zeros((96000,1),np.float64))
            with self.assertRaises(AssertionError):prefix.sha_prefix(p)

class RestartTests(unittest.TestCase):
    def fixture(self,root):
        ref=root/'long-500ms-refined-384000-mixed-pedal'
        run=root/'restart-500ms-refined-384000-mixed-pedal'
        ref.mkdir();run.mkdir()
        row={k:0 for k in restart.FIELDS}
        row.update(blocks=192000,rate=384000,events=[{'step':10,'held':[48],'pedal':1,'update_ms':.5}])
        ref.with_suffix('.json').write_text(json.dumps(row))
        row['events'][0]['update_ms']=1.5
        run.with_suffix('.json').write_text(json.dumps(row))
        data=np.arange(192000,dtype=np.float64).reshape(-1,1)
        for k in restart.SIGNALS:
            np.save(ref/(k+'.npy'),data);np.save(run/(k+'.npy'),data)
        for step in restart.STEPS:
            path=run/f'restart-{step}.npz'
            np.savez(path,exterior_t=step,active=[step==22000,False,False],q=[0.],mechanical_v=[0.],fractions=[1.])
            meta=dict(N=192000,step=step,state_file=path.name,state_sha256=restart.digest(path),signature='fixture-only',prefix_sha256={k:restart.arr_digest(data,step) for k in restart.SIGNALS})
            (run/f'restart-{step}.json').write_text(json.dumps(meta))
        (run/'restart.json').write_text(json.dumps(meta))
        return run
    def invoke(self,root):
        with patch.object(restart,'ROOT',root),contextlib.redirect_stdout(io.StringIO()):
            restart.main()
    def test_equal_and_changed_suffix(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);run=self.fixture(root);self.invoke(root)
            report=json.loads((root/'restart-500ms-regression.json').read_text())
            self.assertTrue(report['gate'])
            self.assertEqual(len(report['signals']),5)
            self.assertEqual(len(report['snapshots']),3)
            a=np.load(run/'velocity.npy',mmap_mode='r+');a[-1]+=1;a.flush();del a
            with self.assertRaises(SystemExit):self.invoke(root)
            report=json.loads((root/'restart-500ms-regression.json').read_text())
            self.assertFalse(report['gate'])
            self.assertFalse(report['signals']['velocity']['exact'])
    def test_corrupt_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);run=self.fixture(root)
            with (run/'restart-96000.npz').open('ab') as f:f.write(b'corruption')
            with self.assertRaises(AssertionError):self.invoke(root)
    def test_changed_command_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);run=self.fixture(root)
            p=run.with_suffix('.json');row=json.loads(p.read_text());row['events'][0]['pedal']=0;p.write_text(json.dumps(row))
            with self.assertRaises(SystemExit):self.invoke(root)
            self.assertFalse(json.loads((root/'restart-500ms-regression.json').read_text())['metadata']['commands'])

if __name__=='__main__':unittest.main(verbosity=2)
