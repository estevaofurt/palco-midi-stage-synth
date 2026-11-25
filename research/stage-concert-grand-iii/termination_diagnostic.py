"""G3.03a moving boundary pulse and reciprocity proof; diagnostic load only."""
import argparse,json,hashlib,math
from pathlib import Path
import numpy as np
from moving_termination import basis,Boundary
ROOT=Path(__file__).parent
LOAD={'massKg':.005,'stiffnessNm':1e6,'dampingNsm':5.,'status':'arbitrary passive diagnostic fixture; not measured or selected piano bridge'}
def pulse(t,h):
    def integral(x):
        u=min(max(x,0.),.001)
        return .1*(u/2-.001*math.sin(2*math.pi*u/.001)/(4*math.pi))
    return (integral(t+h)-integral(t))/h
def simulate(w,P,sr,drag,drive):
    t=Boundary(w,P,sr,drag);h=1/sr;work=err=inc=forceerr=0.;peak=0.;trace=[]
    contactLoss=None
    for i in range(round(.02*sr)):
        old=t.energy();F=np.zeros(2);F[drive]=pulse(i*h,h)
        z=t.step(F);work+=z['work'];E=t.energy();err=max(err,abs(E+t.loss-work));forceerr=max(forceerr,z['damperResidualN'])
        if i>=round(.001*sr):inc=max(inc,E-old)
        if i+1==round(.001*sr):contactLoss=t.loss
        peak=max(peak,abs(float(t.position()[1])))
        if (i+1)%(sr//4000)==0:trace.append(np.r_[t.position(),t.loss].tolist())
    assert err<=max(1e-12,abs(work)*1e-7) and inc<=1e-12 and forceerr<=1e-10
    assert peak>0 and (t.loss>0 if drag>0 else t.loss==0)
    return dict(sr=sr,drive=drive,drag=drag,modes=len(w),workJ=work,energyJ=t.energy(),lossJ=t.loss,lossAtPulseEndJ=contactLoss,
        maxBalanceJ=err,maxIncreaseJ=inc,maxForceResidualN=forceerr,peakBoundaryM=peak,trace=trace)
def compare(a,b):
    x,y=np.array(a['trace']),np.array(b['trace'])
    diff={name:float(np.linalg.norm(x[:,i]-y[:,i])/max(np.linalg.norm(y[:,i]),1e-30)) for i,name in enumerate(('hammer','rear','lossTrace'))}
    for k in ('workJ','lossJ','peakBoundaryM'):diff[k]=abs(a[k]-b[k])/max(abs(b[k]),1e-30)
    return dict(errors=diff,gate=max(diff.values())<=.05)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--key',type=int,required=True);a=p.parse_args()
    raw=a.scale.read_bytes();scale=json.loads(raw);assert scale['version']=='G3-scale-hypothesis-02' and scale['summary']['gate'] and a.key in (21,49,60,84,108)
    r=scale['rows'][a.key-21];m=LOAD['massKg'];k=LOAD['stiffnessNm'];c=LOAD['dampingNsm']
    # Check base independently at 24k for all keys; higher band is diagnostic.
    w0,P0=basis(r,512,24000,m,k);w1,P1=basis(r,768,24000,m,k)
    same=len(w0)==len(w1)
    freq=float(np.max(abs(1200*np.log2(np.sqrt(w0/w1))))) if same else None
    # Compare static port receptance retained in each basis.
    A=(P0.T/w0)@P0;B=(P1.T/w1)@P1
    static=float(np.linalg.norm(A-B)/max(np.linalg.norm(B),1e-30))
    bgate=same and freq<=.1 and static<=.01
    w,P=basis(r,768,48000,m,k)
    mask=np.sqrt(w)/(2*np.pi)<=24000
    rows=[simulate(w[mask],P[mask],192000,c,0),simulate(w,P,192000,c,0),simulate(w,P,384000,c,0),
          simulate(w,P,384000,c,1),simulate(w,P,384000,0.,0)]
    # Reciprocal displacement response to identical force pulses (swap input/output).
    reciprocal=float(np.linalg.norm(np.array(rows[2]['trace'])[:,1]-np.array(rows[3]['trace'])[:,0])/max(np.linalg.norm(np.array(rows[2]['trace'])[:,1]),1e-30))
    assert reciprocal<=1e-7
    time=compare(rows[1],rows[2]);band=compare(rows[0],rows[1])
    summary=dict(key=a.key,simulations=len(rows),basisGate=bgate,basisFrequencyErrorCents=freq,basisStaticError=static,reciprocityError=reciprocal,
        time=time,band=band,maxBalanceJ=max(z['maxBalanceJ'] for z in rows),gate=bgate and time['gate'] and band['gate'],terminationReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'termination.json').write_text(json.dumps(dict(summary=summary,load=LOAD,rows=rows,scaleSha256=hashlib.sha256(raw).hexdigest(),
        scope='vertical linear string, fixed front, mobile rear diagnostic load, no hammer or acoustic output'),indent=2,allow_nan=False))
    print('G3_TERMINATION_GATE '+json.dumps(summary),flush=True)
    print('G3_TERMINATION_ENERGY '+json.dumps(dict(key=a.key,workJ=rows[2]['workJ'],lossAtPulseEndJ=rows[2]['lossAtPulseEndJ'],loss20msJ=rows[2]['lossJ'],peakRearM=rows[2]['peakBoundaryM'])),flush=True)
    assert summary['gate'],'moving-boundary basis/time/band convergence'
if __name__=='__main__':main()
