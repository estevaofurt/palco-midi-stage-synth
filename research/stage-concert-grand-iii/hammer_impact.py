"""G3.02b mechanical impact fixture, not a complete string or piano solver.
Discrete gradient contact, implicit midpoint linear target, independent felt memory.
"""
import argparse,json,math
from pathlib import Path
from scipy.optimize import brentq
import numpy as np
from felt_law import params,energy,relax,frozen_force
ROOT=Path(__file__).parent
def impact(r,s,c,sr,speed,kind,*,stagger=False,propagator='midpoint'):
    hm,f=params(r['key'],r['count'],s,c);m=hm['massKg'];N=r['count'];h=1/sr
    if kind not in ('rigid','elastic') or sr<=0 or speed<=0:raise ValueError('fixture domain')
    if propagator not in ('midpoint','exact'):raise ValueError('propagator')
    if stagger and N==1:raise ValueError('stagger fixture needs multiple contacts')
    # Diagnostic oscillator at nominal f0. For a uniform simply supported string
    # first-mode port effective mass = mu*L/(2 sin^2(pi*s/L)).
    # For wound strings this is only a proxy, not the nonuniform eigenbasis.
    mt=r['groupVibratingMassKg']/N/(2*math.sin(math.pi*r['strikeFraction'])**2)
    kt=mt*(2*math.pi*r['nominalHz'])**2
    den=1+h*h*kt/(4*mt);g=h*h/(2*mt*den) if kind=='elastic' else 0.
    omega=math.sqrt(kt/mt);co=math.cos(omega*h);si=math.sin(omega*h);J=si/omega
    if kind=='elastic' and propagator=='exact':g=2*math.sin(omega*h/2)**2/(mt*omega**2)
    gh=h*h/(2*m)
    gaps=[i*30e-6 if stagger else 0. for i in range(N)]
    y=[0.]*N;u=[0.]*N;z=[0.]*N;x=0.;v=speed
    E0=.5*m*speed*speed;loss=impulse=peak=0.;maxbal=maxinc=maxres=0.;previous=E0
    maxCompression=0.;contactSamples=0;started=False;separated=False
    perImpulse=[0.]*N;perPeak=[0.]*N
    for i in range(int(.04*sr)):
        d0=[x-y[j]-gaps[j] for j in range(N)]
        for j in range(N):
            z[j],l,e=relax(d0[j],z[j],h/2,f);loss+=l;maxres=max(maxres,abs(e))
        xf=x+h*v
        yf=[y[j]+(h*u[j]-h*h*kt*y[j]/(2*mt))/den if kind=='elastic' else 0. for j in range(N)]
        if kind=='elastic' and propagator=='exact':yf=[co*y[j]+J*u[j] for j in range(N)]
        free=[xf-yf[j]-gaps[j] for j in range(N)]
        def per(total):
            result=[]
            for j in range(N):
                D=free[j]-gh*total
                hi=frozen_force(d0[j],D,z[j],f)
                if hi<=0:result.append(0.);continue
                if g==0:result.append(hi);continue
                fun=lambda F:F-frozen_force(d0[j],D-g*F,z[j],f)
                result.append(brentq(fun,0.,hi,xtol=1e-12) if fun(hi)>0 else hi)
            return result
        hi=sum(per(0.))
        if hi>0:
            fun=lambda total:total-sum(per(total))
            total=brentq(fun,0.,hi,xtol=1e-12) if fun(hi)>0 else hi
            F=per(total)
        else:F=[0.]*N
        total=sum(F)
        x1=xf-gh*total;v1=v-h*total/m
        y1=[yf[j]+g*F[j] for j in range(N)]
        u1=[2*(y1[j]-y[j])/h-u[j] if kind=='elastic' else 0. for j in range(N)]
        if kind=='elastic' and propagator=='exact':u1=[-omega*si*y[j]+co*u[j]+J*F[j]/mt for j in range(N)]
        d1=[x1-y1[j]-gaps[j] for j in range(N)]
        for j in range(N):
            assert F[j]>=0
            z[j],l,e=relax(d1[j],z[j],h/2,f);loss+=l;maxres=max(maxres,abs(e))
            perImpulse[j]+=h*F[j];perPeak[j]=max(perPeak[j],F[j])
        x,v,y,u=x1,v1,y1,u1
        Es=.5*sum(mt*q*q+kt*p*p for q,p in zip(u,y)) if kind=='elastic' else 0.
        Ef=sum(energy(d,zj,f) for d,zj in zip(d1,z))
        Eh=.5*m*v*v;E=Eh+Es+Ef
        maxbal=max(maxbal,abs(E+loss-E0));maxinc=max(maxinc,E-previous);previous=E
        impulse+=h*total;peak=max(peak,total);maxCompression=max(maxCompression,max(d1))
        if total>0:contactSamples+=1;started=True
        # Report first complete separation, not subsequent action/catcher or recollision.
        if started and max(d1)<=0 and v<0 and all(v-q<=0 for q in u):
            separated=True;break
    assert started and separated and v<0,(r['key'],speed,kind,stagger,v,max(d1))
    assert maxbal<=max(1e-10,E0*1e-7) and maxinc<=1e-11 and maxres<=1e-11
    impulseError=abs(m*(speed-v)-impulse)
    assert impulseError<=1e-10 and loss>=0 and peak>0
    assert abs(sum(perImpulse)-impulse)<=1e-10
    if not stagger:assert max(perImpulse)-min(perImpulse)<=1e-10
    return dict(key=r['key'],kind=kind,propagator=propagator,stagger=stagger,sampleRateHz=sr,speedMps=speed,contacts=N,
        injectedJ=E0,hammerReboundJ=Eh,targetJ=Es,storedFeltJ=Ef,lossJ=loss,
        maxBalanceJ=maxbal,maxIncreaseJ=maxinc,maxRelaxResidualJ=maxres,impulseErrorNs=impulseError,
        peakForceN=peak,impulseNs=impulse,contactDurationMs=1000*contactSamples/sr,
        maxCompressionM=maxCompression,reboundMps=-v,perImpulseNs=perImpulse,perPeakN=perPeak,
        targetMassKg=mt if kind=='elastic' else None,targetStiffnessNm=kt if kind=='elastic' else None)
