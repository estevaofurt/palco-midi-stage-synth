"""G3.04c distributed relative bridge/board displacement interface.
Two vertical arclength beams and one rectangular orthotropic plate fixture.
No ground spring, no string load, no calibrated bond or actual board.
"""
import numpy as np
from scipy.linalg import block_diag,solve
from numpy.polynomial.legendre import leggauss
from continuous_bridge import build

def plate(bounds,c,n):
    a=bounds['x'][1]-bounds['x'][0];b=bounds['y'][1]-bounds['y'][0]
    h=c['thicknessM'];rho=c['densityKgM3'];ex=c['ExPa'];ey=c['EyPa'];g=c['GxyPa'];v=c['nuXY'];vy=v*ey/ex
    assert min(a,b,h,rho,ex,ey,g)>0 and 1-v*vy>0
    d=h**3/(12*(1-v*vy));dx=d*ex;dy=d*ey;dxy=d*v*ey;ds=g*h**3/12
    i,j=np.meshgrid(np.arange(1,n+1),np.arange(1,n+1),indexing='ij')
    kx=np.pi*i.ravel()/a;ky=np.pi*j.ravel()/b
    # Unit peak sine-sine modes; mass consistent with same normalization.
    mass=rho*h*a*b/4
    K=a*b/4*(dx*kx**4+2*(dxy+2*ds)*kx*kx*ky*ky+dy*ky**4)
    def shape(xy):
        p=np.asarray(xy)-np.array([bounds['x'][0],bounds['y'][0]])
        return np.sin(p[...,0,None]*kx)*np.sin(p[...,1,None]*ky)
    return np.full(n*n,mass),K,shape

def joint_rows(center,beam,sub,shape,order):
    # Each row maps physical coordinates to the relative normal displacement.
    # Gauss quadrature weights are in meters; no concentrated per-wire springs.
    xi,wi=leggauss(order);t=(xi+1)/2;weights=wi/2
    xyz=center['xyz'];nb=len(beam['M']);br=[];pl=[];w=[]
    for e,L in enumerate(np.diff(beam['mesh'])):
        j=e//sub;u0=(e%sub)/sub;u=u0+t/sub
        xy=(1-u[:,None])*xyz[j,:2]+u[:,None]*xyz[j+1,:2]
        N=np.stack([1-3*t*t+2*t**3,L*(t-2*t*t+t**3),3*t*t-2*t**3,L*(-t*t+t**3)],axis=1)
        B=np.zeros((order,nb));B[:,2*e:2*e+4]=N
        br.append(B);pl.append(shape(xy));w.extend((L*weights).tolist())
    return np.vstack(br),np.vstack(pl),np.array(w)

def assemble(centers,layout,cfg,bcfg,sub,n,order,connected=True):
    c=cfg['plate'];pm,pk,shape=plate(layout['boardEnvelope'],c,n)
    beams=[];mass=[];stiff=[];drag=[]
    for section in ('bass','treble'):
        m=bcfg['material'];s=bcfg['section'][section];f=bcfg['fixture']
        b=build(centers[section]['xyz'],sub,m['densityKgM3'],m['youngAlongPa'],s['widthM'],s['heightM'],0.)
        beams.append(b);mass.append(b['M']);stiff.append(b['K'])
        drag.append(f['massDampingPerS']*b['M']+f['stiffnessDampingS']*b['K'])
    mass.append(np.diag(pm));stiff.append(np.diag(pk));drag.append(np.diag(c['alphaPerS']*pm+c['betaS']*pk))
    M=block_diag(*mass);K0=block_diag(*stiff);D=block_diag(*drag)
    nb=[len(b['M']) for b in beams];size=len(M);joint=np.zeros_like(M);maps=[];start=0
    for section,b in zip(('bass','treble'),beams):
        B,S,w=joint_rows(centers[section],b,sub,shape,order)
        R=np.zeros((len(w),size));R[:,start:start+len(b['M'])]=B;R[:,sum(nb):]=-S
        if connected:joint+=R.T@((cfg['joint']['stiffnessNperM2']*w)[:,None]*R)
        maps.append((R,w));start+=len(b['M'])
    # One representative force and moment port per bridge, plus two plate pressure-point
    # force ports at projected bridge attachment centers. All are work-conjugate.
    P=np.zeros((size,6));start=0
    for j,(section,b) in enumerate(zip(('bass','treble'),beams)):
        idx=len(centers[section]['keys'])//2;dof=start+b['attachmentDofs'][idx]
        P[dof,2*j]=1.;P[dof+1,2*j+1]=1.
        P[sum(nb):,4+j]=shape(centers[section]['xyz'][idx,:2]);start+=len(b['M'])
    return M,K0,joint,D,P,maps,nb

def mobility(M,K,D,P,freq):
    scale=np.array([1.,.02,1.,.02,1.,1.]);out=[];recip=0.;passmin=0.
    for f in freq:
        w=2*np.pi*f
        Y=1j*w*(P.T@solve(K-w*w*M+1j*w*D,P,assume_a='gen'))
        recip=max(recip,float(np.linalg.norm(Y-Y.T)/max(np.linalg.norm(Y),1e-30)))
        Z=Y*scale[:,None]*scale[None,:];H=(Z+Z.conj().T)/2
        passmin=min(passmin,float(np.linalg.eigvalsh(H)[0]/max(np.linalg.norm(H),1e-30)))
        out.append(Y)
    assert recip<=1e-8 and passmin>=-1e-8
    return np.array(out),recip,passmin
