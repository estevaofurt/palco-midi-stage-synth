"""Compare two actual stopped/restarted processes with uninterrupted 18 ms control."""
import hashlib,json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ref=ROOT/'long-18ms-refined-384000-mixed-pedal';case=ROOT/'restart-18ms-refined-384000-mixed-pedal'
old=json.loads(ref.with_suffix('.json').read_text());new=json.loads(case.with_suffix('.json').read_text());records={}
fields=('launches','captures','energy_error','continuity','work_error','compression_residual','force_residual','minimum_exterior_work','injected_energy','final_mechanical_energy','final_cavity_energy','peak_force','impulse','felt_loss','catch_loss','mechanical_loss','cavity_loss','exterior_work')
meta={k:old[k]==new[k] for k in fields};assert all(meta.values()),meta
for k in ('force','compression','velocity','flow','ledger'):
    a=np.load(ref/(k+'.npy'),mmap_mode='r',allow_pickle=False);b=np.load(case/(k+'.npy'),mmap_mode='r',allow_pickle=False);assert a.shape==b.shape;h=hashlib.sha256()
    for i in range(0,len(a),1200):assert np.array_equal(a[i:i+1200],b[i:i+1200]),(k,i);h.update(np.ascontiguousarray(b[i:i+1200]).tobytes())
    records[k]=dict(shape=list(b.shape),exact=True,sha256=h.hexdigest())
report=dict(gate=True,checkpoints=[1200,3200],reference_steps=old['blocks'],signals=records,metadata=meta,scope='Actual 18 ms interrupted integration; snapshots include mechanical, felt and hammer states, cavity modes, exterior history/ring, exact time index and energy ledger. Not yet tested for long-window resume.')
(ROOT/'restart-regression.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
