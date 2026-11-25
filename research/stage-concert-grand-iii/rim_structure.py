"""Closed arclength beam around polygon; scalar flexure, relative vertical joint.
Separate rim foundation is a temporary fixture, not real case or soundboard loss.
"""
import numpy as np
from scipy.linalg import block_diag,solve
from numpy.polynomial.legendre import leggauss
from continuous_bridge import segment
def beam(poly,sub,rho,E,width,height,kf):
    lengths=np.linalg.norm(np.roll(poly,-1,axis=0)-poly,axis=1)
    assert min(lengths)>0 and sub>=1
    n=len(poly)*sub;M=np.zeros((2*n,2*n));K=np.zeros_like(M);F=np.zeros_like(M)
    A=width*height;I=width*height**3/12
    for i,L in enumerate(np.repeat(lengths/sub,sub)):
        m,k,f=segment(L,rho*A,E*I,kf)
        j=(i+1)%n;ids=[2*i,2*i+1,2*j,2*j+1]
        M[np.ix_(ids,ids)]+=m;K[np.ix_(ids,ids)]+=k;F[np.ix_(ids,ids)]+=f
    return M,K,F,float(sum(lengths)*rho*A)
def assemble(model,cfg,sub,order,connected=True):
    b=model['basis'];T=model['T'];poly=b.poly
    if b.essential:raise ValueError('free plate basis required')
    r=cfg['rim'];c=cfg['joint'];p=cfg['plate']
    Mr,Kr,F,mass=beam(poly,sub,r['densityKgM3'],r['youngAlongPa'],r['widthM'],r['heightM'],r['foundationNperM2'])
    Mp=model['M']+model['Mr'];Kp=model['K']+model['Kr'];np_=len(Mp);nr=len(Mr)
    M=block_diag(Mp,Mr);K=block_diag(Kp,Kr+F)
    D=block_diag(p['alphaPerS']*Mp+p['betaS']*Kp,r['alphaPerS']*Mr+r['betaS']*Kr)
    J=np.zeros_like(M);maps=[]
    # Integrate joint exactly enough across both spline knots and beam element boundaries.
    for i,(a,z) in enumerate(zip(poly,np.roll(poly,-1,axis=0))):
        for j in range(sub):
            A=a+(z-a)*j/sub;B=a+(z-a)*(j+1)/sub;d=B-A;L=float(np.linalg.norm(d))
            ix=i*sub+j;end=(ix+1)%(nr//2);ids=[2*ix,2*ix+1,2*end,2*end+1]
            for xy,w in b.line(A,B,order):
                t=(xy-A)@d/L**2
                H=np.stack([1-3*t*t+2*t**3,L*(t-2*t*t+t**3),3*t*t-2*t**3,L*(-t*t+t**3)],axis=1)
                R=np.zeros((len(w),np_+nr));R[:,:np_]=b.evaluate(xy)[0]@T;R[:,np_+np.array(ids)]=-H
                if connected:J+=R.T@((c['stiffnessNperM2']*w)[:,None]*R)
                maps.append((R,w))
    return dict(M=M,K=K,J=J,D=D,maps=maps,rimMassKg=mass,plateDofs=np_,rimDofs=nr)
def response(model,assembled,points,freq):
    b=model['basis'];T=model['T'];a=assembled;n=a['plateDofs']
    P=np.zeros((len(a['M']),len(points)+1))
    P[:n,:len(points)]=(b.evaluate(points)[0]@T).T;P[n,-1]=1.
    M=a['M'];K=a['K']+a['J'];D=a['D'];s=1/np.sqrt(np.diag(M));W=s[:,None]*s[None,:]
    P=P*s[:,None];M=M*W;K=K*W;D=D*W
    Y=[];rec=0.;pas=0.
    for f in freq:
        w=2*np.pi*f;Z=1j*w*P.T@solve(K-w*w*M+1j*w*D,P)
        rec=max(rec,float(np.linalg.norm(Z-Z.T)/max(np.linalg.norm(Z),1e-30)))
        H=(Z+Z.conj().T)/2;pas=min(pas,float(min(np.linalg.eigvalsh(H))/max(np.linalg.norm(H),1e-30)))
        Y.append(Z)
    assert rec<=1e-8 and pas>=-1e-8
    return np.array(Y),rec,pas
