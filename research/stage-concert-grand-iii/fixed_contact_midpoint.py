"""Fixed-contact compiled midpoint. The nonlinear hammer/pedal transition
remains on PointSchur. No change to original compiled dry kernel."""
import numpy as np
from numba import njit
from scipy.linalg import cho_solve
from compiled_wire_midpoint import Compiled

@njit(cache=True)
def fixed_kernel(h,k,D,A,P,ports,hammer,m0,k0,d0,mi,ki,di,ks,ds,C,invHi,J,
           q,v,x,u,rv,rq,rm,ri,rb,vm,um,forces,obs,ledger,board_acceleration,B,I,V,U,small,levels,contact_y,contact_t):
    n=len(q);nw=len(x);ns=x.shape[1];np_=P.shape[1];a=2/h
    for t in range(len(forces)):
        F=forces[t]
        for w in range(nw):
            vv=0.;qq=0.
            for j in range(n):
                vv+=A[w,j]*v[j];qq+=A[w,j]*q[j]
            rv[w]=vv;rq[w]=qq
            b=a*m0[w]*vv-k0[w]*qq
            for i in range(ns):
                R=a*u[w,i]-ks[w,i]*x[w,i]+a*mi[w,i]*vv-ki[w,i]*qq+hammer[w,i]*F[ports[w]]
                ri[w,i]=R
                b+=a*mi[w,i]*u[w,i]-ki[w,i]*x[w,i]-C[w,i]*R*invHi[w,i]
            rm[w]=b
        for j in range(n):
            b=a*v[j]-k[j]*q[j]
            for w in range(nw):b+=A[w,j]*rm[w]
            for i in range(np_):b+=P[j,i]*F[i]
            rb[j]=b
        for j in range(n):
            s=0.
            for i in range(n):s+=J[j,i]*rb[i]
            vm[j]=s
        # Free midpoint velocity in all wire interiors.
        for w in range(nw):
            vv=0.
            for j in range(n):vv+=A[w,j]*vm[j]
            for i in range(ns):um[w,i]=(ri[w,i]-C[w,i]*vv)*invHi[w,i]
        # Woodbury correction for the fixed, active damper contacts.
        for c in range(len(levels)):
            s=0.
            for j in range(n):s+=B[j,c]*vm[j]
            for w in range(nw):
                for i in range(ns):s+=I[w,i,c]*um[w,i]
            contact_y[c]=s
        for c in range(len(levels)):
            s=0.
            for d in range(len(levels)):s+=small[c,d]*contact_y[d]
            contact_t[c]=s
        for j in range(n):
            for c in range(len(levels)):vm[j]-=V[j,c]*contact_t[c]
        for w in range(nw):
            for i in range(ns):
                for c in range(len(levels)):um[w,i]-=U[w,i,c]*contact_t[c]
        loss=0.
        for c in range(len(levels)):
            s=0.
            for j in range(n):s+=B[j,c]*vm[j]
            for w in range(nw):
                for i in range(ns):s+=I[w,i,c]*um[w,i]
            loss+=levels[c]*s*s
        for j in range(n):
            d=0.
            for i in range(n):d+=D[j,i]*vm[i]
            loss+=vm[j]*d
        for i in range(np_):
            y=0.
            for j in range(n):y+=P[j,i]*vm[j]
            obs[t,i]=y
        for w in range(nw):
            vv=0.
            for j in range(n):vv+=A[w,j]*vm[j]
            loss+=d0[w]*vv*vv
            for i in range(ns):
                s=um[w,i]
                loss+=ds[w,i]*s*s+2*di[w,i]*vv*s
                obs[t,ports[w]]+=hammer[w,i]*s
        work=0.
        for i in range(np_):work+=F[i]*obs[t,i]
        ledger[t,0]=h*work;ledger[t,1]=h*loss
        for j in range(n):
            if board_acceleration is not None:board_acceleration[t,j]=2*(vm[j]-v[j])/h
            q[j]+=h*vm[j];v[j]=2*vm[j]-v[j]
        for w in range(nw):
            for i in range(ns):
                x[w,i]+=h*um[w,i];u[w,i]=2*um[w,i]-u[w,i]

class FixedContacts:
    def __init__(self,target):
        a=target.a
        if not isinstance(a,Compiled):raise TypeError('compiled wire required')
        self.a=a;self.target=target;self.levels=target.d.copy()
        active=np.flatnonzero(self.levels>0.)
        self.d=np.ascontiguousarray(self.levels[active])
        self.B=np.ascontiguousarray(target.B[:,active])
        self.I=np.ascontiguousarray(target.I[:,:,active])
        self.V=np.ascontiguousarray(target.V[:,active])
        self.U=np.ascontiguousarray(target.U[:,:,active])
        s=np.sqrt(self.d)
        # H^-1 Q diag(s) (Id+diag(s)Q^T H^-1 Q diag(s))^-1 diag(s) Q^T
        if len(active):
            C=target.C[np.ix_(active,active)]
            self.small=np.ascontiguousarray((s[:,None]*np.linalg.solve(np.eye(len(s))+(s[:,None]*C)*s,np.diag(s))))
        else:self.small=np.empty((0,0))
        self.y=np.zeros(len(active));self.t=self.y.copy()
    def process(self,forces,obs,ledger,acc):
        a=self.a;n=len(forces);p=a.P.shape[1]
        if not np.array_equal(self.levels,self.target.d):raise ValueError('fixed contact changed')
        bufs=(forces,obs,ledger,acc)
        for x,shape in zip(bufs,((n,p),(n,p),(n,2),(n,a.n))):
            if not isinstance(x,np.ndarray) or x.shape!=shape or x.dtype!=np.float64 or not x.flags.c_contiguous:raise ValueError('buffer shape/type')
        if not np.isfinite(forces).all() or not all(x.flags.writeable for x in bufs[1:]):raise ValueError('invalid buffer')
        for i,x in enumerate(bufs):
            for z in (*bufs[i+1:],a.q,a.v,a.x,a.u,a.J,a.P,a.A,a.ri,a.um,a.rb,a.vm,self.B,self.I,self.V,self.U,self.small,self.y,self.t):
                if np.shares_memory(x,z):raise ValueError('buffer alias')
        if not len(self.d):a.process(forces,obs,ledger,acc);return
        fixed_kernel(a.h,a.k,a.D,a.A,a.P,a.ports,a.hammer,a.m0,a.k0,a.d0,
            a.mi,a.ki,a.di,a.ks,a.ds,a.C,a.invHi,a.J,a.q,a.v,a.x,a.u,
            a.rv,a.rq,a.rm,a.ri,a.rb,a.vm,a.um,forces,obs,ledger,acc,
            self.B,self.I,self.V,self.U,self.small,self.d,self.y,self.t)
