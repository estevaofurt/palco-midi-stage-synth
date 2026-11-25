"""Uniform volume-velocity port on a finite flat top aperture.
A vented rigid cavity fixture, NOT tilted-lid diffraction or full exterior BEM.
"""
import numpy as np
from board_contour import properties
from closed_cavity import response as closed_response
from radiation_impedance import impedance

def clip_x(poly,cut):
    out=[]
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        va=a[0]-cut;vb=b[0]-cut
        if va>=0:out.append(a)
        if (va>0 and vb<0) or (va<0 and vb>0):out.append(a+(b-a)*va/(va-vb))
    return np.asarray(out)

def aperture(model,poly,cut):
    """Exact P1 trace integral on the part of the top face with x>=cut."""
    ap=clip_x(np.asarray(poly),cut);area,_,_=properties(ap)
    xy=model['xy'];tri=model['tri'];top=len(model['xyz'])-len(xy)
    c=np.zeros(len(model['xyz']));total=0.
    for ids in tri:
        t=xy[ids];part=clip_x(t,cut)
        if len(part)<3:continue
        J=(t[1:]-t[0]).T
        for j in range(1,len(part)-1):
            v=np.array([part[0],part[j],part[j+1]])
            a=abs(np.linalg.det((v[1:]-v[0]).T))/2
            if a==0:continue
            xi=np.linalg.solve(J,v.mean(axis=0)-t[0]);N=np.r_[1-xi.sum(),xi]
            c[top+ids]+=a*N;total+=a
    assert abs(total-area)<1e-10 and abs(sum(c)-area)<1e-10
    assert min(c)>=-1e-12
    return ap,area,c/area

def exterior(ap,area,s,rho,c,outer,inner):
    return impedance(ap,lambda xy,p:np.full((len(xy),1),1/area),s,rho,c,outer,inner)[0,0]

def response(model,C,s,points,Zext):
    """Eliminate outward aperture flow U from pressure continuity.
    C maps unit volume flow (m3/s) to boundary normal velocity load.
    The full cavity port vector is [board generalized velocities, -U].
    """
    if Zext.real< -1e-12*max(abs(Zext),1):raise ValueError('active exterior')
    q=dict(model,B=np.column_stack([model['B'],C]))
    Z,P,report=closed_response(q,s,points)
    U=Z[-1,:-1]/(Z[-1,-1]+Zext)
    Q=np.vstack([np.eye(len(U)),-U])
    Ze=Z[:-1]@Q;Pe=P@Q
    pc=Z[-1]@Q
    R=(Ze+Ze.conj().T)/2;H=(Z+Z.conj().T)/2
    expected=Q.conj().T@H@Q+Zext.real*np.outer(U.conj(),U)
    den=max(np.linalg.norm(Ze),1e-30)
    rec=float(np.linalg.norm(Ze-Ze.T)/den)
    powerr=float(np.linalg.norm(R-expected)/den)
    continuity=float(np.linalg.norm(pc-Zext*U)/max(np.linalg.norm(pc),np.linalg.norm(Zext*U),1e-30))
    pas=float(min(np.linalg.eigvalsh(R))/den)
    metrics=dict(cavity=report,reciprocity=rec,powerRelative=powerr,pressureContinuity=continuity,
       passivityMinRelative=pas,exteriorPowerTrace=float(Zext.real*np.vdot(U,U).real/2))
    metrics['gate']=report['gate'] and rec<=1e-8 and powerr<=1e-8 and continuity<=1e-8 and pas>=-1e-8
    return Ze,Pe,U,metrics
