"""Replay the archived weak 4 ms prefix on the extended reference."""
from pathlib import Path
import json
import numpy as np
from pressure_refine import rel
ROOT=Path(__file__).parent
old=np.load(ROOT.parent/'G3_Ataque_Acoplado_Fino/64-384000-0.3-1536.npz')
new=np.load(ROOT/'64-384000-0.3-4608.npz')
r={k:rel(new[k][:len(old[k])],old[k]) for k in ('flow','force','compression','velocity')}
assert max(r.values())<1e-10,r
(ROOT/'weak-prefix.json').write_text(json.dumps(r,indent=2))
print(r)
