"""G3.06g: exact wire interior condensation on a truncated structural modal space.
Acoustic load and observer share the same surface velocity, no second radiation loss.
Frequency domain only; no hammer contact, no causal time-domain engine.
"""
import numpy as np
from scipy.linalg import solve

def response(modal,wirePorts,wires,Z,H,f):
    M,K,D,P=(modal[x] for x in ('M','K','D','P'))
    w=2*np.pi*f;n,p=P.shape
    assert Z.shape==(n,n) and H.shape[1]==n and len(wirePorts)==len(wires)
    R=(Z+Z.conj().T)/2
    assert min(np.linalg.eigvalsh(R))>=-1e-10*max(np.linalg.norm(R),1e-30)
    A=K-w*w*M+1j*w*(D+Z);rhs=P.astype(complex);feed=np.zeros((p,p),complex);local=[]
    for a,wire in zip(wirePorts,wires):
        z,g,h,b,c=wire.condense(w)
        A+=z*np.outer(a,a);rhs[:,wire.port]+=g*a;feed[wire.port,wire.port]+=h
        local.append((a,wire,b,c))
    x=solve(A,rhs);v=1j*w*x
    Y=1j*w*(rhs.T@x+feed);Obs=H@v
    wood=v.conj().T@D@v;air=v.conj().T@R@v;strings=np.zeros_like(wood)
    force=np.eye(p);reconstructed=P.T@x;residual=(K-w*w*M+1j*w*(D+Z))@x-P
    internal=0.
    for a,wire,b,c in local:
        q=wire.recover(a@x,force[wire.port],b,c)
        vv=1j*w*q;strings+=vv.conj().T@wire.D@vv
        eq=(wire.K-w*w*wire.M+1j*w*wire.D)@q-wire.P[:,None]*force[wire.port]
        residual+=a[:,None]*eq[0]
        internal=max(internal,float(np.linalg.norm(eq[1:])/max(np.linalg.norm(wire.P),1e-30)))
        reconstructed[wire.port]+=wire.P@q
    power=(Y+Y.conj().T)/2;den=max(np.linalg.norm(power),1e-30)
    fractions=[float(np.trace(q).real/max(np.trace(power).real,1e-30)) for q in (wood,strings,air)]
    metrics=dict(reciprocity=float(np.linalg.norm(Y-Y.T)/max(np.linalg.norm(Y),1e-30)),
        passivityMinRelative=float(min(np.linalg.eigvalsh(power))/den),
        powerRelative=float(np.linalg.norm(power-wood-strings-air)/den),
        structuralResidual=float(np.linalg.norm(residual)/max(np.linalg.norm(rhs),1e-30)),internalResidual=internal,
        observationRelative=float(np.linalg.norm(Y-1j*w*reconstructed)/max(np.linalg.norm(Y),1e-30)),
        lossFractions=dict(structure=fractions[0],strings=fractions[1],air=fractions[2]))
    metrics['gate']=metrics['reciprocity']<=1e-8 and metrics['passivityMinRelative']>=-1e-8 and metrics['powerRelative']<=1e-6 and metrics['structuralResidual']<=1e-5 and metrics['internalResidual']<=1e-5 and metrics['observationRelative']<=1e-8 and min(fractions)>=-1e-10
    return Y,Obs,metrics

def truncate(q,n):
    return dict(M=q['M'][:n,:n],K=q['K'][:n,:n],D=q['D'][:n,:n],P=q['P'][:n])
