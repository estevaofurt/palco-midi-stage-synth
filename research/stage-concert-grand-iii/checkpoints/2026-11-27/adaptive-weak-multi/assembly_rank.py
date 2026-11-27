import numpy as np
from historical_screen import wire
KEYS=(45,48,60,64); SPREAD={45:0.,48:.5,60:1.,64:1.}
def assemble(i0,scale,held,partials):
    held_keys={held} if isinstance(held,int) else set(held); rows={v['key']:v for v in scale['rows']}; ids=[v for v in scale['wires'] if v['key'] in KEYS]; n=80+partials*len(ids)
    M=np.eye(n);K=np.zeros((n,n));D=K.copy();K[:80,:80]=i0['nominal']+.025*(i0['treble_low']+i0['treble_high']);D[:80,:80]=i0['damping'];P=np.zeros((n,len(ids)));wires=[]
    for j,a in enumerate(ids):
        key=a['key'];rr=rows[key];off=np.linspace(-SPREAD[key],SPREAD[key],rr['count'])[a['unisonIndex']-1];w=wire(rr,off,5.5 if key==48 else 0.,partials=partials);g=i0['wire_ports_all'][key-21];sl=slice(80+partials*j,80+partials*(j+1));o=np.outer(g,g)
        for X,x,diag,cross in ((M,'m0',np.ones(partials),'m'),(K,'k0',w['w2'],'k'),(D,'d0',w['gamma'],'d')):
            X[:80,:80]+=w[x]*o;X[sl,sl]=np.diag(diag);X[sl,:80]=np.outer(w[cross],g);X[:80,sl]=X[sl,:80].T
        dam=np.zeros(n);dam[:80]=.18*g;dam[sl]=w['damper'];strength=0 if key in held_keys else 2/rr['count'];D+=strength*np.outer(dam,dam)
        P[:80,j]=w['p0']*g;P[sl,j]=w['p'];wires.append((a,w,g,strength))
    L=np.zeros((80,n));L[:,:80]=np.eye(80)
    return M,K,D,P,L,wires

