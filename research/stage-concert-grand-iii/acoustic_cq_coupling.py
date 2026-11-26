"""G3.14d.1: isolated BDF2 mechanical/CQ coupling.
Compare an impedance convolution against independently integrated passive
states. No piano surface, hammer contact, or real-time feedback acceptance.
"""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from acoustic_cq_pilot import coefficients
from split_radiation import relative

def hist(x,y,h):
    return (-2*x+.5*y)/h

def g_energy(x,y,M):
    t=2*x-y
    return .25*float(x@M@x+t@M@t)

def numerical_loss(x,y,z,M):
    d=x-2*y+z
    return .25*float(d@M@d)

def fixture():
    M=np.diag([.08,.12]);K=np.array([[1.8e5,-2.e4],[-2.e4,2.5e5]])
    D=np.diag([.7,1.]);A=np.array([[.012,.003],[.003,.008]])
    R=np.array([[2.,.4],[.4,1.5]])
    return M,K,D,A,R,2*np.pi*800.

def simulate(rate,n,steps=1536):
    M,K,D,A,R,a=fixture();h=1/rate;d=1.5/h
    def impedance(s):return A*s+R*s/(s+a)
    W,imag=coefficients(impedance,rate,n,np.exp(-8/n))
    Fc=cho_factor(d*M+D+K/d+W[0])
    Fr=cho_factor(d*(M+A)+D+K/d+R*d/(d+a))
    # Histories newest first; start at rest and preserve the zero prehistory.
    q=np.zeros((2,2));v=q.copy();qr=q.copy();vr=q.copy();x=q.copy()
    velocities=np.zeros((steps,2));reference=velocities.copy()
    forces=velocities.copy();expected=velocities.copy()
    work=loss=peak=balance=0.;airwork=0.;airmin=0.
    cqwork=cqloss=cqbalance=0.;cqpeak=0.
    for i in range(steps):
        t=i*h
        F=np.array([np.sin(2*np.pi*261.63*t),.3*np.sin(2*np.pi*150*t)])*(i<steps//4)
        past=min(i,n-1)
        memory=np.einsum('kij,kj->i',W[1:past+1],velocities[i-past:i][::-1])
        hq=hist(*q,h);hv=hist(*v,h)
        vc=cho_solve(Fc,F-M@hv+K@hq/d-memory)
        qc=(vc-hq)/d;fc=W[0]@vc+memory
        velocities[i]=vc;forces[i]=fc
        # Independent state realization: M+A and one relaxation state x.
        hqr=hist(*qr,h);hvr=hist(*vr,h);hx=hist(*x,h)
        vv=cho_solve(Fr,F-(M+A)@hvr+K@hqr/d-R@(a*hx/(d+a)))
        qq=(vv-hqr)/d;xx=(vv-hx)/(d+a);xd=d*xx+hx
        fr=A@(d*vv+hvr)+R@xd
        reference[i]=vv;expected[i]=fr
        E=g_energy(vv,vr[0],M+A)+g_energy(qq,qr[0],K)+g_energy(xx,x[0],a*R)
        loss+=h*float(vv@D@vv+xd@R@xd)+numerical_loss(vv,*vr,M+A)+numerical_loss(qq,*qr,K)+numerical_loss(xx,*x,a*R)
        work+=h*float(F@vv);peak=max(peak,E,abs(work),loss,1e-30)
        balance=max(balance,abs(E+loss-work)/peak)
        # Separate CQ ledger with acoustic work as a port term; do not
        # double count the reference's inertance or relaxation energy.
        Ec=g_energy(vc,v[0],M)+g_energy(qc,q[0],K)
        cqloss+=h*float(vc@D@vc)+numerical_loss(vc,*v,M)+numerical_loss(qc,*q,K)
        cqwork+=h*float(F@vc);airwork+=h*float(fc@vc);airmin=min(airmin,airwork)
        cqpeak=max(cqpeak,Ec,abs(cqwork),cqloss,abs(airwork),1e-30)
        cqbalance=max(cqbalance,abs(Ec+cqloss+airwork-cqwork)/cqpeak)
        q=np.stack([qc,q[0]]);v=np.stack([vc,v[0]])
        qr=np.stack([qq,qr[0]]);vr=np.stack([vv,vr[0]]);x=np.stack([xx,x[0]])
    state=relative(velocities,reference);force=relative(forces,expected)
    minimumAir=airmin/max(cqpeak,1e-30)
    gate=bool(max(state,force,imag,balance,cqbalance)<=1e-8 and minimumAir>=-1e-8)
    return dict(rate=rate,contourSamples=n,steps=steps,velocityRelative=state,forceRelative=force,
        coefficientImaginaryRelative=imag,referenceEnergyRelative=balance,cqPortEnergyRelative=cqbalance,
        minimumAcousticWorkRelative=minimumAir,acousticWorkJ=airwork,screeningGate=gate)

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[]
    for rate in (48000,96000):
        for n in (512,1024):
            row=simulate(rate,n);rows.append(row)
            print('G3_CQ_COUPLING_CASE '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=True,diagnosticOnly=True,syntheticMechanicalFixture=True,configurations=len(rows),
        screeningPassed=sum(r['screeningGate'] for r in rows),pianoSurfaceValidated=False,
        physicalFeedbackAccepted=False,polyphonyValidated=False,audibleSustainMeasured=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'acoustic_cq_coupling.json').write_text(json.dumps(dict(summary=summary,cases=rows),indent=2,allow_nan=False))
    print('G3_CQ_COUPLING_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
