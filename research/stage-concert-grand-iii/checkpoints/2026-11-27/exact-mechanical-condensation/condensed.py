"""Exact block elimination of string coordinates; no reduction of modes.
Diagonal plus rank-one damper blocks from the archived physical assembly.
"""
import numpy as np
from scipy.linalg import lu_factor, lu_solve
from scipy.sparse import csr_matrix
from hammer import Wet

class BlockSolve:
    def __init__(self,J,wires,rank):
        self.rank=rank;self.nw=len(wires);n=80+rank*self.nw
        assert J.shape==(n,n)
        self.B=J[:80,80:].copy();self.C=J[80:,:80].copy()
        inner=J[80:,80:];diag=[];vs=[];strength=[];reconstructed=np.zeros_like(inner)
        for j,(_,w,_,a) in enumerate(wires):
            sl=slice(j*rank,(j+1)*rank);v=w['damper'];d=np.diag(inner[sl,sl])-a*v*v
            assert np.all(d>0);diag.append(d);vs.append(v);strength.append(a)
            reconstructed[sl,sl]=np.diag(d)+a*np.outer(v,v)
        self.structure_error=float(np.max(abs(inner-reconstructed))/np.max(abs(inner)))
        assert np.allclose(inner,reconstructed,rtol=1e-13,atol=1e-14)
        self.inv=1/np.array(diag);self.v=np.array(vs);self.iv=self.inv*self.v
        a=np.array(strength);self.alpha=a/(1+a*np.sum(self.v*self.iv,axis=1))
        self.X=self.inner(self.C);self.fac=lu_factor(J[:80,:80]-self.B@self.X)
    def inner(self,r):
        vec=r.ndim==1;R=r.reshape(self.nw,self.rank,-1);Y=self.inv[:,:,None]*R
        Y-=self.iv[:,:,None]*(self.alpha[:,None,None]*np.sum(self.v[:,:,None]*Y,axis=1,keepdims=True))
        return Y.reshape(-1) if vec else Y.reshape(self.nw*self.rank,-1)
    def solve(self,r):
        y=self.inner(r[80:]);x=lu_solve(self.fac,r[:80]-self.B@y)
        return np.concatenate((x,y-self.X@x),axis=0)

class CondensedWet(Wet):
    def __init__(self,c,e,Z,s,M,K,D,lift,wires,rank):
        super().__init__(c,e,Z,s,M,K,D,lift)
        assert not np.any(self.Z[80:,:]) and not np.any(self.Z[:,80:])
        self.block=BlockSolve(self.H+self.Z,wires,rank)
        self.Ms,self.Ks,self.Ds=map(csr_matrix,(M,K,D))
        self.Xb=self.X[:,:80];self.Wb=self.W[:,:80];self.Pb=self.P[:80]
    def solve(self,r):return self.block.solve(r)
    def free(self):
        hist=(self.c.history()+self.e.history()).ravel();hb=lu_solve(self.fb,hist[self.bot]);rhs=2*(self.Ms@self.v)/self.h-self.Ks@self.q
        rhs[:80]-=self.Pb@(hist[self.top]-self.Ab@hb)
        return self.solve(rhs)
    def step(self,f,reference=False):
        if reference:raise ValueError('use dense Bridge for reference')
        ch=self.c.history();eh=self.e.history();hist=(ch+eh).ravel();hb=lu_solve(self.fb,hist[self.bot]);rhs=f+2*(self.Ms@self.v)/self.h-self.Ks@self.q
        rhs[:80]-=self.Pb@(hist[self.top]-self.Ab@hb);v=self.solve(rhs);u=np.zeros(self.c.Q.shape[1]*self.c.n);u[self.top]=self.Wb@v[:80];u[self.bot]=-self.Xb@v[:80]-hb
        u=u.reshape(self.c.Q.shape[1],self.c.n);yi,dc,Ei=self.c.step(u);ye=self.e.commit(u,eh);y=yi+ye;F=self.Pb@y[0,:self.c.p]
        self.q+=self.h*v;self.v=2*v-self.v;Em=.5*(self.v@(self.Ms@self.v)+self.q@(self.Ks@self.q))
        return dict(v=v,u=u,load=np.r_[F,np.zeros(self.m-80)],Em=float(Em),Ei=Ei,dc=dc,w=self.h*float(f@v),dm=self.h*float(v@(self.Ds@v)),air=self.h*float(F@v[:80]),port=float(np.sum(u*y)/384000),wi=float(np.sum(u*yi)/384000),we=float(np.sum(u*ye)/384000),continuity=float(np.linalg.norm(y.ravel()[self.bot])/max(np.linalg.norm(yi)+np.linalg.norm(ye),1e-300)),joint_error=0.)
