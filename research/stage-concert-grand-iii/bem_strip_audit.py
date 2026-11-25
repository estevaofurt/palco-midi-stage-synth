"""Independent work and residual convergence on an unchanged strip mesh."""
import numpy as np
from bem_power_partition import herm,partition
from split_radiation import relative

def audit_change(a,b,P,C,Q,D):
    return dict(prescribedWork=relative(herm(P),herm(Q)),computedWork=relative(herm(C),herm(D)),
        residual=abs(a['heldoutResidual']-b['heldoutResidual'])/max(b['heldoutResidual'],1e-30),
        worstColumn=abs(a['heldoutWorstColumn']-b['heldoutWorstColumn'])/max(b['heldoutWorstColumn'],1e-30))

def reliable(change):
    return all(np.isfinite(change[k]) and 0<=change[k]<=limit for k,limit in
        [('prescribedWork',.01),('computedWork',.01),('residual',.05),('worstColumn',.05)])

def physical(a,P,C,F):
    part=partition(P,C,F);H=herm(P);scale=max(np.linalg.norm(P),1e-30)
    pas=float(np.linalg.eigvalsh(H).min()/scale)
    rep=dict(**a,**part,passivityMinRelative=pas,powerRelative=part['totalPowerRelative'])
    gate=all(np.isfinite(rep[k]) and 0<=rep[k]<=limit for k,limit in
        [('heldoutResidual',.05),('heldoutWorstColumn',.05),('reciprocity',.01),('powerRelative',.01)])
    rep['physicalGate']=bool(gate and pas>=-1e-8 and part['partitionClosure']<=1e-10)
    return rep
