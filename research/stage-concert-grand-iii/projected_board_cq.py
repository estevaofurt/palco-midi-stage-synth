"""G3.14d.7: acoustic CQ on a mechanical board with a projected port.
Same locally rebuilt coordinates; no strings, hammer, sound or full-engine approval."""
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from acoustic_cq_pilot import transfer,convolve
from retarded_surface import impedance
from surface_reactive_fft import cell_integrals
from polygon_radiation import SurfaceModes
from split_radiation import relative

def bridge_ports(A,wires):
    B=np.column_stack([np.mean([a for a,w in zip(A,wires) if w.port==j],axis=0) for j in range(4)])
    return B/np.linalg.norm(B,axis=0)

def simulate(k,D,U,W,rate,F):
    n=len(k);h=1/rate;d=2/h
    if U.shape[0]!=n or W.shape[1:]!=(U.shape[1],U.shape[1]) or F.shape[1]!=n:raise ValueError('shape')
    if relative(W,W.transpose(0,2,1))>1e-10:raise ValueError('reciprocity')
    H=np.diag(d+k/d)+D+U@W[0]@U.T
    fac=cho_factor(H);q=np.zeros(n);v=q.copy()
    y=np.zeros((len(F),U.shape[1]));g=y.copy()
    work=loss=air=peak=err=0.;minimum=0.;energy=[]
    for i,f in enumerate(F):
        past=min(i,len(W)-1)
        memory=np.einsum('kij,kj->i',W[1:past+1],y[i-past:i][::-1])
        u=cho_solve(fac,f+d*v-k*q-U@memory)
        y[i]=U.T@u;g[i]=W[0]@y[i]+memory
        q+=h*u;v=2*u-v
        E=.5*float(v@v+np.sum(k*q*q));energy.append(E)
        work+=h*float(f@u);loss+=h*float(u@D@u);air+=h*float(y[i]@g[i]);minimum=min(minimum,air)
        peak=max(peak,E,abs(work),loss,abs(air),1e-30);err=max(err,abs(E+loss+air-work)/peak)
    replay=relative(g,convolve(W,y)) if np.any(W) else float(np.linalg.norm(g))
    return dict(energyRelative=err,convolutionReplay=replay,minimumAcousticWorkRelative=minimum/max(peak,1e-30),
        peakMechanicalEnergyJ=max(energy),finalMechanicalEnergyJ=energy[-1],externalWorkJ=work,
        structuralLossJ=loss,acousticPortWorkJ=air,
        gate=bool(max(err,replay)<=1e-8 and minimum/max(peak,1e-30)>=-1e-8))

def harmonic(k,D,B,Z,f):
    s=2j*np.pi*f
    V=np.linalg.solve(np.diag(k)+s*s*np.eye(len(k))+s*(D+Z),s*B)
    return B.T@V,V

def screen(k,D,A,wires,U,W,rate,local):
    B=bridge_ports(A,wires)
    field=SurfaceModes(local['plate'],local['lift']);grids={}
    for n in (120,240):
        cells,dx,dy,area=cell_integrals(local['poly'],field,n)
        if abs(area-local['plate']['areaM2'])/local['plate']['areaM2']>1e-9:raise ValueError('area')
        grids[n]=(cells,dx,dy)
    fs=np.array([110.,130.81,150.,261.63,329.63,400.,500.]);Zp=transfer(W,fs,rate);rows=[]
    for f,Z in zip(fs,Zp):
        # Compare with complete local load, same mechanical frequency,
        # report spatial truncation separately from CQ discretization.
        full=impedance(*grids[240],2j*np.pi*f)
        coarse=impedance(*grids[120],2j*np.pi*f)
        projected=U@(U.T@full@U)@U.T;actual=U@Z@U.T
        y,v=harmonic(k,D,B,full,f);yp,vp=harmonic(k,D,B,projected,f);ya,va=harmonic(k,D,B,actual,f)
        rows.append(dict(frequencyHz=float(f),gridRelative=relative(coarse,full),projectionMobilityRelative=relative(yp,y),
            projectionStateRelative=relative(vp,v),hybridMobilityRelative=relative(ya,y),hybridStateRelative=relative(va,v)))
    t=np.arange(int(rate*.15))/rate;duration=.025;envelope=np.where(t<duration,np.sin(np.pi*np.minimum(t/duration,1.))**2,0.)
    cases=[]
    for j,f in enumerate((110.,130.81,261.63,329.63)):
        F=(envelope*np.sin(2*np.pi*f*t))[:,None]*B[:,j]
        wet=simulate(k,D,U,W,rate,F);dry=simulate(k,D,U,np.zeros((1,U.shape[1],U.shape[1])),rate,F)
        cases.append(dict(key=(45,48,60,64)[j],frequencyHz=f,wet=wet,dry=dry))
    m=max(max(v['hybridMobilityRelative'],v['hybridStateRelative']) for v in rows)
    grid=max(v['gridRelative'] for v in rows)
    return dict(diagnosticOnly=True,boardOnly=True,mechanicalCoordinates=len(k),acousticDirections=U.shape[1],
        harmonic=rows,cases=cases,maximumHybridResponse=m,maximumGridRelative=grid,
        responseGate=bool(m<=.05 and grid<=.01),energyGate=all(v['wet']['gate'] and v['dry']['gate'] for v in cases),
        stringsIncluded=False,hammerIncluded=False,audibleSustainMeasured=False,physicalFeedbackAccepted=False)
