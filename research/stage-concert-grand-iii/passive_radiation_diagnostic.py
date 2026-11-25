"""Causal passive spectral approximation on a compact diagnostic rectangle.
No actual soundboard loading or calibration. Compare analytic continuum reference.
"""
import argparse,json
from pathlib import Path
import numpy as np
from ribbed_plate import quadrature
from radiation_resistance import surface
from radiation_impedance import impedance
from passive_radiation import spectral
POLY=np.array([[0.,0.],[.3,0.],[.3,.2],[0.,.2]])
RHO=1.204;C=343.
def fields(x,p):
    return np.c_[np.ones(len(x)),2*x[:,0]/.3-1]
def rel(x,y):return float(np.linalg.norm(x-y)/max(np.linalg.norm(y),1e-30))
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'passive_radiation.json'
    freq=np.array([80.,125.,180.,250.,375.,500.,750.,1000.]);rho=RHO;c=C
    xy,w=quadrature(POLY,16);S=fields(xy,POLY);high=rho*c*(S.T@(w[:,None]*S))
    # Reuse exact distance matrix; sample real resistance without complex singularity.
    # Each sampled matrix is checked PSD before forming factors.
    dist=np.linalg.norm(xy[:,None,:]-xy[None,:,:],axis=-1);A=w[:,None]*S
    cache={}
    def R(f):
        if f not in cache:
            om=2*np.pi*f;cache[f]=rho*om**2/(2*np.pi*c)*(A.T@(np.sinc(om/c*dist/np.pi)@A))
        return cache[f]
    ref=np.array([impedance(POLY,fields,2j*np.pi*f,rho,c,24,32) for f in freq])
    rows=[];allZ=[]
    for fmax,df,gamma in [(4000.,25.,40.),(4000.,12.5,20.),(4000.,6.25,10.),(6000.,6.25,10.)]:
        load=spectral(R,high,fmax,df,gamma);Z=np.array([load.impedance(2j*np.pi*f) for f in freq]);allZ.append(Z)
        errors=[rel(z,q) for z,q in zip(Z,ref)]
        pas=min(float(min(np.linalg.eigvalsh((z+z.conj().T)/2))/max(np.linalg.norm(z),1e-30)) for z in Z)
        # Verify independent time-domain storage accounting for a short smooth pulse.
        work=loss=err=0.;h=1/48000
        for i in range(2400):
            t=(i+1)*h;u=np.array([.01,.003])*np.sin(np.pi*t/.01)**2 if t<.01 else np.zeros(2)
            _,w0,l=load.step(u,h);work+=w0;loss+=l;err=max(err,abs(work-loss-load.storage()))
        assert err<=max(1e-11,abs(work)*1e-8) and loss>=0 and pas>=-1e-10
        row=dict(fmaxHz=fmax,spacingHz=df,dampingHz=gamma,oscillators=len(load.omega),errors=errors,
           complexRelative=rel(Z,ref),maxFrequencyRelative=max(errors),minPassivityRelative=pas,
           workJ=work,lossJ=loss,storedJ=load.storage(),maxBalanceJ=err)
        rows.append(row);path.write_text(json.dumps(dict(rows=rows,complete=False),indent=2,allow_nan=False))
        print('G3_PASSIVE_LOAD_CASE '+json.dumps(row),flush=True)
    # Verify resistance quadrature at the upper end independently; it is not a free fit.
    x,w=quadrature(POLY,24);T=fields(x,POLY)
    spatial=max(rel(R(f),surface(x,w,T,f,rho,c)) for f in (1000.,4000.,6000.))
    checks=[rel(x,y) for x,y in zip(allZ,allZ[1:])]
    summary=dict(rows=rows,refinement=checks,spatialResistanceRelative=spatial,
        gate=rows[-1]['maxFrequencyRelative']<=.05 and checks[-2]<=.05 and checks[-1]<=.05 and spatial<=.05,
        radiationReady=False,selectedLoad=None)
    path.write_text(json.dumps(dict(summary=summary,frequenciesHz=freq.tolist(),referenceReal=ref.real.tolist(),referenceImag=ref.imag.tolist(),scope='compact rectangle, two prescribed fields; not full piano soundboard'),indent=2,allow_nan=False))
    print('G3_PASSIVE_LOAD_GATE '+json.dumps(summary),flush=True);assert summary['gate'],'passive impedance approximation'
if __name__=='__main__':main()
