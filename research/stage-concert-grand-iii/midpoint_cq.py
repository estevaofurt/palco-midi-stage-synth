"""G3.14d.4: trapezoidal CQ at the mechanical midpoint.
Synthetic passive rational load; exact inertance split to avoid Nyquist pole.
No physical-surface passivity claim or audio."""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from acoustic_cq_coupling import fixture
from split_radiation import relative

def symbol(z,rate):
    z=np.asarray(z,complex)
    if rate<=0 or not np.isfinite(z).all() or np.any(abs(z)>=1):raise ValueError('open unit disk')
    return 2*rate*(1-z)/(1+z)

def weights(R,a,rate,n):
    if n<16 or n%2 or a<=0:raise ValueError('contour')
    radius=np.exp(-8/n);z=radius*np.exp(-2j*np.pi*np.arange(n)/n)
    s=symbol(z,rate)
    W=np.fft.ifft((s/(s+a))[:,None,None]*R,axis=0)/radius**np.arange(n)[:,None,None]
    err=float(np.linalg.norm(W.imag)/max(np.linalg.norm(W.real),1e-30))
    if err>1e-8:raise ValueError('complex weights')
    return W.real

def simulate(rate,n,steps=4096):
    M,K,D,A,R,a=fixture();M=M+A;h=1/rate;d=2/h
    W=weights(R,a,rate,n)
    # midpoint equations; CQ takes midpoint velocity and returns midpoint force
    Fc=cho_factor(d*M+D+K/d+W[0])
    Fr=cho_factor(d*M+D+K/d+R*d/(d+a))
    q=np.zeros(2);v=q.copy();qr=q.copy();vr=q.copy();x=q.copy()
    mid=np.zeros((steps,2));ref=mid.copy();fc=mid.copy();fr=mid.copy()
    work=loss=air=peak=err=0.;rw=rl=rp=re=0.;minimum=0.
    for i in range(steps):
        t=(i+.5)*h
        F=np.array([np.sin(2*np.pi*261.63*t),.3*np.sin(2*np.pi*150*t)])*(i<steps//4)
        k=min(i,n-1);mem=np.einsum('kij,kj->i',W[1:k+1],mid[i-k:i][::-1])
        u=cho_solve(Fc,F+d*M@v-K@q-mem);mid[i]=u
        f=W[0]@u+mem;fc[i]=f
        q+=h*u;v=2*u-v
        work+=h*float(F@u);loss+=h*float(u@D@u);air+=h*float(u@f);minimum=min(minimum,air)
        E=.5*float(v@M@v+q@K@q);peak=max(peak,E,abs(work),loss,abs(air),1e-30)
        err=max(err,abs(E+loss+air-work)/peak)
        # Independent state: xdot=u-a*xmid; relaxation force R*xdot.
        ur=cho_solve(Fr,F+d*M@vr-K@qr+R@(a*d*x/(d+a)))
        xm=(ur+d*x)/(d+a);xd=ur-a*xm
        ref[i]=ur;fr[i]=R@xd
        qr+=h*ur;vr=2*ur-vr;x=2*xm-x
        rw+=h*float(F@ur);rl+=h*float(ur@D@ur+xd@R@xd)
        E=.5*float(vr@M@vr+qr@K@qr+a*x@R@x);rp=max(rp,E,abs(rw),rl,1e-30)
        re=max(re,abs(E+rl-rw)/rp)
    e=relative(mid,ref);f=relative(fc,fr);mw=minimum/max(peak,1e-30)
    return dict(rate=rate,contourSamples=n,steps=steps,velocityRelative=e,forceRelative=f,
        midpointEnergyRelative=err,referenceEnergyRelative=re,minimumAcousticWorkRelative=mw,
        screeningGate=bool(max(e,f,err,re)<=1e-8 and mw>=-1e-8))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    rows=[simulate(r,n) for r in (48000,96000) for n in (512,1024)]
    for row in rows:print('G3_TRAPEZOID_CQ_CASE '+json.dumps(row,allow_nan=False),flush=True)
    summary=dict(gate=True,screeningPassed=sum(r['screeningGate'] for r in rows),configurations=len(rows),
        diagnosticOnly=True,syntheticFixture=True,exactInertanceSplit=True,physicalSurfaceValidated=False,
        feedbackIntegrated=False,audibleSustainMeasured=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'midpoint_cq.json').write_text(json.dumps(dict(summary=summary,cases=rows),indent=2,allow_nan=False))
    print('G3_TRAPEZOID_CQ_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
