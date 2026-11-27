"""Conservative dry natural-mode check; not damped wet resonance or measured tuning."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh
from assembly_rank import assemble
ROOT=Path(__file__).parent
scale=json.loads((ROOT/'scale_geometry.json').read_text());rows={r['key']:r for r in scale['rows']}
base=np.load(ROOT.parent/'G3_consolidacao_20261127/G3_Base_Estrutural/integrated_80.npz')
results=[]
for key in (48,60,64):
    f0=rows[key]['nominalHz'];lo=f0*2**(-100/1200);hi=f0*2**(100/1200)
    for rank in (64,96,128):
        M,K,D,P,L,wires=assemble(base,scale,key,rank)
        w2,V=eigh(K,M,subset_by_value=((2*np.pi*lo)**2,(2*np.pi*hi)**2),driver='gvx')
        f=np.sqrt(w2)/(2*np.pi);ids=[j for j,(w,*_) in enumerate(wires) if w['key']==key]
        # In mass-normalized internal wire coordinates, sum squared first-mode amplitudes.
        # This is an indicator, not a fraction of total energy (mass cross terms retained).
        part=np.sum(V[80+rank*np.array(ids)]**2,axis=0)
        residual=np.linalg.norm(K@V-(M@V)*w2,axis=0)/np.maximum(np.linalg.norm(K@V,axis=0)+np.linalg.norm((M@V)*w2,axis=0),1e-300)
        ortho=np.linalg.norm(V.T@M@V-np.eye(len(f)))
        # Full-scale K poorly conditioned, report residual without asserting tight forward accuracy.
        result=dict(key=key,rank=rank,nominal_hz=f0,max_relative_residual=float(max(residual,default=0)),mass_orthogonality=float(ortho),modes=[dict(hz=float(x),cents=float(1200*np.log2(x/f0)),wire_first_indicator=float(y)) for x,y in zip(f,part)],fixed_hz=[wires[j][1]['fixed_hz'] for j in ids])
        results.append(result);print(json.dumps(result),flush=True)
(ROOT/'dry-modes.json').write_text(json.dumps(results,indent=2))
