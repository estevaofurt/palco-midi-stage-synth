"""Verify disk-streaming executor against the immutable refined 18ms arrays."""
from pathlib import Path
import argparse, hashlib, json, numpy as np
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('reference',type=Path);args=p.parse_args()
ref=args.reference; name='long-18ms-refined-384000-mixed-pedal'
a=json.loads((ROOT/f'{name}.json').read_text());b=json.loads((ref/'refined-384000-mixed-pedal.json').read_text())
fields=('launches','captures','energy_error','continuity','work_error','compression_residual','force_residual','minimum_exterior_work','injected_energy','final_mechanical_energy','final_cavity_energy','peak_force','impulse','felt_loss','catch_loss','mechanical_loss','cavity_loss','exterior_work')
exact_meta={k:a[k]==b[k] for k in fields}; assert all(exact_meta.values()),exact_meta
checks={}
with np.load(ref/'refined-384000-mixed-pedal.npz',allow_pickle=False) as z:
    for k in ('force','compression','velocity','flow','ledger'):
        old=z[k];new=np.load(ROOT/name/f'{k}.npy',mmap_mode='r',allow_pickle=False)
        assert new.shape==old.shape
        same=np.array_equal(new,old); assert same,k
        checks[k]=dict(shape=list(new.shape),exact=bool(same),sha256=hashlib.sha256(np.ascontiguousarray(new).tobytes()).hexdigest())
report=dict(gate=True,reference='refined-384000-mixed-pedal',samples=a['blocks'],metadata=exact_meta,signals=checks)
(ROOT/'stream-regression.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
