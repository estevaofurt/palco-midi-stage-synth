"""Simultaneous historical felt contacts; shared mass per hammer, separate memory per wire.
All launches at t=0; stationary dampers lifted on struck keys. No MIDI/repedal model.
"""
import numpy as np
from scipy.linalg import lu_solve
from scipy.optimize import brentq
from hammer import params,relax,force,energy

def solve(d,free,z,G,felts,reverse=False):
    F=np.zeros(len(d))
    for sweep in range(1,401):
        for j in (range(len(d)-1,-1,-1) if reverse else range(len(d))):
            b=free[j]-G[j]@F+G[j,j]*F[j];hi=force(d[j],b,z[j],felts[j])
            fun=lambda x:x-force(d[j],b-G[j,j]*x,z[j],felts[j])
            F[j]=brentq(fun,0.,hi,xtol=1e-13) if hi>0 and fun(hi)>0 else hi
        target=np.array([force(a,b,c,f) for a,b,c,f in zip(d,free-G@F,z,felts)])
        residual=float(np.max(abs(F-target)))
        if residual<=1e-11*max(1.,float(F.max())):return F,sweep,residual
    raise ValueError('simultaneous contact failed')

def simultaneous(a,P,groups,keys,speeds,N,reverse=False):
    h=a.h;groups=np.asarray(groups,int);speeds=np.asarray(speeds,float);n=len(groups);nh=len(keys)
    assert P.shape==(len(a.q),n) and set(groups)==set(range(nh)) and len(speeds)==nh and np.all(speeds>0)
    pars=[params(k,int(np.count_nonzero(groups==j))) for j,k in enumerate(keys)];mass=np.array([v[0] for v in pars]);felts=[pars[j][1] for j in groups];B=np.eye(nh)[groups]
    C=P.T@lu_solve(a.fm,P);G=h*(C+h/2*(B/mass)@B.T);assert np.linalg.eigvalsh((G+G.T)/2)[0]>0
    x=np.full(nh,-.0001);v=speeds.copy();z=np.zeros(n);active=np.ones(nh,bool);touched=np.zeros(nh,bool);capture=np.zeros(nh,int)
    E0=.5*mass@(v*v);loss=catch=dm=dc=we=err=ce=fr=continuity=workerr=0.;minwe=0.;sweeps=concurrent=0;forces=[];positions=[];states=[];flows=[]
    for step in range(N):
        d0=np.where(active[groups],x[groups]-P.T@a.q,0.);first=[relax(d,b,h/2,f) for d,b,f in zip(d0,z,felts)];zz=np.array([b[0] for b in first]);loss+=sum(b[1] for b in first)
        ids=np.flatnonzero(active[groups]);F=np.zeros(n);dx=np.zeros(nh)
        if len(ids):
            free=d0[ids]+h*(v[groups[ids]]-(P.T@a.free())[ids]);g=G[np.ix_(ids,ids)];F[ids],sw,re=solve(d0[ids],free,zz[ids],g,[felts[j] for j in ids],reverse);sweeps=max(sweeps,sw);fr=max(fr,re)
            total=B.T@F;dx=h*v-h*h*total/(2*mass);x+=dx;v-=h*total/mass;touched|=total>0
        y=a.step(P@F);d1=np.where(active[groups],x[groups]-P.T@a.q,0.)
        if len(ids):
            ce=max(ce,float(np.max(abs(d1[ids]-(free-g@F[ids])))));workerr=max(workerr,abs(y['w']-float(F@(dx[groups]-(d1-d0))))/E0)
        second=[relax(d,b,h/2,f) for d,b,f in zip(d1,zz,felts)];z=np.array([b[0] for b in second]);loss+=sum(b[1] for b in second)
        velocity=P.T@a.v
        for j in np.flatnonzero(active):
            mask=groups==j
            if touched[j] and v[j]<0 and np.all(d1[mask]<=0) and np.all(v[j]-velocity[mask]<=0):
                catch+=.5*mass[j]*v[j]**2;v[j]=0.;active[j]=False;capture[j]=step+1;d1[mask]=0.
        dm+=y['dm'];dc+=y['dc'];we+=y['we'];minwe=min(minwe,we);continuity=max(continuity,y['continuity']);stored=y['Em']+y['Ei']+.5*mass@(v*v)+sum(energy(d,b,f) for d,b,f in zip(d1,z,felts));err=max(err,abs(stored+loss+catch+dm+dc+we-E0)/E0)
        concurrent=max(concurrent,int(np.count_nonzero(B.T@F>0)));forces.append(F);positions.append(d1);states.append(a.v.copy());
        if 'u' in y:flows.append(y['u'])
    F=np.array(forces);assert np.isfinite(F).all() and np.min(F)>=0 and np.all(capture>0) and err<1e-8 and ce<1e-12 and workerr<1e-8 and minwe/E0>=-1e-10 and continuity<1e-10,(err,ce,workerr,capture)
    result=dict(keys=list(keys),speeds=speeds.tolist(),rate=round(1/h),blocks=N,coordinates=len(a.q),initial_energy=float(E0),energy_error=float(err),compression_residual=ce,force_residual=fr,work_error=float(workerr),continuity=continuity,minimum_exterior_work=float(minwe/E0),max_sweeps=sweeps,capture_steps=capture.tolist(),concurrent_hammers=concurrent,peak_force=(F@B).max(0).tolist(),impulse=(h*(F@B).sum(0)).tolist(),felt_loss=float(loss),catch_loss=float(catch),mechanical_loss=float(dm),cavity_loss=float(dc),exterior_work=float(we),final_mechanical_energy=float(y['Em']),final_cavity_energy=float(y['Ei']))
    return result,dict(force=F,compression=np.array(positions),velocity=np.array(states),flow=np.array(flows))
