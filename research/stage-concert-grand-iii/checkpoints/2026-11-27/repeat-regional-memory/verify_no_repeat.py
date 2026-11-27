"""Additional independent reconstruction of stored energy and damper work for both cases."""
from pathlib import Path
import json,numpy as np
from compact_mechanics import assemble_compact
from dynamic_dampers import Dampers
ROOT=Path(__file__).parent;FS=384000;N=38400
scale=json.loads((ROOT/'scale_geometry.json').read_text())
base=np.load(ROOT.parent/'G3_consolidacao_20261127/G3_Base_Estrutural/integrated_80.npz')
M,K,D,P,w=assemble_compact(base,scale,[45,48,60,64],{45:64,48:128,60:64,64:64});dam=Dampers(D,w,scale)
result={}
for case in ['pedal','a2-closed']:
    row=json.loads((ROOT/f'{case}.json').read_text())
    with np.load(ROOT/f'{case}.npz') as f:
        v=f['velocity'];ledger=f['ledger'];F=f['force'];U=f['flow'];compression=f['compression']
        assert all(np.isfinite(x).all() for x in [v,ledger,F,U,compression]);assert np.min(F)>=0 and v.shape==(N,848) and U.shape==(N,1,369)
        mid=(v+np.vstack((np.zeros((1,M.n)),v[:-1])))/2;q=np.cumsum(mid,axis=0)/FS
        mech=np.array([.5*(x@(M@x)+y@(K@y)) for x,y in zip(v,q)])
        mech_err=float(np.max(abs(mech-ledger[:,0]))/row['injected_energy'])
        energy=ledger[:,7]+ledger[:,2:7].sum(1)-ledger[:,10];balance=float(np.max(abs(energy))/row['injected_energy'])
        frac=np.tile(dam.fractions([48],0),(N,1));
        for ev in row['events']:frac[ev['step']:]=ev['after']
        d=.18*(mid[:,:80]@D.g.T)
        for j in range(len(w)):
            ix=D.ids==j;d[:,j]+=mid[:,80:][:,ix]@D.v[ix]
        damper=d*d*frac*dam.maximum/FS;base_loss=np.array([x@(D@x)/FS for x in mid]);per_step=base_loss+damper.sum(1)
        loss_err=float(np.max(abs(np.cumsum(per_step)-ledger[:,2]))/row['injected_energy']);assert min(per_step)>=-1e-18
        assert max(mech_err,balance,loss_err)<1e-8 and np.min(ledger[:,4])/row['injected_energy']>=-1e-10
        result[case]=dict(mechanical_reconstruction=mech_err,ledger_balance=balance,mechanical_loss_reconstruction=loss_err,force_min=float(F.min()),steps=N,all_captured=len(row['captures'])==len(row['launches']),final_mechanical=float(mech[-1]),a2_damper_loss=float(damper[:,dam.keys==45].sum()))
(ROOT/'independent-no-repeat.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
