"""Conforming local refinement of a closed triangular surface.
Mark by relative boundary residual, split all marked edges; neighboring
elements with one or two marked edges are subdivided by a centroid fan.
No geometrical smoothing or material fitting.
"""
import numpy as np
from exterior_bem import elements,topology,heldout,subdivide,field,far_gram
from bem_static_split import operators
from bem_linear import targets,CHECK
from split_radiation import relative

def key(x):return tuple(np.round(x,12))
def edge(a,b):return tuple(sorted((key(a),key(b))))

def refine(t,labels,marked):
    marked=np.asarray(marked,bool);t=np.asarray(t);labels=np.asarray(labels)
    if len(t)!=len(marked) or len(t)!=len(labels):raise ValueError('invalid marking')
    edges=set()
    for tri in t[marked]:
        for a,b in zip(tri,np.roll(tri,-1,axis=0)):edges.add(edge(a,b))
    result=[];lab=[]
    for tri,label in zip(t,labels):
        flags=[edge(a,b) in edges for a,b in zip(tri,np.roll(tri,-1,axis=0))]
        if all(flags):q=subdivide(tri[None,:,:])
        elif not any(flags):q=tri[None,:,:]
        else:
            poly=[]
            for a,b,flag in zip(tri,np.roll(tri,-1,axis=0),flags):
                poly.append(a)
                if flag:poly.append((a+b)/2)
            c=tri.mean(0);q=np.array([[c,a,b] for a,b in zip(poly,np.roll(poly,-1,axis=0))])
        result.extend(q);lab.extend([label]*len(q))
    out=np.asarray(result);lab=np.asarray(lab)
    before=topology(t);after=topology(out)
    if not before['gate'] or not after['gate'] or abs(before['volume']-after['volume'])>1e-10:
        raise ValueError('refinement changed closed surface topology or volume')
    return out,lab

def indicator(t,q,V,k,order):
    x,n,w,owner=heldout(t);_,D=operators(t,x,n,owner,k,order)
    R=np.sqrt(w)[:,None]*(D@q+V);T=np.sqrt(w)[:,None]*V
    scale=np.maximum(np.linalg.norm(T,axis=0),1e-30)
    return np.sum(abs(R/scale[None,:])**2,axis=1).reshape(len(t),3).sum(1)

def mark(scores,fraction=.6,max_fraction=.4):
    scores=np.asarray(scores,float)
    if not np.isfinite(scores).all() or min(scores)<0 or not 0<fraction<=1 or not 0<max_fraction<=1:
        raise ValueError('invalid marking scores')
    idx=np.argsort(-scores,kind='stable');n=np.searchsorted(np.cumsum(scores[idx]),fraction*scores.sum())+1
    n=min(n,max(1,int(np.ceil(len(scores)*max_fraction))))
    mask=np.zeros(len(scores),bool);mask[idx[:n]]=True
    return mask

def independent(t,q,V,k,points,order,rho=1.204,c=343.):
    x,n,w,owner=targets(t,CHECK);G,D=operators(t,x,n,owner,k,order)
    R=np.sqrt(w)[:,None]*(D@q+V);T=np.sqrt(w)[:,None]*V
    Z=1j*rho*c*k*V.T@(w[:,None]*(G@q));P=1j*rho*c*k*field(t,q,points,k,order)
    H=(Z+Z.conj().T)/2;expected=rho*c*k*k/(4*np.pi)*far_gram(t,q,k,surface_order=order)
    den=max(np.linalg.norm(Z),1e-30)
    rep=dict(heldoutResidual=float(np.linalg.norm(R)/max(np.linalg.norm(T),1e-30)),
        heldoutWorstColumn=float(max(np.linalg.norm(R,axis=0)/np.maximum(np.linalg.norm(T,axis=0),1e-30))),
        reciprocity=relative(Z,Z.T),powerRelative=relative(H,expected),
        passivityMinRelative=float(min(np.linalg.eigvalsh(H))/den))
    rep['gate']=max(rep['heldoutResidual'],rep['heldoutWorstColumn'])<=.05 and rep['reciprocity']<=.01 and rep['powerRelative']<=.01 and rep['passivityMinRelative']>=-1e-8
    return Z,P,rep
