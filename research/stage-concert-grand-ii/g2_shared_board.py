"""G2.09e: shared board + three modal groups, simultaneous reciprocal joints."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh, cho_factor, cho_solve
OUT=Path('/tmp/g2-shared-board')
data=json.loads((OUT/'model.json').read_text())
KJ=1e7; CJ=1.
def pulse(t,h):
    def I(x):
        u=min(max(x,0.),.001)
        return .1*(u/2-.001*np.sin(2*np.pi*u/.001)/(4*np.pi))
    return (I(t+h)-I(t))/h
class Block:
    def __init__(self,w2,D,P,sr):
        self.w2=w2; self.D=D; self.P=P; self.h=h=1/sr
        w=np.sqrt(w2); self.w=w;self.c=np.cos(w*h);self.s=np.sin(w*h)
        self.G=G=2*np.sin(w*h/2)**2/w2;self.J=self.s/w
        self.sg=sg=np.sqrt(G)
        if D.ndim==1:
            self.inv=1/(1+G*D/h)
            self.HP=(G*self.inv)[:,None]*P
        else:
            self.inv=cho_solve(cho_factor(np.eye(len(w))+(sg[:,None]*D*sg[None,:])/h),np.eye(len(w)))
            self.HP=sg[:,None]*(self.inv@(sg[:,None]*P))
        self.H=P.T@self.HP; self.q=np.zeros(len(w));self.v=np.zeros(len(w))
        self.loss=0.
    def energy(self):return .5*(self.v@self.v+(self.w2*self.q)@self.q)
    def free(self):
        r=(self.c-1)*self.q+self.J*self.v
        self.df=self.inv*r if self.D.ndim==1 else self.sg*(self.inv@(r/self.sg))
        return self.P.T@self.df
    def step(self,f):
        delta=self.df+self.HP@f
        damp=(self.D*delta if self.D.ndim==1 else self.D@delta)/self.h
        self.v=-self.w*self.s*self.q+self.c*self.v+self.J*(self.P@f-damp);self.q+=delta
        d=float(delta@damp);self.loss+=d
        return d
GROUPS=[]
for a in data['groups']:
    M,C,K=(np.array(a[k]) for k in ('M','C','K'));w2,U=eigh(K,M)
    D=U.T@C@U;D=(D+D.T)/2
    assert np.min(w2)>0 and np.min(eigh(D,eigvals_only=True))>=-1e-9
    raw=np.zeros((a['n'],2));raw[0,0]=1;raw[:,1]=a['ports'][0]
    GROUPS.append((w2,D,U.T@raw))
def run(basis,cut,sr,drive,open_joint=False):
    h=1/sr; board=next(x for x in data['boards'] if x['basis']==basis)
    modes=[m for m in board['modes'] if m['f']<cut]
    w2=np.array([m['lambda'] for m in modes]);D=2*(2+.0005*np.sqrt(w2));P=np.array([m['w'] for m in modes])
    g=[Block(*a,sr) for a in GROUPS];b=Block(w2,D,P,sr)
    k=0. if open_joint else KJ;c=0. if open_joint else CJ
    alpha=k/2+c/h
    H=b.H+np.diag([a.H[0,0] for a in g])
    inv=cho_solve(cho_factor(np.eye(3)+alpha*H),np.eye(3))
    work=0.;jl=0.;maxbal=0.;minloss=0.;maxinc=0.;peakOther=0.;peakBoard=0.;maxres=0.;trace=[]
    def rel():return np.array([a.P[:,0]@a.q for a in g])-b.P.T@b.q
    def total():return sum(a.energy() for a in g)+b.energy()+.5*k*(rel()@rel())
    for i in range(round(sr*.02)):
        prev=total();r0=rel()
        u=pulse(i*h,h) if i*h<.001 else 0.
        ext=np.zeros(3);ext[drive]=u
        free=np.array([a.free()[0]+a.H[0,1]*ext[j] for j,a in enumerate(g)])-b.free()
        f=inv@(-k*r0-alpha*free)
        old=g[drive].P[:,1]@g[drive].q
        ds=[a.step(np.array([f[j],ext[j]])) for j,a in enumerate(g)]
        db=b.step(-f);dr=rel()-r0
        dj=c*(dr@dr)/h;jl+=dj
        maxres=max(maxres,float(np.max(abs(f+k*(r0+dr/2)+c*dr/h))))
        work+=u*(g[drive].P[:,1]@g[drive].q-old)
        E=total();maxbal=max(maxbal,abs(E+sum(a.loss for a in g)+b.loss+jl-work))
        minloss=min(minloss,*ds,db,dj)
        if u==0:maxinc=max(maxinc,E-prev)
        peakOther=max(peakOther,sum(a.energy() for j,a in enumerate(g) if j!=drive));peakBoard=max(peakBoard,b.energy())
        if (i+1)%(sr//1000)==0:
            trace.append(np.r_[[a.P[:,0]@a.q for a in g],b.P.T@b.q,[a.P[:,1]@a.q for a in g]].tolist())
    assert maxbal<1e-10 and minloss>=-1e-12 and maxinc<=1e-12 and maxres<1e-7
    if open_joint:assert peakOther==0 and peakBoard==0 and jl==0
    else:assert peakOther>0 and peakBoard>0 and jl>0
    return dict(basis=basis,cut=cut,sr=sr,drive=drive,modes=len(modes),open=open_joint,trace=trace,work=work,energy=total(),boardEnergy=b.energy(),groupEnergy=[a.energy() for a in g],jointLoss=jl,boardLoss=b.loss,groupLoss=sum(a.loss for a in g),maxBalance=maxbal,minLoss=minloss,maxIncrease=maxinc,maxResidual=maxres,peakOther=peakOther,peakBoard=peakBoard)
def compare(a,b):
    x=np.array(a['trace']);y=np.array(b['trace'])
    err={k:float(np.linalg.norm(x[:,sl]-y[:,sl])/max(np.linalg.norm(y[:,sl]),1e-30)) for k,sl in [('bridge',slice(0,3)),('board',slice(3,6)),('contacts',slice(6,9))]}
    for k in ['work','energy']:err[k]=abs(a[k]-b[k])/max(abs(b[k]),1e-30)
    return dict(errors=err,pass_=all(v<=.1 for v in err.values()))
rows=[];checks=[]
for drive in range(3):
    op=run(4000,3000,48000,drive,True);rows.append(op)
    ref=run(6000,6000,192000,drive);rows.append(ref)
    for tag,basis,cut,sr in [('time96',6000,6000,96000),('time48',6000,6000,48000),('band5k',6000,5000,96000),('band3k',6000,3000,96000),('basis4k',4000,3000,96000)]:
        r=run(basis,cut,sr,drive);rows.append(r)
        # Separate time and band comparisons from Ritz basis comparison.
        target=ref if tag.startswith('time') else next(z for z in rows if z['drive']==drive and z['basis']==6000 and z['sr']==96000 and z['cut']==(3000 if tag=='basis4k' else 6000))
        ck=dict(drive=drive,tag=tag,**compare(r,target));checks.append(ck);print('G2_SHARED_CHECK '+json.dumps(ck),flush=True)
    for r in rows:
        if r['drive']==drive:print('G2_SHARED '+json.dumps({k:v for k,v in r.items() if k!='trace'}),flush=True)
required=[x for x in checks if x['tag'] in ('time96','band5k','basis4k')]
gate=all(x['pass_'] for x in required)
report=dict(scope='linear three groups one shared board; passive joints; no hammer, radiation, or audio',rows=rows,checks=checks,required=len(required),passed=sum(x['pass_'] for x in required),gate=gate)
(OUT/'report.json').write_text(json.dumps(report,indent=2))
print('G2_SHARED_GATE '+json.dumps({k:report[k] for k in ('required','passed','gate')}),flush=True)
if not gate:raise SystemExit(1)
