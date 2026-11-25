"""G3.01b analytical scale hypothesis, no instrument simulation or audio."""
import argparse,json,math
from pathlib import Path
ROOT=Path(__file__).parent
def interp(k,points):
    for (a,x),(b,y) in zip(points,points[1:]):
        if a<=k<=b:return math.exp(math.log(x)+(math.log(y)-math.log(x))*(k-a)/(b-a))
    raise ValueError('no extrapolation')
def area(d):return math.pi*d*d/4
def wrap_mass(d,w,layers,rho):
    # Close-wound circular wire: pitch=w, circumference at wire centre.
    total=0.
    for i in range(layers):
        mean=d+(2*i+1)*w
        total+=rho*area(w)*math.hypot(1,math.pi*mean/w)
    return total
def winding(d,extra,layers,rho,fraction):
    if extra<=0 or layers not in (1,2) or not 0<fraction<=1:raise ValueError('winding domain')
    lo,hi=1e-9,.0025
    if fraction*wrap_mass(d,hi,layers,rho)<extra:raise ValueError('winding outside bracket')
    for _ in range(70):
        mid=(lo+hi)/2
        if fraction*wrap_mass(d,mid,layers,rho)<extra:lo=mid
        else:hi=mid
    return (lo+hi)/2
def build(c):
    rho,E=c['steel']['density'],c['steel']['young'];cu=c['copper']['density'];q=c['wrappedFraction'];s=c['screen'];t=c['topology']
    rows=[]
    for k in range(21,109):
        f=440*2**((k-69)/12);wrapped=k<=t['wrappedLast'];count=1 if k<=t['single'][1] else 2 if k<=t['double'][1] else 3
        if wrapped:
            L=interp(k,c['wrappedLengthBass'] if k<=t['bassBridgeLast'] else c['wrappedLengthTreble']);d=interp(k,c['wrappedCoreMm'])/1000;T=interp(k,c['wrappedTensionN'])
        else:L=interp(k,c['solidLength']);d=interp(k,c['solidDiameterMm'])/1000
        EI=E*math.pi*d**4/64;core=rho*area(d);bend=math.pi**2*EI/L**2
        if wrapped:
            mu=(T+bend)/(4*L*L*f*f);layers=2 if k<=t['doubleWrapLast'] else 1
            w=winding(d,mu-core,layers,cu,q);actual=core+q*wrap_mass(d,w,layers,cu)
        else:
            mu=core;actual=core;T=4*L*L*f*f*mu-bend;layers=0;w=0.
        B=bend/T;Z=math.sqrt(T*actual);freq=math.sqrt((T+bend)/actual)/(2*L);cents=1200*math.log2(freq/f)
        stress=T/area(d);outer=d+2*layers*w;strike=interp(k,c['strikeFraction'])
        if not (0<L<=s['maxLengthM'] and s['minTensionN']<=T<=s['maxTensionN'] and 0<stress<=s['maxCoreStressPa'] and outer<=s['maxOuterDiameterM'] and abs(cents)<=s['maxFrequencyResidualCents'] and 0<strike<1):raise ValueError(f'domain screen key {k}')
        rows.append(dict(key=k,status='engineering_hypothesis',nominalHz=f,analyticalHz=freq,residualCents=cents,count=count,bridge='bass' if k<=t['bassBridgeLast'] else 'treble',lengthM=L,coreDiameterM=d,wrapLayers=layers,wrapWireDiameterM=w,wrapLengthM=L*q if layers else 0,outerDiameterM=outer,linearDensityKgM=actual,coreMassPerM=core,tensionPerStringN=T,coreStressPa=stress,bendingNm2=EI,inharmonicity=B,impedancePerStringNsM=Z,groupImpedanceNsM=count*Z,groupVibratingMassKg=count*L*actual,strikeFraction=strike,hammerPositionM=L*strike))
    edges=[]
    for a,b in zip(rows,rows[1:]):
        dz=20*math.log10(b['groupImpedanceNsM']/a['groupImpedanceNsM']);br=max(a['inharmonicity']/b['inharmonicity'],b['inharmonicity']/a['inharmonicity'])
        transition=a['count']!=b['count'] or a['bridge']!=b['bridge'] or a['wrapLayers']!=b['wrapLayers']
        edges.append(dict(keys=[a['key'],b['key']],groupImpedanceDeltaDb=dz,inharmonicityRatio=br,transition=transition,review=abs(dz)>s['adjacentGroupImpedanceDb'] or br>s['adjacentInharmonicityRatio'] or transition))
    summary=dict(keys=len(rows),strings=sum(r['count'] for r in rows),wrappedKeys=sum(r['wrapLayers']>0 for r in rows),totalTensionN=sum(r['tensionPerStringN']*r['count'] for r in rows),maxResidualCents=max(abs(r['residualCents']) for r in rows),maxStressPa=max(r['coreStressPa'] for r in rows),reviewEdges=sum(e['review'] for e in edges),gate=True,scaleReady=False)
    return dict(scope=c['status'],version=c['version'],summary=summary,rows=rows,edges=edges,limitations=c['notes'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    report=build(json.loads((ROOT/'scale_hypothesis.json').read_text()));a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'scale.json').write_text(json.dumps(report,indent=2,allow_nan=False))
    print('G3_SCALE_SCREEN '+json.dumps(report['summary']))
    for r in report['rows']:
        if r['key'] in (21,29,30,46,47,49,50,60,72,84,108):print('G3_SCALE_KEY '+json.dumps(r))
    for e in report['edges']:
        if e['review']:print('G3_SCALE_EDGE '+json.dumps(e))
if __name__=='__main__':main()
