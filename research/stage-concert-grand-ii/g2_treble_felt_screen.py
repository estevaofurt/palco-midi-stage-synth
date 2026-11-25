"""G2.10c-B: one-factor felt stiffness screen, no voicing selection."""
import json
from pathlib import Path
import numpy as np
from scipy.signal import periodogram
from g2_shared_hammer import run,compare
from g2_treble_ledger import Ledger
from g2_acoustic_integrated import make_kernels,render,freqs,SR
OUT=Path('/tmp/g2-shared-board')
MASSES=(6,3)
SPEEDS=(.5,1.,2.)
SCALES=(1.,1.5,3.)
F0=440*2**((84-69)/12)
def acoustic(p):
    z=p[:,round(.02*SR):round(.08*SR)]
    f,P=periodogram(z,fs=SR,axis=1,window='hann',detrend=False)
    P=P.mean(axis=0);df=f[1]-f[0]
    def band(lo,hi):return float(P[(f>=lo)&(f<hi)].sum()*df)
    total=float(P.sum()*df)
    h=[band(.965*k*F0,1.08*k*F0) for k in range(1,5)]
    assert total>0 and h[0]>0
    return dict(fundamentalPa2=h[0],fundamentalFraction=h[0]/total,
        belowFraction=band(80,.7*F0)/total,partialPa2=h,peakPa=np.max(abs(p),axis=1).tolist(),
        rmsPa=np.sqrt(np.mean(z*z,axis=1)).tolist())
def main():
    count=int(np.sum(freqs<6000));ks=[k[:count] for k in make_kernels(128,96)]
    cases={}; mechanics={}
    for m in MASSES:
        for scale in SCALES:
            for speed in SPEEDS:
                ledger=Ledger(2,speed,m/1000);cap={}
                r=run([2],speed,SR,6000,m,capture=cap,duration_s=.16,diagnostic=ledger,trebleStiffnessScale=scale)
                p=render(cap['acc'],ks);assert np.isfinite(p).all()
                assert cap['maxDerivativeError']<=1e-9*max(1.,cap['peakAcceleration'])
                if scale==1:
                    default=run([2],speed,SR,6000,m,duration_s=.16)
                    assert r==default
                l=next(z for z in ledger.rows if z['t']==.008)
                row=dict(massG=m,scale=scale,speed=speed,initialJ=r['initialJ'],
                    contactMs=r['duration'][0],contactPeakN=r['peak'][0],
                    contactWorkFraction=l['contactWorkFraction'][2],
                    reboundFraction=l['hammerKineticFraction'],
                    fundamentalGroupJ=l['activeGroupModalEnergyFraction']['fundamental']*r['initialJ'],
                    boardWorkFraction=(r['boardJ']+r['boardLoss'])/r['initialJ'],
                    maxBalance=r['maxBalance'],**acoustic(p))
                cases[m,scale,speed]=row;mechanics[m,scale,speed]=r
                print('G2_10C_FELT '+json.dumps(row,allow_nan=False),flush=True)
    screens=[]
    for m in MASSES:
        for scale in SCALES[1:]:
            checks=[]
            for speed in SPEEDS:
                a=cases[m,scale,speed];b=cases[m,1.,speed]
                delta=10*np.log10(a['fundamentalPa2']/b['fundamentalPa2'])
                below=a['belowFraction']-b['belowFraction']
                threshold=3 if speed<2 else -1
                # Diagnostic screen, not a perceptual or instrument gate.
                ck=dict(speed=speed,fundamentalDeltaDb=float(delta),belowDelta=float(below),
                    pass_=bool(delta>=threshold and below<=.05))
                checks.append(ck)
            eligible=all(x['pass_'] for x in checks);convergence=[]
            if eligible:
                for speed in SPEEDS:
                    r=run([2],speed,192000,6000,m,duration_s=.16,trebleStiffnessScale=scale)
                    ck=compare(mechanics[m,scale,speed],r)
                    convergence.append(dict(speed=speed,**ck))
            row=dict(massG=m,scale=scale,screen=checks,eligible=eligible,
                 convergence=convergence,eligibleForExploratoryAudio=eligible and all(z['pass_'] for z in convergence))
            screens.append(row);print('G2_10C_FELT_SCREEN '+json.dumps(row,allow_nan=False),flush=True)
    report=dict(scope='one factor within fixed mass, uncalibrated pressure; no selected model',
        rows=list(cases.values()),screens=screens,required=18,passed=len(cases),gate=len(cases)==18)
    (OUT/'treble_felt_screen.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G2_10C_FELT_GATE '+json.dumps({k:report[k] for k in ('required','passed','gate')}),flush=True)
if __name__=='__main__':main()
