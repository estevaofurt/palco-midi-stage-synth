"""G3.05e joint assembly of two bridge beams, ribbed free plate and mobile rim.
Vertical scalar fixture, no strings, no acoustic load, no selected parameters.
"""
import numpy as np
from scipy.linalg import block_diag,solve
from continuous_bridge import build
from rim_structure import assemble as rim_assemble

def assemble(model,centers,bcfg,icfg,rcfg,bridgeSub,rimSub,order,connected=True):
    a=rim_assemble(model,rcfg,rimSub,order)
    b=model['basis'];T=model['T'];np_=a['plateDofs'];nr=a['rimDofs']
    beams=[];m=[];k=[];d=[]
    for section in ('bass','treble'):
        p=bcfg['material'];s=bcfg['section'][section];f=bcfg['fixture']
        q=build(centers[section]['xyz'],bridgeSub,p['densityKgM3'],p['youngAlongPa'],s['widthM'],s['heightM'],0.)
        beams.append(q);m.append(q['M']);k.append(q['K']);d.append(f['massDampingPerS']*q['M']+f['stiffnessDampingS']*q['K'])
    M=block_diag(a['M'],*m);K=block_diag(a['K'],*k);D=block_diag(a['D'],*d)
    J0=block_diag(a['J'],*[np.zeros_like(q) for q in m])
    J=np.zeros_like(M);P=np.zeros((len(M),6));maps=[];start=np_+nr
    for j,(section,q) in enumerate(zip(('bass','treble'),beams)):
        xyz=centers[section]['xyz'];nb=len(q['M'])
        for e,L in enumerate(np.diff(q['mesh'])):
            idx=e//bridgeSub;v=(e%bridgeSub)/bridgeSub;w=v+1/bridgeSub
            A=(1-v)*xyz[idx,:2]+v*xyz[idx+1,:2];B=(1-w)*xyz[idx,:2]+w*xyz[idx+1,:2]
            delta=B-A
            # Split bridge integration at every spline knot to avoid aliasing.
            for xy,weights in b.line(A,B,order):
                t=(xy-A)@delta/(delta@delta)
                H=np.stack([1-3*t*t+2*t**3,L*(t-2*t*t+t**3),3*t*t-2*t**3,L*(-t*t+t**3)],axis=1)
                R=np.zeros((len(weights),len(M)));R[:,:np_]=-(b.evaluate(xy)[0]@T);R[:,start+2*e:start+2*e+4]=H
                # XY and arclength equal here, but preserve the arclength metric.
                weights=weights*L/np.linalg.norm(delta)
                if connected:J+=R.T@((icfg['joint']['stiffnessNperM2']*weights)[:,None]*R)
                maps.append((R,weights))
        idx=len(xyz)//2;ids=start+q['attachmentDofs'][idx]
        P[ids,2*j]=1.;P[ids+1,2*j+1]=1.
        P[:np_,4+j]=(b.evaluate(xyz[idx,:2])[0]@T)[0]
        start+=nb
    J=(J+J.T)/2
    return dict(M=M,K=K,D=D,Jrim=J0,Jbridge=J,P=P,maps=maps,plateDofs=np_,rimDofs=nr,bridgeDofs=[len(q['M']) for q in beams],
                rimMassKg=a['rimMassKg'],bridgeMassKg=[q['massKg'] for q in beams])
def mobility(a,frequencies):
    M=a['M'];K=a['K']+a['Jrim']+a['Jbridge'];D=a['D'];P=a['P']
    # Congruence conditioning, preserves physical work at the ports.
    s=1/np.sqrt(np.diag(M));W=s[:,None]*s[None,:]
    M=M*W;K=K*W;D=D*W;P=P*s[:,None]
    unit=np.array([1.,.02,1.,.02,1.,1.]);Y=[];rec=0.;pas=0.
    for f in frequencies:
        w=2*np.pi*f
        Z=1j*w*(P.T@solve(K-w*w*M+1j*w*D,P))
        rec=max(rec,float(np.linalg.norm(Z-Z.T)/max(np.linalg.norm(Z),1e-30)))
        H=Z*unit[:,None]*unit[None,:];H=(H+H.conj().T)/2
        pas=min(pas,float(min(np.linalg.eigvalsh(H))/max(np.linalg.norm(H),1e-30)))
        Y.append(Z)
    assert rec<=1e-8 and pas>=-1e-8
    return np.array(Y),rec,pas
