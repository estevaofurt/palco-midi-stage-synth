"""G3.02a passive internal-variable felt law. Constitutive tests only, no piano render."""
import math,json,argparse
from pathlib import Path
from dataclasses import dataclass
from physical_inventory import hammer
ROOT=Path(__file__).parent
@dataclass(frozen=True)
class Felt:
    ke:float
    km:float
    kr:float
    eta:float
    p:float
    def __post_init__(self):
        if not all(math.isfinite(x) and x>0 for x in (self.ke,self.kr,self.eta)) or not math.isfinite(self.km) or self.km<0 or not math.isfinite(self.p) or self.p<1:raise ValueError('felt domain')
def potential(d,k,p):return k*max(0.,d)**(p+1)/(p+1)
def secant(a,b,k,p):
    if a==b:return k*max(0.,a)**p
    lo,hi=sorted((a,b))
    if hi<=0 or k==0:return 0.
    # Stable difference of powers for adjacent positive endpoints.
    diff=hi**(p+1) if lo<=0 else -hi**(p+1)*math.expm1((p+1)*math.log1p((lo-hi)/hi)) if lo/hi>.5 else hi**(p+1)-lo**(p+1)
    return k*diff/((p+1)*(hi-lo))
def energy(d,z,f):return potential(d,f.ke,f.p)+potential(d-z,f.km,f.p)+.5*f.kr*z*z
def force(d,z,f):return f.ke*max(d,0.)**f.p+f.km*max(d-z,0.)**f.p
def frozen_force(a,b,z,f):return secant(a,b,f.ke,f.p)+secant(a-z,b-z,f.km,f.p)
def relax(d,z,h,f):
    if not all(math.isfinite(x) for x in (d,z,h)) or z<0 or h<=0 or h*f.kr>2*f.eta:raise ValueError('relax domain')
    def residual(q):return f.eta*(q-z)/h-secant(d-z,d-q,f.km,f.p)+f.kr*(q+z)/2
    lo=0.;hi=max(z,d,0.)
    # At q=0 residual <=0 under timestep bound; at q=max(z,d,0), >=0.
    if hi==0:return 0.,0.,0.
    for _ in range(64):
        m=(lo+hi)/2
        if residual(m)>0:hi=m
        else:lo=m
    q=(lo+hi)/2;loss=f.eta*(q-z)**2/h
    return q,loss,energy(d,z,f)-energy(d,q,f)-loss
def step(d0,d1,z,h,f):
    # Strang split: relaxation, conservative work at frozen z, relaxation.
    a,l0,r0=relax(d0,z,h/2,f)
    F=frozen_force(d0,d1,a,f);work=F*(d1-d0)
    b,l1,r1=relax(d1,a,h/2,f)
    return dict(z=b,forceN=F,workJ=work,lossJ=l0+l1,residualJ=energy(d1,b,f)-energy(d0,z,f)-work+l0+l1,relaxResidualJ=max(abs(r0),abs(r1)))
def params(k,count,s,c):
    h=hammer(k,s['hammer']);K=h['K_N_per_m_pow_p'];p=h['power'];d=c['compressionReferenceM'];kr=c['recoveryStiffnessFactor']*K*d**(p-1)
    if count not in (1,2,3) or not math.isclose(c['equilibriumFraction']+c['memoryFraction'],1.,abs_tol=1e-12):raise ValueError('split')
    return h,Felt(K*c['equilibriumFraction']/count,K*c['memoryFraction']/count,kr/count,kr*c['freeRecoveryTimeS']/count,p)
def screen(scale,s,c):
    rows=[]
    for r in scale['rows']:
        h,f=params(r['key'],r['count'],s,c);d=c['compressionReferenceM']
        assert abs(r['count']*force(d,0.,f)/h['forceAt1mmN']-1)<1e-12
        # Prescribed loading/unloading and recovery; no moving hammer/string yet.
        z=0.;last=0.;work=loss=err=0.;peak=0.;hold=[]
        for i in range(1,801):
            x=d*min(i/200,1.,max(0.,(600-i)/200))
            out=step(last,x,z,1e-5,f);z=out['z'];last=x
            work+=out['workJ'];loss+=out['lossJ'];err=max(err,abs(out['residualJ']),out['relaxResidualJ']);peak=max(peak,out['forceN'])
            assert z>=0 and out['forceN']>=0 and out['lossJ']>=0
            if i in (200,400,600,800):hold.append(dict(step=i,memoryM=z,forceN=force(x,z,f)))
        balance=abs(work-loss-energy(last,z,f))
        assert loss>0 and balance<1e-10 and err<1e-11 and hold[1]['forceN']<hold[0]['forceN'] and hold[3]['memoryM']<hold[2]['memoryM']
        rows.append(dict(key=r['key'],count=r['count'],hammerMassKg=h['massKg'],power=f.p,elasticTotalK=h['K_N_per_m_pow_p'],feltPerContact=f.__dict__,peakPrescribedForceN=peak,lossJ=loss,balanceJ=balance,maxResidualJ=err,memorySnapshots=hold))
    return dict(summary=dict(keys=len(rows),maxBalanceJ=max(x['balanceJ'] for x in rows),maxStepResidualJ=max(x['maxResidualJ'] for x in rows),gate=True,impactReady=False),rows=rows,scope='prescribed compression material law only; no hammer rebound, string dynamics, MIDI calibration or audio')
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'felt_hypothesis.json').read_text());scale=json.loads(a.scale.read_text())
    assert scale['version']=='G3-scale-hypothesis-02' and scale['summary']['gate']
    result=screen(scale,s,c);a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'felt.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    print('G3_FELT_LAW_GATE '+json.dumps(result['summary']),flush=True)
if __name__=='__main__':main()
