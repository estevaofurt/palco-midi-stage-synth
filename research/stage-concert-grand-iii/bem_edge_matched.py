"""Matched element counts for two mesh refinement strategies.
Use identical ranked physical-edge sectors and a strict common budget.
Only geometry is inspected during mesh selection, never solution error.
"""
import numpy as np
from bem_edge_strip import refine_strips
from bem_adaptive import refine

def matched(t,labels,sector_scores,eligible,budget,fraction=.25):
    S=np.asarray(sector_scores,float);M=np.asarray(eligible,bool)
    if S.shape!=(len(t),3) or M.shape!=S.shape or not np.isfinite(S).all() or np.any(S<0) or budget<=len(t):
        raise ValueError('invalid comparison inputs')
    Q=np.where(M,S,0.);which=Q.argmax(1);rank=Q.max(1)
    ids=np.argsort(-rank,kind='stable');ids=ids[rank[ids]>0]
    if not len(ids):raise ValueError('no positive eligible sectors')
    red={};strip={}
    for n in range(1,len(ids)+1):
        sel=np.full(len(t),-1,int);sel[ids[:n]]=which[ids[:n]]
        a,l=refine(t,labels,sel>=0)
        c,ll,parents,rr=refine_strips(t,labels,sel,fraction)
        captured=float(rank[ids[:n]].sum()/max(Q.sum(),1e-60))
        if len(a)<=budget:red[len(a)]=(a,l,dict(selectedTriangles=n,capturedSelectedIndicator=captured))
        if len(c)<=budget:strip[len(c)]=(c,ll,dict(**rr,capturedSelectedIndicator=captured))
    common=set(red)&set(strip)
    if not common:raise ValueError('no exactly matched mesh sizes within budget')
    count=max(common)
    return red[count],strip[count],dict(matchedElements=count,elementBudget=budget,eligibleTriangles=len(ids),exactCountMatch=True)
