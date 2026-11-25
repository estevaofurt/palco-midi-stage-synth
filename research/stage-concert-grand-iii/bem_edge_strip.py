"""Conforming edge-aligned strip refinement of planar triangles.
For a selected edge AB, split AC and BC towards A and B; keep AB
unless a neighboring request requires a split. Shared requests are
resolved symmetrically. No displacement of the physical surface.
"""
import numpy as np
from exterior_bem import elements,topology
from bem_adaptive import edge,key

def refine_strips(t,labels,selected,fraction=.25):
    t=np.asarray(t,float);labels=np.asarray(labels);selected=np.asarray(selected)
    if labels.shape!=(len(t),) or selected.shape!=(len(t),) or not np.issubdtype(selected.dtype,np.integer):
        raise ValueError('invalid labels or selected edges')
    if np.any(selected<-1) or np.any(selected>2) or not np.any(selected>=0) or not 0<fraction<.5:
        raise ValueError('invalid strip requests')
    before=topology(t)
    if not before['gate']:raise ValueError('input must be closed and oriented')
    requests={}
    for tri,j in zip(t,selected):
        if j<0:continue
        a,b,c=tri[[j,(j+1)%3,(j+2)%3]]
        for v in (a,b):
            e=edge(v,c);f=fraction if key(v)==e[0] else 1-fraction
            requests.setdefault(e,[]).append((f,v,c))
    splits={};conflicts=0
    for e,req in requests.items():
        fs=np.array([x[0] for x in req]);f,v,c=req[0]
        # Opposite requests are resolved by a shared midpoint, never
        # nonconforming independent points on the same edge.
        if np.ptp(fs)>1e-12:
            splits[e]=(v+c)/2;conflicts+=1
        else:splits[e]=(1-fraction)*v+fraction*c
    out=[];lab=[];parents=[];strips=0
    for i,(tri,j,label) in enumerate(zip(t,selected,labels)):
        points=[splits.get(edge(tri[k],tri[(k+1)%3])) for k in range(3)]
        flags=[x is not None for x in points]
        if not any(flags):parts=[tri]
        elif j>=0 and not flags[j] and flags[(j+1)%3] and flags[(j+2)%3]:
            a,b,c=tri[[j,(j+1)%3,(j+2)%3]]
            bc=points[(j+1)%3];ac=points[(j+2)%3]
            parts=[[a,b,bc],[a,bc,ac],[ac,bc,c]];strips+=1
        elif sum(flags)==1:
            k=flags.index(True);a,b,c=tri[[k,(k+1)%3,(k+2)%3]];m=points[k]
            parts=[[a,m,c],[m,b,c]]
        else:
            boundary=[]
            for k in range(3):
                boundary.append(tri[k])
                if flags[k]:boundary.append(points[k])
            c=tri.mean(0)
            parts=[[c,a,b] for a,b in zip(boundary,np.roll(boundary,-1,axis=0))]
        out.extend(parts);lab.extend([label]*len(parts));parents.extend([i]*len(parts))
    out=np.asarray(out);lab=np.asarray(lab);parents=np.asarray(parents)
    _,normal0,area0=elements(t);_,normal1,area1=elements(out)
    after=topology(out)
    area_error=float(np.max(abs(np.bincount(parents,weights=area1,minlength=len(t))-area0)/area0))
    orientation_error=float(np.max(np.linalg.norm(normal1-normal0[parents],axis=1)))
    volume_error=abs(after['volume']-before['volume'])
    if not after['gate'] or area_error>1e-9 or orientation_error>1e-9 or volume_error>1e-10:
        raise ValueError('strip refinement violated geometry')
    return out,lab,parents,dict(oldElements=len(t),newElements=len(out),selectedTriangles=int(np.sum(selected>=0)),
        alignedStrips=strips,sharedSplitEdges=len(splits),conflictingRequests=conflicts,
        fraction=fraction,areaRelative=area_error,orientationError=orientation_error,volumeError=volume_error,gate=True)

def budget_strips(t,labels,sector_scores,eligible,budget,fraction=.25):
    """Rank only eligible triangle-edge sectors; choose one edge per triangle.
    The budget is strict. Scores are supplied by a separate audit.
    """
    S=np.asarray(sector_scores,float);M=np.asarray(eligible,bool)
    if S.shape!=(len(t),3) or M.shape!=S.shape or not np.isfinite(S).all() or np.any(S<0) or budget<=len(t):
        raise ValueError('invalid sector indicators or budget')
    Q=np.where(M,S,0.);which=Q.argmax(axis=1);rank=Q.max(axis=1)
    ids=np.argsort(-rank,kind='stable');ids=ids[rank[ids]>0]
    if not len(ids):raise ValueError('no positive eligible indicators')
    n=len(ids)
    while n:
        sel=np.full(len(t),-1,int);sel[ids[:n]]=which[ids[:n]]
        q,l,parents,rep=refine_strips(t,labels,sel,fraction)
        if len(q)<=budget:
            rep.update(elementBudget=budget,capturedSelectedIndicator=float(rank[ids[:n]].sum()/max(Q.sum(),1e-60)))
            return q,l,parents,rep
        n-=max(1,n//5)
    raise ValueError('budget insufficient for strip refinement')
