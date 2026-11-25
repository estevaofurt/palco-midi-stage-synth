"""Nested upper edge enrichment in the canonical exterior coordinates.
The lower mouth and all original 55-mode spans remain unchanged.
"""
import copy
import numpy as np
from edge_enriched_flux import EdgeEnrichedFlux

def enrich(ports,width=.06):
    if len(ports)!=7 or any(p.basis.count!=55 for p in ports):
        raise ValueError('seven canonical 55-mode ports required')
    panels=[];checks=[]
    for i,p in enumerate(ports):
        q=copy.copy(p)
        if i<6:
            q.basis=EdgeEnrichedFlux(p.poly,p.basis,width)
            a=q.basis.audit()
            if a['massRelative']>1e-8 or a['maximumIntegralError']>1e-8 or a['baselineRelative']>1e-14:
                raise ValueError('invalid nested enrichment')
            checks.append(dict(panel=i,**a))
        panels.append(q)
    counts=[p.basis.count for p in panels]
    offsets=np.r_[0,np.cumsum(counts)]
    indices=np.concatenate([np.arange(j,j+55) for j in offsets[:-1]])
    if sum(counts)!=429 or len(indices)!=385:raise ValueError('unexpected enriched dimensions')
    return panels,counts,indices,checks

def restrict(A,indices):
    A=np.asarray(A)
    if A.ndim<2 or A.shape[-2]!=A.shape[-1]:raise ValueError('square operator required')
    return A[...,indices[:,None],indices]
