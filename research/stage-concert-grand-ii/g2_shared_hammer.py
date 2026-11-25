"""G2.09f: nonlinear hammers on the three-group shared structural board."""
import json,math
from pathlib import Path
import numpy as np
from scipy.linalg import eigh,cho_factor,cho_solve
from scipy.optimize import brentq
from g2_shared_board import Block,data,KJ,CJ
OUT=Path('/tmp/g2-shared-board')
KEYS=[48,60,84];MASS=[.012,.010,.006]
def potential(d,k): return k*max(d,0.)**3.5/3.5
def secant(a,b,k):
    if a==b:return k*max(a,0.)**2.5
    lo,hi=sorted((a,b))
    if hi<=0:return 0.
    if lo<=0:return potential(hi,k)/(hi-lo)
    return k*lo**3.5*math.expm1(3.5*math.log1p((hi-lo)/lo))/(3.5*(hi-lo)) if (hi-lo)/lo<.5 else (potential(hi,k)-potential(lo,k))/(hi-lo)

groups=[]
for a in data['groups']:
    M,C,K=(np.asarray(a[k]) for k in ('M','C','K'))
    w2,U=eigh(K,M);D=U.T@C@U;D=(D+D.T)/2
    assert np.min(w2)>0 and np.min(eigh(D,eigvals_only=True))>=-1e-9
    nc=len(a['ports'])//2
    raw=np.zeros((a['n'],1));raw[0,0]=1
    raw=np.column_stack((raw,np.asarray(a['ports'][:nc]).T))
    groups.append((w2,D,U.T@raw))