def compare(a,b):
    keys=('peakForceN','impulseNs','reboundMps','lossJ','maxCompressionM')
    diffs={k:abs(a[k]-b[k])/max(abs(b[k]),1e-12) for k in keys}
    if b['kind']=='elastic':diffs['targetJ']=abs(a['targetJ']-b['targetJ'])/max(b['targetJ'],1e-12)
    duration=abs(a['contactDurationMs']-b['contactDurationMs'])
    return dict(relative=diffs,durationDeltaMs=duration,gate=max(diffs.values())<=.05 and duration<=.1)
def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',type=Path,required=True);p.add_argument('--felt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    scale=json.loads(a.scale.read_text());fproof=json.loads(a.felt.read_text());s=json.loads((ROOT/'physical_sources.json').read_text());c=json.loads((ROOT/'felt_hypothesis.json').read_text())
    assert scale['version']=='G3-scale-hypothesis-02' and scale['summary']['gate'] and fproof['summary']['gate']
    rows=[]
    for key in (21,30,49,60,72,84,108):
        r=scale['rows'][key-21]
        for speed in c['impactSpeedsMps']:
            for kind in ('rigid','elastic'):
                lo=impact(r,s,c,96000,speed,kind);hi=impact(r,s,c,192000,speed,kind);conv=compare(lo,hi)
                rows.append(dict(lo=lo,hi=hi,convergence=conv))
        if r['count']>1:
            lo=impact(r,s,c,96000,1.,'elastic',stagger=True);hi=impact(r,s,c,192000,1.,'elastic',stagger=True)
            rows.append(dict(lo=lo,hi=hi,convergence=compare(lo,hi)))
    summary=dict(pairs=len(rows),simulations=2*len(rows),passPairs=sum(r['convergence']['gate'] for r in rows),
        maxBalanceJ=max(r[q]['maxBalanceJ'] for r in rows for q in ('lo','hi')),
        maxImpulseErrorNs=max(r[q]['impulseErrorNs'] for r in rows for q in ('lo','hi')),
        maxRelative=max(v for r in rows for v in r['convergence']['relative'].values()),
        maxDurationDeltaMs=max(r['convergence']['durationDeltaMs'] for r in rows),
        gate=all(r['convergence']['gate'] for r in rows),impactReady=False)
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'impact.json').write_text(json.dumps(dict(summary=summary,rows=rows,scope='rigid and single-mode independent targets; not coupled strings, action or audio'),indent=2,allow_nan=False))
    print('G3_IMPACT_GATE '+json.dumps(summary),flush=True)
    for row in rows:
        if not row['convergence']['gate'] or (row['hi']['speedMps']==1 and not row['hi']['stagger']):print('G3_IMPACT_CASE '+json.dumps(row),flush=True)
    assert summary['gate'],'fixture convergence'
if __name__=='__main__':main()
