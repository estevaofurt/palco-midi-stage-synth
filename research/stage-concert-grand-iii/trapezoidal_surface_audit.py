"""G3.14d.5: physical surface trapezoidal CQ contour accuracy audit.
Integrate singular-cell radial weights analytically. No temporal feedback."""
import argparse,json
from pathlib import Path
import numpy as np
from numpy.polynomial.legendre import leggauss
from acoustic_cq_surface import ProjectedLoad,directions
from midpoint_cq import symbol
from wire_physical_midpoint import load
from structural_region_decay import rebuild
from polygon_radiation import SurfaceModes
from surface_reactive_fft import cell_integrals
from retarded_surface import C,RHO,delay_kernel as old_kernel
from split_radiation import relative

def moments(z):
    z=np.asarray(z,complex)
    J=np.empty((3,*z.shape),complex)
    small=abs(z)<1.
    x=z[small];term=np.ones_like(x);v=np.zeros((3,len(x)),complex)
    for k in range(26):
        for j in range(3):v[j]+=term/(k+j+1)
        term*=(-x)/(k+1)
    J[:,small]=v
    x=z[~small];e=np.exp(-x)
    J[0,~small]=-np.expm1(-x)/x
    J[1,~small]=(J[0,~small]-e)/x
    J[2,~small]=(2*J[1,~small]-e)/x
    return J

def delay_kernel(n,dx,dy,s,order=8):
    """Average exp(-s*r/c)/r over cell pairs. Duffy integration handles
    touching/self cells without a fabricated minimum distance."""
    if n<1 or min(dx,dy)<=0 or s.real<0 or not np.isfinite(s):raise ValueError('domain')
    z,w=leggauss(order);t=(z+1)/2;w=w/2
    u,v=np.meshgrid(t,t,indexing='ij');u=u.ravel();v=v.ravel()
    wt=(w[:,None]*w[None,:]).ravel()
    i,j=np.meshgrid(np.arange(n),np.arange(n),indexing='ij');i=i.ravel();j=j.ravel()
    K=np.zeros(n*n,complex)
    for sx in (-1,1):
        for sy in (-1,1):
            singular=(i<=1)&(j<=1)&((i==0)|(sx==-1))&((j==0)|(sy==-1))
            ids=np.flatnonzero(~singular)
            for start in range(0,len(ids),2048):
                a=ids[start:start+2048]
                R=np.hypot(dx*(i[a,None]+sx*u),dy*(j[a,None]+sy*v))
                K[a]+=np.sum(np.exp(-s*R/C)/R*(wt*(1-u)*(1-v))[None,:],axis=1)
            for a in np.flatnonzero(singular):
                value=0j
                # Duffy radial variable cancels the singular 1/r.
                # Integrate its degree-two triangular weight exactly.
                for x,y in ((t,np.ones_like(t)),(np.ones_like(t),t)):
                    L=np.hypot(dx*x,dy*y)
                    ax,bx=(1.,-x) if i[a]==0 else (0.,x)
                    ay,by=(1.,-y) if j[a]==0 else (0.,y)
                    J0,J1,J2=moments(s*L/C)
                    value+=np.sum(w*(ax*ay*J0+(ax*by+ay*bx)*J1+bx*by*J2)/L)
                K[a]+=value
    return K.reshape(n,n)

def evaluate(L,s,order,legacy=False):
    K=(old_kernel if legacy else delay_kernel)(L.n,L.dx,L.dy,s,order)
    return RHO*s/(2*np.pi)*(K.ravel()@L.corr).reshape(L.m,L.m)

def positive(Z):
    return float(np.linalg.eigvalsh((Z+Z.conj().T)/2).min()/max(np.linalg.norm(Z),1e-30))