def run(active,speed,sr,cut,trebleMass=6,capture=None,duration_s=.04,sink=None,diagnostic=None,trebleStiffnessScale=1.):
    if not math.isfinite(duration_s) or duration_s<.04:raise ValueError('duration')
    if not math.isfinite(trebleStiffnessScale) or trebleStiffnessScale<=0:raise ValueError('treble stiffness scale')
    steps=round(sr*duration_s)
    h=1/sr
    g=[Block(*a,sr) for a in groups]
    board=next(x for x in data['boards'] if x['basis']==6000)
    modes=[m for m in board['modes'] if m['f']<cut];w2=np.array([m['lambda'] for m in modes])
    b=Block(w2,2*(2+.0005*np.sqrt(w2)),np.array([m['w'] for m in modes]),sr)
    H=b.H+np.diag([a.H[0,0] for a in g]);alpha=KJ/2+CJ/h
    inv=cho_solve(cho_factor(np.eye(3)+alpha*H),np.eye(3));R=alpha*inv
    owners=[];local=[];slices={};masses=np.array(MASS);masses[2]=trebleMass/1000
    for j in active:
        start=len(owners);nc=g[j].P.shape[1]-1
        owners.extend([j]*nc);local.extend(range(nc));slices[j]=slice(start,start+nc)
    n=len(owners);T=np.zeros((3,n));C=np.zeros((n,n));ks=np.zeros(n)
    for j in active:
        sl=slices[j];T[j,sl]=g[j].H[0,1:]
        C[sl,sl]=g[j].H[1:,1:]+h*h/(2*masses[j]);ks[sl]=2e9*(trebleStiffnessScale if j==2 else 1.)/(sl.stop-sl.start)
    C-=T.T@R@T;assert np.min(eigh(C,eigvals_only=True))>0
    x=np.full(3,-.0002);v=np.zeros(3);v[active]=speed
    initial=.5*np.sum(masses*v*v);felt=0.;jl=0.;peak=np.zeros(3);impulse=np.zeros(3)
    first=np.full(3,-1);last=np.full(3,-1);maxbal=0.;maxres=0.;maxjoint=0.;minloss=0.;maxinc=0.;peakBoard=0.;peakOther=0.;maxsweeps=0;trace=[]
    def rel():return np.array([a.P[:,0]@a.q for a in g])-b.P.T@b.q
    def positions():return [a.P.T@a.q for a in g]
    def compression(pos):return np.array([x[j]-pos[j][l+1] for j,l in zip(owners,local)])
    def mech():r=rel();return sum(a.energy() for a in g)+b.energy()+.5*KJ*(r@r)
    def total(d):return mech()+.5*np.sum(masses*v*v)+sum(potential(di,k) for di,k in zip(d,ks))
    if capture is not None:
        capture['acc']=np.empty((len(modes),steps))
        capture['maxDerivativeError']=0.;capture['peakAcceleration']=0.
    for i in range(steps):
        r0=rel();pos=positions();d0=compression(pos);old=total(d0)
        free=[a.free() for a in g];df=np.array([z[0] for z in free])-b.free()
        j0=inv@(-KJ*r0-alpha*df)
        cf=np.array([x[j]+h*v[j]-pos[j][l+1]-free[j][l+1] for j,l in zip(owners,local)])-T.T@j0
        def law(j,d):return secant(float(d0[j]),float(d),ks[j])*max(0.,1+.12*(d-d0[j])/h)
        f=np.zeros(n)
        if any(law(j,cf[j])>0 for j in range(n)):
            for sweep in range(128):
                for j in range(n):
                    a=cf[j]-(C[j]@f-C[j,j]*f[j]);hi=law(j,a)
                    f[j]=brentq(lambda z:z-law(j,a-C[j,j]*z),0,hi,xtol=1e-13) if hi>0 else 0.
                d=cf-C@f
                if max(abs(f[j]-law(j,d[j])) for j in range(n))<1e-9:break
            else:raise RuntimeError('shared contact convergence')
            maxsweeps=max(maxsweeps,sweep+1)
        jf=j0-R@(T@f)
        ds=[]
        for j,a in enumerate(g):
            contacts=f[slices[j]] if j in slices else np.zeros(a.P.shape[1]-1)
            ds.append(a.step(np.r_[jf[j],contacts]))
            if j in slices:
                ft=float(contacts.sum());x[j]+=h*v[j]-h*h*ft/(2*masses[j]);v[j]-=h*ft/masses[j]
                peak[j]=max(peak[j],ft);impulse[j]+=h*ft
                if ft>1e-8:
                    if first[j]<0:first[j]=i
                    last[j]=i
        if capture is not None or sink is not None: q0=b.q.copy();v0=b.v.copy()
        db=b.step(-jf)
        if capture is not None or sink is not None:
            acc=(b.v-v0)/h
        if capture is not None:
            delta=b.q-q0;fe=b.P@(-jf)-b.D*delta/h
            integral=q0*b.J+v0*b.G+(h-b.J)*fe/b.w2
            oracle=fe-b.w2*integral/h
            capture['acc'][:,i]=acc
            capture['maxDerivativeError']=max(capture['maxDerivativeError'],float(np.max(abs(acc-oracle))))
            capture['peakAcceleration']=max(capture['peakAcceleration'],float(np.max(abs(acc))))
        if sink is not None:sink(acc)
        dr=rel()-r0;dj=CJ*(dr@dr)/h;jl+=dj
        maxjoint=max(maxjoint,float(np.max(abs(jf+KJ*(r0+dr/2)+CJ*dr/h))))
        d1=compression(positions())
        dl=sum(float(f[j])*(d1[j]-d0[j])-potential(d1[j],ks[j])+potential(d0[j],ks[j]) for j in range(n));felt+=dl
        assert all(f[j]==0 for j in range(n) if d0[j]<=0 and d1[j]<=0)
        assert np.all(np.isfinite(f)) and np.all(f>=0)
        maxres=max(maxres,max(abs(f[j]-law(j,d1[j])) for j in range(n)))
        E=total(d1);maxinc=max(maxinc,E-old);minloss=min(minloss,*ds,db,dj,dl)
        maxbal=max(maxbal,abs(initial-E-felt-jl-b.loss-sum(a.loss for a in g)))
        peakBoard=max(peakBoard,b.energy());peakOther=max(peakOther,sum(a.energy() for j,a in enumerate(g) if j not in active))
        if diagnostic is not None:
            diagnostic(i,g,b,v,masses,f,jf,owners,local,pos,r0,felt,jl)
        if (i+1)%(sr//1000)==0:
            trace.append(np.r_[[a.P[:,0]@a.q for a in g],b.P.T@b.q,*[z[1:] for z in positions()]].tolist())
    assert all(first[j]>=0 and v[j]<0 for j in active) and np.all(d1<0) and np.all(f==0)
    assert maxbal<=max(1e-10,1e-7*initial) and maxinc<=1e-11 and minloss>=-1e-11 and maxres<=1e-7*max(1,peak.max()) and maxjoint<1e-7
    assert peakBoard>0 and jl>0 and b.loss>0
    if len(active)==1:assert peakOther>0
    return dict(active=[KEYS[j] for j in active],speed=speed,sr=sr,cut=cut,trebleMass=trebleMass,modes=len(modes),initialJ=float(initial),peak=peak[active].tolist(),impulse=impulse[active].tolist(),duration=((last[active]-first[active]+1)*1000/sr).tolist(),mechanicalJ=mech(),boardJ=b.energy(),groupJ=[a.energy() for a in g],feltJ=felt,boardLoss=b.loss,jointLoss=jl,groupLoss=sum(a.loss for a in g),peakBoardJ=peakBoard,peakOtherJ=peakOther,maxBalance=maxbal,maxResidual=maxres,maxJointResidual=maxjoint,maxSweeps=maxsweeps,trace=trace)
def compare(a,b):
    e={}
    for k in ('peak','impulse'):
        e[k]=float(np.max(abs(np.array(a[k])-b[k])/np.maximum(abs(np.array(b[k])),1e-20)))
    for k in ('mechanicalJ','boardJ','feltJ','boardLoss','jointLoss','groupLoss'):
        e[k]=abs(a[k]-b[k])/max(abs(b[k]),1e-20)
    x=np.array(a['trace']);y=np.array(b['trace'])
    for k,sl in [('bridge',slice(0,3)),('board',slice(3,6)),('contacts',slice(6,None))]:
        e[k]=float(np.linalg.norm(x[:,sl]-y[:,sl])/max(np.linalg.norm(y[:,sl]),1e-30))
    d=float(np.max(abs(np.array(a['duration'])-b['duration'])))
    return dict(errors=e,durationErrorMs=d,pass_=all(z<=.1 for z in e.values()) and d<=.1)
if __name__ == '__main__':
    rows=[];checks=[]
    def record(r):
        rows.append(r);print('G2_SHARED_HAMMER '+json.dumps({k:v for k,v in r.items() if k!='trace'}),flush=True)
    for active,speeds in [([0],[.5,1.,2.]),([1],[.5,1.,2.]),([2],[.5,1.,2.]),([0,1,2],[1.])]:
        for speed in speeds:
            ref=run(active,speed,192000,6000);record(ref)
            a=run(active,speed,96000,6000);record(a)
            b=run(active,speed,96000,5000);record(b)
            for tag,r,t in [('time96',a,ref),('band5k',b,a)]:
                ck=dict(active=r['active'],speed=speed,tag=tag,**compare(r,t));checks.append(ck);print('G2_SHARED_HAMMER_CHECK '+json.dumps(ck),flush=True)
    for speed in (.5,1.,2.):record(run([2],speed,96000,6000,3))
    required=[r for r in checks if r['tag']=='time96']
    gate=all(r['pass_'] for r in required)
    report=dict(scope='nonlinear shared board, vertical joint, no acoustic radiation, no dampers',rows=rows,checks=checks,required=len(required),passed=sum(r['pass_'] for r in required),gate=gate)
    (OUT/'hammer_report.json').write_text(json.dumps(report,indent=2))
    print('G2_SHARED_HAMMER_GATE '+json.dumps({k:report[k] for k in ('required','passed','gate')}),flush=True)
    if not gate:raise SystemExit(1)
