"""Alternative conforming Ritz space: exact polynomial boundary trace constraints.
No changes to plate/rib material, no penalty springs for essential condition.
"""
import numpy as np
from scipy.linalg import svd
from spline_plate import assemble
def restrict(model,order=8):
    b=model['basis'];T=model['T']
    if b.essential:raise ValueError('unconstrained input required')
    if order<7:raise ValueError('degree six trace needs seven points per knot interval')
    blocks=[]
    for a,c in zip(b.poly,np.roll(b.poly,-1,axis=0)):
        for xy,w in b.line(a,c,order):
            blocks.append(b.evaluate(xy)[0]@T)
    C=np.vstack(blocks)
    norms=np.linalg.norm(C,axis=1);assert min(norms)>0
    C=C/norms[:,None]
    _,s,V=svd(C,full_matrices=True)
    rank=int(sum(s>s[0]*1e-10))
    Q=V[rank:].T;assert Q.shape[1]>8
    residual=float(np.max(np.linalg.norm(C@Q,axis=1)));assert residual<=1e-8
    z=dict(model);z['T']=T@Q
    for name in ('M','K','Mr','Kr'):
        A=Q.T@model[name]@Q;z[name]=(A+A.T)/2
    # Validate independently sampled trace, not only collocation rows.
    independent=0.
    for a,c in zip(b.poly,np.roll(b.poly,-1,axis=0)):
        for xy,w in b.line(a,c,order+3):
            raw=b.evaluate(xy)[0]@T
            independent=max(independent,float(np.max(np.linalg.norm(raw@Q,axis=1)/np.linalg.norm(raw,axis=1))))
    assert independent<=1e-8
    z.update(constraintRank=rank,constrainedRank=Q.shape[1],traceResidual=residual,independentTraceResidual=independent)
    return z
def constrained(poly,ribs,plate,rib,cells,order):
    return restrict(assemble(poly,ribs,plate,rib,cells,order,False))
