"""Audit exact prefix against immutable 50 ms arrays, launch/capture sequence and releases."""
from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parent
FS=384000; N=38400; PREFIX=19200
KEYS=('force','compression','velocity','flow')
EXPECTED=[(0,48,.3),(5760,60,1.),(11520,64,3.),(21120,48,1.)]
REFERENCE=json.loads((ROOT/'prefix-50ms.sha256.json').read_text())
def digest(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
result={}
for case in ('pedal','a2-closed'):
    row=json.loads((ROOT/f'{case}.json').read_text());launches=row['launches'];captures=row['captures']
    assert [(x['step'],x['key'],x['speed']) for x in launches]==EXPECTED
    assert len(captures)==4 and sorted(x['id'] for x in captures)==list(range(4))
    cap={x['id']:x for x in captures}; assert all(cap[x['id']]['key']==x['key'] and cap[x['id']]['step']>x['step'] for x in launches)
    assert cap[0]['step']<launches[3]['step'] and cap[3]['step']<28800
    assert [x['step'] for x in row['events']]==[1920,5760,11520,15360,21120,24960,26880,28800,32640]
    assert row['events'][-2]['held']==[48] and row['events'][-2]['pedal']==0
    assert row['events'][-1]['held']==[] and row['events'][-1]['pedal']==0 and all(x==1 for x in row['events'][-1]['after'])
    with np.load(ROOT/f'{case}.npz') as z:
        actual={k:digest(z[k][:PREFIX]) for k in KEYS}; assert actual==REFERENCE[case],(case,actual)
        ledger=z['ledger'];F=z['force'];C=z['compression'];assert F.shape==(N,8) and C.shape==F.shape
        cumulative=np.zeros(N)
        for x in launches:cumulative[x['step']:]+=x['energy']
        assert np.array_equal(cumulative,ledger[:,10])
        # Every wire of the associated key is force-free outside its launch/capture windows.
        ranges={48:slice(0,2),60:slice(2,5),64:slice(5,8)}
        for k,sl in ranges.items():
            active=np.zeros(N,dtype=bool)
            for x in launches:
                if x['key']==k:active[x['step']:cap[x['id']]['step']]=True
            assert np.all(F[~active,sl]==0)
        result[case]=dict(prefix_samples=PREFIX,prefix_exact=True,launches=launches,captures=captures,energy_injection_exact=True,force_outside_contact_zero=True,final_dampers_closed=True,final_energy=row['final_mechanical_energy'])
(ROOT/'events-100ms.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
