"""G3.14d.19: consolidate existing dry energy attribution, without rerendering.
Net window work is not gross transfer. No wet/dry causal attribution."""
import argparse,csv,json,math
from pathlib import Path
from regional_evidence import load,IDENTITY

TIMES=(1,2,5,10,15,20,30,40)
FIELDS=('energyFraction','lossFraction','netBridgeWorkFraction','positiveWindowNetFraction','negativeWindowNetFraction')

def aggregate(row,key):
    ids=row['components'];n=len(ids);initial=row['initialEnergyFraction'];E=row['initialEnergyJ']
    if n!=11 or ids[0]!='board' or len(set(ids))!=n or len(initial)!=n or E<=0 or not math.isfinite(E):raise ValueError('component identity')
    if not all(math.isfinite(x) and x>=-1e-10 for x in initial) or abs(sum(initial)-1)>1e-8:raise ValueError('initial energy')
    struck=[i for i,name in enumerate(ids) if name.startswith(f'k{key}-')]
    if not struck:raise ValueError('missing struck group')
    other=[i for i in range(1,n) if i not in struck]
    groups={'board':[0],'struckWires':struck,'otherWires':other}
    previous=None;maxerr=0.;series=[]
    for s in row['snapshots']:
        t=s['timeS'];a=[s[f] for f in FIELDS]
        if not math.isfinite(t) or not 0<t<=40 or previous is not None and t<=previous['timeS']:raise ValueError('snapshot order')
        if any(len(v)!=n or not all(math.isfinite(x) for x in v) for v in a):raise ValueError('snapshot data')
        e,l,w,p,m=a
        err=max(abs(sum(e)+sum(l)-1),abs(sum(w)),
            max(abs(e[i]-initial[i]+l[i]-w[i]) for i in range(n)),
            max(abs(p[i]-m[i]-w[i]) for i in range(n)))
        if min(e+l+p+m)<-1e-10:raise ValueError('negative component')
        if previous is not None:
            for f in (FIELDS[1],FIELDS[3],FIELDS[4]):
                if min(x-y for x,y in zip(s[f],previous[f]))<-1e-10:raise ValueError('nonmonotonic cumulative work')
        maxerr=max(maxerr,err)
        if err>1e-8:raise ValueError('partition identity')
        series.append(dict(timeS=t,groups={name:dict(initialFraction=sum(initial[i] for i in ii),
            **{f:sum(s[f][i] for i in ii) for f in FIELDS}) for name,ii in groups.items()}))
        previous=s
    if not series or series[-1]['timeS']!=40:raise ValueError('incomplete tail')
    sampled=[]
    for t in TIMES:
        s=next((v for v in series if v['timeS']>=t),None)
        if s is None or s['timeS']-t>.051:raise ValueError('snapshot coverage')
        sampled.append(dict(requestedS=t,**s))
    return dict(key=key,variant=row['variant'],speed=row['speed'],initialEnergyJ=E,maximumIdentityError=maxerr,
        initialGroups={name:sum(initial[i] for i in ii) for name,ii in groups.items()},samples=sampled)

def main():
    p=argparse.ArgumentParser();p.add_argument('--bridge',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    cases=[];identity=None;hashes={}
    for key in (48,60):
        s,rows,h=load(a.bridge/f'G3-bridge-energy-{key}'/'bridge_energy.json',key,True)
        current=tuple(s[k] for k in IDENTITY)
        if identity is not None and current!=identity:raise ValueError('source identity')
        identity=current;hashes[str(key)]=h
        for row in rows.values():
            case=aggregate(row,key);cases.append(case)
            print('G3_LOSS_ATTRIBUTION_CASE '+json.dumps(case,allow_nan=False),flush=True)
    a.out.mkdir(parents=True,exist_ok=True)
    summary=dict(gate=True,diagnosticOnly=True,cases=len(cases),sampleTimes=list(TIMES),
        acousticFeedbackIncluded=False,selectedParameters=None,audibleSustainMeasured=False,
        netWindowWorkNotGrossTransfer=True,initialEnergyReference='30ms after attack',
        maximumIdentityError=max(v['maximumIdentityError'] for v in cases),
        provenance=dict(zip(IDENTITY,identity)),manifestSha256=hashes)
    (a.out/'loss_attribution.json').write_text(json.dumps(dict(summary=summary,cases=cases),indent=2,allow_nan=False))
    with (a.out/'loss_attribution.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(['key','variant','speed','requestedS','timeS','component','initialEnergyJ','initialFraction',*FIELDS])
        for c in cases:
            for s in c['samples']:
                for name,v in s['groups'].items():
                    w.writerow([c['key'],c['variant'],c['speed'],s['requestedS'],s['timeS'],name,c['initialEnergyJ'],v['initialFraction'],*(v[k] for k in FIELDS)])
    print('G3_LOSS_ATTRIBUTION_GATE '+json.dumps(summary,allow_nan=False),flush=True)
if __name__=='__main__':main()
