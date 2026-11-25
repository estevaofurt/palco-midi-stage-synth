"""G2.10c: time-resolved diagnostic only, original mechanical control."""
import json
from pathlib import Path
import numpy as np
from g2_shared_hammer import run,KEYS
from g2_acoustic_integrated import make_kernels,render,freqs,SR
from scipy.signal import periodogram
OUT=Path('/tmp/g2-shared-board')
TIMES=[.002,.004,.008,.02,.04,.08,.16]
CASES=[(0,6,1.),(1,6,1.)]+[(2,m,s) for m in (6,3) for s in (.5,1.,2.)]
def db(v):return float(20*np.log10(v)) if v>0 else None
def measure(p,f0,lo,hi):
    z=p[:,round(lo*SR):round(hi*SR)]
    f,P=periodogram(z,fs=SR,axis=1,window='hann',detrend=False)
    P=P.mean(axis=0);df=f[1]-f[0]
    total=float(P.sum()*df)
    def band(a,b):return float(P[(f>=a)&(f<b)].sum()*df)
    return dict(fundamentalFraction=band(.965*f0,1.08*f0)/max(total,1e-300),
        belowFraction=band(80,.7*f0)/max(total,1e-300),
        rmsPa=np.sqrt(np.mean(z*z,axis=1)).tolist())
class Ledger:
    def __init__(self,j,speed,mass):
        self.j=j;self.f0=440*2**((KEYS[j]-69)/12)
        self.initial=.5*mass*speed**2
        self.n=round(.16*SR);self.force=np.zeros(self.n);self.bridge=np.zeros((3,self.n))
        self.contactWork=np.zeros(3);self.bridgeWork=np.zeros(3);self.boardWork=np.zeros(3)
        self.boardPos=np.zeros(3);self.rows=[]
        self.at={round(t*SR)-1 for t in TIMES}
    def __call__(self,i,g,b,v,masses,f,jf,owners,local,pos,r0,felt,jl):
        # Read-only observation: conjugate force times exact step displacement.
        new=[a.P.T@a.q for a in g];bp=b.P.T@b.q
        self.force[i]=sum(f);self.bridge[:,i]=jf
        for k,(j,l) in enumerate(zip(owners,local)):
            self.contactWork[j]+=f[k]*(new[j][l+1]-pos[j][l+1])
        self.bridgeWork+=jf*np.array([new[j][0]-pos[j][0] for j in range(3)])
        self.boardWork-=jf*(bp-self.boardPos);self.boardPos=bp
        if i in self.at:
            a=g[self.j];freq=np.sqrt(a.w2)/(2*np.pi)
            em=.5*(a.v*a.v+a.w2*a.q*a.q)
            f0=self.f0
            row=dict(t=(i+1)/SR,hammerKineticFraction=float(.5*np.sum(masses*v*v)/self.initial),
                feltLossFraction=float(felt/self.initial),contactWorkFraction=(self.contactWork/self.initial).tolist(),
                bridgeWorkFraction=(self.bridgeWork/self.initial).tolist(),
                boardWorkFraction=(self.boardWork/self.initial).tolist(),
                boardEnergyFraction=float(b.energy()/self.initial),boardLossFraction=float(b.loss/self.initial),
                jointLossFraction=float(jl/self.initial),groupEnergyFraction=[float(z.energy()/self.initial) for z in g],
                groupLossFraction=[float(z.loss/self.initial) for z in g],
                activeGroupModalEnergyFraction={label:float(em[mask].sum()/self.initial) for label,mask in (
                    ('below',freq<.7*f0),('fundamental',(freq>=.965*f0)&(freq<1.08*f0)),
                    ('other',(freq>=.7*f0)&~((freq>=.965*f0)&(freq<1.08*f0))))})
            # Independent energy identities at each snapshot.
            assert abs(self.boardWork.sum()-b.energy()-b.loss)<1e-9
            assert max(abs(self.contactWork+self.bridgeWork-np.array([z.energy()+z.loss for z in g])))<1e-9
            self.rows.append(row)
def main():
    count=int(np.sum(freqs<6000));ks=[k[:count] for k in make_kernels(128,96)]
    rows=[]
    for j,m,s in CASES:
        mass=[.012,.010,m/1000][j];l=Ledger(j,s,mass);cap={}
        r=run([j],s,SR,6000,m,capture=cap,duration_s=.16,diagnostic=l)
        control=run([j],s,SR,6000,m,duration_s=.16)
        assert r==control,'observer changed mechanics'
        p=render(cap['acc'],ks)
        assert np.isfinite(p).all()
        assert cap['maxDerivativeError']<=1e-9*max(1.,cap['peakAcceleration'])
        f0=l.f0;t=np.arange(l.n)/SR
        # Fourier integral of full force histories, not a transfer estimate.
        forceSpectrum={}
        for harmonic in (1,2,3,4):
            phase=np.exp(-2j*np.pi*harmonic*f0*t)
            forceSpectrum[str(harmonic)]=dict(contactNs=float(abs(l.force@phase)/SR),
                bridgeNs=float(abs(l.bridge[j]@phase)/SR))
        row=dict(key=KEYS[j],massG=m,speed=s,initialJ=r['initialJ'],
                 parity=True,maxBalance=r['maxBalance'],trajectory=l.rows,
                 forceSpectrum=forceSpectrum,pressure={f'{a:g}-{b:g}':measure(p,f0,a,b)
                  for a,b in [(.02,.08),(.08,.16)]})
        rows.append(row);print('G2_10C_LEDGER '+json.dumps(row,allow_nan=False),flush=True)
    report=dict(scope='read-only 160ms control diagnosis, no parameter changes; modal bands not individual strings',rows=rows,required=len(CASES),passed=len(rows),gate=len(rows)==len(CASES))
    (OUT/'treble_ledger.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G2_10C_LEDGER_GATE '+json.dumps({k:report[k] for k in ('required','passed','gate')}),flush=True)
if __name__=='__main__':main()
