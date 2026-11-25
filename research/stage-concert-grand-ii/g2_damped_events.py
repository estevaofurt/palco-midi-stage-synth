"""G2.11-R1: experimental reciprocal viscous dampers, not a calibrated action."""
import json, math
from pathlib import Path
import numpy as np
from scipy.linalg import eigh,cho_factor,cho_solve
from scipy.optimize import brentq
from g2_shared_board import Block,KJ,CJ,data
from g2_shared_hammer import potential,secant
ROOT=Path('/tmp/g2-shared-board')
def modal(group):
    M,C,K=(np.asarray(group[k]) for k in ('M','C','K'))
    w2,U=eigh(K,M);D=U.T@C@U;D=(D+D.T)/2
    assert np.min(w2)>0 and np.min(eigh(D,eigvals_only=True))>=-1e-9
    nc=len(group['ports'])//2
    raw=np.zeros((group['n'],1));raw[0,0]=1
    return w2,D,U.T@np.column_stack((raw,np.asarray(group['ports'][:nc]).T))
def run_damped(model,events,sr,duration,sink=None,retain_trace=False,*,releases=(),mode="dry",damperC=1.,diagnostic=None):
    boardLossScale=feltScale=1.
    if mode not in ("bypass","release-only","dry") or not math.isfinite(damperC) or damperC<=0:raise ValueError("damper mode/coefficient")
    if mode=="bypass" and releases:raise ValueError("bypass has no releases")
    if not all(math.isfinite(z) and z>0 for z in (boardLossScale,feltScale)):raise ValueError('positive finite physical scales')
    keys=[a['key'] for a in model['groups']];ng=len(keys)
    masses=np.array([a.get('massKg',{48:.012,60:.010,84:.006}.get(a['key'])) for a in model['groups']])
    assert np.isfinite(masses).all() and np.all(masses>0)
    steps=round(duration*sr);h=1/sr
    assert sr in (96000,192000) and steps>0 and events
    schedule={}
    for time,key,speed in events:
        if key not in keys or not math.isfinite(speed) or speed<=0 or not 0<=time<duration:raise ValueError('event')
        i=round(time*sr);j=keys.index(key)
        if i>=steps or any(z[0]==j for z in schedule.get(i,[])):raise ValueError('duplicate or out-of-range event')
        schedule.setdefault(i,[]).append((j,speed))
    off={}
    for time,key in releases:
        if key not in keys or not math.isfinite(time) or not 0<=time<duration:raise ValueError("release")
        i=round(time*sr);j=keys.index(key)
        if i>=steps or j in off.get(i,[]) or any(k==j for k,_ in schedule.get(i,[])):raise ValueError("ambiguous release")
        off.setdefault(i,[]).append(j)
    g=[Block(*modal(a),sr) for a in model['groups']]
    modes=[m for m in next(b for b in model['boards'] if b['basis']==6000)['modes'] if m['f']<6000]
    w2=np.array([m['lambda'] for m in modes])
    b=Block(w2,boardLossScale*2*(2+.0005*np.sqrt(w2)),np.array([m['w'] for m in modes]),sr)
    alpha=KJ/2+CJ/h
    # Passive damper at existing vertical contact port; implicit elimination of its force.
    # 25 uniform coefficient increments over 25ms, preserving state at each change.
    localDamper={}
    for j,a in enumerate(g):
        for level in range(1,26):
            c=damperC*level/25
            Q=cho_solve(cho_factor(a.H[1:,1:]+(h/c)*np.eye(a.H.shape[0]-1)),np.eye(a.H.shape[0]-1))
            assert np.max(abs(Q-Q.T))<=1e-10*max(1.,np.max(abs(Q)))
            heff=a.H[0,0]-a.H[0,1:]@Q@a.H[1:,0]
            assert heff>0
            localDamper[j,level]=(Q,heff,c)
    held=set();released={};damperLoss=np.zeros(ng);maxDamperResidual=0.;maxDamperWorkResidual=0.
    rampSamples=sr//1000
    x=np.zeros(ng);v=np.zeros(ng);live={};history=[];removed=0.;injected=0.;felt=0.;jl=0.;maxbal=0.;maxinc=0.;minloss=0.;maxres=0.;maxjoint=0.;peakBoard=0.;trace=[]
    def positions():return [a.P.T@a.q for a in g]
    def rel():return np.array([a.P[:,0]@a.q for a in g])-b.P.T@b.q
    def mech():
        rr=rel()
        return sum(a.energy() for a in g)+b.energy()+.5*KJ*(rr@rr)
    def energy(pos):
        return mech()+sum(.5*masses[j]*v[j]**2+sum(potential(x[j]-z,feltScale*2e9/(len(pos[j])-1)) for z in pos[j][1:]) for j in live)
    cache={}
    for i in range(steps):
        pos=positions()
        for j in off.get(i,[]):
            if j not in held or j in live:raise ValueError("release requires held key and retired hammer")
            held.remove(j);released[j]=i
        for j,speed in schedule.get(i,[]):
            if j in live:raise ValueError('reattack while hammer still in flight')
            held.add(j);released.pop(j,None)
            before=mech()
            x[j]=min(pos[j][1:])-.0002;v[j]=speed
            e=.5*masses[j]*speed**2;injected+=e
            assert mech()==before
            rec=dict(key=keys[j],launchSample=i,speed=speed,injectedJ=e,residualMechanicalJ=before,first=None,last=None,peakN=0.,impulseNs=0.)
            live[j]=rec;history.append(rec)
        active=tuple(sorted(live));r0=rel();old=energy(pos)
        levels=tuple(0 if mode=="bypass" or j in held or j in live else min(25,(i-released[j])//rampSamples) if j in released else 25 if mode=="dry" else 0 for j in range(ng))
        assert all(levels[j]==0 for j in active)
        tag=(active,levels)
        if tag not in cache:
            H=b.H+np.diag([localDamper[j,lev][1] if lev else a.H[0,0] for j,(a,lev) in enumerate(zip(g,levels))])
            inv=cho_solve(cho_factor(np.eye(ng)+alpha*H),np.eye(ng));R=alpha*inv
            owners=[];local=[];slices={}
            for j in active:
                start=len(owners);nc=g[j].P.shape[1]-1;owners.extend([j]*nc);local.extend(range(nc));slices[j]=slice(start,start+nc)
            n=len(owners);T=np.zeros((ng,n));C=np.zeros((n,n));ks=np.zeros(n)
            for j in active:
                sl=slices[j];T[j,sl]=g[j].H[0,1:];C[sl,sl]=g[j].H[1:,1:]+h*h/(2*masses[j]);ks[sl]=feltScale*2e9/(sl.stop-sl.start)
            C-=T.T@R@T
            if n:assert np.min(eigh(C,eigvals_only=True))>0
            cache[tag]=(owners,local,slices,T,C,ks,inv,R)
            if len(cache)>256:cache.pop(next(iter(cache)))
        owners,local,slices,T,C,ks,inv,R=cache[tag];n=len(owners)
        d0=np.array([x[j]-pos[j][l+1] for j,l in zip(owners,local)])
        free=[a.free() for a in g]
        effective=np.array([z[0]-g[j].H[0,1:]@localDamper[j,lev][0]@z[1:] if lev else z[0] for j,(z,lev) in enumerate(zip(free,levels))])
        j0=inv@(-KJ*r0-alpha*(effective-b.free()))
        cf=np.array([x[j]+h*v[j]-pos[j][l+1]-free[j][l+1] for j,l in zip(owners,local)])-T.T@j0
        def law(k,d):return secant(float(d0[k]),float(d),ks[k])*max(0.,1+.12*(d-d0[k])/h)
        f=np.zeros(n)
        if any(law(k,cf[k])>0 for k in range(n)):
            for sweep in range(128):
                for k in range(n):
                    aa=cf[k]-(C[k]@f-C[k,k]*f[k]);hi=law(k,aa)
                    f[k]=brentq(lambda z:z-law(k,aa-C[k,k]*z),0,hi,xtol=1e-13) if hi>0 else 0.
                d=cf-C@f
                if max(abs(f[k]-law(k,d[k])) for k in range(n))<1e-9:break
            else:raise RuntimeError('contact convergence')
        jf=j0-R@(T@f);ds=[];dforces={}
        for j,a in enumerate(g):
            lev=levels[j]
            if lev:
                Q,_,c=localDamper[j,lev];contacts=-Q@(free[j][1:]+a.H[1:,0]*jf[j]);dforces[j]=(contacts,c)
            else:contacts=f[slices[j]] if j in live else np.zeros(a.P.shape[1]-1)
            ds.append(a.step(np.r_[jf[j],contacts]))
            if j in live:
                ft=float(contacts.sum());x[j]+=h*v[j]-h*h*ft/(2*masses[j]);v[j]-=h*ft/masses[j]
                rec=live[j];rec['peakN']=max(rec['peakN'],ft);rec['impulseNs']+=h*ft
                if ft>1e-8:
                    if rec['first'] is None:rec['first']=i
                    rec['last']=i
        v0=b.v.copy() if sink is not None else None
        db=b.step(-jf)
        if sink is not None:sink((b.v-v0)/h)
        dr=rel()-r0;dj=CJ*(dr@dr)/h;jl+=dj
        maxjoint=max(maxjoint,float(np.max(abs(jf+KJ*(r0+dr/2)+CJ*dr/h))))
        pos1=positions();d1=np.array([x[j]-pos1[j][l+1] for j,l in zip(owners,local)])
        for j,(force,c) in dforces.items():
            delta=pos1[j][1:]-pos[j][1:];loss=float(c*(delta@delta)/h)
            maxDamperResidual=max(maxDamperResidual,float(np.max(abs(force+c*delta/h))))
            maxDamperWorkResidual=max(maxDamperWorkResidual,abs(float(force@delta)+loss))
            damperLoss[j]+=loss;minloss=min(minloss,loss)
        dl=sum(float(f[k])*(d1[k]-d0[k])-potential(d1[k],ks[k])+potential(d0[k],ks[k]) for k in range(n));felt+=dl
        assert all(f[k]==0 for k in range(n) if d0[k]<=0 and d1[k]<=0)
        assert np.isfinite(f).all() and np.all(f>=0)
        maxres=max(maxres,max((abs(f[k]-law(k,d1[k])) for k in range(n)),default=0.))
        if diagnostic is not None:diagnostic(i,g,b,jf,f,owners,pos,pos1)
        E=energy(pos1);maxinc=max(maxinc,E-old);minloss=min(minloss,*ds,db,dj,dl)
        for j in active:
            sl=slices[j];rec=live[j]
            if rec['first'] is not None and v[j]<0 and np.all(f[sl]==0) and np.all(d1[sl]<=-.0002):
                carry=.5*masses[j]*v[j]**2;removed+=carry
                rec.update(retireSample=i,reboundJ=carry,durationMs=(rec['last']-rec['first']+1)*1000/sr)
                del live[j]
        E=energy(pos1)
        maxbal=max(maxbal,abs(injected-E-removed-felt-jl-b.loss-sum(a.loss for a in g)-float(damperLoss.sum())))
        peakBoard=max(peakBoard,b.energy())
        if retain_trace and (i+1)%(sr//1000)==0:trace.append([a.P[:,0]@a.q for a in g]+(b.P.T@b.q).tolist())
    assert not live and len(history)==len(events) and all(r['first'] is not None and 'retireSample' in r for r in history)
    peak=max(r['peakN'] for r in history)
    assert maxbal<=max(1e-10,1e-7*injected) and maxinc<=1e-11 and minloss>=-1e-11 and maxres<=1e-7*max(1,peak) and maxjoint<1e-7
    assert peakBoard>0 and b.loss>0
    assert maxDamperResidual<=1e-7 and maxDamperWorkResidual<=1e-11
    if mode=="bypass":assert not np.any(damperLoss)
    return dict(keys=keys,sr=sr,events=history,mode=mode,damperC=damperC,releases=[list(x) for x in releases],damperLossJ=float(damperLoss.sum()),damperGroupLossJ=damperLoss.tolist(),maxDamperResidual=maxDamperResidual,maxDamperWorkResidual=maxDamperWorkResidual,injectedJ=injected,reboundRemovedJ=removed,mechanicalJ=mech(),boardJ=b.energy(),boardLoss=b.loss,groupLoss=sum(a.loss for a in g),groupJ=[a.energy() for a in g],feltJ=felt,jointLoss=jl,maxBalance=maxbal,maxIncrease=maxinc,minLoss=minloss,maxResidual=maxres,maxJointResidual=maxjoint,trace=trace)
