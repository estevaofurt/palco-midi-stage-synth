"""G3.05h: iterative refinement of the original condensed structural equations.
No change of physical matrices, tolerances, geometry or string loss.
Extended precision is an offline diagnostic, not a deployment requirement.
"""
import numpy as np
from scipy.linalg import cholesky,solve_triangular,lu_factor,lu_solve
from structural_response import congruence,symmetric

def extended_dynamic(M,K,D,w):
    # Preserve the same double-precision frequency coefficients as the original
    # model, but evaluate the subtraction and residual with a wider mantissa.
    A=np.array(K,dtype=np.clongdouble)
    A.real-=np.longdouble(w*w)*np.asarray(M,dtype=np.longdouble)
    A.imag=np.longdouble(w)*np.asarray(D,dtype=np.longdouble)
    return A

def refine(A,extra,rhs,L,factor,x0,maxSteps=5):
    if np.finfo(np.longdouble).nmant<=np.finfo(np.float64).nmant:
        raise RuntimeError('extended precision unavailable; cannot run this proof')
    x=np.array(x0,dtype=np.clongdouble)
    def residual(y):return np.asarray(rhs,dtype=np.clongdouble)-A@y-extra[:,None]*y
    den=max(float(np.linalg.norm(rhs)),1e-30)
    e=residual(x);initial=float(np.linalg.norm(e))/den;best=initial;steps=0
    for _ in range(maxSteps):
        if best<=1e-8:break
        R=solve_triangular(L,np.asarray(e,dtype=np.complex128),lower=True)
        dx=solve_triangular(L.T,lu_solve(factor,R),lower=False)
        candidate=x+dx.astype(np.clongdouble)
        ne=residual(candidate);err=float(np.linalg.norm(ne))/den
        if err>=best:break
        x,e,best=candidate,ne,err;steps+=1
    return x,dict(initial=initial,final=best,corrections=steps)

def response(M,K,D,P,wires,freq):
    M,_=symmetric(M);K,_=symmetric(K);D,_=symmetric(D)
    n=len(M);p=P.shape[1];Y=[];records=[]
    s=1/np.sqrt(np.diag(M));W=s[:,None]*s[None,:]
    M=M*W;K=K*W;D=D*W;P=P*s[:,None]
    for f in freq:
        w=2*np.pi*f;assert w>0
        # Base physical structural matrices, scaled by mass; add exact Schur terms.
        rhs=P.astype(complex);feed=np.zeros((p,p),complex)
        extra=np.zeros(n,complex);pre=np.zeros(n);local=[]
        for wire in wires:
            z,r,h,b,c=wire.condense(w);j=wire.rear;i=wire.port
            extra[j]+=z*s[j]**2;rhs[j,i]+=r*s[j];feed[i,i]+=h
            pre[j]+=(wire.K[0,0]+w*w*wire.M[0,0]+w*wire.D[0,0])*s[j]**2
            local.append((wire,b,c))
        L=cholesky(K+w*w*M+w*D+np.diag(pre),lower=True)
        G=congruence(L,K)-congruence(L,w*w*M)+1j*congruence(L,w*D)
        # Complex symmetric, not Hermitian, congruence for condensed impedance.
        idx=np.flatnonzero(extra)
        if len(idx):
            E=np.zeros((n,len(idx)));E[idx,np.arange(len(idx))]=1.
            E=solve_triangular(L,E,lower=True)
            G+=(E*extra[idx])@E.T
        R=solve_triangular(L,rhs,lower=True);factor=lu_factor(G);v=lu_solve(factor,R)
        x0=solve_triangular(L.T,v,lower=False)
        # Keep the physical residual separate from the normalized solve. Reuse the
        # existing factorization only for correction, not as an audit of itself.
        A=extended_dynamic(M,K,D,w)
        x,refinement=refine(A,extra,rhs,L,factor,x0)
        x64=np.asarray(x,dtype=np.complex128)
        H=np.asarray(rhs.T@x+feed,dtype=np.complex128);Z=1j*w*H
        # Independent physical force/velocity power audit after reconstructing all wire states.
        expected=w*w*(x64.conj().T@D@x64)
        force=np.eye(p);residual=A@x-P
        residual64=(K-w*w*M+1j*w*D)@x64-P
        internal=0.;observation=P.T@x
        for wire,b,c in local:
            j=wire.rear;i=wire.port
            q=wire.recover(s[j]*x[j],force[i],b,c)
            q64=np.asarray(q,dtype=np.complex128)
            expected+=w*w*(q64.conj().T@wire.D@q64)
            z=extended_dynamic(wire.M,wire.K,wire.D,w)@q-wire.P[:,None]*force[i]
            z64=(wire.K-w*w*wire.M+1j*w*wire.D)@q64-wire.P[:,None]*force[i]
            residual[j]+=s[j]*z[0];residual64[j]+=s[j]*z64[0]
            internal=max(internal,float(np.linalg.norm(z[1:])/max(np.linalg.norm(wire.P),1e-30)))
            observation[i]+=wire.P@q
        herm=(Z+Z.conj().T)/2
        row=dict(frequencyHz=float(f),reciprocity=float(np.linalg.norm(Z-Z.T)/max(np.linalg.norm(Z),1e-30)),
           passivityMinRelative=float(min(np.linalg.eigvalsh(herm))/max(np.linalg.norm(herm),1e-30)),
           powerRelative=float(np.linalg.norm(herm-expected)/max(np.linalg.norm(herm),np.linalg.norm(expected),1e-30)),
           structuralResidual=float(np.linalg.norm(residual)/max(np.linalg.norm(rhs),1e-30)),
           structuralResidualFloat64=float(np.linalg.norm(residual64)/max(np.linalg.norm(rhs),1e-30)),
           condensedResidualInitial=refinement['initial'],condensedResidualFinal=refinement['final'],
           corrections=refinement['corrections'],
           internalResidual=internal,observationRelative=float(np.linalg.norm(H-observation)/max(np.linalg.norm(H),1e-30)),
           scaledResidual=float(np.linalg.norm(G@v-R)/max(np.linalg.norm(R),1e-30)))
        Y.append(Z);records.append(row)
    summary={k:(min if k=='passivityMinRelative' else max)(q[k] for q in records) for k in records[0] if k!='frequencyHz'}
    summary['gate']=summary['reciprocity']<=1e-8 and summary['passivityMinRelative']>=-1e-8 and summary['powerRelative']<=1e-6 and summary['structuralResidual']<=1e-5 and summary['internalResidual']<=1e-5 and summary['observationRelative']<=1e-8 and summary['scaledResidual']<=1e-8
    summary['extendedMantissaBits']=int(np.finfo(np.longdouble).nmant)
    return np.array(Y),summary,records

