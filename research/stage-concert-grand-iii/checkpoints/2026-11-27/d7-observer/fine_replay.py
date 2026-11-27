"""Replay fine pressure at the aperture on the independent burst, without resolving flows again."""
import json,sys,time
from pathlib import Path
import numpy as np
import replay as r
from fused import FusedGrouped
from spatial import apply,rel
from enrich import verify

def main():
    root,prev=map(Path,sys.argv[1:3]);out=Path(__file__).parent
    verify(root,out/'INPUT_SHA256SUMS');verify(prev,prev/'SHA256SUMS')
    r.load_defs(root,'G3_Exterior_Acoplamento/coupled.py',['Cavity']);z=np.load(root/'G3_Cavidade_Compactacao_Local/adaptive_candidate.npz');g=np.load(prev/'grid-b64.npz');A,B,Q=g['A'],g['B'],g['Q'];c=FusedGrouped(z,A,B,np.ones((1,1)));p=A.shape[1];rows=[]
    for name in ['d6','targeted','d7','reference']:
        start=time.perf_counter();f=np.load(out/('new-'+name+'.npz'));u=f['flow'];N=len(u);c.reset();I=np.array([c.step(v[None])[0][0] for v in u]);O=apply(g['G'][:,:N,None,None],A,B,u[:,None])[:N,0];Y=I+O;R=Y[:,p:];res=float(np.linalg.norm(R)/(np.linalg.norm(I[:,p:])+np.linalg.norm(O[:,p:])));load=Y[:,:p] if name=='reference' else Q.T@Y[:,:p].reshape(-1,8,p);load_error=rel(load,f['load']);assert load_error<1e-10,load_error
        if name=='reference':assert res<1e-10,res
        row=dict(mode=name,fine_residual=res,load_replay=load_error,seconds=time.perf_counter()-start);rows.append(row);print(row,flush=True);(out/'fine-replay-results.json').write_text(json.dumps(rows,indent=2))
if __name__=='__main__':main()
