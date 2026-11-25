"""G2.09c: simultaneous nonlinear contact on the validated passive modal network."""
import json, math
from pathlib import Path
import numpy as np
from scipy.linalg import eigh, cho_factor, cho_solve
from scipy.optimize import brentq
OUT=Path('/tmp/g2-modal-bridge')
DATA=json.loads((OUT/'physical.json').read_text())
REF=json.loads((OUT/'hammer_reference.json').read_text())
MASS={48:.012,60:.010,84:.006}
def potential(d,k): return k*max(d,0.)**3.5/3.5
def secant(a,b,k):
    if a==b:return k*max(a,0.)**2.5
    lo,hi=sorted((a,b))
    if hi<=0:return 0.
    if lo<=0:return potential(hi,k)/(hi-lo)
    return k*lo**3.5*math.expm1(3.5*math.log1p((hi-lo)/lo))/(3.5*(hi-lo)) if (hi-lo)/lo<.5 else (potential(hi,k)-potential(lo,k))/(hi-lo)
def run(w2,D,P,sr,mass,speed):
    h=1/sr; n=len(w2); nc=(P.shape[1]-2)//2; B=P[:,2:2+nc]
    k=2e9/nc; eta=.12; hm=h*h/(2*mass)
    w=np.sqrt(w2); c=np.cos(w*h); s=np.sin(w*h); G=2*np.sin(w*h/2)**2/w2; J=s/w
    sg=np.sqrt(G); inv=cho_solve(cho_factor(np.eye(n)+(sg[:,None]*D*sg[None,:])/h),np.eye(n))
    H=sg[:,None]*inv*sg[None,:]; HB=H@B; C=B.T@HB+hm
    assert np.min(eigh(C,eigvals_only=True))>0
    q=np.zeros(n);v=np.zeros(n);x=-.0002;vh=speed
    E0=.5*mass*speed**2;felt=0.;structural=0.;peak=0.;impulse=0.;first=-1;last=-1;maxbal=0.;maxres=0.;minfelt=0.;minstruct=0.;trace=[];maxsweeps=0
    for i in range(round(sr*.04)):
        d0=x-B.T@q
        free_delta=sg*(inv@(((c-1)*q+J*v)/sg))
        free=x+h*vh-B.T@(q+free_delta)
        def law(j,d):
            return secant(float(d0[j]),float(d),k)*max(0.,1+eta*(d-d0[j])/h)
        f=np.zeros(nc)
        if any(law(j,free[j])>0 for j in range(nc)):
            for sweep in range(128):
                for j in range(nc):
                    a=free[j]-(C[j]@f-C[j,j]*f[j])
                    hi=law(j,a)
                    f[j]=brentq(lambda z:z-law(j,a-C[j,j]*z),0,hi,xtol=1e-13) if hi>0 else 0.
                d=free-C@f
                if max(abs(f[j]-law(j,d[j])) for j in range(nc))<1e-9:break
            else:raise RuntimeError('contact convergence')
            maxsweeps=max(maxsweeps,sweep+1)
        total=float(f.sum());x+=h*vh-hm*total;vh-=h*total/mass
        delta=free_delta+HB@f;damping=D@delta/h
        v=-w*s*q+c*v+J*(B@f-damping);q+=delta
        d1=x-B.T@q
        dl=sum(float(f[j])*(d1[j]-d0[j])-potential(d1[j],k)+potential(d0[j],k) for j in range(nc))
        ds=float(delta@damping);felt+=dl;structural+=ds
        minfelt=min(minfelt,dl);minstruct=min(minstruct,ds)
        maxres=max(maxres,max(abs(f[j]-law(j,d1[j])) for j in range(nc)))
        assert all(f[j]==0 for j in range(nc) if d0[j]<=0 and d1[j]<=0)
        em=.5*(v@v+(w2*q)@q)
        maxbal=max(maxbal,abs(E0-(em+.5*mass*vh**2+sum(potential(d,k) for d in d1))-felt-structural))
        peak=max(peak,total);impulse+=h*total
        if total>1e-8:
            if first<0:first=i
            last=i
        if (i+1)%(sr//1000)==0:trace.append((P[:,:2+nc].T@q).tolist())
    assert first>=0 and vh<0 and np.all(d1<0) and np.all(f==0)
    assert maxbal<=max(1e-10,1e-7*E0) and minfelt>=-1e-11 and minstruct>=-1e-12 and maxres<=1e-7*max(1,peak)
    return dict(peak=peak,impulse=impulse,duration=(last-first+1)*1000/sr,mechanicalJ=float(em),feltJ=float(felt),structuralJ=structural,initialJ=E0,maxBalance=float(maxbal),maxResidual=float(maxres),maxSweeps=maxsweeps,trace=trace)
def compare(a,b):
    keys=['peak','impulse','mechanicalJ','feltJ','structuralJ']
    err={k:abs(a[k]-b[k])/max(abs(b[k]),1e-20) for k in keys}
    x=np.asarray(a['trace']);y=np.asarray(b['trace'])
    err['bridge']=float(np.linalg.norm(x[:,:2]-y[:,:2])/max(np.linalg.norm(y[:,:2]),1e-30))
    err['contacts']=float(np.linalg.norm(x[:,2:]-y[:,2:])/max(np.linalg.norm(y[:,2:]),1e-30))
    dur=abs(a['duration']-b['duration'])
    return dict(errors=err,durationErrorMs=dur,pass_=all(v<=.10 for v in err.values()) and dur<=.10)
rows=[];checks=[]
for a in DATA:
    key=a['key'];loss=a['lossId'];M,C,K=(np.asarray(a[k]) for k in ('M','C','K'))
    raw=np.zeros((a['n'],2));raw[0,0]=1;raw[a['N'],1]=1
    raw=np.column_stack((raw,np.asarray(a['ports']).T));w2,U=eigh(K,M)
    D=U.T@C@U;D=(D+D.T)/2;P=U.T@raw;hz=np.sqrt(w2)/(2*np.pi)
    for speed in (.5,1.,2.):
        ref={r['sr']:r for r in REF if r['key']==key and r['lossId']==loss and r['speed']==speed}
        ck=compare(ref[192000],ref[384000]);checks.append(dict(key=key,lossId=loss,speed=speed,tag='reference192',**ck))
        for tag,idx,sr in [('full96',np.arange(len(w2)),96000),('full48',np.arange(len(w2)),48000),('reduced96',np.flatnonzero(hz<.75*a['cutoffHz']),96000)]:
            r=run(w2[idx],D[np.ix_(idx,idx)],P[idx,:],sr,MASS[key],speed)
            ck=compare(r,ref[384000]);row=dict(key=key,lossId=loss,speed=speed,tag=tag,sr=sr,modes=len(idx),**r,**ck)
            rows.append(row)
            if tag=='full96':checks.append({k:row[k] for k in ('key','lossId','speed','tag','errors','durationErrorMs','pass_')})
            print('G2_MODAL_HAMMER '+json.dumps({k:v for k,v in row.items() if k!='trace'}),flush=True)
for r in checks:print('G2_MODAL_HAMMER_CHECK '+json.dumps(r),flush=True)
report=dict(scope='moving-boundary nonlinear contact, offline, no pressure or voicing',rows=rows,checks=checks,required=len(checks),passed=sum(r['pass_'] for r in checks))
report['gate']=report['passed']==report['required']
(OUT/'hammer_report.json').write_text(json.dumps(report,indent=2))
print('G2_MODAL_HAMMER_GATE '+json.dumps({k:report[k] for k in ('required','passed','gate')}),flush=True)
if not report['gate']:raise SystemExit(1)
