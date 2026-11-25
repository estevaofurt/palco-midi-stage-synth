"""Residual-driven conforming h-refinement with discontinuous P1 density.
Independent marking and final audit target sets. Explicit element budget.
"""
import numpy as np
from bem_linear import targets,operators,COL,CHECK
from bem_adaptive import mark,refine

MARK=np.array([[.5,.25,.25],[.25,.5,.25],[.25,.25,.5]])

def indicator(t,q,V,k,order):
    x,n,w,owner=targets(t,MARK);_,D=operators(t,x,n,owner,k,order)
    R=np.sqrt(w)[:,None]*(D@q+V);T=np.sqrt(w)[:,None]*V
    denom=np.maximum(np.linalg.norm(T,axis=0),1e-30)
    return np.sum(abs(R/denom)**2,axis=1).reshape(len(t),len(MARK)).sum(1)

def budget_refine(t,labels,scores,budget,fraction=.6,max_fraction=.25):
    if budget<=len(t):raise ValueError('budget must exceed current mesh')
    mask=mark(scores,fraction,max_fraction)
    indices=np.argsort(-np.asarray(scores),kind='stable')[:int(sum(mask))]
    n=len(indices)
    while n>0:
        mask=np.zeros(len(t),bool);mask[indices[:n]]=True
        q,l=refine(t,labels,mask)
        if len(q)<=budget:
            total=float(np.sum(scores))
            return q,l,dict(marked=n,elementBudget=budget,oldElements=len(t),newElements=len(q),
                capturedIndicator=float(np.sum(np.asarray(scores)[mask])/max(total,1e-30)))
        n-=max(1,n//5)
    raise ValueError('budget insufficient for conforming refinement')
