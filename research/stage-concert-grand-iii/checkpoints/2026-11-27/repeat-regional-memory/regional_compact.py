"""Parameterized assembly for a declared regional scale; original compact model is immutable."""
import numpy as np
from scipy.linalg import cholesky
from compact_mechanics import Operator
from historical_screen import wire
def assemble_regional(base,scale,held,ranks,spread,shift):
    assert set(ranks)==set(spread)==set(shift) and set(ranks)<=set(range(21,109)) and all(type(n)==int and 1<=n<=128 for n in ranks.values())
    held={held} if isinstance(held,int) else set(held);rows={v['key']:v for v in scale['rows']};wires=[];g=[];ids=[];d=[[],[],[]];c=[[],[],[]];v=[];a=[]
    board=[np.eye(80),base['nominal']+.025*(base['treble_low']+base['treble_high']),base['damping'].copy()]
    src=[w for w in scale['wires'] if w['key'] in ranks];P=np.zeros((80+sum(ranks[w['key']] for w in src),len(src)));offset=80
    for j,w in enumerate(src):
        k=w['key'];r=rows[k];n=ranks[k];f=wire(r,np.linspace(-spread[k],spread[k],r['count'])[w['unisonIndex']-1],shift[k],partials=128);b=base['wire_ports_all'][k-21];s=0. if k in held else 2/r['count'];o=np.outer(b,b);z=f['damper'][:n];g.append(b);ids.extend([j]*n);v.extend(z);a.append(s)
        for i,(scalar,diag,cross) in enumerate(((f['m0'],np.ones(n),f['m'][:n]),(f['k0'],f['w2'][:n],f['k'][:n]),(f['d0'],f['gamma'][:n],f['d'][:n]))):
            board[i]+=scalar*o
            if i==2:board[i]+=s*np.outer(.18*b,.18*b);cross=cross+s*.18*z
            d[i].extend(diag);c[i].extend(cross)
        P[:80,j]=f['p0']*b;P[offset:offset+n,j]=f['p'][:n];offset+=n;wires.append((w,f,b,s))
    g,ids,v,a=map(np.asarray,(g,ids,v,a));ops=[Operator(board[i],g,ids,np.asarray(d[i]),np.asarray(c[i]),v,a if i==2 else np.zeros_like(a)) for i in range(3)]
    for op in ops:
        S=op.schur();cholesky((S+S.T)/2,lower=True)
    return (*ops,P,wires)
