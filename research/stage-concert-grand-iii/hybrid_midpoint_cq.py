"""G3.14d.6: mechanical midpoint with BDF2 CQ on acoustic port only.
Independent synthetic passive state realization; no physical piano feedback."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from acoustic_cq_pilot import coefficients
from acoustic_cq_coupling import fixture,hist,g_energy,numerical_loss
from split_radiation import relative

def simulate(rate,n,steps=4096):
    M,K,D,A,R,a=fixture();h=1/rate;d=2/h;b=1.5/h
    W,imag=coefficients(lambda s:A*s+R*s/(s+a),rate,n,np.exp(-8/n))
    Fc=cho_factor(d*M+D+K/d+W[0])
    Fr=cho_factor(d*M+D+K/d+b*A+R*b/(b+a))
    q=np.zeros(2);v=q.copy();qr=q.copy();vr=q.copy()
    uold=np.zeros((2,2));x=uold.copy()
    mid=np.zeros((steps,2));ref=mid.copy();fc=mid.copy();fr=mid.copy()
    work=loss=air=peak=balance=0.
    rw=rl=rp=rb=minimum=0.;acousticDissipation=0.;numerical=0.
    for i in range(steps):
        t=(i+.5)*h
        F=np.array([np.sin(2*np.pi*261.63*t),.3*np.sin(2*np.pi*150*t)])*(i<steps//4)
        k=min(i,n-1);memory=np.einsum('kij,kj->i',W[1:k+1],mid[i-k:i][::-1])
        u=cho_solve(Fc,F+d*M@v-K@q-memory);mid[i]=u
        f=W[0]@u+memory;fc[i]=f
        q+=h*u;v=2*u-v
        work+=h*float(F@u);loss+=h*float(u@D@u);air+=h*float(u@f);minimum=min(minimum,air)
        E=.5*float(v@M@v+q@K@q);peak=max(peak,E,abs(work),loss,abs(air),1e-30)
        balance=max(balance,abs(E+loss+air-work)/peak)
        # Independent realization: BDF2 only at the midpoint acoustic port.
        hu=hist(*uold,h);hx=hist(*x,h)
        ur=cho_solve(Fr,F+d*M@vr-K@qr-A@hu-R@(a*hx/(b+a)))
        xx=(ur-hx)/(b+a);xd=b*xx+hx
        ref[i]=ur;fr[i]=A@(b*ur+hu)+R@xd
        qr+=h*ur;vr=2*ur-vr
        stored=g_energy(ur,uold[0],A)+g_energy(xx,x[0],a*R)
        numerical+=numerical_loss(ur,*uold,A)+numerical_loss(xx,*x,a*R)
        acousticDissipation+=h*float(xd@R@xd)
        rw+=h*float(F@ur);rl+=h*float(ur@D@ur)
        E=.5*float(vr@M@vr+qr@K@qr)+stored
        rp=max(rp,E,abs(rw),rl+numerical+acousticDissipation,1e-30)
        rb=max(rb,abs(E+rl+numerical+acousticDissipation-rw)/rp)
        uold=np.stack([ur,uold[0]]);x=np.stack([xx,x[0]])
    e=relative(mid,ref);f=relative(fc,fr);mw=minimum/max(peak,1e-30)
    # Compare the independently accounted acoustic energy to CQ port work.
    port=abs(stored+numerical+acousticDissipation-air)/max(peak,1e-30)
    return dict(rate=rate,contourSamples=n,steps=steps,velocityRelative=e,forceRelative=f,
        coefficientImaginaryRelative=imag,midpointEnergyRelative=balance,referenceEnergyRelative=rb,
        acousticPortRelative=port,minimumAcousticWorkRelative=mw,
        acousticPhysicalDissipationJ=acousticDissipation,acousticNumericalDissipationJ=numerical,
        mechanicalNumericalDissipationIncluded=False,
        screeningGate=bool(max(e,f,imag,balance,rb,port)<=1e-8 and mw>=-1e-8))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[simulate(r,n) for r in (48000,96000) for n in (512,1024)]
    for row in rows:print('G3_HYBRID_CQ_CASE '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=True,screeningPassed=sum(r['screeningGate'] for r in rows),configurations=len(rows),
        diagnosticOnly=True,syntheticFixture=True,mechanicalMidpoint=True,acousticBDF2Only=True,
        physicalSurfaceValidated=False,feedbackIntegrated=False,audibleSustainMeasured=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'hybrid_midpoint_cq.json').write_text(json.dumps(dict(summary=summary,cases=rows),indent=2,allow_nan=False))
    print('G3_HYBRID_CQ_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
