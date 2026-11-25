"""Closed envelope of the upper cavity. Lid, upper rim, aperture faces,
and exposed underside at z=0. The lower skirt/recess is deliberately absent.
Aperture faces are artificial interfaces, not solid walls.
"""
import numpy as np
from board_contour import properties
from common_exterior import board_panel
from lid_exterior import Panel
from numpy.polynomial.legendre import leggauss

def envelope(poly,height,angle,count,field):
    poly=np.asarray(poly,float);_,xy,_=properties(poly)
    h=poly[:,0].min();a=np.deg2rad(angle)
    low=np.c_[poly,np.zeros(len(poly))];rim=np.c_[poly,np.full(len(poly),height)]
    lid=rim.copy();lid[:,0]=h+np.cos(a)*(poly[:,0]-h);lid[:,2]+=np.sin(a)*(poly[:,0]-h)
    inside=np.r_[xy,height/2]
    surfaces=[];ports=[]
    def add(vertices,kind,basis=None):
        vertices=np.asarray(vertices);v=[]
        for point in vertices:
            if not any(np.linalg.norm(point-q)<1e-12 for q in v):v.append(point)
        if len(v)<3:return
        v=np.array(v);normal=np.cross(v[1]-v[0],v[2]-v[0]);normal/=np.linalg.norm(normal)
        if normal@(v.mean(0)-inside)<0:normal=-normal
        p=Panel(v,normal,count) if basis is None else basis
        surfaces.append(dict(panel=p,normal=normal,kind=kind,port=len(ports) if kind!='rigid' else None))
        if kind!='rigid':ports.append(p)
    # Order upper apertures exactly as inclined_lid.build, then board.
    for i in range(len(poly)):
        j=(i+1)%len(poly)
        add([rim[i],rim[j],lid[j],lid[i]],'aperture')
    for i in range(len(poly)):
        j=(i+1)%len(poly)
        add([low[i],low[j],rim[j],rim[i]],'rigid')
    add(lid,'rigid')
    add(low,'board',board_panel(poly,field))
    return surfaces,ports,inside

def samples(surfaces,ports,order):
    X=[];N=[];W=[];V=[]
    offsets=np.r_[0,np.cumsum([p.basis.count for p in ports])]
    for s in surfaces:
        p=s['panel'];_,x,w,v=p.samples(order)
        B=np.zeros((len(x),offsets[-1]))
        j=s['port']
        if j is not None:B[:,offsets[j]:offsets[j+1]]=v
        X.append(x);N.append(np.broadcast_to(s['normal'],x.shape));W.append(w);V.append(B)
    return np.vstack(X),np.vstack(N),np.concatenate(W),np.vstack(V)

def internal(surfaces,ports,inside,order,scale=.68):
    if not 0<scale<1:raise ValueError('interior scale')
    x,n,w,V=samples(surfaces,ports,order)
    q=inside+scale*(x-inside)
    for s in surfaces:
        if np.max((q-s['panel'].origin)@s['normal'])>=-1e-10:
            raise ValueError('equivalent source outside convex envelope')
    return q

def geometry_audit(surfaces,ports,inside):
    x,n,w,V=samples(surfaces,ports,5)
    flux=np.sum(w[:,None]*n,axis=0)
    volume=float(np.sum(w*np.einsum('ij,ij->i',x-inside,n))/3)
    return dict(area=float(w.sum()),volume=volume,normalClosure=float(np.linalg.norm(flux)),
        gate=np.linalg.norm(flux)<1e-10 and volume>0)
