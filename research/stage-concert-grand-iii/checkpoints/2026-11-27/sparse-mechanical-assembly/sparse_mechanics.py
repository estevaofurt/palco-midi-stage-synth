"""Sparse assembly and exact block midpoint solve for the existing pilot scale.
No full mechanical matrix or dense mechanical LU is retained or factored.
"""
import numpy as np
from scipy.sparse import csr_matrix, bmat, block_diag, diags
from scipy.linalg import lu_factor, lu_solve, cholesky
from assembly_rank import KEYS, SPREAD
from historical_screen import wire
from condensed import CondensedWet, BlockSolve

def assemble_sparse(i0,scale,held,rank):
    held_keys={held} if isinstance(held,int) else set(held)
    rows={v['key']:v for v in scale['rows']}; ids=[v for v in scale['wires'] if v['key'] in KEYS]
    n=80+rank*len(ids);P=np.zeros((n,len(ids)));wires=[]
    board=[np.eye(80),i0['nominal']+.025*(i0['treble_low']+i0['treble_high']),i0['damping'].copy()]
    cross=[[],[],[]];inner=[[],[],[]];diagonal=[[],[],[]]
    for j,a in enumerate(ids):
        key=a['key'];rr=rows[key];off=np.linspace(-SPREAD[key],SPREAD[key],rr['count'])[a['unisonIndex']-1]
        w=wire(rr,off,5.5 if key==48 else 0.,partials=rank);g=i0['wire_ports_all'][key-21];o=np.outer(g,g);sl=slice(80+rank*j,80+rank*(j+1))
        strength=0 if key in held_keys else 2/rr['count'];v=w['damper'];b=.18*g
        for k,(x,d,c) in enumerate((('m0',np.ones(rank),'m'),('k0',w['w2'],'k'),('d0',w['gamma'],'d'))):
            board[k]+=w[x]*o;C=np.outer(w[c],g);I=np.diag(d)
            if k==2:
                board[k]+=strength*np.outer(b,b);C+=strength*np.outer(v,b);I+=strength*np.outer(v,v)
            cross[k].append(C);inner[k].append(csr_matrix(I));diagonal[k].append(d)
        P[:80,j]=w['p0']*g;P[sl,j]=w['p'];wires.append((a,w,g,strength))
    mats=[]
    for k in range(3):
        C=np.concatenate(cross[k],axis=0);mats.append(bmat([[csr_matrix(board[k]),csr_matrix(C.T)],[csr_matrix(C),block_diag(inner[k],format='csr')]],format='csr'))
    return (*mats,P,wires,diagonal)

class SparseBlock(BlockSolve):
    def __init__(self,J,diagonal,wires,rank,damper=True,positive=False):
        self.rank=rank;self.nw=len(wires);assert J.shape==(80+rank*self.nw,)*2
        self.B=J[:80,80:].toarray();self.C=J[80:,:80].toarray();d=np.asarray(diagonal);assert np.all(d>0)
        self.inv=1/d;self.v=np.array([w['damper'] for _,w,_,_ in wires]);self.iv=self.inv*self.v
        a=np.array([a if damper else 0. for _,_,_,a in wires]);self.alpha=a/(1+a*np.sum(self.v*self.iv,axis=1))
        self.X=self.inner(self.C);S=J[:80,:80].toarray()-self.B@self.X
        if positive:
            np.testing.assert_allclose(S,S.T,rtol=1e-10,atol=1e-10)
            cholesky((S+S.T)/2,lower=True)
        self.fac=lu_factor(S)

class SparseWet(CondensedWet):
    def __init__(self,c,e,Z,s,M,K,D,wires,rank,diagonal):
        self.c,self.e=c,e;self.Q=c.Q;self.m=M.shape[0];self.h=len(c.Q)/384000
        self.Ms,self.Ks,self.Ds=M,K,D
        for k,A in enumerate((M,K,D)):
            assert np.isfinite(A.data).all();delta=A-A.T;assert not delta.nnz or np.max(abs(delta.data))<1e-12*max(1.,np.max(abs(A.data)))
            SparseBlock(A,diagonal[k],wires,rank,damper=(k==2),positive=True)
        np.testing.assert_allclose(c.Q[:,0],1/np.sqrt(len(c.Q)),rtol=0,atol=1e-14)
        assert c.p==80 and np.all(s>0)
        self.Wb=np.diag(np.sqrt(len(c.Q))*s);self.Pb=np.diag(s/np.sqrt(len(c.Q)))
        self.top=np.arange(c.p);self.bot=(np.arange(c.Q.shape[1])[:,None]*c.n+np.arange(c.p,c.n)).ravel();T,B=self.top,self.bot
        self.Aa=Z[np.ix_(T,T)];self.Ab=Z[np.ix_(T,B)];self.Ba=Z[np.ix_(B,T)];self.Bb=Z[np.ix_(B,B)]
        self.fb=lu_factor(self.Bb);self.Xb=lu_solve(self.fb,self.Ba@self.Wb)
        Zb=self.Pb@(self.Aa@self.Wb-self.Ab@self.Xb)
        J=2*M/self.h+D+self.h*K/2+bmat([[csr_matrix(Zb),None],[None,csr_matrix((self.m-80,self.m-80))]],format='csr')
        d=2*np.asarray(diagonal[0])/self.h+np.asarray(diagonal[2])+self.h*np.asarray(diagonal[1])/2
        self.block=SparseBlock(J,d,wires,rank);self.reset()
