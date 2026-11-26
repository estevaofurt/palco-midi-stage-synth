"""G3.11f: energy-balanced midpoint realization of a positive-real
board load. Diagnostic only; a passive fit can still be physically wrong."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from passive_board_fit import CENTERS,GAMMA_HZ,audit,evaluate
from acoustic_matrix_archive import read_npz
from dual_cavity_spatial_diagnostic import FREQ
from split_radiation import relative

def factor_psd(A):
    A=np.asarray(A)
    if np.iscomplexobj(A) or A.ndim!=2 or A.shape[0]!=A.shape[1] or not np.isfinite(A).all() or relative(A,A.T)>1e-10:raise ValueError('invalid real symmetric coefficient')
    d,U=np.linalg.eigh((A+A.T)/2)
    if d.min()<-1e-10*max(np.linalg.norm(A),1e-30):raise ValueError('nonpassive coefficient')
    return U*np.sqrt(np.maximum(d,0))[None,:]

class MidpointLoad:
    def __init__(self,C,centers,gamma_hz,sample_rate):
        C=np.asarray(C);centers=np.asarray(centers,float)
        if C.ndim!=3 or C.shape[0]!=len(centers)+3 or C.shape[1]!=C.shape[2] or not len(centers) or not np.isfinite(centers).all() or np.any(centers<=0) or not np.isfinite([gamma_hz,sample_rate]).all() or gamma_hz<=0 or sample_rate<=0:raise ValueError('invalid dynamic load')
        B=[factor_psd(A) for A in C]
        self.R,self.M,self.K=[v@v.T for v in B[:3]]
        self.B=np.asarray(B[3:]);self.om2=(2*np.pi*centers[:,None])**2
        self.gamma=2*np.pi*gamma_hz;self.h=1/sample_rate;self.n=C.shape[1]
        self.den=1+self.h*self.gamma+.25*self.h**2*self.om2
        self.x=np.zeros((len(centers),self.n));self.v=self.x.copy()
        self.u=np.zeros(self.n);self.q=self.u.copy()
    def storage(self):
        return .5*float(self.u@self.M@self.u+self.q@self.K@self.q+np.sum(self.v**2+self.om2*self.x**2))
    def step(self,u):
        u=np.asarray(u)
        if u.shape!=(self.n,) or np.iscomplexobj(u) or not np.isfinite(u).all():raise ValueError('invalid velocity')
        h=self.h;mid=(u+self.u)*.5
        drive=np.einsum('jik,i->jk',self.B,mid)
        vm=(self.v+.5*h*(drive-self.om2*self.x))/self.den
        qm=self.q+.5*h*mid
        force=self.R@mid+self.M@(u-self.u)/h+self.K@qm+np.einsum('jik,jk->i',self.B,vm)
        loss=h*float(mid@self.R@mid+2*self.gamma*np.sum(vm**2))
        work=h*float(mid@force)
        self.x+=h*vm;self.v=2*vm-self.v;self.q+=h*mid;self.u=u.copy()
        return force,work,loss

def energy_probe(C,centers,gamma_hz,rate):
    a=MidpointLoad(C,centers,gamma_hz,rate);W=L=absolute=peak=err=0.;minloss=0.;maxforce=0.
    for i in range(round(.25*rate)):
        t=(i+1)/rate
        u=np.sin(np.arange(1,a.n+1)*2*np.pi*73*t)*np.sin(np.pi*t/.05)**2 if t<.05 else np.zeros(a.n)
        force,w,l=a.step(u);W+=w;L+=l;absolute+=abs(w)
        E=a.storage();peak=max(peak,E);maxforce=max(maxforce,float(np.linalg.norm(force)))
        minloss=min(minloss,l);err=max(err,abs(W-L-E))
        if not np.isfinite([W,L,E,maxforce]).all():raise ValueError('nonfinite temporal response')
    scale=max(absolute,peak,1e-30)
    result=dict(sampleRate=rate,samples=round(.25*rate),energyBalanceRelative=err/scale,minimumLoss=minloss,
        peakStoredEnergy=peak,finalStoredEnergy=a.storage(),totalLoss=L,peakForce=maxforce)
    result['gate']=bool(err/scale<=1e-9 and minloss>=-1e-12*scale and L>=0)
    return result

def harmonic_probe(C,centers,gamma_hz,rate,f):
    # Midpoint velocity and force share the same time origin; compare to
    # bilinear-warped analytic impedance, not an unwarped continuous sample.
    a=MidpointLoad(C,centers,gamma_hz,rate);h=a.h
    direction=np.arange(1,a.n+1,dtype=float);direction/=np.linalg.norm(direction)
    settle=max(1.,12/(2*np.pi*gamma_hz));duration=max(.2,8/f)
    end=round((settle+duration)*rate);start=round(settle*rate)
    # Estimate sine/cosine and DC offset (spring displacement may retain DC).
    G=np.zeros((3,3));rhs=np.zeros((3,a.n));input_rhs=np.zeros((3,a.n))
    for i in range(end):
        t=(i+1)*h;u=np.sin(2*np.pi*f*t)*direction;mid=(a.u+u)/2
        force,_,_=a.step(u)
        if i>=start:
            th=2*np.pi*f*(t-.5*h);b=np.array([np.sin(th),np.cos(th),1.])
            G+=np.outer(b,b);rhs+=b[:,None]*force;input_rhs+=b[:,None]*mid
    y=np.linalg.solve(G,rhs);v=np.linalg.solve(G,input_rhs)
    measured=y[0]+1j*y[1];exc=v[0]+1j*v[1]
    s=2j/h*np.tan(np.pi*f*h)
    expected=evaluate([s],C,centers,gamma_hz)[0]@exc
    error=relative(measured,expected)
    return dict(sampleRate=rate,frequencyHz=f,discreteTransferRelative=error,gate=bool(error<=1e-5))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','fit','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--angle',type=float,choices=[30.,55.],required=True);a=p.parse_args()
    sha=hashlib.sha256(a.scale.read_bytes()).hexdigest()
    d=json.loads((a.fit/'passive_board_fit.json').read_text());s=d['summary']
    expected=dict(gate=True,angleDeg=a.angle,diagnosticOnly=True,boardFields=4,oscillatorAtoms=len(CENTERS),gammaHz=GAMMA_HZ,passiveStructureGate=True,timeDomainReady=False,radiationReady=False)
    if d.get('scaleSha256')!=sha or d.get('frequenciesHz')!=FREQ or any(s.get(k)!=v for k,v in expected.items()):raise ValueError('invalid passive stress-test source')
    b=read_npz(a.fit,d['archive'],dict(coefficients=(len(CENTERS)+3,4,4),centersHz=(len(CENTERS),)),FREQ)
    C=b['coefficients'];centers=b['centersHz']
    if not np.array_equal(centers,CENTERS) or not audit(C,centers,GAMMA_HZ)['gate']:raise ValueError('invalid passive structure')
    rows=[energy_probe(C,centers,GAMMA_HZ,r) for r in (44100,48000,96000)]
    harmonic=[harmonic_probe(C,centers,GAMMA_HZ,48000,f) for f in (55.,175.,275.)]
    gate=all(v['gate'] for v in rows+harmonic)
    summary=dict(gate=gate,angleDeg=a.angle,diagnosticOnly=True,sourceFitGate=s['fitGate'],physicalFitAccepted=False,
        energyBalanceGate=all(v['gate'] for v in rows),discreteTransferGate=all(v['gate'] for v in harmonic),
        timeDomainReady=False,radiationReady=False,maximumEnergyError=max(v['energyBalanceRelative'] for v in rows),
        maximumDiscreteTransferError=max(v['discreteTransferRelative'] for v in harmonic))
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'passive_midpoint.json').write_text(json.dumps(dict(summary=summary,energy=rows,harmonic=harmonic,scaleSha256=sha,
        sourceManifestSha256=hashlib.sha256((a.fit/'passive_board_fit.json').read_bytes()).hexdigest()),indent=2,allow_nan=False))
    print('G3_MIDPOINT_GATE '+json.dumps(summary),flush=True)
    if not gate:raise ValueError('temporal structure failed')
if __name__=='__main__':main()