def main():
    p=argparse.ArgumentParser()
    for k in ('scale','source','surface','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--rate',type=int,choices=(48000,96000),required=True);a=p.parse_args()
    archive,wires,sha=load(a.source,a.scale);local={}
    def sink(plate,poly,lift):local.update(plate=plate,poly=poly,lift=lift)
    k,D,P,A,wires,G,lift,replay=rebuild(a.scale,a.surface,archive,wires,surface_sink=sink)
    U=directions(A,wires);field=SurfaceModes(local['plate'],local['lift']@U);grids={}
    for n in (60,120):
        B,dx,dy,area=cell_integrals(local['poly'],field,n)
        if abs(area-local['plate']['areaM2'])/local['plate']['areaM2']>1e-9:raise ValueError('area')
        grids[n]=(B,dx,dy)
    L=ProjectedLoad(*grids[60]);fine=ProjectedLoad(*grids[120])
    B,dx,dy=grids[60];flat=B.reshape(-1,4)
    limit=RHO*C*(flat.T@flat)/(dx*dy)
    # The exact piecewise-constant cell model approaches rho*c times
    # its area Gram along the positive real s-axis, not zero.
    n=1024 if a.rate==48000 else 2048
    radius=np.exp(-8/n)
    ids=np.unique(np.r_[np.linspace(0,n//2,21,dtype=int),n//2-np.array([1,2,4,8,16,32])])
    z=radius*np.exp(-2j*np.pi*ids/n);ss=symbol(z,a.rate)
    rows=[]
    for i,s in zip(ids,ss):
        v8=evaluate(L,s,8);v16=evaluate(L,s,16);v32=evaluate(L,s,32)
        old=evaluate(L,s,8,True)
        row=dict(index=int(i),realPerS=float(s.real),imagPerS=float(s.imag),
            order8To16=relative(v8,v16),order16To32=relative(v16,v32),
            legacyToAnalytic=relative(old,v32),positiveRealMinimum=positive(v32))
        if i==n//2:row['positiveAxisLimitRelative']=relative(v32,limit)
        rows.append(row)
        print('G3_TRAP_SURFACE_CONTOUR '+json.dumps(row,allow_nan=False),flush=True)
    band=[]
    for f in (30.,110.,130.81,150.,261.63,329.63,400.,500.):
        exact=evaluate(fine,2j*np.pi*f,16)
        coarse=evaluate(L,2j*np.pi*f,16)
        # Stable exact unit-circle trapezoidal symbol away from Nyquist.
        warped=evaluate(L,2j*a.rate*np.tan(np.pi*f/a.rate),16)
        row=dict(frequencyHz=f,gridRelative=relative(coarse,exact),
            warpRelative=relative(warped,coarse),combinedRelative=relative(warped,exact))
        band.append(row)
    high=[]
    for s in (1e6,1e7,1e8):
        v=evaluate(L,complex(s),32)
        high.append(dict(realPerS=s,limitRelative=relative(v,limit),positiveRealMinimum=positive(v)))
    contour=max(v['order16To32'] for v in rows);minPR=min(v['positiveRealMinimum'] for v in rows)
    bandMax=max(v['combinedRelative'] for v in band)
    summary=dict(gate=True,screeningGate=bool(contour<=1e-3 and minPR>=-1e-8 and bandMax<=.05 and high[-1]['limitRelative']<=.01),
        diagnosticOnly=True,physicalSurfaceHypothesis=True,projectedDirections=4,rate=a.rate,contourSamples=n,
        evaluatedContourPoints=len(rows),maximumContourQuadratureRelative=contour,minimumSampledPositiveReal=minPR,
        maximumBandRelative=bandMax,highRealLimitRelative=high[-1]['limitRelative'],
        sourceFrozenSha256=sha,weightsGenerated=False,feedbackIntegrated=False,passivityCertified=False,audibleSustainMeasured=False)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'trapezoidal_surface_audit.json').write_text(json.dumps(dict(summary=summary,contour=rows,band=band,highReal=high),indent=2,allow_nan=False))
    print('G3_TRAP_SURFACE_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
