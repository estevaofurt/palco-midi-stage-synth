"""Select a principal subspace of the original full modal model by key.
No coordinate rescaling, damping refit, or alteration of the acoustic lift.
"""
import numpy as np
from assembly_rank import assemble

def select(base,scale,held,ranks):
    if set(ranks)!={45,48,60,64} or any(type(n)!=int or not 1<=n<=128 for n in ranks.values()):raise ValueError('rank map')
    M,K,D,P,L,wires=assemble(base,scale,held,128)
    idx=np.r_[np.arange(80),*[80+128*j+np.arange(ranks[w['key']]) for j,(w,*_) in enumerate(wires)]]
    assert len(idx)==len(np.unique(idx))
    return tuple(x[np.ix_(idx,idx)] for x in (M,K,D))+(P[idx],L[:,idx],wires)
