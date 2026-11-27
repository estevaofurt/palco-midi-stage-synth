"""Midpoint coupling, using work-conjugate archived surface coordinates.
Mechanical matrices and lift must share a verified coordinate basis.
"""
import numpy as np
from scipy.linalg import lu_factor,lu_solve,eigvalsh
from scipy.fft import dctn

def scales(z,g):
    area=float(g['dx']*g['dy']); s=np.linalg.norm(z['T'],axis=0)*np.sqrt(area)
    a=dctn(g['A'].reshape(30,30,80),axes=(0,1),norm='ortho').reshape(900,80)
    np.testing.assert_allclose(a*s,z['T']*np.sqrt(area),atol=1e-14,rtol=0)
    assert np.all(s>0)
    return s

class Bridge:
    def __init__(self,c,e,Z,s,M,K,D,lift):
        self.c,self.e=c,e;self.Q=c.Q;self.m=len(M);self.h=len(c.Q)/384000;self.M,self.K,self.D=M,K,D
        self.S=s[:,None]*lift;assert self.S.shape==(c.p,self.m)
        assert np.allclose(c.Q[:,0],1/np.sqrt(len(c.Q)),atol=1e-14,rtol=0)
        for X in (M,K,D):
            assert X.shape==(self.m,self.m) and np.isfinite(X).all() and np.allclose(X,X.T)
            assert eigvalsh(X)[0]>=0
        assert eigvalsh(M)[0]>0
        self.W=np.sqrt(len(c.Q))*self.S;self.P=self.S.T/np.sqrt(len(c.Q))
        self.top=np.arange(c.p);self.bot=(np.arange(c.Q.shape[1])[:,None]*c.n+np.arange(c.p,c.n)).ravel()
        T,B=self.top,self.bot
        self.Aa=Z[np.ix_(T,T)];self.Ab=Z[np.ix_(T,B)];self.Ba=Z[np.ix_(B,T)];self.Bb=Z[np.ix_(B,B)]
        self.fb=lu_factor(self.Bb);self.X=lu_solve(self.fb,self.Ba@self.W)
        self.H=2*M/self.h+D+self.h*K/2;self.Z=self.P@(self.Aa@self.W-self.Ab@self.X);self.fm=lu_factor(self.H+self.Z)
        self.reset()
    def reset(self):
        self.c.reset();self.e.reset();self.q=np.zeros(self.m);self.v=np.zeros(self.m)
    def step(self,f,reference=False):
        ch=self.c.history();eh=self.e.history();hist=(ch+eh).ravel();hb=lu_solve(self.fb,hist[self.bot]);rhs=f+2*self.M@self.v/self.h-self.K@self.q
        v=lu_solve(self.fm,rhs-self.P@(hist[self.top]-self.Ab@hb));u=np.zeros(self.c.Q.shape[1]*self.c.n);u[self.top]=self.W@v;u[self.bot]=-self.X@v-hb
        err=0.
        if reference:
            J=np.block([[self.H+self.P@self.Aa@self.W,self.P@self.Ab],[self.Ba@self.W,self.Bb]])
            x=np.linalg.solve(J,np.r_[rhs-self.P@hist[self.top],-hist[self.bot]])
            err=np.linalg.norm(np.r_[v,u[self.bot]]-x)/max(np.linalg.norm(x),1e-300)
        u=u.reshape(self.c.Q.shape[1],self.c.n);yi,dc,Ei=self.c.step(u);ye=self.e.commit(u,eh);y=yi+ye;F=self.P@y[0,:self.c.p]
        self.q+=self.h*v;self.v=2*v-self.v;Em=.5*(self.v@self.M@self.v+self.q@self.K@self.q)
        return dict(v=v,u=u,load=F,Em=float(Em),Ei=Ei,dc=dc,w=self.h*float(f@v),dm=self.h*float(v@self.D@v),air=self.h*float(F@v),port=float(np.sum(u*y)/384000),wi=float(np.sum(u*yi)/384000),we=float(np.sum(u*ye)/384000),continuity=float(np.linalg.norm(y.ravel()[self.bot])/max(np.linalg.norm(yi)+np.linalg.norm(ye),1e-300)),joint_error=float(err))
