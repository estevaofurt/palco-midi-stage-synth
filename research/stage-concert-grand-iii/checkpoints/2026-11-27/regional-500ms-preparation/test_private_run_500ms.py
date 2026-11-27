"""Non-physical tests of the workspace journal and strict acceptance."""
from pathlib import Path
import tempfile
import unittest
import private_run_500ms as m

class Journal(unittest.TestCase):
    def test_verified_stage_skips_execution_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);spec=('fixture','fake.py',[],['out.dat'])
            calls=[]
            def fake(*a,**kw):
                calls.append(1);(root/'out.dat').write_bytes(b'exact')
            self.assertEqual(m.run_stage(root,spec,{},run=fake),'executed')
            self.assertEqual(m.run_stage(root,spec,{},run=fake),'verified')
            self.assertEqual(len(calls),1)
            (root/'out.dat').write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError,'Completed output changed'):m.run_stage(root,spec,{},run=fake)
    def test_interrupted_stage_never_overwrites(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);spec=('fixture','fake.py',[],['out.dat'])
            def fail(*a,**kw):
                (root/'out.dat').write_bytes(b'partial')
                raise ValueError('interrupted')
            with self.assertRaises(ValueError):m.run_stage(root,spec,{},run=fail)
            with self.assertRaisesRegex(RuntimeError,'Interrupted stage'):m.run_stage(root,spec,{},run=fail)
            self.assertEqual((root/'out.dat').read_bytes(),b'partial')
    def test_final_restart_reuses_preallocated_arrays(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);spec=next(s for s in m.stage_plan() if s[0]=='restart-final')
            for n in spec[3][1:]:
                f=root/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(b'prefix')
            def fake(*a,**kw):
                for n in spec[3]:(root/n).write_bytes(b'complete')
            self.assertEqual(m.run_stage(root,spec,{},run=fake),'executed')
            self.assertEqual(m.run_stage(root,spec,{},run=fake),'verified')
    def test_unsafe_path(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaisesRegex(RuntimeError,'escapes'):m.checked_path(Path(t),'../escape')
    def test_plan_preserves_restart_snapshots(self):
        plan=m.stage_plan()
        self.assertEqual(len(plan),9)
        self.assertEqual([s[0] for s in plan if s[0].startswith('restart-')],['restart-22000','restart-96000','restart-153600','restart-final','restart-audit'])
        outputs=[x for s in plan for x in s[3]]
        self.assertEqual(len(outputs),len(set(outputs)))
    def test_acceptance_rejects_any_failed_prefix(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);tail=dict(no_injection=True,no_hammer_force=True,all_dampers_closed=True)
            p=dict(final_gate=True,all_prefix_gates=True,comparisons=[dict(causal_gate=True) for _ in range(10)],cases={k:dict(steps=192000,tail_after_200ms=tail) for k in ('mixed','uniform')})
            q=dict(gate=True,files={str(i):dict(exact=True) for i in range(10)})
            r=dict(gate=True,signals={k:dict(exact=True,snapshot_prefix_gates=[True]*3) for k in m.SIGNALS},snapshots=[dict(step=s) for s in m.STOPS],metadata={'force':True})
            for name,obj in [('long-500ms-audit.json',p),('prefix-250ms-of-500ms.json',q),('restart-500ms-regression.json',r)]:m.atomic_json(root/name,obj)
            self.assertTrue(m.acceptance(root)['complete'])
            p['comparisons'][3]['causal_gate']=False;m.atomic_json(root/'long-500ms-audit.json',p)
            self.assertFalse(m.acceptance(root)['complete'])

if __name__=='__main__':unittest.main(verbosity=2)
