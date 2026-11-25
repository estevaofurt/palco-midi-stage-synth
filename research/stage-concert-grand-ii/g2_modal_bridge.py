"""G2.09b: offline exact local modal updates with a reciprocal PSD damping port."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh, expm, solve, cho_factor, cho_solve

OUT = Path('/tmp/g2-modal-bridge')
DATA = json.loads((OUT/'physical.json').read_text())
T = .04
def energy(q,v,w2): return .5*(v@v+(w2*q)@q)
def relative(a,b):
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-30))
def pulse(t,h):
    # Integral of the same raised cosine force over each interval.
    def integ(x):
        u=np.clip(x,0,.001)
        return .1*(u/2-.001*np.sin(2*np.pi*u/.001)/(4*np.pi))
    return float((integ(t+h)-integ(t))/h)
def run(w2,D,P,q0,v0,sr,kind,exact=False):
    h=1/sr; n=len(w2); q=q0.copy(); v=v0.copy()
    if kind=='forced': q.fill(0);v.fill(0)
    E0=energy(q,v,w2);work=0.;loss=0.;maxbal=0.;minloss=0.;trace=[]
    if exact:
        # Full damped linear continuous state + constant input over step.
        A=np.zeros((2*n+1,2*n+1))
        A[:n,n:2*n]=np.eye(n);A[n:2*n,:n]=-np.diag(w2)
        A[n:2*n,n:2*n]=-D;A[n:2*n,-1]=P[:,2]
        E=expm(h*A); B=E[:2*n,-1];Ad=E[:2*n,:2*n]
    else:
        w=np.sqrt(w2);c=np.cos(w*h);s=np.sin(w*h)
        G=2*np.sin(w*h/2)**2/w2;J=s/w
        # delta = sqrt(G) (I+sqrt(G) D sqrt(G)/h)^-1 rhs / sqrt(G)
        sg=np.sqrt(G);assert np.all(sg>0)
        F=cho_factor(np.eye(n)+(sg[:,None]*D*sg[None,:])/h)
        inv=cho_solve(F,np.eye(n))
    for i in range(round(sr*T)):
        u=pulse(i*h,h) if kind=='forced' and i*h<.001 else 0.
        old=q.copy()
        if exact:
            y=Ad@np.concatenate((q,v))+B*u;q,v=y[:n],y[n:]
        else:
            f=P[:,2]*u
            r=(c-1)*q+J*v+G*f
            delta=sg*(inv@(r/sg))
            damping=D@delta/h
            v=-w*s*q+c*v+J*(f-damping);q+=delta
            d=float(delta@damping);loss+=d;minloss=min(minloss,d)
        work+=float(u*(P[:,2]@(q-old)))
        if not exact:
            maxbal=max(maxbal,abs(E0+work-energy(q,v,w2)-loss))
        if (i+1)%(sr//1000)==0:trace.append(P.T@q)
    E1=energy(q,v,w2)
    if not exact:
        assert minloss>=-1e-12 and maxbal<=max(1e-10,1e-7*(E0+abs(work)))
    return dict(trace=np.array(trace),initial=E0,final=E1,work=work,loss=loss if not exact else E0+work-E1,balance=maxbal,minloss=minloss)
rows=[];bases=[];checks=[]
for a in DATA:
    M,C,K=(np.asarray(a[k]) for k in ('M','C','K'));N=a['N'];n=a['n']
    raw=np.zeros((n,2));raw[0,0]=1;raw[N,1]=1
    raw=np.column_stack((raw,np.asarray(a['ports']).T))
    w2,U=eigh(K,M);assert np.all(w2>0)
    assert np.max(abs(U.T@M@U-np.eye(n)))<1e-9
    D=U.T@C@U;D=(D+D.T)/2
    assert np.min(eigh(D,eigvals_only=True))>=-1e-9
    P=U.T@raw;q0=U.T@M@np.asarray(a['initial']['x']);v0=U.T@M@np.asarray(a['initial']['v'])
    f=np.sqrt(w2)/(2*np.pi);assert f[-1]<.49*48000
    bases.append(dict(key=a['key'],lossId=a['lossId'],full=n,maxHz=float(f[-1]),minD=float(eigh(D,eigvals_only=True)[0])))
    for kind in ('free','forced'):
        ref=run(w2,D,P,q0,v0,96000,kind,True)
        if kind=='free':
            err=relative(ref['trace'][:,:2],np.asarray(a['trace']))
            assert err<.02
        else:err=None
        for tag,idx in [('full',np.arange(n)),('band',np.flatnonzero(f<a['cutoffHz'])),('reduced75',np.flatnonzero(f<.75*a['cutoffHz']))]:
            assert len(idx)>0
            for sr in (48000,96000):
                z=run(w2[idx],D[np.ix_(idx,idx)],P[idx,:],q0[idx],v0[idx],sr,kind)
                errors=dict(bridge=relative(z['trace'][:,:2],ref['trace'][:,:2]),contacts=relative(z['trace'][:,2:],ref['trace'][:,2:]),energy=abs(z['final']-ref['final'])/max(abs(ref['final']),1e-30),work=abs(z['work']-ref['work'])/max(abs(ref['work']),1e-30) if kind=='forced' else 0.)
                passed=all(v<=.10 for v in errors.values())
                r=dict(key=a['key'],lossId=a['lossId'],kind=kind,tag=tag,sr=sr,modes=len(idx),full=n,errors=errors,pass_=passed,reference384Error=err,balance=z['balance'],minloss=z['minloss'],initial=z['initial'],final=z['final'],work=z['work'],loss=z['loss'])
                rows.append(r)
                # Full-basis 96k is the algorithm gate; selected band at 96k is truncation gate.
                # 48k and aggressive truncation are diagnostics, not realtime approval.
                if sr==96000 and tag in ('full','band'): checks.append(r)
                print('G2_MODAL_BRIDGE '+json.dumps(r),flush=True)
gate=all(r['pass_'] for r in checks)
report=dict(scope='offline modal proof: exact local oscillators, full PSD midpoint damping, not realtime or sound pressure',bases=bases,rows=rows,required=len(checks),passed=sum(r['pass_'] for r in checks),gate=gate)
(OUT/'report.json').write_text(json.dumps(report,indent=2))
print('G2_MODAL_BRIDGE_GATE '+json.dumps({k:report[k] for k in ('required','passed','gate')}),flush=True)
if not gate: raise SystemExit(1)
