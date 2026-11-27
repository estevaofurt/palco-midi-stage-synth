"""Independent long-window restart gate: exact continuous vs restarted arrays and physics."""
from pathlib import Path
import hashlib,json,numpy as np
ROOT=Path(__file__).resolve().parent
STEPS=(22000,96000,153600)
FIELDS=('launches','captures','energy_error','continuity','work_error','compression_residual','force_residual','minimum_exterior_work','injected_energy','final_mechanical_energy','final_cavity_energy','peak_force','impulse','felt_loss','catch_loss','mechanical_loss','cavity_loss','exterior_work')
SIGNALS=('force','compression','velocity','flow','ledger')
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def arr_digest(a,n):
    h=hashlib.sha256()
    for i in range(0,n,1200):h.update(np.ascontiguousarray(a[i:min(i+1200,n)]).tobytes())
    return h.hexdigest()
def main():
    ref=ROOT/'long-500ms-refined-384000-mixed-pedal'
    run=ROOT/'restart-500ms-refined-384000-mixed-pedal'
    old=json.loads(ref.with_suffix('.json').read_text());new=json.loads(run.with_suffix('.json').read_text())
    assert old['blocks']==new['blocks']==192000 and old['rate']==new['rate']==384000
    metadata={k:old[k]==new[k] for k in FIELDS}
    events=lambda r:[{k:v for k,v in x.items() if k!='update_ms'} for x in r['events']]
    metadata['commands']=events(old)==events(new)
    records={};snapshots=[]
    for step in STEPS:
        meta=json.loads((run/f'restart-{step}.json').read_text())
        path=run/f'restart-{step}.npz'
        assert meta['N']==192000 and meta['step']==step and meta['state_file']==path.name
        assert digest(path)==meta['state_sha256']
        with np.load(path,allow_pickle=False) as z:
            assert int(z['exterior_t'])==step
            active=z['active'].tolist()
            assert active==([True,False,False] if step==22000 else [False,False,False])
            assert np.isfinite(z['q']).all() and np.isfinite(z['mechanical_v']).all()
            if step>=96000:assert np.all(z['fractions']==1)
        snapshots.append(dict(step=step,state_sha256=meta['state_sha256'],signature=meta['signature'],active=active,prefix=meta['prefix_sha256']))
    assert len({x['signature'] for x in snapshots})==1
    assert json.loads((run/'restart.json').read_text())==json.loads((run/f'restart-{STEPS[-1]}.json').read_text())
    for k in SIGNALS:
        a=np.load(ref/(k+'.npy'),mmap_mode='r',allow_pickle=False);b=np.load(run/(k+'.npy'),mmap_mode='r',allow_pickle=False)
        assert a.shape==b.shape and a.dtype==b.dtype==np.float64 and len(a)==192000
        exact=all(np.array_equal(a[i:i+1200],b[i:i+1200]) for i in range(0,len(a),1200))
        checks=[]
        for s in snapshots:
            ah=arr_digest(a,s['step']);bh=arr_digest(b,s['step'])
            checks.append(ah==bh==s['prefix'][k])
        records[k]=dict(exact=exact,shape=list(b.shape),sha256=arr_digest(b,len(b)),snapshot_prefix_gates=checks)
    gate=all(metadata.values()) and all(x['exact'] and all(x['snapshot_prefix_gates']) for x in records.values())
    report=dict(gate=gate,metadata=metadata,signals=records,snapshots=snapshots,scope='Three actual restart points; no timing equality required.')
    (ROOT/'restart-500ms-regression.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print(json.dumps(report,indent=2))
    if not gate:raise SystemExit('Long restart gate failed')
if __name__=='__main__':main()
