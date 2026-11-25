"""Nested edge-localized functions for the pressure jump on a planar screen.
Lengths are numerical basis-resolution choices, not fitted material parameters.
All functions vanish on the screen boundary; no change to the Green kernel.
"""
import numpy as np
from scipy.linalg import qr,solve_triangular
from edge_screen import EdgeBasis,graded

class LocalBasis:
    def __init__(self,poly,degree=4,widths=(.25,.08,.025),order=40):
        self.global_basis=EdgeBasis(poly,degree)
        self.poly=self.global_basis.poly;self.degree=degree
        self.widths=tuple(widths);self.n0=len(self.global_basis.indices)
        if not self.widths or min(self.widths)<=0:raise ValueError('positive basis widths')
        self.normals=self.global_basis.normals
        edges=np.roll(self.poly,-1,axis=0)-self.poly
        self.tangents=2*edges/np.sum(edges*edges,axis=1)[:,None]
        self.centers=self.poly+edges/2
        self.block=2*len(self.poly)
        self.count=self.n0+len(self.widths)*self.block
        x,w=self.samples(order);V,_,_=self.raw(x)
        _,R=qr(np.sqrt(w)[:,None]*V,mode='economic',check_finite=True)
        if min(abs(np.diag(R)))<1e-10*max(abs(np.diag(R))):raise ValueError('dependent local basis')
        R=np.sign(np.diag(R))[:,None]*R
        self.T=solve_triangular(R,np.eye(len(R)),lower=False)
    def samples(self,order):return graded(self.poly,order)
    def raw(self,q):
        q=np.atleast_2d(q);V,X,Y=self.global_basis.raw(q)
        root,rx,ry=V[:,0],X[:,0],Y[:,0]
        vals=[V];dx=[X];dy=[Y]
        for width in self.widths:
            for a,n,t,mid in zip(self.poly,self.normals,self.tangents,self.centers):
                d=(q-a)@n;tau=(q-mid)@t
                g=np.exp(-d/width);v=root*g
                vx=g*(rx-root*n[0]/width);vy=g*(ry-root*n[1]/width)
                vals.append(np.column_stack([v,v*tau]))
                dx.append(np.column_stack([vx,vx*tau+v*t[0]]))
                dy.append(np.column_stack([vy,vy*tau+v*t[1]]))
        return tuple(np.column_stack(a) for a in (vals,dx,dy))
    def evaluate(self,q):return tuple(a@self.T for a in self.raw(q))
    def prefix(self,blocks):return self.n0+blocks*self.block
