"""Event-driven relaunch after capture; persistent felt memory and explicit energy injection.
Launch gap measured from nearest current wire; no calibrated repetition action.
"""
import numpy as np
from pathlib import Path
import json, time, hashlib, os
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

def sequential(a,P,groups,keys,launches,N,reverse=False,command=None,output=None,stop=None,resume=False,commands=None,command_log=None,signature=None):
    h=a.h;groups=np.asarray(groups,int);n=len(groups);nh=len(keys)
    assert P.shape==(len(a.q),n) and set(groups)==set(range(nh))
    pars=[params(k,int(np.count_nonzero(groups==j))) for j,k in enumerate(keys)];mass=np.array([v[0] for v in pars]);felts=[pars[j][1] for j in groups];B=np.eye(nh)[groups]
    C=P.T@(a.solve(P) if hasattr(a,"solve") else lu_solve(a.fm,P));G=h*(C+h/2*(B/mass)@B.T);assert np.linalg.eigvalsh((G+G.T)/2)[0]>0
    x=np.full(nh,-.0001);v=np.zeros(nh);z=np.zeros(n);active=np.zeros(nh,bool);touched=np.zeros(nh,bool);capture=[];events=[];pending={};current=np.full(nh,-1,int)
    for j,(step,key,speed) in enumerate(launches):
        if not 0<=step<N or key not in keys or not np.isfinite(speed) or speed<=0:raise ValueError("invalid launch")
        pending.setdefault(step,[]).append((j,keys.index(key),speed))
    Eref=sum(.5*mass[keys.index(k)]*s*s for _,k,s in launches)
    E0=0.;loss=catch=dm=dc=we=err=ce=fr=continuity=workerr=0.;minwe=0.;sweeps=concurrent=0;out=Path(output);out.mkdir(parents=True,exist_ok=resume)
    shapes=dict(force=(N,n),compression=(N,n),velocity=(N,len(a.q)),flow=(N,*a.e.history().shape),ledger=(N,11))
    arrays={k:(np.load(out/(k+'.npy'),mmap_mode='r+',allow_pickle=False) if resume else np.lib.format.open_memmap(out/(k+'.npy'),mode='w+',dtype=np.float64,shape=shape)) for k,shape in shapes.items()}
    assert all(arrays[k].shape==shape and arrays[k].dtype==np.float64 for k,shape in shapes.items())
    F_all=arrays['force'];positions=arrays['compression'];states=arrays['velocity'];flows=arrays['flow'];ledger=arrays['ledger'];start=time.perf_counter()
    # Only this opt-in executor restores explicit numeric states, never pickle.
    begin=0; stop=N if stop is None else stop; assert 0<stop<=N
    cav=a.c.obj.c; ext=a.e.obj
    meta_path=out/'restart.json'
    if resume:
        meta=json.loads(meta_path.read_text()); assert meta['signature']==signature and meta['N']==N
        state_name=f"restart-{meta['step']}.npz"; assert meta['state_file']==state_name
        state_path=out/state_name
        with state_path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==meta['state_sha256']
        begin=meta['step'];assert 0<begin<stop<=N
        # Verify written prefix arrays before using state; no uninitialized suffix is hashed.
        for k,arr in arrays.items():
            hh=hashlib.sha256()
            for j in range(0,begin,1200):hh.update(np.ascontiguousarray(arr[j:min(j+1200,begin)]).tobytes())
            assert hh.hexdigest()==meta['prefix_sha256'][k],k
        with np.load(state_path,allow_pickle=False) as ss:
            earlier=[(i,t) for i,t in commands.items() if i<begin]
            if earlier:
                _,(held,pedal)=max(earlier,key=lambda t:t[0]);a.command(held,pedal)
            assert np.array_equal(a.fractions,ss['fractions'])
            for target,key in ((a.q,'q'),(a.v,'mechanical_v'),(cav.x,'cavity_x'),(cav.v,'cavity_v'),(ext.X0,'exterior_x0'),(ext.X1,'exterior_x1'),(ext.ring,'exterior_ring')):
                assert target.shape==ss[key].shape;target[:]=ss[key]
            ext.t=int(ss['exterior_t']);assert ext.t==begin
            a.c.h=None;a.e.h=None
            x,v,z,active,touched,current,G=[ss[k].copy() for k in ('hammer_x','hammer_v','felt_z','active','touched','current','G')]
        capture=meta['captures'];events=meta['launches'];command_log.extend(meta['commands'])
        E0,loss,catch,dm,dc,we,err,ce,fr,continuity,workerr,minwe,sweeps,concurrent=meta['accumulators']
    for step in range(begin,stop):
        if command is not None and command(a,step):
            C=P.T@a.solve(P);G=h*(C+h/2*(B/mass)@B.T);assert np.linalg.eigvalsh((G+G.T)/2)[0]>0
        for eid,j,speed in pending.get(step,[]):
            if active[j]:raise ValueError("hammer has not been captured")
            mask=groups==j;wirepos=P[:,mask].T@a.q; x[j]=wirepos.min()-.0001; v[j]=speed; active[j]=True; touched[j]=False; current[j]=eid
            injection=.5*mass[j]*speed**2; E0+=injection
            events.append(dict(id=eid,key=keys[j],step=step,speed=speed,energy=float(injection),memory=z[mask].tolist(),gap=float(np.min(wirepos-x[j]))))
        d0=np.where(active[groups],x[groups]-P.T@a.q,0.);first=[relax(d,b,h/2,f) for d,b,f in zip(d0,z,felts)];zz=np.array([b[0] for b in first]);loss+=sum(b[1] for b in first)
        ids=np.flatnonzero(active[groups]);F=np.zeros(n);dx=np.zeros(nh)
        if len(ids):
            free=d0[ids]+h*(v[groups[ids]]-(P.T@a.free())[ids]);g=G[np.ix_(ids,ids)];F[ids],sw,re=solve(d0[ids],free,zz[ids],g,[felts[j] for j in ids],reverse);sweeps=max(sweeps,sw);fr=max(fr,re)
            total=B.T@F;dx=h*v-h*h*total/(2*mass);x+=dx;v-=h*total/mass;touched|=total>0
        y=a.step(P@F);d1=np.where(active[groups],x[groups]-P.T@a.q,0.)
        if len(ids):
            ce=max(ce,float(np.max(abs(d1[ids]-(free-g@F[ids])))));workerr=max(workerr,abs(y['w']-float(F@(dx[groups]-(d1-d0))))/Eref)
        second=[relax(d,b,h/2,f) for d,b,f in zip(d1,zz,felts)];z=np.array([b[0] for b in second]);loss+=sum(b[1] for b in second)
        velocity=P.T@a.v
        for j in np.flatnonzero(active):
            mask=groups==j
            if touched[j] and v[j]<0 and np.all(d1[mask]<=0) and np.all(v[j]-velocity[mask]<=0):
                catch+=.5*mass[j]*v[j]**2;v[j]=0.;active[j]=False;capture.append(dict(id=int(current[j]),key=keys[j],step=step+1));d1[mask]=0.
        dm+=y['dm'];dc+=y['dc'];we+=y['we'];minwe=min(minwe,we);continuity=max(continuity,y['continuity']);stored=y['Em']+y['Ei']+.5*mass@(v*v)+sum(energy(d,b,f) for d,b,f in zip(d1,z,felts));err=max(err,abs(stored+loss+catch+dm+dc+we-E0)/Eref)
        ledger[step]=[y['Em'],y['Ei'],dm,dc,we,loss,catch,stored,err,y['dm'],E0];assert y['dm']>=-1e-18
        concurrent=max(concurrent,int(np.count_nonzero(B.T@F>0)));F_all[step]=F;positions[step]=d1;states[step]=a.v;flows[step]=y['u']
        if (step+1)%19200==0 or step+1==stop:
            for arr in arrays.values():arr.flush()
            progress=dict(steps=step+1,elapsed=time.perf_counter()-start,energy_error=float(err),continuity=continuity,captures=capture.copy(),launches=events.copy(),injected_energy=float(E0),final_mechanical_energy=float(y['Em']),final_cavity_energy=float(y['Ei']),minimum_exterior_work=float(minwe/Eref),compression_residual=ce,work_error=float(workerr),active_hammers=active.tolist())
            tmp=out/'progress.tmp';tmp.write_text(json.dumps(progress,indent=2));tmp.replace(out/'progress.json');print('PROGRESS',json.dumps(progress),flush=True)
    if stop<N:
        assert a.c.h is None and a.e.h is None and ext.t==stop
        # Atomic files; metadata contains exact digest of state and all prefix arrays.
        state_path=out/f'restart-{stop}.npz';assert not state_path.exists();tmp=out/f'restart-{stop}.tmp.npz';np.savez(tmp,q=a.q,mechanical_v=a.v,cavity_x=cav.x,cavity_v=cav.v,exterior_x0=ext.X0,exterior_x1=ext.X1,exterior_ring=ext.ring,exterior_t=ext.t,hammer_x=x,hammer_v=v,felt_z=z,active=active,touched=touched,current=current,G=G,fractions=a.fractions)
        with tmp.open('rb') as f:state_hash=hashlib.file_digest(f,'sha256').hexdigest()
        hashes={}
        for k,arr in arrays.items():
            hh=hashlib.sha256()
            for j in range(0,stop,1200):hh.update(np.ascontiguousarray(arr[j:min(j+1200,stop)]).tobytes())
            hashes[k]=hh.hexdigest()
        meta=dict(signature=signature,N=N,step=stop,state_file=state_path.name,state_sha256=state_hash,prefix_sha256=hashes,captures=capture,launches=events,commands=command_log,accumulators=[float(q) for q in [E0,loss,catch,dm,dc,we,err,ce,fr,continuity,workerr,minwe]]+[int(sweeps),int(concurrent)])
        tmp.replace(state_path)
        # Versioned snapshot and immutable metadata keep earlier valid restart points.
        record=out/f'restart-{stop}.json';assert not record.exists();temp=out/f'restart-{stop}.tmp.json';temp.write_text(json.dumps(meta,indent=2));temp.replace(record)
        temp=out/'restart.tmp.json';temp.write_text(json.dumps(meta,indent=2));temp.replace(meta_path)
        return None,arrays
    F=F_all;assert np.isfinite(F).all() and np.min(F)>=0 and len(capture)==len(launches) and err<1e-8 and ce<1e-12 and workerr<1e-8 and minwe/Eref>=-1e-10 and continuity<1e-10,(err,ce,workerr,capture)
    result=dict(keys=list(keys),launches=events,rate=round(1/h),blocks=N,coordinates=len(a.q),injected_energy=float(E0),energy_error=float(err),compression_residual=ce,force_residual=fr,work_error=float(workerr),continuity=continuity,minimum_exterior_work=float(minwe/Eref),max_sweeps=sweeps,captures=capture,concurrent_hammers=concurrent,peak_force=(F@B).max(0).tolist(),impulse=(h*(F@B).sum(0)).tolist(),felt_loss=float(loss),catch_loss=float(catch),mechanical_loss=float(dm),cavity_loss=float(dc),exterior_work=float(we),final_mechanical_energy=float(y['Em']),final_cavity_energy=float(y['Ei']))
    return result,arrays
