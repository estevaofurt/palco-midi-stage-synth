"""Fused modal update: exact historical coefficients, no state reduction."""
import numpy as np
from numba import njit
from coupled369 import Grouped
import replay as r

@njit
def free_output(x,v,ch,H):
    y=np.zeros((H.shape[0],1800))
    for i in range(len(x)):
        for j in range(H.shape[0]):
            y[j,ch[i]]+=H[j,0,i]*x[i]+H[j,1,i]*v[i]
    return y

@njit
def update(x,v,ch,Q,g,coef,zero,mu1,mu2,gamma,dt):
    y=np.zeros((Q.shape[1],1800));loss=0.;energy=0.
    for i in range(len(x)):
        a,b,c,d,g0,g1,cx,cv,feed,eq,res=coef[:,i];xx=x[i];vv=v[i];k=ch[i]
        for j in range(Q.shape[0]):
            f=g[j,k];nx=a*xx+b*vv+g0*f;nv=c*xx+d*vv+g1*f
            yy=cx*xx+cv*vv+feed*f
            for t in range(Q.shape[1]):y[t,k]+=Q[j,t]*yy
            if zero[i]:
                ve=res*f/gamma;dv=vv-ve;loss+=gamma*ve**2*dt+2*ve*dv*mu1+.5*dv**2*mu2
            else:
                xe=xx-eq*f;nxe=nx-eq*f;loss+=.5*((xe-nxe)*(xe+nxe)+(vv-nv)*(vv+nv))
            xx=nx;vv=nv
        x[i]=xx;v[i]=vv;energy+=.5*(xx*xx+vv*vv)
    return y,loss,energy

class FusedGrouped(Grouped):
    def __init__(self,z,A,B,Q):
        super().__init__(z,A,B,Q);c=self.c
        ax=np.ones_like(c.x);av=np.zeros_like(c.x);bx=av.copy();bv=ax.copy();H=[]
        for _ in range(len(Q)):
            H.append(np.stack([c.cx*ax+c.cv*av,c.cx*bx+c.cv*bv]));ax,av=c.a*ax+c.b*av,c.c*ax+c.d*av;bx,bv=c.a*bx+c.b*bv,c.c*bx+c.d*bv
        self.H=np.einsum('td,tkn->dkn',Q,np.array(H));self.coef=np.stack([c.a,c.b,c.c,c.d,c.g0,c.g1,c.cx,c.cv,c.feed,c.eq,c.g]);self.mu1=-np.expm1(-r.GAMMA*c.dt);self.mu2=-np.expm1(-2*r.GAMMA*c.dt)
    def history(self):return free_output(self.c.x,self.c.v,self.ch,self.H)@self.F
    def step(self,u):
        y,l,e=update(self.c.x,self.c.v,self.ch,self.Q,(self.Q@u)@self.F.T,self.coef,self.c.z,self.mu1,self.mu2,r.GAMMA,self.c.dt)
        return y@self.F,float(l),float(e)
