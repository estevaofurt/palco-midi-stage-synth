"""Actual analytic simply-supported rectangle bending modes, coupled to one-sided air.
Small diagnostic plate, not the full G3 geometry. No WAV.
"""
import argparse,json
from pathlib import Path
import numpy as np
from ribbed_plate import quadrature
from radiation_resistance import surface,pressure
from radiation_impedance import impedance
from passive_radiation import spectral,Load
from vibroacoustic_coupling import Coupled,mobility
ROOT=Path(__file__).parent
POLY=np.array([[0.,0.],[.3,0.],[.3,.2],[0.,.2]])
MODES=np.array([[1,1],[1,3]])
def fields(x,p):
    k=np.pi*MODES/np.array([.3,.2])
    return np.sin(x[:,0,None]*k[:,0])*np.sin(x[:,1,None]*k[:,1])
def rel(x,y):return float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-30))
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'vibroacoustic.json'
    c=json.loads((ROOT/'board_interface_hypothesis.json').read_text())['plate']
    h=c['thicknessM'];ex=c['ExPa'];ey=c['EyPa'];nu=c['nuXY'];g=c['GxyPa'];d=h**3/(12*(1-nu*nu*ey/ex))
    k=np.pi*MODES/np.array([.3,.2]);kx,ky=k.T;area=.06
    M=np.eye(2)*c['densityKgM3']*h*area/4
    K=np.diag(area/4*(d*ex*kx**4+2*(d*nu*ey+2*g*h**3/12)*kx*kx*ky*ky+d*ey*ky**4))
    D=c['alphaPerS']*M+c['betaS']*K;A=np.eye(2)
    rho=1.204;speed=343.;xy,w=quadrature(POLY,24);S=fields(xy,POLY)
    high=rho*speed*(S.T@(w[:,None]*S));dist=np.linalg.norm(xy[:,None,:]-xy[None,:,:],axis=-1);Q=w[:,None]*S
    cache={}
    def R(f):
        if f not in cache:
            om=2*np.pi*f;cache[f]=rho*om**2/(2*np.pi*speed)*(Q.T@(np.sinc(om/speed*dist/np.pi)@Q))
        return cache[f]
    freq=np.array([80.,125.,180.,250.,375.,500.,750.,1000.])
    ref=np.array([impedance(POLY,fields,2j*np.pi*f,rho,speed,24,32) for f in freq])
    rows=[];loads=[]
    for fmax,df,gamma in [(4000.,12.5,20.),(6000.,6.25,10.)]:
        load=spectral(R,high,fmax,df,gamma);loads.append(load)
        Z=np.array([load.impedance(2j*np.pi*f) for f in freq])
        Y=[];Y0=[];P=[];P0=[];metrics=[]
        # Symmetry of reference quadrature is measured before using its symmetric part.
        reciprocity=max(rel(z,z.T) for z in ref)
        assert reciprocity<=1e-3
        for f,z,z0 in zip(freq,Z,ref):
            y,m=mobility(M,K,D,A,z,f);y0,_=mobility(M,K,D,A,(z0+z0.T)/2,f)
            Y.append(y);Y0.append(y0);metrics.append(m)
            obs=pressure(xy,w,S,[[.1,.1,.17],[.23,.1,.17]],f,rho,speed)
            P.append(obs@y);P0.append(obs@y0)
        errs=[rel(z,z0) for z,z0 in zip(Z,ref)]
        rows.append(dict(fmaxHz=fmax,spacingHz=df,dampingHz=gamma,oscillators=len(load.omega),
          impedanceMaxRelative=max(errs),mobilityRelative=rel(np.array(Y),np.array(Y0)),pressureRelative=rel(np.array(P),np.array(P0)),
          reciprocity=max(m['reciprocity'] for m in metrics),powerRelative=max(m['powerRelative'] for m in metrics),
          passivityMinRelative=min(m['passivityMinRelative'] for m in metrics)))
        print('G3_VIBROACOUSTIC_CASE '+json.dumps(rows[-1]),flush=True)
    path.write_text(json.dumps(dict(frequencyCases=rows,complete=False),indent=2))
    time=[];traces=[]
    # Smooth force pulse, same physical event; sample every 1/4000 s.
    for sr in (48000,96000,192000):
        t=Coupled(M,K,D,A,loads[-1],sr);W=err=0.;trace=[]
        for i in range(round(.04*sr)):
            tm=(i+.5)/sr;F=np.array([.1*np.sin(np.pi*tm/.004)**2,0.]) if tm<.004 else np.zeros(2)
            W+=t.step(F);err=max(err,abs(W-t.energy()-t.lossAir-t.lossStructure))
            if (i+1)%(sr//4000)==0:trace.append(np.r_[t.q,t.v,list(t.partition().values()),t.lossAir,t.lossStructure])
        traces.append(np.array(trace));time.append(dict(rateHz=sr,workJ=W,energyJ=t.energy(),airLossJ=t.lossAir,
             structureLossJ=t.lossStructure,maxBalanceJ=err,gate=err<=max(1e-11,abs(W)*1e-8)))
    checks=[[rel(x[:,i],y[:,i]) for i in range(x.shape[1])] for x,y in zip(traces,traces[1:])]
    last=rows[-1];gate=max(last['impedanceMaxRelative'],last['mobilityRelative'],last['pressureRelative'])<=.05 and last['reciprocity']<=1e-8 and last['powerRelative']<=1e-6 and last['passivityMinRelative']>=-1e-8 and max(checks[-1])<=.05 and all(q['gate'] for q in time)
    summary=dict(modes=MODES.tolist(),unloadedHz=(np.sqrt(np.diag(K)/np.diag(M))/(2*np.pi)).tolist(),frequencyCases=rows,timeCases=time,timeRefinement=checks,gate=gate,radiationReady=False)
    path.write_text(json.dumps(dict(summary=summary,scope='two analytical modes of compact rectangular plate; linear passive acoustic load, not full soundboard',frequenciesHz=freq.tolist()),indent=2,allow_nan=False))
    print('G3_VIBROACOUSTIC_GATE '+json.dumps(summary),flush=True);assert gate,'coupled load accuracy'
if __name__=='__main__':main()
